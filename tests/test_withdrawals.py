"""Withdrawal records produce tombstones and leave no live artifacts (#196)."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from withdrawals import (  # noqa: E402
    build_tombstones, load_withdrawals, remove_withdrawn_entity_pages,
    tombstone_page,
)


class WithdrawalTests(unittest.TestCase):
    def test_repository_records_are_complete_and_archived(self):
        records = load_withdrawals(ROOT / "data" / "withdrawals.json")
        expected = {
            *(f"saa-000{number}-test" for number in range(1, 7)),
            "epic2-test-doc",
        }
        self.assertEqual(set(records), expected)
        for doc_id in expected:
            self.assertTrue((ROOT / "data" / "withdrawn" / doc_id / "pipeline.json").exists())
            self.assertFalse((ROOT / "docs" / doc_id / "pipeline.json").exists())

    def test_withdrawn_ids_do_not_survive_in_discovery_outputs(self):
        records = load_withdrawals(ROOT / "data" / "withdrawals.json")
        discovery_paths = [
            ROOT / "docs" / "index.md",
            ROOT / "docs" / "feed.xml",
            ROOT / "docs" / "sitemap.xml",
            ROOT / "docs" / "tests" / "index.md",
            *sorted((ROOT / "docs" / "entities").glob("**/index.md")),
        ]
        discovery = "\n".join(
            path.read_text(encoding="utf-8") for path in discovery_paths
        )
        for doc_id in records:
            self.assertNotIn(doc_id, discovery)

    def test_invalid_record_fails_loudly(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "withdrawals.json"
            path.write_text(json.dumps({"test": {"status": "withdrawn"}}))
            with self.assertRaises(ValueError):
                load_withdrawals(path)

    def test_tombstone_is_explicit_and_has_no_artifact_links(self):
        page = tombstone_page("test-id", {
            "status": "withdrawn",
            "withdrawal_date": "2026-08-01",
            "reason": "Fixture",
            "decision_reference": "https://example.org/decision",
            "replacement": None,
        })
        self.assertIn("must not be cited", page)
        self.assertIn('data-status="withdrawn"', page)
        for artifact in ("pipeline.json", "transcription.tei.xml", "CITATION.cff", ".zip"):
            self.assertNotIn(artifact, page)

    def test_builder_removes_live_artifacts(self):
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp)
            directory = docs / "fixture-test"
            (directory / "recognitions").mkdir(parents=True)
            (directory / "pipeline.json").write_text("{}")
            (directory / "recognitions" / "candidate.txt").write_text("x")
            record = {
                "status": "withdrawn",
                "withdrawal_date": "2026-08-01",
                "reason": "Fixture",
                "decision_reference": "https://example.org/decision",
                "replacement": None,
            }
            build_tombstones(docs, {"fixture-test": record})
            self.assertEqual(
                {path.name for path in directory.iterdir()}, {"index.md"}
            )

    def test_orphan_entity_page_for_withdrawn_id_is_removed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            orphan = root / "test-person"
            orphan.mkdir()
            (orphan / "index.md").write_text(
                '<a href="../../fixture-test/">fixture-test</a>'
            )
            keep = root / "historian"
            keep.mkdir()
            (keep / "index.md").write_text(
                '<a href="../../real-document/">real-document</a>'
            )
            remove_withdrawn_entity_pages(root, {"fixture-test"})
            self.assertFalse(orphan.exists())
            self.assertTrue(keep.exists())


if __name__ == "__main__":
    unittest.main()
