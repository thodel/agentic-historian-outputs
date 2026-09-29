"""Tests for the training.json contract (issue #220 / TR-1)."""

from __future__ import annotations

import json
import sys
import tempfile
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


#: Keys the fixture file carries for this test harness, not for the contract.
#: They must be stripped before a case is validated — feeding them in made the
#: contract quietly tolerate unknown fields, which is exactly the hole that let
#: a foreign record validate as an almost-empty run.
HARNESS_KEYS = frozenset({"name", "_expect_error"})


def _load_fixtures():
    with open(FIXTURE_PATH) as fh:
        return json.load(fh)


def _payload(case: dict) -> dict:
    """The record a producer would actually write, without harness metadata."""
    return {k: v for k, v in case.items() if k not in HARNESS_KEYS}


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
                TrainingContract(_payload(case))
        else:
            TrainingContract(_payload(case))  # must not raise

    def test_all_cases(self):
        for case in _load_fixtures():
            with self.subTest(name=case["name"]):
                self._run(case)


# ── Schema constraint tests ──────────────────────────────────────────────────

class TestSchemaConstraints(unittest.TestCase):

    def test_valid_engines_accepted(self):
        for engine in VALID_ENGINES:
            TrainingContract({
                "schema_version": 1,
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
                "schema_version": 1,
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
                "schema_version": 1,
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
            "schema_version": 1,
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
                "schema_version": 1,
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
                "schema_version": 1,
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


# ── Hostile and foreign input ────────────────────────────────────────────────

class HostileInputTests(unittest.TestCase):
    """A bad record must be reported, never crash, never pass silently.

    Two failure modes were live here. Some inputs escaped the ContractError
    path entirely — a list root raised AttributeError from ``data.get``, a
    numeric run_id raised TypeError from ``RUN_ID_RE.match`` — so the caller
    got a traceback rather than a violation it could report, and one bad
    record took the whole site build down.

    Others passed. ``bool`` is an ``int`` in Python, so ``cer: true`` cleared
    every range check and would have been published as an error rate of 1.0;
    a non-finite CER cleared them too; ``epochs: 2.7`` was truncated to an
    epoch count the trainer never ran; a missing ``schema_version`` was
    defaulted although it is documented as required.
    """

    VALID = {
        "schema_version": 1, "run_id": "run-001", "model_id": "m",
        "base_model": "owner/base", "engine": "kraken",
        "created_at": "2026-01-01T00:00:00+00:00",
        "epochs": 2, "epochs_trained": 2, "status": "completed",
        "curves": [], "datasets": [{"hf_repo": "owner/name"}],
    }

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _check(self, payload, raw=False, run_dir="run-001"):
        directory = self.root / "training" / run_dir
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / "training.json"
        path.write_text(payload if raw else json.dumps(payload), encoding="utf-8")
        return validate_training_json(path)

    def test_the_baseline_is_actually_valid(self):
        """Otherwise every case below would pass for the wrong reason."""
        ok, err = self._check(self.VALID)
        self.assertTrue(ok, err)

    def test_non_object_roots_are_reported_not_raised(self):
        for label, payload, raw in (
            ("list", [1, 2, 3], False),
            ("string", '"hallo"', True),
            ("number", "42", True),
        ):
            with self.subTest(root=label):
                ok, err = self._check(payload, raw=raw)
                self.assertFalse(ok)
                self.assertIn("JSON object", err)

    def test_wrongly_typed_run_id_is_reported_not_raised(self):
        ok, err = self._check({**self.VALID, "run_id": 123})
        self.assertFalse(ok)
        self.assertIn("run_id", err)

    def test_boolean_metrics_are_rejected(self):
        ok, err = self._check({**self.VALID, "metrics": {"cer": True}})
        self.assertFalse(ok, "cer: true was accepted as an error rate of 1.0")
        self.assertIn("cer", err)

    def test_non_finite_metrics_are_rejected(self):
        ok, err = self._check(
            json.dumps(self.VALID)[:-1] + ', "metrics": {"cer": Infinity}}', raw=True)
        self.assertFalse(ok)
        self.assertIn("finite", err)

    def test_fractional_epochs_are_rejected_not_truncated(self):
        ok, err = self._check({**self.VALID, "epochs": 2.7})
        self.assertFalse(ok, "2.7 epochs was truncated to 2 and published")
        self.assertIn("epochs", err)

    def test_schema_version_is_required(self):
        payload = {k: v for k, v in self.VALID.items() if k != "schema_version"}
        ok, err = self._check(payload)
        self.assertFalse(ok)
        self.assertIn("schema_version", err)

    def test_run_id_must_match_its_directory(self):
        """The run id is the published URL; a mismatch links somewhere wrong.

        Checked where the published tree is walked rather than by the schema
        validator, which must stay usable on a record sitting anywhere.
        """
        ok, err = self._check(self.VALID, run_dir="a-different-folder")
        self.assertTrue(ok, f"the record itself is well formed: {err}")

        results = validate_all_training_jsons(self.root)
        self.assertIn("a-different-folder", results)
        self.assertIn("does not match its directory",
                      results["a-different-folder"])

    def test_unknown_fields_are_rejected(self):
        """Silently ignoring them is how a foreign record renders as an empty run."""
        ok, err = self._check({**self.VALID, "cer": 0.1})
        self.assertFalse(ok)
        self.assertIn("unknown field", err)

    def test_the_trainer_own_training_json_is_refused_clearly(self):
        """The producer writes a different document under the same filename.

        serving-atr-inference#38 emits {job_id, source, complete, note,
        points[]} — not one field in common with this contract. Publishing it
        must fail with a message naming the mismatch, not validate as a run
        with no metrics and no curve.
        """
        ok, err = self._check({
            "job_id": "20260807T161137Z-kraken",
            "source": "checkpoint filenames",
            "complete": False,
            "note": "kraken keeps the top 10 checkpoints",
            "points": [{"epoch": 1, "val_metric": 0.91, "val_error": 0.09}],
        })
        self.assertFalse(ok)
        for field in ("job_id", "points", "complete"):
            with self.subTest(field=field):
                self.assertIn(field, err)


# ── Standalone validator tests ───────────────────────────────────────────────

class TestStandaloneValidator(unittest.TestCase):
    """Runs live under ``<docs>/training/<run_id>/training.json``.

    These cases used to sit outside the stdlib runner, so nobody noticed when
    they drifted: they still wrote ``<root>/<run_id>/training.json``, the
    layout runs had before they moved out from under a document.  The
    discovery glob had long since moved on, so the "mixed" case was asserting
    against an empty result set.  Anything that writes a fixture here must use
    the same layout the generator scans.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _write_run(self, run_id, fixture):
        run_dir = self.root / "training" / run_id
        run_dir.mkdir(parents=True)
        path = run_dir / "training.json"
        path.write_text(json.dumps(fixture), encoding="utf-8")
        return path

    def test_validate_success(self):
        fixtures = _load_fixtures()
        tpath = self.root / "training.json"
        tpath.write_text(json.dumps(_payload(fixtures[0])), encoding="utf-8")
        ok, err = validate_training_json(tpath)
        self.assertTrue(ok, err)

    def test_validate_missing_file(self):
        ok, err = validate_training_json(self.root / "nope.json")
        self.assertFalse(ok)
        self.assertIn("cannot read", err)

    def test_validate_invalid(self):
        fixtures = _load_fixtures()
        tpath = self.root / "training.json"
        tpath.write_text(json.dumps(_payload(fixtures[5])), encoding="utf-8")  # bad run_id
        ok, err = validate_training_json(tpath)
        self.assertFalse(ok)
        self.assertIn("run_id", err)

    def test_validate_all_empty(self):
        self.assertEqual({}, validate_all_training_jsons(self.root))

    def test_validate_all_mixed(self):
        """Directories are named after the runs in them, as published.

        Naming them anything else now fails placement, which is the point:
        the run id is the URL.
        """
        good, bad = _payload(_load_fixtures()[0]), _payload(_load_fixtures()[5])
        self._write_run(good["run_id"], good)
        self._write_run("run-with-a-bad-record", bad)

        results = validate_all_training_jsons(self.root)
        self.assertIn("run-with-a-bad-record", results)
        self.assertNotIn(good["run_id"], results)

    def test_records_outside_the_training_tree_are_ignored(self):
        """The layout the stale fixture used must stay undiscovered.

        A record dropped beside a document rather than under ``training/`` is
        not a run.  Asserting that keeps the next drift visible instead of
        silently emptying the result set.
        """
        fixtures = _load_fixtures()
        stray = self.root / "doc-bad"
        stray.mkdir()
        (stray / "training.json").write_text(
            json.dumps(_payload(fixtures[5])), encoding="utf-8")

        self.assertEqual(
            {}, validate_all_training_jsons(self.root),
            "a training.json outside training/<run_id>/ was discovered; "
            "either the layout or this test is wrong",
        )


# ── to_dict round-trip ───────────────────────────────────────────────────────

class TestToDict(unittest.TestCase):

    def test_preserves_required_fields(self):
        for case in _load_fixtures():
            if case.get("_expect_error"):
                continue
            c = TrainingContract(_payload(case))
            d = c.to_dict()
            for key in ("run_id", "model_id", "engine", "status",
                        "created_at", "epochs", "epochs_trained"):
                self.assertEqual(d[key], case[key], f"{key} in {case['name']}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
