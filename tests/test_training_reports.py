"""Regression tests for training report issues #222–#225."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_training import (  # noqa: E402
    build_training,
    _build_rows,
    _render_curves,
    _render_dataset_panel,
    _render_metrics,
    _render_recognition_usages,
    _render_reproducibility,
    _render_run_report,
    _recognition_usages,
)
from training_contract import ContractError, CurveEpoch, TrainingContract  # noqa: E402
from quality import training_reference_evaluations  # noqa: E402


def valid_case() -> dict:
    cases = json.loads(
        (ROOT / "tests" / "fixtures" / "training_contract_cases.json").read_text(
            encoding="utf-8"
        )
    )
    return next(case for case in cases if case["name"] == "valid completed kraken run")


class AccessibleCurvesTests(unittest.TestCase):
    def test_curves_are_inline_labelled_svg_with_tabular_fallback(self):
        markup = _render_curves(TrainingContract(valid_case()))
        self.assertIn('<svg viewBox="0 0 720 280" role="img"', markup)
        self.assertIn("<title", markup)
        self.assertIn("<desc", markup)
        self.assertIn("Trainingsverlust", markup)
        self.assertIn("Validierungsverlust", markup)
        self.assertIn("stroke-dasharray", (ROOT / "scripts" / "build_training.py").read_text())
        self.assertIn("Kurvendaten als Tabelle", markup)
        self.assertIn('<th scope="col">Epoche</th>', markup)

    def test_missing_curves_are_stated_not_drawn_as_zero(self):
        data = valid_case()
        data["curves"] = None
        markup = _render_curves(TrainingContract(data))
        self.assertIn("keine Kurvendaten", markup)
        self.assertNotIn("<svg", markup)


class DatasetProvenanceTests(unittest.TestCase):
    def test_panel_names_revision_splits_projects_and_counts(self):
        markup = _render_dataset_panel(TrainingContract(valid_case()))
        self.assertIn("dh-unibe/image-text_medieval-scripts_xiv-xv-xvi", markup)
        self.assertIn("/tree/729e9b2721ba2a31901f776368d8aacf0a5e9406", markup)
        self.assertIn("Trainingsprojekte", markup)
        self.assertIn("Evaluationsprojekte", markup)
        self.assertIn("Übersprungene Seiten", markup)
        self.assertIn("122,096", markup)

    def test_all_datasets_are_rendered(self):
        data = valid_case()
        data["datasets"].append({
            "hf_repo": "dh-unibe/second-corpus",
            "train_projects": ["project-two"],
        })
        markup = _render_dataset_panel(TrainingContract(data))
        self.assertEqual(markup.count('class="training-dataset"'), 2)
        self.assertIn("second-corpus", markup)


class ReproducibilityTests(unittest.TestCase):
    def test_model_card_exposes_identity_timing_params_and_raw_record(self):
        markup = _render_reproducibility(TrainingContract(valid_case()))
        for label in (
            "Erzeugtes Modell", "Basismodell", "Engine", "Lauf-ID", "Schema",
            "Gestartet", "Beendet", "Epochen", "Hyperparameter",
        ):
            self.assertIn(label, markup)
        self.assertIn("batch_size", markup)
        self.assertIn("training.json öffnen", markup)

    def test_untrusted_parameter_text_is_escaped(self):
        data = valid_case()
        data["params"]["note"] = '<script>alert("x")</script>'
        markup = _render_reproducibility(TrainingContract(data))
        self.assertNotIn("<script>", markup)
        self.assertIn("&lt;script&gt;", markup)


class ScopedMetricsTests(unittest.TestCase):
    def test_shared_vocabulary_owns_training_reference_semantics(self):
        contract = TrainingContract(valid_case())
        records = training_reference_evaluations(
            contract.metrics, contract.datasets, contract.params,
            contract.engine, contract.model_id,
        )
        self.assertEqual([record.unit for record in records], ["CER", "WER"])
        for record in records:
            self.assertEqual(record.metric_type, "reference_evaluation")
            self.assertEqual(record.scope, "corpus")
            self.assertFalse(record.is_comparable)
            self.assertEqual(record.normalisation, "NFD")
            self.assertIn("729e9b", record.reference_version)
            self.assertEqual(record.raw["source"], "training.json")

    def test_shared_vocabulary_keeps_absent_metrics_absent(self):
        contract = TrainingContract(valid_case())
        self.assertEqual(
            training_reference_evaluations(
                None, contract.datasets, contract.params,
                contract.engine, contract.model_id,
            ),
            [],
        )

    def test_metrics_state_unit_scope_direction_and_comparability_limit(self):
        markup = _render_metrics(TrainingContract(valid_case()))
        self.assertIn('class="quality-reference-eval"', markup)
        self.assertIn('&quot;metric_type&quot;: &quot;reference_evaluation&quot;', markup)
        self.assertIn("CER", markup)
        self.assertIn("6.0", markup)
        self.assertIn("niedrig", markup)
        self.assertIn("Auswertungsherkunft", markup)
        self.assertIn("Referenzversion", markup)
        self.assertIn("Normalisierung", markup)
        self.assertIn("nur zwischen Läufen", markup)
        self.assertIn("GT_Thun-Test_(DEMO_TEST)", markup)

    def test_absent_metrics_are_not_presented_as_zero(self):
        data = valid_case()
        data["metrics"] = None
        markup = _render_metrics(TrainingContract(data))
        self.assertIn("Keine Validierungsmetriken", markup)
        self.assertNotIn("0.00%", markup)


class IntegratedReportTests(unittest.TestCase):
    def test_report_contains_all_four_issue_sections(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / valid_case()["run_id"] / "training.json"
            path.parent.mkdir()
            path.write_text(json.dumps(valid_case()), encoding="utf-8")
            row = _build_rows([path])[0]
        markup = _render_run_report(row)
        self.assertIn("Trainingskurven", markup)
        self.assertIn("Datensatzprovenienz", markup)
        self.assertIn("Reproduzierbarkeit und Modellkarte", markup)
        self.assertIn("Validierungsmetriken", markup)
        self.assertIn("Verwendungen in Erkennungen", markup)

    def test_model_links_to_exact_recognition_candidates(self):
        case = valid_case()
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp) / "docs"
            run = docs / "training" / case["run_id"]
            run.mkdir(parents=True)
            (run / "training.json").write_text(json.dumps(case), encoding="utf-8")
            doc = docs / "sample-document"
            doc.mkdir()
            (doc / "pipeline.json").write_text(json.dumps({
                "transcription": "selected text",
                "recognitions": [{
                    "engine": "kraken", "model_id": case["model_id"],
                    "page": "folio 1r", "text": "candidate text",
                }],
            }), encoding="utf-8")
            usages = _recognition_usages(docs)
            rows = _build_rows([run / "training.json"], usages)
        self.assertEqual(len(usages[case["model_id"]]), 1)
        usage = usages[case["model_id"]][0]
        self.assertEqual(usage["candidate_id"], "folio-1r-kraken-kf-kraken-20240615")
        markup = _render_run_report(rows[0])
        self.assertIn("?rec=folio-1r-kraken-kf-kraken-20240615", markup)
        self.assertIn("#recognition-folio-1r-kraken-kf-kraken-20240615", markup)
        self.assertIn("sample-document", markup)

    def test_unmatched_model_has_an_explicit_empty_state(self):
        markup = _render_recognition_usages("unused-model", [])
        self.assertIn("noch keine Erkennungsversuche", markup)
        self.assertNotIn("<a ", markup)

    def test_full_builder_writes_a_self_contained_report(self):
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp) / "docs"
            run = docs / "training" / valid_case()["run_id"]
            run.mkdir(parents=True)
            (run / "training.json").write_text(json.dumps(valid_case()), encoding="utf-8")
            target = docs / "training" / "index.md"
            with patch("build_training.DOCS", docs), patch("build_training.TRAINING_INDEX", target):
                self.assertEqual(build_training(), 1)
            index = target.read_text(encoding="utf-8")
            run_pages = sorted((docs / "training").glob("*/index.md"))
            report = run_pages[0].read_text(encoding="utf-8")

        # The index is an index: it links to runs and carries no charts (#231).
        self.assertIn("Training runs", index)
        self.assertIn('href="', index)
        self.assertNotIn("<svg", index)
        self.assertNotIn("Datensatzprovenienz", index)

        # The run page carries the report.
        self.assertEqual(len(run_pages), 1)
        self.assertIn("quality-explain.js", report)
        self.assertIn("<svg", report)
        self.assertIn("Datensatzprovenienz", report)
        self.assertIn("data-provenance=", report)
        # …and identifies its subject as a run, not a document (#233)
        self.assertIn("run_id", report)
        self.assertIn("training-evaluation/v1", report)
        self.assertNotIn("&quot;doc_id&quot;", report)


class HardenedContractTests(unittest.TestCase):
    def test_non_finite_curve_values_are_rejected(self):
        data = valid_case()
        data["curves"][0]["train_loss"] = float("nan")
        with self.assertRaises(ContractError):
            TrainingContract(data)

    def test_invalid_provenance_revision_is_rejected(self):
        data = valid_case()
        data["datasets"][0]["revision"] = "../../escape"
        with self.assertRaises(ContractError):
            TrainingContract(data)


if __name__ == "__main__":
    unittest.main()


class ChartAxisTests(unittest.TestCase):
    """#232 — loss and accuracy need opposite axis treatment."""

    def _chart(self, curves: list[dict], kind: str) -> str:
        from build_training import _render_svg_chart
        return _render_svg_chart([CurveEpoch(**c) for c in curves], "run-1", kind)

    def test_flat_high_loss_is_not_drawn_as_a_flat_line_at_the_top(self):
        """The first real run's loss moved 55210 -> 52980 over 50 epochs — a
        non-convergence. On a zero-based axis that is a flat line pinned to the
        top, indistinguishable from a converged model that has plateaued."""
        curves = [{"epoch": e, "train_loss": 55210.0 - e * 45.0} for e in range(50)]
        svg = self._chart(curves, "loss")
        # y-axis ticks are the x="54" labels; the x-axis epoch-0 tick is not one
        y_ticks = re.findall(r'x="54"[^>]*>([^<]+)</text>', svg)
        self.assertNotIn("0", y_ticks)              # axis does not start at zero
        self.assertIn("nicht bei null beginnend", svg)  # and says so
        # the drawn line must actually span the plot, not hug one edge
        ys = [float(p.split(",")[1]) for p in
              svg.split('points="')[1].split('"')[0].split()]
        self.assertGreater(max(ys) - min(ys), 100.0)

    def test_accuracy_axis_keeps_the_origin(self):
        """Validation accuracy pinned at 0 IS the finding; rescaling to its own
        range would draw it mid-height as though something had happened."""
        curves = [{"epoch": 0, "val_accuracy": 1.62}] + [
            {"epoch": e, "val_accuracy": 0.0} for e in range(1, 20)
        ]
        svg = self._chart(curves, "accuracy")
        self.assertIn("Achse beginnt bei null", svg)
        ys = [float(p.split(",")[1]) for p in
              svg.split('points="')[1].split('"')[0].split()]
        self.assertAlmostEqual(max(ys), 234.0, delta=0.5)  # zero sits on the axis

    def test_axis_range_is_stated_in_the_accessible_description(self):
        curves = [{"epoch": e, "train_loss": 1000.0 + e} for e in range(5)]
        svg = self._chart(curves, "loss")
        self.assertIn("<desc", svg)
        self.assertIn("Wertebereich", svg)
        self.assertIn("<figcaption>", svg)
