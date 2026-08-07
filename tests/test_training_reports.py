"""Regression tests for training report issues #222–#225."""

from __future__ import annotations

import json
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
from training_contract import ContractError, TrainingContract  # noqa: E402


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
            page = target.read_text(encoding="utf-8")
        self.assertIn("quality-explain.js", page)
        self.assertIn("Laufberichte", page)
        self.assertIn("<svg", page)
        self.assertIn("Datensatzprovenienz", page)
        self.assertIn("data-provenance=", page)


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
