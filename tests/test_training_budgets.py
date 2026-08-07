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

from build_training import (  # noqa: E402
    TRAINING_PERFORMANCE_BUDGETS,
    _build_rows,
    _render_curves,
    _render_run_report,
    _render_table,
)
from training_contract import CurveEpoch, TrainingContract  # noqa: E402


def fixture() -> dict:
    cases = json.loads(
        (ROOT / "tests" / "fixtures" / "training_contract_cases.json").read_text()
    )
    return next(case for case in cases if case["name"] == "valid completed kraken run")


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

    def test_long_svg_series_is_bounded_but_table_keeps_every_epoch(self):
        count = TRAINING_PERFORMANCE_BUDGETS["svg_points_per_series"] * 4
        curves = [CurveEpoch(epoch=i, train_loss=1 / (i + 1), val_loss=1.1 / (i + 1))
                  for i in range(count)]
        contract = TrainingContract({**fixture(), "epochs": count, "epochs_trained": count,
                                     "curves": [
                                         {"epoch": c.epoch, "train_loss": c.train_loss,
                                          "val_loss": c.val_loss}
                                         for c in curves
                                     ]})
        markup = _render_curves(contract)
        polylines = re.findall(r'<polyline[^>]+points="([^"]+)"', markup)
        self.assertTrue(polylines)
        for points in polylines:
            self.assertLessEqual(
                len(points.split()),
                TRAINING_PERFORMANCE_BUDGETS["svg_points_per_series"],
            )
        self.assertEqual(markup.count("<tr><th scope=\"row\">"), count)

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
