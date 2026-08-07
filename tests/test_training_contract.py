"""Tests for the training.json contract (issue #220 / TR-1)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from training_contract import (
    ContractError,
    CurveEpoch,
    RUN_ID_RE,
    SLUG_RE,
    TrainingContract,
    VALID_ENGINES,
    VALID_STATUSES,
    validate_all_training_jsons,
    validate_training_json,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "training_contract_cases.json"


def _load_fixtures():
    with open(FIXTURE_PATH) as fh:
        return json.load(fh)


# ── CurveEpoch unit tests ────────────────────────────────────────────────────

class TestCurveEpoch(unittest.TestCase):

    def test_valid(self):
        e = CurveEpoch(epoch=3, train_loss=0.44, val_loss=0.38, val_accuracy=89.1, lr=1e-4)
        self.assertEqual(e.epoch, 3)
        self.assertAlmostEqual(e.train_loss, 0.44)
        self.assertAlmostEqual(e.val_loss, 0.38)
        self.assertAlmostEqual(e.val_accuracy, 89.1)
        self.assertAlmostEqual(e.lr, 1e-4)

    def test_partial(self):
        e = CurveEpoch(epoch=0, train_loss=2.3)
        self.assertEqual(e.epoch, 0)
        self.assertAlmostEqual(e.train_loss, 2.3)
        self.assertIsNone(e.val_loss)
        self.assertIsNone(e.val_accuracy)

    def test_negative_epoch_rejected(self):
        with self.assertRaises(ContractError):
            CurveEpoch(epoch=-1)

    def test_non_numeric_train_loss_rejected(self):
        with self.assertRaises(ContractError):
            CurveEpoch(epoch=0, train_loss="high")


# ── Contract fixture tests ───────────────────────────────────────────────────

class TestTrainingContractFixtures(unittest.TestCase):
    """Run every case in tests/fixtures/training_contract_cases.json."""

    def _run(self, case: dict) -> None:
        if case.get("_expect_error"):
            with self.assertRaises(ContractError, msg=case["name"]):
                TrainingContract(case)
        else:
            TrainingContract(case)  # must not raise

    def test_all_cases(self):
        for case in _load_fixtures():
            with self.subTest(name=case["name"]):
                self._run(case)


# ── Schema constraint tests ──────────────────────────────────────────────────

class TestSchemaConstraints(unittest.TestCase):

    def test_valid_engines_accepted(self):
        for engine in VALID_ENGINES:
            TrainingContract({
                "run_id": "20260601T120000Z-test-model",
                "model_id": "test-model", "engine": engine,
                "status": "completed", "created_at": "2024-06-01T12:00:00+00:00",
                "finished_at": "2024-06-01T14:00:00+00:00",
                "epochs": 10, "epochs_trained": 10,
                "params": {}, "metrics": None, "curves": None,
                "base_model": None, "log": None,
                "datasets": [{"hf_repo": "dh-unibe/image-text_kurrent-xix"}],
            })

    def test_unknown_engine_rejected(self):
        with self.assertRaises(ContractError) as ctx:
            TrainingContract({
                "run_id": "20260601T120000Z-test-model",
                "model_id": "test-model", "engine": "unknown_engine",
                "status": "completed", "created_at": "2024-06-01T12:00:00+00:00",
                "finished_at": "2024-06-01T14:00:00+00:00",
                "epochs": 10, "epochs_trained": 10,
                "params": {}, "metrics": None, "curves": None,
                "base_model": None, "log": None,
                "datasets": [{"hf_repo": "dh-unibe/image-text_kurrent-xix"}],
            })
        self.assertIn("engine must be one of", str(ctx.exception))

    def test_unknown_status_rejected(self):
        with self.assertRaises(ContractError) as ctx:
            TrainingContract({
                "run_id": "20260601T120000Z-test-model",
                "model_id": "test-model", "engine": "kraken",
                "status": "running",
                "created_at": "2024-06-01T12:00:00+00:00",
                "finished_at": "2024-06-01T14:00:00+00:00",
                "epochs": 10, "epochs_trained": 0,
                "params": {}, "metrics": None, "curves": None,
                "base_model": None, "log": None,
                "datasets": [{"hf_repo": "dh-unibe/image-text_kurrent-xix"}],
            })
        self.assertIn("status must be one of", str(ctx.exception))

    def _completed(self, **overrides):
        base = {
            "run_id": "20260601T120000Z-test-model",
            "model_id": "test-model", "engine": "kraken",
            "status": "completed", "created_at": "2024-06-01T12:00:00+00:00",
            "finished_at": "2024-06-01T14:00:00+00:00",
            "epochs": 50, "epochs_trained": 50,
            "params": {}, "metrics": None, "curves": None,
            "base_model": None, "log": None,
            "datasets": [{"hf_repo": "dh-unibe/image-text_kurrent-xix"}],
        }
        return {**base, **overrides}

    def test_completed_run_may_stop_early(self):
        """`quit: early` stops when validation stops improving — the recommended
        setting for fine-tuning. Requiring the full epoch count would reject
        every early-stopped run as malformed."""
        TrainingContract(self._completed(epochs=50, epochs_trained=12))  # must not raise

    def test_completed_run_must_train_something(self):
        with self.assertRaises(ContractError) as ctx:
            TrainingContract(self._completed(epochs_trained=0))
        self.assertIn("at least one epoch", str(ctx.exception))

    def test_more_epochs_than_requested_rejected(self):
        with self.assertRaises(ContractError) as ctx:
            TrainingContract(self._completed(epochs=10, epochs_trained=11))
        self.assertIn("more epochs than requested", str(ctx.exception))

    def test_several_datasets_accepted(self):
        """1..n: a model trained on two corpora is a different model, and the
        record has to be able to say so."""
        c = TrainingContract(self._completed(datasets=[
            {"hf_repo": "dh-unibe/image-text_medieval-scripts_xiv-xv-xvi",
             "train_projects": ["GT_Thun-Training_(TEST-DEMO)"], "pages": 127},
            {"hf_repo": "dh-unibe/image-text_kurrent-xix", "pages": 4200},
        ]))
        self.assertEqual(len(c.datasets), 2)
        self.assertEqual(c.datasets[1]["hf_repo"], "dh-unibe/image-text_kurrent-xix")

    def test_datasets_required(self):
        for bad in ([], None):
            with self.assertRaises(ContractError) as ctx:
                TrainingContract(self._completed(datasets=bad))
            self.assertIn("at least one dataset", str(ctx.exception))

    def test_dataset_needs_a_hub_repo(self):
        with self.assertRaises(ContractError) as ctx:
            TrainingContract(self._completed(datasets=[{"train_projects": ["x"]}]))
        self.assertIn("hf_repo", str(ctx.exception))

    def test_dataset_repo_must_look_like_owner_name(self):
        with self.assertRaises(ContractError):
            TrainingContract(self._completed(datasets=[{"hf_repo": "not-a-repo"}]))

    def test_cer_out_of_range_rejected(self):
        with self.assertRaises(ContractError) as ctx:
            TrainingContract({
                "run_id": "20260601T120000Z-test-model",
                "model_id": "test-model", "engine": "kraken",
                "status": "completed", "created_at": "2024-06-01T12:00:00+00:00",
                "finished_at": "2024-06-01T14:00:00+00:00",
                "epochs": 10, "epochs_trained": 10,
                "params": {}, "metrics": {"cer": 1.42, "wer": 0.19}, "curves": None,
                "base_model": None, "log": None,
                "datasets": [{"hf_repo": "dh-unibe/image-text_kurrent-xix"}],
            })
        self.assertIn("cer", str(ctx.exception))

    def test_wer_out_of_range_rejected(self):
        with self.assertRaises(ContractError) as ctx:
            TrainingContract({
                "run_id": "20260601T120000Z-test-model",
                "model_id": "test-model", "engine": "kraken",
                "status": "completed", "created_at": "2024-06-01T12:00:00+00:00",
                "finished_at": "2024-06-01T14:00:00+00:00",
                "epochs": 10, "epochs_trained": 10,
                "params": {}, "metrics": {"cer": 0.06, "wer": 2.1}, "curves": None,
                "base_model": None, "log": None,
                "datasets": [{"hf_repo": "dh-unibe/image-text_kurrent-xix"}],
            })
        self.assertIn("wer", str(ctx.exception))


# ── Regex tests ──────────────────────────────────────────────────────────────

class TestRegexPatterns(unittest.TestCase):

    def test_run_id_valid(self):
        # the real producer format, plus older hand-made ids
        self.assertTrue(RUN_ID_RE.match("20260807T201321Z-kraken-medieval-scripts-v1"))
        self.assertTrue(RUN_ID_RE.match("tr-kf-kraken-20240615-093041"))
        self.assertTrue(RUN_ID_RE.match("tr-model_v2-20240101-000000"))

    def test_run_id_invalid(self):
        # a run id only has to be a safe directory slug — the FORMAT belongs to
        # the producer (serving-atr-inference emits "<utc>-<model_id>")
        self.assertTrue(RUN_ID_RE.match("20260807T161137Z-kraken-thun-missiven-v1"))
        self.assertFalse(RUN_ID_RE.match("../escape"))
        self.assertFalse(RUN_ID_RE.match("has spaces"))
        self.assertFalse(RUN_ID_RE.match("ab"))  # too short to be meaningful
        self.assertFalse(RUN_ID_RE.match(""))
        self.assertFalse(RUN_ID_RE.match("-leading-dash"))

    def test_slug_valid(self):
        self.assertTrue(SLUG_RE.match("BAT_664_r_00027"))
        self.assertTrue(SLUG_RE.match("u-17-test"))
        self.assertTrue(SLUG_RE.match("kf-simple"))

    def test_slug_invalid_trailing_underscore(self):
        self.assertFalse(SLUG_RE.match("u-17__"))
        self.assertFalse(SLUG_RE.match("doc-"))


# ── Standalone validator tests ───────────────────────────────────────────────

class TestStandaloneValidator:

    def test_validate_success(self, tmp_path):
        fixtures = _load_fixtures()
        tpath = tmp_path / "training.json"
        tpath.write_text(json.dumps(fixtures[0]), encoding="utf-8")
        ok, err = validate_training_json(tpath)
        assert ok, err

    def test_validate_missing_file(self, tmp_path):
        ok, err = validate_training_json(tmp_path / "nope.json")
        assert not ok
        assert "cannot read" in err

    def test_validate_invalid(self, tmp_path):
        fixtures = _load_fixtures()
        tpath = tmp_path / "training.json"
        tpath.write_text(json.dumps(fixtures[5]), encoding="utf-8")  # bad run_id
        ok, err = validate_training_json(tpath)
        assert not ok
        assert "run_id" in err

    def test_validate_all_empty(self, tmp_path):
        results = validate_all_training_jsons(tmp_path)
        assert results == {}

    def test_validate_all_mixed(self, tmp_path):
        fixtures = _load_fixtures()
        (tmp_path / "doc-ok").mkdir()
        (tmp_path / "doc-ok" / "training.json").write_text(
            json.dumps(fixtures[0]), encoding="utf-8"
        )
        (tmp_path / "doc-bad").mkdir()
        (tmp_path / "doc-bad" / "training.json").write_text(
            json.dumps(fixtures[5]), encoding="utf-8"
        )
        results = validate_all_training_jsons(tmp_path)
        assert "doc-bad" in results
        assert "doc-ok" not in results


# ── to_dict round-trip ───────────────────────────────────────────────────────

class TestToDict(unittest.TestCase):

    def test_preserves_required_fields(self):
        for case in _load_fixtures():
            if case.get("_expect_error"):
                continue
            c = TrainingContract(case)
            d = c.to_dict()
            for key in ("run_id", "model_id", "engine", "status",
                        "created_at", "epochs", "epochs_trained"):
                self.assertEqual(d[key], case[key], f"{key} in {case['name']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
