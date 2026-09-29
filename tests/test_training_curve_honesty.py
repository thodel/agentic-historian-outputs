"""A training chart must not claim more, or less, than its data supports (#227).

Two separate honesty problems meet in the same picture.

**Reduction.** The SVG is capped at a point budget. Uniform sampling met the
budget and deleted exactly what a reader looks at a loss curve for: with 1,000
epochs at 1.0 and one spike to 1,000 at epoch 1, every kept index missed the
spike, the line was flat, and the chart's own caption reported a range of
0.99-1.01 — because the axis was derived from the sampled points too. Nothing
said reduction had happened at all.

**Completeness.** A curve is not automatically every epoch. kraken keeps its
ten best checkpoints and the trainer reads the curve off those filenames,
because ketos renders progress through `rich` and the numbers do not survive a
redirected stdout (serving-atr-inference#38/#51). Ten best epochs drawn as a
line is a different claim from a training curve, and which epochs survived is
itself the finding — late ones mean the run was still improving, early ones
mean it peaked and then got worse. The schema had no way to say so, so a
selection rendered as if it were the whole run.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import build_training  # noqa: E402
from build_training import TRAINING_PERFORMANCE_BUDGETS  # noqa: E402
from training_contract import ContractError, CurveEpoch, TrainingContract  # noqa: E402

LIMIT = TRAINING_PERFORMANCE_BUDGETS["svg_points_per_series"]


def record(**overrides):
    payload = {
        "schema_version": 1, "run_id": "r-1", "model_id": "m",
        "base_model": None, "engine": "kraken",
        "created_at": "2026-01-01T00:00:00+00:00",
        "epochs": 3, "epochs_trained": 3, "status": "completed",
        "datasets": [{"hf_repo": "owner/name"}],
        "curves": [{"epoch": i, "train_loss": 1.0 - i / 10} for i in range(3)],
    }
    payload.update(overrides)
    return TrainingContract(payload)


def description(svg: str) -> str:
    match = re.search(r"<desc[^>]*>(.*?)</desc>", svg, re.S)
    return match.group(1) if match else ""


class ExtremaPreservingReductionTests(unittest.TestCase):
    def spiky(self, count=1000, spike_at=1, spike=1000.0):
        points = [(i, 1.0) for i in range(count)]
        points[spike_at] = (spike_at, spike)
        return points

    def test_an_isolated_spike_survives_reduction(self):
        points = self.spiky()
        drawn = build_training._sample_points(points)
        self.assertEqual(
            1000.0, max(y for _, y in drawn),
            "the single most important value in the series was sampled away",
        )

    def test_an_isolated_trough_survives_reduction(self):
        points = [(i, 1.0) for i in range(1000)]
        points[673] = (673, -5.0)
        drawn = build_training._sample_points(points)
        self.assertEqual(-5.0, min(y for _, y in drawn))

    def test_endpoints_are_kept(self):
        points = [(i, float(i)) for i in range(1000)]
        drawn = build_training._sample_points(points)
        self.assertEqual(points[0], drawn[0])
        self.assertEqual(points[-1], drawn[-1])

    def test_reduction_respects_the_point_budget(self):
        for count in (LIMIT + 1, 1000, 5000):
            with self.subTest(points=count):
                drawn = build_training._sample_points(
                    [(i, float(i % 17)) for i in range(count)])
                self.assertLessEqual(len(drawn), LIMIT)

    def test_short_series_are_returned_untouched(self):
        for count in (0, 1, 2, LIMIT):
            with self.subTest(points=count):
                points = [(i, float(i)) for i in range(count)]
                self.assertEqual(points, build_training._sample_points(points))

    def test_reduction_is_deterministic(self):
        points = self.spiky()
        self.assertEqual(build_training._sample_points(points),
                         build_training._sample_points(points))


class ChartDescriptionTests(unittest.TestCase):
    def curves(self, count=1000, spike=1000.0):
        return [CurveEpoch(epoch=i, train_loss=(spike if i == 1 else 1.0))
                for i in range(count)]

    def test_axis_range_comes_from_the_full_series(self):
        svg = build_training._render_svg_chart(self.curves(), "r-1", "loss")
        text = description(svg)
        self.assertNotIn(
            "1.01", text,
            "the range still describes the sampled points, so the chart "
            "contradicts the table beneath it",
        )
        self.assertIn("e+03", text, f"the spike is missing from the range: {text}")

    def test_reduction_is_disclosed(self):
        text = description(build_training._render_svg_chart(self.curves(), "r-1", "loss"))
        self.assertIn("Messpunkten", text,
                      "the chart drew fewer points than it has and said nothing")

    def test_no_reduction_notice_when_nothing_was_reduced(self):
        short = [CurveEpoch(epoch=i, train_loss=1.0 - i / 100) for i in range(10)]
        text = description(build_training._render_svg_chart(short, "r-1", "loss"))
        self.assertNotIn("Messpunkten", text)


class CurveProvenanceTests(unittest.TestCase):
    """The record must be able to say a curve is a selection, and it must show."""

    PRODUCER_NOTE = ("kraken keeps the top 10 checkpoints, so these are the "
                     "best epochs rather than every epoch.")

    def test_an_incomplete_curve_is_marked_as_a_selection(self):
        html = build_training._render_curve_provenance(record(
            curves_provenance={"complete": False,
                               "source": "checkpoint filenames",
                               "note": self.PRODUCER_NOTE}))
        self.assertIn("Unvollständige Kurve", html)
        self.assertIn("notice--warning", html)
        self.assertIn("checkpoint filenames", html)
        self.assertIn("top 10 checkpoints", html)

    def test_a_complete_curve_says_so(self):
        html = build_training._render_curve_provenance(
            record(curves_provenance={"complete": True}))
        self.assertIn("Vollständige Kurve", html)
        self.assertNotIn("notice--warning", html)

    def test_silence_is_reported_as_unknown_not_as_complete(self):
        html = build_training._render_curve_provenance(record())
        self.assertIn("nicht angegeben", html.casefold())
        self.assertNotIn("Vollständige Kurve", html)

    def test_the_notice_reaches_the_rendered_curves(self):
        html = build_training._render_curves(record(
            curves_provenance={"complete": False, "note": self.PRODUCER_NOTE}))
        self.assertIn("Unvollständige Kurve", html)

    def test_an_incomplete_curve_must_explain_itself(self):
        """`complete: false` with no note overstates nothing but explains nothing."""
        with self.assertRaises(ContractError) as caught:
            record(curves_provenance={"complete": False})
        self.assertIn("note", str(caught.exception))

    def test_complete_must_be_a_boolean(self):
        with self.assertRaises(ContractError):
            record(curves_provenance={"complete": "yes"})

    def test_provenance_must_be_an_object(self):
        with self.assertRaises(ContractError):
            record(curves_provenance=["complete"])


if __name__ == "__main__":
    unittest.main()
