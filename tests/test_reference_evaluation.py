"""Tests for reference-based CER/WER display with provenance (issue #31).

Covers:
- render_reference_evaluation(): full HTML with badge, table, explanation, export
- render_evaluation_unavailable(): absent/missing evaluation notice
- is_evaluation_available(): guard function (reference_name required)
- evaluation_scope_label(): human-readable scope labels
- Corpus scope preserved; never silently collapsed to document scope
- Corpus-scope warning text present in rendered HTML
- Machine-readable data-provenance attribute present
- JSON export details element present
- reference_evaluation_json_export() (rec_exports): schema, all fields, corpus scope
- Fixture-based round-trips for evaluated, partially evaluated, and unevaluated outputs
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from quality import (
    Provenance,
    evaluation_scope_label,
    is_evaluation_available,
    normalize_metric,
    normalize_candidate_metrics,
    render_evaluation_unavailable,
    render_reference_evaluation,
)
from rec_exports import reference_evaluation_json_export

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "reference_evaluation_cases.json"


def _load_fixtures() -> list[dict]:
    with open(FIXTURE_PATH) as fh:
        return json.load(fh)


def _prov_cer_full(**overrides) -> Provenance:
    """Return a full CER Provenance for use in rendering tests."""
    base = dict(
        metric_type="reference_evaluation",
        value=0.042,
        unit="CER",
        scope="document",
        reference_name="KF-GT-2024",
        reference_version="v2",
        normalisation="nfc",
        dataset="koenigsfelden-2024",
        is_comparable=False,
        explanation_key="reference_evaluation",
    )
    base.update(overrides)
    return Provenance(**base)


# ---------------------------------------------------------------------------
# Fixture-based round-trip tests
# ---------------------------------------------------------------------------

class ReferenceEvaluationFixtureTests(unittest.TestCase):
    """Run every case in tests/fixtures/reference_evaluation_cases.json."""

    def _run_case(self, case: dict) -> None:
        name = case["name"]
        desc = case.get("desc", "")
        candidate = case["candidate"]
        expected = case["expected"]
        is_avail = case.get("is_available")

        # Derive provenance via normalize_candidate_metrics
        prov = normalize_candidate_metrics(candidate)
        self.assertIsInstance(prov, Provenance, f"{name}: expected Provenance")

        for key, exp_val in expected.items():
            actual = getattr(prov, key, None)
            self.assertEqual(
                actual,
                exp_val,
                f"{name} ({desc}): expected {key}={exp_val!r}, got {actual!r}",
            )

        if is_avail is not None:
            actual_avail = is_evaluation_available(candidate)
            self.assertEqual(
                actual_avail,
                is_avail,
                f"{name}: is_evaluation_available expected {is_avail}, got {actual_avail}",
            )

    def test_all_fixture_cases(self):
        for case in _load_fixtures():
            with self.subTest(name=case["name"]):
                self._run_case(case)


# ---------------------------------------------------------------------------
# Scope label tests
# ---------------------------------------------------------------------------

class EvaluationScopeLabelTests(unittest.TestCase):
    """evaluation_scope_label() returns correct German labels."""

    def test_document_scope(self):
        self.assertEqual(evaluation_scope_label("document"), "Dokument")

    def test_page_scope(self):
        self.assertEqual(evaluation_scope_label("page"), "Seite")

    def test_corpus_scope(self):
        self.assertEqual(evaluation_scope_label("corpus"), "Korpus")

    def test_candidate_scope(self):
        self.assertEqual(evaluation_scope_label("candidate"), "Einzelkandidat")

    def test_run_scope(self):
        self.assertEqual(evaluation_scope_label("run"), "Durchlauf")

    def test_na_scope(self):
        self.assertIn("k.", evaluation_scope_label("n/a"))

    def test_unknown_scope_falls_back_to_value(self):
        self.assertEqual(evaluation_scope_label("galaxy"), "galaxy")


# ---------------------------------------------------------------------------
# Availability guard tests
# ---------------------------------------------------------------------------

class EvaluationAvailabilityTests(unittest.TestCase):
    """is_evaluation_available() requires reference_name to return True."""

    def test_candidate_with_reference_eval_and_name(self):
        self.assertTrue(is_evaluation_available({
            "reference_eval": {"metric_type": "reference_evaluation",
                               "reference_name": "KF-GT-2024", "cer": 0.04}
        }))

    def test_candidate_without_reference_eval(self):
        self.assertFalse(is_evaluation_available({"engine": "tesseract", "confidence": 0.9}))

    def test_candidate_with_reference_eval_but_no_name(self):
        self.assertFalse(is_evaluation_available({
            "reference_eval": {"metric_type": "reference_evaluation", "cer": 0.04}
        }))

    def test_candidate_with_empty_reference_eval(self):
        self.assertFalse(is_evaluation_available({"reference_eval": {}}))

    def test_top_level_metric_type_with_name(self):
        self.assertTrue(is_evaluation_available({
            "metric_type": "reference_evaluation",
            "reference_name": "KF-GT-2024",
        }))

    def test_top_level_metric_type_without_name(self):
        self.assertFalse(is_evaluation_available({
            "metric_type": "reference_evaluation",
        }))

    def test_non_dict_returns_false(self):
        self.assertFalse(is_evaluation_available(None))
        self.assertFalse(is_evaluation_available("string"))
        self.assertFalse(is_evaluation_available(42))

    def test_empty_dict(self):
        self.assertFalse(is_evaluation_available({}))


# ---------------------------------------------------------------------------
# Unavailable notice tests
# ---------------------------------------------------------------------------

class EvaluationUnavailableTests(unittest.TestCase):
    """render_evaluation_unavailable() returns correct HTML."""

    def setUp(self):
        self.html = render_evaluation_unavailable()

    def test_contains_unavailable_class(self):
        self.assertIn("quality-eval-unavailable", self.html)

    def test_has_aria_label(self):
        self.assertIn("aria-label", self.html)

    def test_no_numeric_metric_value(self):
        # Must not render a number that looks like a percentage
        import re
        self.assertNotRegex(self.html, r"\d+\.\d+\s*%")

    def test_contains_missing_badge_class(self):
        self.assertIn("quality-badge--missing", self.html)

    def test_non_reference_prov_returns_unavailable(self):
        prov = Provenance(metric_type="engine_confidence", value=0.9, engine="tesseract")
        html_out = render_reference_evaluation(prov)
        self.assertIn("quality-eval-unavailable", html_out)

    def test_none_prov_returns_unavailable(self):
        html_out = render_reference_evaluation(None)
        self.assertIn("quality-eval-unavailable", html_out)

    def test_failed_prov_returns_unavailable(self):
        prov = Provenance(metric_type="failed")
        html_out = render_reference_evaluation(prov)
        self.assertIn("quality-eval-unavailable", html_out)


# ---------------------------------------------------------------------------
# Rendering tests
# ---------------------------------------------------------------------------

class ReferenceEvaluationDisplayTests(unittest.TestCase):
    """render_reference_evaluation() produces correct accessible HTML."""

    def setUp(self):
        self.prov = _prov_cer_full()
        self.html = render_reference_evaluation(self.prov, suffix="t1", doc_id="doc-001")

    def test_has_outer_div_with_class(self):
        self.assertIn('class="quality-reference-eval"', self.html)

    def test_has_aria_label(self):
        self.assertIn("aria-label=", self.html)

    def test_has_quality_badge_eval_class(self):
        self.assertIn("quality-badge--eval", self.html)

    def test_badge_shows_cer(self):
        self.assertIn("CER", self.html)

    def test_badge_shows_value_percentage(self):
        # 0.042 → 4.2%
        self.assertIn("4.2", self.html)

    def test_reference_name_in_table(self):
        self.assertIn("KF-GT-2024", self.html)

    def test_reference_version_in_table(self):
        self.assertIn("v2", self.html)

    def test_normalisation_in_table(self):
        self.assertIn("nfc", self.html)

    def test_dataset_in_table(self):
        self.assertIn("koenigsfelden-2024", self.html)

    def test_scope_label_in_table(self):
        self.assertIn("Dokument", self.html)

    def test_explanation_button_present(self):
        self.assertIn("quality-explain-btn", self.html)

    def test_explanation_block_present(self):
        self.assertIn("quality-explanation", self.html)

    def test_data_provenance_attribute_present(self):
        self.assertIn("data-provenance=", self.html)

    def test_data_provenance_contains_metric_type(self):
        self.assertIn("reference_evaluation", self.html)

    def test_machine_export_details_present(self):
        self.assertIn("<details", self.html)
        self.assertIn("quality-machine-export", self.html)

    def test_machine_export_contains_schema(self):
        self.assertIn("agentic-historian/reference-evaluation/v1", self.html)

    def test_machine_export_contains_doc_id(self):
        self.assertIn("doc-001", self.html)

    def test_no_corpus_warning_for_document_scope(self):
        self.assertNotIn("quality-corpus-warning", self.html)

    def test_provenance_table_present(self):
        self.assertIn("quality-provenance-table", self.html)

    def test_provenance_table_aria_label(self):
        self.assertIn("Auswertungsherkunft", self.html)

    def test_wer_badge(self):
        prov = _prov_cer_full(unit="WER", value=0.075)
        html_out = render_reference_evaluation(prov, suffix="t2")
        self.assertIn("WER", html_out)
        self.assertIn("7.5", html_out)

    def test_null_value_renders_gracefully(self):
        prov = _prov_cer_full(value=None, unit="n/a")
        html_out = render_reference_evaluation(prov, suffix="t3")
        self.assertIn("quality-reference-eval", html_out)
        self.assertIn("nicht angegeben", html_out)

    def test_optional_fields_absent_when_none(self):
        prov = _prov_cer_full(
            reference_version=None, normalisation=None, dataset=None
        )
        html_out = render_reference_evaluation(prov, suffix="t4")
        # Optional table rows must be absent when values are None.
        # Note: "Normalisierung" appears in the explanation text; check the
        # provenance table section specifically via the <th> header pattern.
        self.assertNotIn("Referenzversion", html_out)
        self.assertNotIn('<th scope="row">Normalisierung</th>', html_out)
        self.assertNotIn('<th scope="row">Datensatz</th>', html_out)


# ---------------------------------------------------------------------------
# Corpus scope tests
# ---------------------------------------------------------------------------

class CorpusScopeTests(unittest.TestCase):
    """Corpus-level results must never be silently presented as document-level."""

    def setUp(self):
        self.prov = _prov_cer_full(scope="corpus", dataset="koenigsfelden-full")
        self.html = render_reference_evaluation(self.prov, suffix="cs1")

    def test_scope_preserved_as_corpus(self):
        self.assertEqual(self.prov.scope, "corpus")

    def test_corpus_warning_present(self):
        self.assertIn("quality-corpus-warning", self.html)

    def test_corpus_warning_mentions_korpus(self):
        self.assertIn("Korpus", self.html)

    def test_corpus_warning_role_note(self):
        self.assertIn('role="note"', self.html)

    def test_corpus_scope_in_data_provenance(self):
        self.assertIn('"scope": "corpus"', self.html.replace("&quot;", '"'))

    def test_no_corpus_warning_for_page_scope(self):
        prov = _prov_cer_full(scope="page")
        html_out = render_reference_evaluation(prov, suffix="cs2")
        self.assertNotIn("quality-corpus-warning", html_out)

    def test_scope_label_corpus_in_table(self):
        self.assertIn("Korpus", self.html)

    def test_corpus_scope_not_rewritten_to_document(self):
        # Normalization must not silently collapse corpus → document
        prov_from_norm = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": 0.031,
            "reference_name": "KF-GT-2024",
            "scope": "corpus",
        })
        self.assertEqual(prov_from_norm.scope, "corpus")


# ---------------------------------------------------------------------------
# Machine-readable export tests (rec_exports)
# ---------------------------------------------------------------------------

class MachineReadableExportTests(unittest.TestCase):
    """reference_evaluation_json_export() produces correct JSON."""

    def _export(self, **overrides):
        prov = _prov_cer_full(**overrides)
        return json.loads(reference_evaluation_json_export(prov, doc_id="doc-42"))

    def test_schema_present(self):
        d = self._export()
        self.assertEqual(d["schema"], "agentic-historian/reference-evaluation/v1")

    def test_doc_id_present(self):
        d = self._export()
        self.assertEqual(d["doc_id"], "doc-42")

    def test_metric_type_present(self):
        d = self._export()
        self.assertEqual(d["metric_type"], "reference_evaluation")

    def test_unit_present(self):
        d = self._export()
        self.assertEqual(d["unit"], "CER")

    def test_value_present(self):
        d = self._export()
        self.assertAlmostEqual(d["value"], 0.042)

    def test_scope_document(self):
        d = self._export()
        self.assertEqual(d["scope"], "document")

    def test_scope_corpus_preserved(self):
        d = self._export(scope="corpus")
        self.assertEqual(d["scope"], "corpus")

    def test_reference_name_present(self):
        d = self._export()
        self.assertEqual(d["reference_name"], "KF-GT-2024")

    def test_reference_version_present(self):
        d = self._export()
        self.assertEqual(d["reference_version"], "v2")

    def test_normalisation_present(self):
        d = self._export()
        self.assertEqual(d["normalisation"], "nfc")

    def test_dataset_present(self):
        d = self._export()
        self.assertEqual(d["dataset"], "koenigsfelden-2024")

    def test_is_comparable_false(self):
        d = self._export()
        self.assertFalse(d["is_comparable"])

    def test_explanation_key_present(self):
        d = self._export()
        self.assertEqual(d["explanation_key"], "reference_evaluation")

    def test_status_available(self):
        d = self._export()
        self.assertEqual(d["status"], "available")

    def test_non_reference_prov_returns_unavailable_status(self):
        prov = Provenance(metric_type="engine_confidence", value=0.9, engine="tesseract",
                          explanation_key="engine_confidence")
        d = json.loads(reference_evaluation_json_export(prov, doc_id="doc-x"))
        self.assertEqual(d["status"], "unavailable")
        self.assertEqual(d["schema"], "agentic-historian/reference-evaluation/v1")

    def test_missing_prov_returns_unavailable_status(self):
        prov = Provenance(metric_type="missing")
        d = json.loads(reference_evaluation_json_export(prov))
        self.assertEqual(d["status"], "unavailable")

    def test_export_is_sorted_json(self):
        prov = _prov_cer_full()
        raw = reference_evaluation_json_export(prov)
        reloaded = json.dumps(json.loads(raw), sort_keys=True, indent=2) + "\n"
        self.assertEqual(raw, reloaded)

    def test_export_ends_with_newline(self):
        prov = _prov_cer_full()
        self.assertTrue(reference_evaluation_json_export(prov).endswith("\n"))


# ---------------------------------------------------------------------------
# CER/WER display presence / absence tests
# ---------------------------------------------------------------------------

class EvaluationPresenceAbsenceTests(unittest.TestCase):
    """Evaluation metrics absent or explicitly unavailable when no reference exists."""

    def test_evaluated_candidate_shows_cer(self):
        prov = normalize_candidate_metrics({
            "reference_eval": {
                "metric_type": "reference_evaluation",
                "cer": 0.05,
                "reference_name": "KF-GT-2024",
                "scope": "document",
            }
        })
        html_out = render_reference_evaluation(prov)
        self.assertIn("CER", html_out)
        self.assertNotIn("quality-eval-unavailable", html_out)

    def test_unevaluated_candidate_shows_unavailable(self):
        prov = normalize_candidate_metrics({
            "engine": "tesseract",
            "confidence": 0.85,
        })
        html_out = render_reference_evaluation(prov)
        self.assertIn("quality-eval-unavailable", html_out)
        self.assertNotIn("quality-badge--eval", html_out)

    def test_missing_prov_shows_unavailable(self):
        prov = Provenance(metric_type="missing")
        html_out = render_reference_evaluation(prov)
        self.assertIn("quality-eval-unavailable", html_out)

    def test_raw_percentage_cer_rejected_value_none(self):
        # CER > 1 is rejected; Provenance should have value=None
        prov = normalize_candidate_metrics({
            "reference_eval": {
                "metric_type": "reference_evaluation",
                "cer": 4.2,
                "reference_name": "KF-GT-2024",
                "scope": "document",
            }
        })
        self.assertIsNone(prov.value)

    def test_partially_evaluated_no_numeric_value_renders(self):
        prov = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": None,
            "wer": None,
            "reference_name": "KF-GT-2024",
            "scope": "document",
        })
        html_out = render_reference_evaluation(prov)
        # Should render (not unavailable) because reference_name is present
        self.assertIn("quality-reference-eval", html_out)
        self.assertNotIn("quality-eval-unavailable", html_out)

    def test_machine_readable_export_traceable(self):
        prov = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": 0.04,
            "reference_name": "KF-GT-2024",
            "scope": "document",
        })
        export_json = json.loads(reference_evaluation_json_export(prov, doc_id="test-doc"))
        # Trace fields: reference, scope, schema
        self.assertEqual(export_json["reference_name"], "KF-GT-2024")
        self.assertEqual(export_json["scope"], "document")
        self.assertEqual(export_json["schema"], "agentic-historian/reference-evaluation/v1")
        self.assertEqual(export_json["doc_id"], "test-doc")


if __name__ == "__main__":
    unittest.main(verbosity=2)
