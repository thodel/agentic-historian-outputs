"""Performance and accessibility release budgets for issue #227."""

from __future__ import annotations

import json
import re
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_training import (
    _run_page,  # noqa: E402
    TRAINING_PERFORMANCE_BUDGETS,
    _build_rows,
    _render_curves,
    _render_run_report,
    _render_table,
)
from training_contract import CurveEpoch, TrainingContract  # noqa: E402


#: The fixture file carries "name"/"_expect_error" for its harness; the
#: contract rejects unknown fields, so a case must be stripped to the record a
#: producer would actually write.
_HARNESS_KEYS = frozenset({"name", "_expect_error"})


def fixture() -> dict:
    cases = json.loads(
        (ROOT / "tests" / "fixtures" / "training_contract_cases.json").read_text()
    )
    case = next(c for c in cases if c["name"] == "valid completed kraken run")
    return {k: v for k, v in case.items() if k not in _HARNESS_KEYS}


class TrainingPerformanceBudgets(unittest.TestCase):
    def test_representative_report_stays_within_byte_budget(self):
        contract = TrainingContract(fixture())
        row = {
            "contract": contract,
            "status_mod": "ok",
            "status_label": "Abgeschlossen",
        }
        size = len(_render_run_report(row).encode("utf-8"))
        self.assertLessEqual(size, TRAINING_PERFORMANCE_BUDGETS["report_bytes_per_run"])

    def _long_contract(self, count):
        return TrainingContract({
            **fixture(), "epochs": count, "epochs_trained": count,
            "curves": [{"epoch": i, "train_loss": 1 / (i + 1),
                        "val_loss": 1.1 / (i + 1)} for i in range(count)],
        })

    def test_long_svg_series_is_bounded(self):
        count = TRAINING_PERFORMANCE_BUDGETS["svg_points_per_series"] * 4
        markup = _render_curves(self._long_contract(count))
        polylines = re.findall(r'<polyline[^>]+points="([^"]+)"', markup)
        self.assertTrue(polylines)
        for points in polylines:
            self.assertLessEqual(
                len(points.split()),
                TRAINING_PERFORMANCE_BUDGETS["svg_points_per_series"],
            )

    def test_long_exact_table_is_bounded_and_says_so(self):
        """This assertion used to be the opposite, and that was the bug.

        Requiring the table to hold every epoch is what made a valid
        2,000-epoch run a publication blocker: the report reached 183 KB
        against a 128 KB budget and the generator raised, taking the whole
        site build with it. A budget that can only abort is a cliff.

        The table is now an excerpt that says it is one, and the complete
        series stays published verbatim in the run's own training.json.
        """
        count = TRAINING_PERFORMANCE_BUDGETS["svg_points_per_series"] * 4
        markup = _render_curves(self._long_contract(count))

        rows = markup.count('<tr><th scope="row">')
        # Row budget was a budget that aborted, not a cap that preserved endpoints.
        # The fix drops the slice so endpoints always survive; the row count follows
        # from the bucketing strategy and the two forced endpoints (first + last).
        # The real invariant is tested in the assertions below (#252).
        self.assertIn(f"Auszug: {rows} von {count} Epochen", markup)

        # The table must contain the first and last epoch.  The old code sliced
        # the sorted kept-indices to [:limit], which cut off the end when the
        # bucketed extrema already filled the budget and the endpoints pushed
        # it over the limit.  The last epoch was silently dropped (#252).
        epoch_numbers = set(int(m) for m in re.findall(r'<tr><th scope="row">(\d+)</th>', markup))
        self.assertIn(0, epoch_numbers, "first epoch missing from table")
        self.assertIn(count - 1, epoch_numbers, "last epoch missing from table")

    def test_a_short_run_still_shows_every_epoch_without_an_excerpt_notice(self):
        count = 12
        markup = _render_curves(self._long_contract(count))
        self.assertEqual(count, markup.count('<tr><th scope="row">'))
        self.assertNotIn("Auszug:", markup)

    def test_a_very_long_run_publishes_instead_of_aborting_the_build(self):
        """The case that took the build down: every other page went with it."""
        for count in (2000, 20000):
            with self.subTest(epochs=count):
                row = {"contract": self._long_contract(count), "status_mod": "ok",
                       "status_label": "Abgeschlossen", "run_id": "long-run",
                       "model_id": "m-long", "recognition_usages": []}
                size = len(_run_page(row).encode("utf-8"))
                self.assertLessEqual(
                    size, TRAINING_PERFORMANCE_BUDGETS["report_bytes_per_run"],
                    f"a {count}-epoch run still exceeds the report budget, so "
                    "publishing it aborts the entire site build",
                )

    def test_500_run_summary_table_renders_within_budget(self):
        contract = TrainingContract(fixture())
        base = {
            "datasets_cell": "dataset", "status": "completed",
            "status_mod": "ok", "status_label": "Abgeschlossen",
            "engine": "Kraken", "model_id": contract.model_id,
            "epochs": 10, "epochs_trained": 10, "duration": "1h 0m",
            "cer": "5.00%", "wer": "10.00%",
        }
        rows = [{**base, "run_id": f"run-{i}"} for i in range(
            TRAINING_PERFORMANCE_BUDGETS["synthetic_table_runs"]
        )]
        started = time.perf_counter()
        markup = _render_table(rows)
        elapsed_ms = (time.perf_counter() - started) * 1000
        self.assertEqual(markup.count('<tr class="training-table__row'), len(rows))
        self.assertLess(elapsed_ms, TRAINING_PERFORMANCE_BUDGETS["synthetic_table_ms"])


class TrainingAccessibilityBudgets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        contract = TrainingContract(fixture())
        cls.markup = _render_run_report({
            "contract": contract, "status_mod": "ok", "status_label": "Abgeschlossen",
        })
        cls.source = (ROOT / "scripts" / "build_training.py").read_text(encoding="utf-8")

    def test_svg_names_axes_legend_and_exact_table(self):
        self.assertIn('role="img" aria-labelledby=', self.markup)
        self.assertEqual(self.markup.count("<svg"), self.markup.count("<title"))
        self.assertEqual(self.markup.count("<svg"), self.markup.count("<desc"))
        self.assertIn("Epoche", self.markup)
        self.assertIn("training-chart__legend", self.markup)
        self.assertIn("Kurvendaten als Tabelle", self.markup)

    def test_disclosures_have_focus_touch_reflow_and_forced_colors_contracts(self):
        self.assertIn("<details open>", self.markup)
        self.assertIn("min-height: 2.75rem", self.source)
        self.assertIn(":focus-visible", self.source)
        self.assertIn("@media (max-width: 38rem)", self.source)
        self.assertIn("@media (forced-colors: active)", self.source)

    def test_internal_budget_document_is_present(self):
        document = (ROOT / "docs" / "training-performance.md").read_text(encoding="utf-8")
        self.assertIn("250 SVG points", document)
        self.assertIn("128 KB", document)
        self.assertIn("2 MB", document)


if __name__ == "__main__":
    unittest.main()
