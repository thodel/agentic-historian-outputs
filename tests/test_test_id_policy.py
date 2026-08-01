"""Test ids cannot silently enter the public document tree (#197)."""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_outputs import is_test_id, validate_no_test_ids  # noqa: E402


class TestIdPolicy(unittest.TestCase):
    def test_delimited_test_component_is_detected(self):
        for doc_id in (
            "saa-0001-test", "epic2-test-doc", "test-document", "document_test",
        ):
            with self.subTest(doc_id=doc_id):
                self.assertTrue(is_test_id(doc_id))

    def test_unrelated_word_is_not_a_test_id(self):
        for doc_id in ("testament", "contest", "attestation", "historical-output"):
            with self.subTest(doc_id=doc_id):
                self.assertFalse(is_test_id(doc_id))

    def test_test_id_fails_with_actionable_message(self):
        with self.assertRaises(SystemExit) as ctx:
            validate_no_test_ids(["real-document", "new-test-run"])
        message = str(ctx.exception)
        self.assertIn("new-test-run", message)
        self.assertIn("tests/", message)
        self.assertIn("withdrawal", message)

    def test_current_public_pipeline_ids_pass(self):
        doc_ids = [
            path.parent.name for path in (ROOT / "docs").glob("*/pipeline.json")
        ]
        validate_no_test_ids(doc_ids)


if __name__ == "__main__":
    unittest.main()
