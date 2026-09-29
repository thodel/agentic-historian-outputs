"""A verified source reference must outlive the run that did not mention it (#182).

Epic #182 asks that every output be checkable against its original. The
capability was built — normalisation, missing-state messages, the evidence
workspace — but the reference itself lived in `pipeline.json`, which a
recognition run overwrites. So a replacement run that omitted `source_url`
silently turned a checkable document into an unverifiable one, and nothing
recorded that anything had been lost. That is the regression this module
exists to make impossible.

The record also could not say who checked, when, or against what. A reference
with no verifier carries no more authority than a guess, which is the whole
problem #182 is about.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from source_ledger import (  # noqa: E402
    apply_source_ledger, coverage, load_source_ledger, summarize,
)
from source_references import normalize_source_reference  # noqa: E402

VERIFIED = {
    "institution": "Staatsarchiv Aargau",
    "shelfmark": "SAA 428",
    "rights": "See the rights statement on e-codices",
    "verified_by": "A. Reviewer",
    "verified_at": "2026-09-29",
    "source_url": "https://www.e-codices.unifr.ch/en/saa/0428",
}


def ledger(**documents):
    return {"version": 1, "documents": documents}


class LedgerValidationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "source-references.json"
        self.addCleanup(self._tmp.cleanup)

    def _write(self, payload):
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        return self.path

    def test_a_missing_file_is_simply_empty(self):
        self.assertEqual({}, load_source_ledger(Path("/nonexistent/ledger.json")))

    def test_a_valid_record_loads(self):
        self._write(ledger(**{"u-17": VERIFIED}))
        self.assertIn("u-17", load_source_ledger(self.path))

    def test_every_required_field_is_enforced(self):
        for field in ("institution", "shelfmark", "rights",
                      "verified_by", "verified_at"):
            with self.subTest(missing=field):
                record = {k: v for k, v in VERIFIED.items() if k != field}
                self._write(ledger(**{"u-17": record}))
                with self.assertRaises(ValueError) as caught:
                    load_source_ledger(self.path)
                self.assertIn(field, str(caught.exception))

    def test_a_reference_nobody_can_open_is_refused(self):
        record = {k: v for k, v in VERIFIED.items() if k != "source_url"}
        self._write(ledger(**{"u-17": record}))
        with self.assertRaises(ValueError) as caught:
            load_source_ledger(self.path)
        self.assertIn("source_url", str(caught.exception))

    def test_a_malformed_date_is_refused(self):
        self._write(ledger(**{"u-17": {**VERIFIED, "verified_at": "29.09.2026"}}))
        with self.assertRaises(ValueError):
            load_source_ledger(self.path)

    def test_the_wrong_version_is_refused(self):
        self.path.write_text(json.dumps({"version": 2, "documents": {}}),
                             encoding="utf-8")
        with self.assertRaises(ValueError):
            load_source_ledger(self.path)


class SurvivesRepublicationTests(unittest.TestCase):
    """The property the epic turns on."""

    def test_a_replacement_run_cannot_drop_a_verified_reference(self):
        records = {"u-17": VERIFIED}

        first_run = {"doc_id": "u-17", "transcription": "…",
                     "source_url": "https://www.e-codices.unifr.ch/en/saa/0428"}
        merged, verified = apply_source_ledger(first_run, "u-17", records)
        self.assertTrue(verified)
        self.assertEqual(VERIFIED["source_url"],
                         normalize_source_reference(merged)["url"])

        # The re-run forgets the source entirely, as a machine record may.
        second_run = {"doc_id": "u-17", "transcription": "… corrected"}
        merged, verified = apply_source_ledger(second_run, "u-17", records)

        self.assertTrue(
            verified,
            "the replacement run dropped the verified reference; the document "
            "went from checkable to unverifiable with nothing recording it",
        )
        self.assertEqual(VERIFIED["source_url"],
                         normalize_source_reference(merged)["url"])

    def test_the_ledger_overrides_a_stale_pipeline_hint(self):
        stale = {"doc_id": "u-17", "source_url": "https://example.org/wrong"}
        merged, _ = apply_source_ledger(stale, "u-17", {"u-17": VERIFIED})
        self.assertEqual(VERIFIED["source_url"], merged["source_url"])

    def test_a_document_with_no_entry_keeps_its_unverified_hint(self):
        """An unverified hint is still shown — as a hint, not as a claim."""
        hint = {"doc_id": "other", "source_url": "https://example.net/scan"}
        merged, verified = apply_source_ledger(hint, "other", {"u-17": VERIFIED})
        self.assertFalse(verified)
        self.assertEqual("https://example.net/scan", merged["source_url"])
        self.assertNotIn("source_verification", merged)

    def test_a_verified_record_carries_its_verifier(self):
        merged, _ = apply_source_ledger({"doc_id": "u-17"}, "u-17", {"u-17": VERIFIED})
        verification = merged["source_verification"]
        self.assertEqual("Staatsarchiv Aargau", verification["institution"])
        self.assertEqual("SAA 428", verification["shelfmark"])
        self.assertEqual("A. Reviewer", verification["verified_by"])
        self.assertEqual("2026-09-29", verification["verified_at"])


class CoverageReportTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.docs = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def _document(self, doc_id, **payload):
        directory = self.docs / doc_id
        directory.mkdir(parents=True)
        (directory / "pipeline.json").write_text(
            json.dumps({"doc_id": doc_id, **payload}), encoding="utf-8")

    def test_reports_one_row_per_document(self):
        self._document("a")
        self._document("b", source_url="https://example.net/scan")
        rows = coverage(self.docs, ledger={})
        self.assertEqual(["a", "b"], [row["doc_id"] for row in rows])

    def test_a_verified_document_is_marked_verified(self):
        self._document("u-17")
        rows = coverage(self.docs, ledger={"u-17": VERIFIED})
        self.assertTrue(rows[0]["verified"])
        self.assertEqual("Staatsarchiv Aargau", rows[0]["institution"])

    def test_an_unverified_document_is_named_in_the_summary(self):
        self._document("a")
        summary = summarize(coverage(self.docs, ledger={}))
        self.assertIn("0/1 verified", summary)
        self.assertIn("a", summary)

    def test_a_recorded_reason_counts_as_answered(self):
        """"We looked and it is not available" is a result, not a gap."""
        self._document("a")
        rows = coverage(self.docs, ledger={
            "a": {**VERIFIED, "unavailable_reason": "no digitised copy exists"}})
        summary = summarize(rows)
        self.assertIn("recorded reason", summary)

    def test_unverified_documents_without_a_reason_are_counted(self):
        self._document("a")
        self._document("b")
        summary = summarize(coverage(self.docs, ledger={}))
        self.assertIn("2 document(s) with neither", summary)


class LedgerDocumentTests(unittest.TestCase):
    """The backfill page is how a contributor learns the entry shape."""

    PAGE = Path(__file__).parent.parent / "docs" / "source-backfill.md"

    def test_the_page_exists_and_is_marked_internal(self):
        text = self.PAGE.read_text(encoding="utf-8")
        self.assertIn("Internal", text)

    def test_every_required_field_is_documented(self):
        text = self.PAGE.read_text(encoding="utf-8")
        for field in ("institution", "shelfmark", "rights",
                      "verified_by", "verified_at", "unavailable_reason"):
            with self.subTest(field=field):
                self.assertIn(field, text)


if __name__ == "__main__":
    unittest.main()
