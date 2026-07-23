"""Tests for the quality metric and provenance contract (issue #27).

Covers:
- normalize_metric() determinism for all metric kinds
- Legacy payload compatibility (qa_score, confidence, fusion)
- Missing/unknown/failed/degenerate states
- Percentage emission rules (no value without known unit/range)
- Candidate confidence attachment (engine/model/page required)
- Reference evaluation context enforcement (reference_name required)
- Corpus vs document scope (not silently collapsed)
- Comparability contract
- normalize_candidate_metrics() priority ordering
- Contract fixture validation (tests/fixtures/metric_contract_cases.json)
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from quality import (
    COMPARABILITY_RULES,
    SAME_CONTEXT_COMPARABLE,
    SCOPE_CONSTRAINTS,
    VALID_SCOPES,
    Provenance,
    normalize_candidate_metrics,
    normalize_metric,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "metric_contract_cases.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_fixtures():
    with open(FIXTURE_PATH) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Contract fixture tests
# ---------------------------------------------------------------------------

class MetricContractFixtureTests(unittest.TestCase):
    """Run every case in tests/fixtures/metric_contract_cases.json."""

    def _run_case(self, case: dict) -> None:
        name = case["name"]
        desc = case.get("desc", "")
        payload = case["payload"]
        expected = case["expected"]

        result = normalize_metric(payload)
        self.assertIsInstance(result, Provenance, f"{name}: expected Provenance, got {type(result)}")

        for key, exp_val in expected.items():
            actual_val = getattr(result, key, None)
            self.assertEqual(
                actual_val,
                exp_val,
                f"{name} ({desc}): expected {key}={exp_val!r}, got {actual_val!r}",
            )

    def test_all_fixture_cases(self):
        for case in _load_fixtures():
            with self.subTest(name=case["name"]):
                self._run_case(case)


# ---------------------------------------------------------------------------
# Metric type vocabulary tests
# ---------------------------------------------------------------------------

class MetricTypeVocabularyTests(unittest.TestCase):

    def test_all_metric_types_have_scope_constraints(self):
        types = [
            "engine_confidence", "agreement", "reference_evaluation",
            "degenerate", "failed", "missing", "legacy_qa",
        ]
        for mt in types:
            self.assertIn(mt, SCOPE_CONSTRAINTS, f"{mt} missing from SCOPE_CONSTRAINTS")
            self.assertIsInstance(SCOPE_CONSTRAINTS[mt], frozenset)

    def test_all_scope_constraints_are_valid_scopes(self):
        for mt, scopes in SCOPE_CONSTRAINTS.items():
            for s in scopes:
                self.assertIn(s, VALID_SCOPES, f"{mt} uses unknown scope {s!r}")

    def test_comparability_rules_exist_for_all_types(self):
        types = [
            "engine_confidence", "agreement", "reference_evaluation",
            "degenerate", "failed", "missing", "legacy_qa",
        ]
        for mt in types:
            self.assertIn(mt, COMPARABILITY_RULES, f"{mt} missing from COMPARABILITY_RULES")
            self.assertIn(mt, SAME_CONTEXT_COMPARABLE, f"{mt} missing from SAME_CONTEXT_COMPARABLE")

    def test_engine_confidence_not_cross_comparable(self):
        self.assertFalse(COMPARABILITY_RULES["engine_confidence"])

    def test_failed_and_missing_not_comparable(self):
        self.assertFalse(COMPARABILITY_RULES["failed"])
        self.assertFalse(COMPARABILITY_RULES["missing"])
        self.assertFalse(SAME_CONTEXT_COMPARABLE["failed"])
        self.assertFalse(SAME_CONTEXT_COMPARABLE["missing"])

    def test_reference_evaluation_same_context_comparable(self):
        self.assertTrue(SAME_CONTEXT_COMPARABLE["reference_evaluation"])

    def test_engine_confidence_same_context_comparable(self):
        self.assertTrue(SAME_CONTEXT_COMPARABLE["engine_confidence"])


# ---------------------------------------------------------------------------
# Percentage emission contract
# ---------------------------------------------------------------------------

class PercentageEmissionTests(unittest.TestCase):
    """Percentages must not be emitted without a known range/meaning."""

    def test_legacy_qa_has_no_unit(self):
        result = normalize_metric({"qa_score": 0.75})
        self.assertEqual(result.metric_type, "legacy_qa")
        self.assertEqual(result.unit, "n/a")

    def test_engine_confidence_has_probability_unit(self):
        result = normalize_metric({
            "metric_type": "engine_confidence",
            "value": 0.80,
            "engine": "kraken",
        })
        self.assertEqual(result.unit, "probability")

    def test_agreement_has_ratio_unit(self):
        result = normalize_metric({
            "metric_type": "agreement",
            "value": 0.66,
        })
        self.assertEqual(result.unit, "ratio")

    def test_cer_unit_emitted(self):
        result = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": 0.05,
            "reference_name": "GT Corpus",
        })
        self.assertEqual(result.unit, "CER")

    def test_wer_unit_emitted(self):
        result = normalize_metric({
            "metric_type": "reference_evaluation",
            "wer": 0.10,
            "reference_name": "GT Corpus",
        })
        self.assertEqual(result.unit, "WER")

    def test_cer_greater_than_one_rejected(self):
        """CER values > 1 are ambiguous percentages and must not produce a non-null value."""
        result = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": 4.5,
            "reference_name": "Some GT",
        })
        self.assertIsNone(result.value)

    def test_cer_exactly_one_accepted(self):
        result = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": 1.0,
            "reference_name": "Some GT",
        })
        self.assertEqual(result.value, 1.0)

    def test_missing_has_no_value(self):
        result = normalize_metric({})
        self.assertIsNone(result.value)


# ---------------------------------------------------------------------------
# Candidate confidence attachment tests
# ---------------------------------------------------------------------------

class CandidateConfidenceAttachmentTests(unittest.TestCase):
    """Engine confidence must always carry engine identification."""

    def test_engine_confidence_requires_engine(self):
        result = normalize_metric({
            "metric_type": "engine_confidence",
            "value": 0.9,
        })
        self.assertEqual(result.metric_type, "missing")

    def test_engine_confidence_preserves_engine(self):
        result = normalize_metric({
            "metric_type": "engine_confidence",
            "value": 0.9,
            "engine": "vlm",
            "model": "internvl-2",
            "page": "p3",
        })
        self.assertEqual(result.engine, "vlm")
        self.assertEqual(result.model, "internvl-2")
        self.assertEqual(result.page, "p3")

    def test_legacy_confidence_requires_engine(self):
        result = normalize_metric({"confidence": 0.80})
        self.assertEqual(result.metric_type, "missing")

    def test_legacy_confidence_with_engine_preserved(self):
        result = normalize_metric({
            "confidence": 0.80,
            "engine": "kraken",
            "model_id": "catmus",
            "page": "p1",
        })
        self.assertEqual(result.metric_type, "engine_confidence")
        self.assertEqual(result.engine, "kraken")
        self.assertEqual(result.model, "catmus")
        self.assertEqual(result.page, "p1")


# ---------------------------------------------------------------------------
# Reference evaluation context enforcement
# ---------------------------------------------------------------------------

class ReferenceEvaluationContextTests(unittest.TestCase):

    def test_reference_evaluation_requires_reference_name(self):
        result = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": 0.05,
        })
        self.assertEqual(result.metric_type, "missing")

    def test_reference_evaluation_preserves_context(self):
        result = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": 0.04,
            "reference_name": "KF Ground Truth",
            "reference_version": "v2",
            "normalisation": "unicode-nfc",
            "dataset": "kf-2024",
            "scope": "page",
        })
        self.assertEqual(result.reference_name, "KF Ground Truth")
        self.assertEqual(result.reference_version, "v2")
        self.assertEqual(result.normalisation, "unicode-nfc")
        self.assertEqual(result.dataset, "kf-2024")

    def test_corpus_scope_is_not_silently_document(self):
        result = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": 0.06,
            "reference_name": "Large Corpus",
            "scope": "corpus",
        })
        self.assertEqual(result.scope, "corpus")

    def test_invalid_scope_normalized_to_document(self):
        result = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": 0.06,
            "reference_name": "GT",
            "scope": "per-word",   # unknown scope
        })
        self.assertEqual(result.scope, "document")


# ---------------------------------------------------------------------------
# Failed / degenerate / missing state tests
# ---------------------------------------------------------------------------

class MissingStateTests(unittest.TestCase):

    def test_failed_takes_priority_over_confidence(self):
        result = normalize_metric({
            "error": "timeout",
            "confidence": 0.9,
            "engine": "kraken",
        })
        self.assertEqual(result.metric_type, "failed")

    def test_degenerate_takes_priority_over_confidence(self):
        result = normalize_metric({
            "degenerate": True,
            "confidence": 0.9,
            "engine": "kraken",
        })
        self.assertEqual(result.metric_type, "degenerate")

    def test_failed_is_not_comparable(self):
        result = normalize_metric({"failed": True})
        self.assertFalse(result.is_comparable)

    def test_missing_is_not_comparable(self):
        result = normalize_metric({})
        self.assertFalse(result.is_comparable)

    def test_null_payload_returns_missing(self):
        result = normalize_metric(None)
        self.assertEqual(result.metric_type, "missing")

    def test_non_dict_payload_returns_missing(self):
        for val in [42, "string", [1, 2, 3], True]:
            result = normalize_metric(val)
            self.assertEqual(result.metric_type, "missing", f"Expected missing for {val!r}")

    def test_unknown_keys_only_returns_missing(self):
        result = normalize_metric({"future_key": 1.0, "another": "x"})
        self.assertEqual(result.metric_type, "missing")


# ---------------------------------------------------------------------------
# Normalization determinism tests
# ---------------------------------------------------------------------------

class NormalizationDeterminismTests(unittest.TestCase):
    """Same payload always produces the same result."""

    def _assert_deterministic(self, payload: dict) -> None:
        first = normalize_metric(payload)
        for _ in range(3):
            subsequent = normalize_metric(payload)
            self.assertEqual(
                first.metric_type,
                subsequent.metric_type,
                f"Non-deterministic: {payload}",
            )
            self.assertEqual(first.value, subsequent.value)
            self.assertEqual(first.unit, subsequent.unit)

    def test_engine_confidence_deterministic(self):
        self._assert_deterministic({
            "metric_type": "engine_confidence",
            "value": 0.87,
            "engine": "kraken",
        })

    def test_reference_evaluation_deterministic(self):
        self._assert_deterministic({
            "metric_type": "reference_evaluation",
            "cer": 0.04,
            "reference_name": "GT",
        })

    def test_legacy_qa_deterministic(self):
        self._assert_deterministic({"qa_score": 0.60})

    def test_empty_payload_deterministic(self):
        self._assert_deterministic({})


# ---------------------------------------------------------------------------
# normalize_candidate_metrics priority tests
# ---------------------------------------------------------------------------

class NormalizeCandidateMetricsTests(unittest.TestCase):

    def test_failed_error_takes_priority(self):
        result = normalize_candidate_metrics({
            "error": "timeout",
            "confidence": 0.9,
            "engine": "kraken",
            "reference_eval": {"cer": 0.1, "reference_name": "GT"},
        })
        self.assertEqual(result.metric_type, "failed")

    def test_degenerate_flag_takes_priority_over_confidence(self):
        result = normalize_candidate_metrics({
            "degenerate": True,
            "confidence": 0.85,
            "engine": "trocr",
        })
        self.assertEqual(result.metric_type, "degenerate")

    def test_reference_eval_beats_engine_confidence(self):
        result = normalize_candidate_metrics({
            "confidence": 0.85,
            "engine": "kraken",
            "reference_eval": {
                "cer": 0.04,
                "reference_name": "KF GT",
            },
        })
        self.assertEqual(result.metric_type, "reference_evaluation")

    def test_engine_confidence_used_when_available(self):
        result = normalize_candidate_metrics({
            "confidence": 0.90,
            "engine": "trocr",
            "model_id": "base",
            "page": "p1",
        })
        self.assertEqual(result.metric_type, "engine_confidence")
        self.assertEqual(result.engine, "trocr")

    def test_agreement_used_when_no_confidence(self):
        result = normalize_candidate_metrics({"agreement": 0.75})
        self.assertEqual(result.metric_type, "agreement")

    def test_legacy_qa_fallback(self):
        result = normalize_candidate_metrics({"qa_score": 0.80})
        self.assertEqual(result.metric_type, "legacy_qa")

    def test_empty_candidate_returns_missing(self):
        result = normalize_candidate_metrics({})
        self.assertEqual(result.metric_type, "missing")

    def test_non_dict_returns_missing(self):
        result = normalize_candidate_metrics(None)
        self.assertEqual(result.metric_type, "missing")


# ---------------------------------------------------------------------------
# Provenance.to_dict() round-trip test
# ---------------------------------------------------------------------------

class ProvenanceToDictTests(unittest.TestCase):

    def test_to_dict_contains_all_required_fields(self):
        p = normalize_metric({
            "metric_type": "engine_confidence",
            "value": 0.85,
            "engine": "kraken",
            "model": "catmus",
            "page": "p1",
            "scope": "candidate",
        })
        d = p.to_dict()
        required_keys = {
            "metric_type", "value", "unit", "scope",
            "engine", "model", "page",
            "is_comparable", "explanation_key",
        }
        for key in required_keys:
            self.assertIn(key, d, f"to_dict() missing key: {key}")

    def test_to_dict_reference_evaluation_context(self):
        p = normalize_metric({
            "metric_type": "reference_evaluation",
            "cer": 0.03,
            "reference_name": "KF GT",
            "reference_version": "v1",
            "normalisation": "nfc",
            "dataset": "kf-2024",
        })
        d = p.to_dict()
        self.assertEqual(d["reference_name"], "KF GT")
        self.assertEqual(d["reference_version"], "v1")
        self.assertEqual(d["normalisation"], "nfc")
        self.assertEqual(d["dataset"], "kf-2024")


if __name__ == "__main__":
    unittest.main(verbosity=2)
