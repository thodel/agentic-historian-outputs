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


#: Every withdrawn output, and why. Adding a withdrawal means adding it here
#: in the same commit, so a document cannot leave the catalogue unremarked.
EXPECTED_WITHDRAWALS = {
    # Engineering fixtures published unintentionally (#196, #197).
    *(f"saa-000{number}-test" for number in range(1, 7)),
    "epic2-test-doc",
    # Every output published up to 2026-10-01 came from a test input rather
    # than a corpus the project meant to edition (#254).
    "BAT_664_r_00027", "bat", "kf", "kf-", "koenige",
    "order-001-group", "order-ens", "saa-0428", "u-17", "u-17__",
}


class WithdrawalTests(unittest.TestCase):
    def test_repository_records_are_complete_and_archived(self):
        records = load_withdrawals(ROOT / "data" / "withdrawals.json")
        self.assertEqual(set(records), EXPECTED_WITHDRAWALS)
        for doc_id in EXPECTED_WITHDRAWALS:
            self.assertTrue(
                (ROOT / "data" / "withdrawn" / doc_id / "pipeline.json").exists(),
                f"{doc_id} was withdrawn without archiving its machine record; "
                "withdrawal retracts a publication, it does not destroy the "
                "evidence",
            )
            self.assertFalse(
                (ROOT / "docs" / doc_id / "pipeline.json").exists(),
                f"{doc_id} is withdrawn but still carries a live machine "
                "record under docs/, from which the catalogue would rebuild it",
            )

    def test_a_withdrawn_document_keeps_its_url_as_a_tombstone(self):
        """Withdrawal is not deletion: the URL has to go on resolving."""
        for doc_id in sorted(EXPECTED_WITHDRAWALS):
            page = ROOT / "docs" / doc_id / "index.md"
            self.assertTrue(page.exists(), f"{doc_id} has no page at all")
            text = page.read_text(encoding="utf-8")
            self.assertIn("must not be cited", text, f"{doc_id} is not a tombstone")
            self.assertIn("robots: noindex", text, f"{doc_id} is still indexable")

    def test_nothing_in_discovery_links_to_a_withdrawn_document(self):
        """No discovery surface may offer a route to a retracted output.

        This checks for *links*, not for the id as a substring. A document id
        can be an ordinary word — `bat`, `kf`, `u-17` — and an entity page
        legitimately named "bat" is not a reference to the document `bat`. The
        substring form of this test passed only while every withdrawn id
        happened to look like a fixture name, and raised a false alarm the
        moment a real one was withdrawn.
        """
        records = load_withdrawals(ROOT / "data" / "withdrawals.json")
        discovery_paths = [
            ROOT / "docs" / "index.md",
            ROOT / "docs" / "feed.xml",
            ROOT / "docs" / "sitemap.xml",
            ROOT / "docs" / "tests" / "index.md",
            *sorted((ROOT / "docs" / "entities").glob("**/index.md")),
        ]
        offenders = []
        for path in discovery_paths:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            for doc_id in records:
                for link in (f'href="{doc_id}/"', f'href="./{doc_id}/"',
                             f'href="../{doc_id}/"', f"/{doc_id}/</loc>"):
                    if link in text:
                        offenders.append(
                            f"{path.relative_to(ROOT)} -> {link}")
        self.assertEqual(
            [], offenders,
            "these discovery surfaces still route readers to a withdrawn "
            "output:\n  " + "\n  ".join(offenders),
        )

    def test_the_catalogue_search_index_holds_no_withdrawn_record(self):
        """The index is what the client filters; a stale row resurrects a card."""
        index = ROOT / "docs" / "catalogue-index.json"
        if not index.exists():
            self.skipTest("no catalogue index generated")
        rows = json.loads(index.read_text(encoding="utf-8"))
        rows = rows if isinstance(rows, list) else rows.get("records", [])
        listed = {str(row.get("i") or row.get("id") or row.get("doc_id") or "")
                  for row in rows}
        self.assertEqual(
            set(), listed & EXPECTED_WITHDRAWALS,
            f"withdrawn records are still in the search index: "
            f"{sorted(listed & EXPECTED_WITHDRAWALS)}",
        )

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
