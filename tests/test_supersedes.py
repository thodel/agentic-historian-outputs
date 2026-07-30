"""Regression tests for document lineage direction (issue #125)."""

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_index
import build_outputs


class SupersedesTests(unittest.TestCase):
    def test_referenced_predecessor_is_marked_superseded(self):
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp)
            for doc_id, payload in (
                ("old", {}),
                ("new", {"supersedes": "old"}),
                ("self", {"supersedes": "self"}),
                ("missing-target", {"supersedes": "absent"}),
            ):
                directory = docs / doc_id
                directory.mkdir()
                (directory / "pipeline.json").write_text(json.dumps(payload))

            records = [
                SimpleNamespace(doc_id=doc_id)
                for doc_id in ("old", "new", "self", "missing-target")
            ]
            with patch.object(build_index, "DOCS", docs):
                self.assertEqual(
                    build_index._superseded_document_ids(records),
                    {"old"},
                )

    def test_older_page_points_to_newest_superseding_run(self):
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp)
            for doc_id, payload in (
                ("old", {}),
                ("new-a", {"supersedes": "old"}),
                ("new-b", {"supersedes": "old"}),
            ):
                directory = docs / doc_id
                directory.mkdir()
                (directory / "pipeline.json").write_text(json.dumps(payload))

            dates = {
                "new-a": date(2026, 1, 1),
                "new-b": date(2026, 2, 1),
            }
            with patch.object(
                build_outputs,
                "pipeline_date",
                side_effect=lambda path: dates[path.parent.name],
            ):
                self.assertEqual(
                    build_outputs._superseding_run("old", docs),
                    ("new-b", date(2026, 2, 1)),
                )
                self.assertIsNone(
                    build_outputs._superseding_run("new-b", docs)
                )


if __name__ == "__main__":
    unittest.main()
