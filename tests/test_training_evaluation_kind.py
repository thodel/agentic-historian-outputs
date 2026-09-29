"""Line-crop CER and full-page CER are different measurements (#225).

`ketos test` scores line crops cut from ground-truth segmentation. The eval
harness scores whole pages through our own segmentation, so it also pays for
every segmentation error. The two will disagree, often by a lot. The training
integration plan states the requirement directly: they must stay visibly
distinct.

The schema exposed one unlabelled CER/WER pair, and the overview took a single
minimum across every completed run. With a 4% line-crop run and a 19%
full-page run of the same model, that reported "lowest CER: 4.00%" — the
easier measurement, presented as the best model.

Supplementary figures pointed the other way too: the engine reports
accuracies, higher-is-better, sitting in the same list as error rates.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import build_training  # noqa: E402
from training_contract import ContractError, TrainingContract  # noqa: E402


def run(run_id="run-001", cer=0.04, kind="line_crop", segmentation="ground_truth",
        **metric_overrides):
    metrics = {"cer": cer, "wer": cer * 2}
    if kind is not None:
        metrics["evaluation_kind"] = kind
    if segmentation is not None:
        metrics["segmentation"] = segmentation
    metrics.update(metric_overrides)
    return TrainingContract({
        "schema_version": 1, "run_id": run_id, "model_id": f"m-{run_id}",
        "base_model": None, "engine": "kraken",
        "created_at": "2026-01-01T00:00:00+00:00",
        "epochs": 3, "epochs_trained": 3, "status": "completed",
        "datasets": [{"hf_repo": "owner/name"}],
        "metrics": metrics,
    })


def text_of(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


class EvaluationKindContractTests(unittest.TestCase):
    def test_a_reported_error_rate_must_say_what_it_measured(self):
        with self.assertRaises(ContractError) as caught:
            run(kind=None, segmentation=None)
        self.assertIn("evaluation_kind", str(caught.exception))

    def test_both_kinds_are_accepted(self):
        for kind in ("line_crop", "full_page"):
            with self.subTest(kind=kind):
                self.assertEqual(kind, run(kind=kind).metrics["evaluation_kind"])

    def test_an_invented_kind_is_rejected(self):
        with self.assertRaises(ContractError):
            run(kind="whatever")

    def test_an_invented_segmentation_is_rejected(self):
        with self.assertRaises(ContractError):
            run(segmentation="guessed")

    def test_a_run_without_error_rates_needs_no_kind(self):
        """A failed or cancelled run has nothing to label."""
        TrainingContract({
            "schema_version": 1, "run_id": "run-002", "model_id": "m",
            "base_model": None, "engine": "kraken",
            "created_at": "2026-01-01T00:00:00+00:00",
            "epochs": 3, "epochs_trained": 0, "status": "failed",
            "datasets": [{"hf_repo": "owner/name"}],
        })  # must not raise


class EvaluationKindRenderingTests(unittest.TestCase):
    def test_line_crop_says_segmentation_error_is_excluded(self):
        html = build_training._render_metrics(run(kind="line_crop"))
        self.assertIn('data-evaluation-kind="line_crop"', html)
        self.assertIn("Zeilenausschnitte", html)
        self.assertIn("nicht in diese Zahl ein", text_of(html))

    def test_full_page_says_segmentation_error_is_included(self):
        html = build_training._render_metrics(
            run(kind="full_page", segmentation="predicted"))
        self.assertIn('data-evaluation-kind="full_page"', html)
        self.assertIn("Ganze Seite", html)
        self.assertIn("enthalten", text_of(html))

    def test_the_comparability_note_mentions_the_measurement(self):
        html = build_training._render_metrics(run())
        self.assertIn("Messart", text_of(html))

    def test_accuracies_also_state_the_matching_error_rate(self):
        """One direction for comparison, without discarding the engine's number."""
        html = build_training._render_metrics(run(char_accuracy=97.5))
        self.assertIn("97.50%", html)
        self.assertIn("Fehlerrate von 2.50%", text_of(html))


class OverviewGroupingTests(unittest.TestCase):
    def rows(self, *contracts):
        return [{"contract": c, "status": "completed"} for c in contracts]

    def test_best_scores_are_reported_per_measurement(self):
        summary = build_training._render_summary(self.rows(
            run("run-lines", cer=0.04, kind="line_crop"),
            run("run-pages", cer=0.19, kind="full_page", segmentation="predicted"),
        ))
        self.assertIn("(Zeilenausschnitte):** 4.00%", summary)
        self.assertIn("(Ganze Seite):** 19.00%", summary)

    def test_no_single_best_is_taken_across_measurements(self):
        """The bug: 4% and 19% collapsed into one 'lowest CER: 4.00%'."""
        summary = build_training._render_summary(self.rows(
            run("run-lines", cer=0.04, kind="line_crop"),
            run("run-pages", cer=0.19, kind="full_page", segmentation="predicted"),
        ))
        headline = [line for line in summary.splitlines() if "CER" in line]
        self.assertEqual(
            2, len(headline),
            f"expected one best score per measurement, got: {headline}",
        )
        for line in headline:
            self.assertRegex(
                line, r"\((Zeilenausschnitte|Ganze Seite)\)",
                "a best score was reported without saying what it measured",
            )

    def test_one_measurement_still_gets_one_best_score(self):
        summary = build_training._render_summary(self.rows(
            run("run-one", cer=0.08, kind="line_crop"),
            run("run-two", cer=0.05, kind="line_crop"),
        ))
        self.assertIn("(Zeilenausschnitte):** 5.00%", summary)


if __name__ == "__main__":
    unittest.main()
