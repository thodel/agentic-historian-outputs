"""A published transcription has to contain text.

Two gaps let ``u-17`` onto the site with 451 characters of "u" and "i" beside
the only facsimile the site can show.

The first is in ``detect_degeneration``: its patterns are anchored across the
whole string, so they match a page that is one unbroken run of one character
and nothing else. A line-based engine failing does not produce that — it
produces one short run per line, and every newline breaks the anchor. So the
check had to become one about the alphabet the text uses rather than its shape.

The second is that nothing looked at a document's published transcription at
all. ``detect_degeneration`` runs over *candidates* inside a recognition, and
a document with no recognitions has no candidates, so nothing inspected it.

The baseline test below is the one that keeps this closed. The four known
documents are recorded with their findings because what to do about an
already-published document is an editorial decision (see
``docs/source-backfill.md``); a fifth appearing anywhere fails here.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import transcription_integrity as integrity  # noqa: E402
from quality import alphabet_profile, detect_degeneration  # noqa: E402

DOCS = ROOT / "docs"

#: What the published corpus is known to contain. Empty, as of #254: every
#: output published up to 2026-10-01 came from a test input and has been
#: withdrawn, and a withdrawn output is not a live publication problem.
#:
#: The five documents this once listed — kf, kf-, u-17 (degenerate text with no
#: recognition behind it), u-17__ (duplicate page set) and order-001-group (no
#: text at all) — are the reason the report exists. Their records are kept under
#: ``data/withdrawn/``; the report's job now is to catch the next publication
#: that looks like them, which is why these tests stay.
KNOWN_FINDINGS: dict[str, set[str]] = {}


class DegenerationDetectionTests(unittest.TestCase):
    """The detector has to see line-wise degeneration, not just one long run."""

    def test_multiline_single_letter_output_is_degenerate(self):
        """The exact shape that reached the site, one garbage token per line."""
        text = "\n".join(["u", "uuu", "uu", "uuuu", "iuuu"] * 20)
        is_degenerate, reason = detect_degeneration(text)
        self.assertTrue(
            is_degenerate,
            "a page of one-letter lines passed as a real transcription; this "
            "is what published u-17",
        )
        self.assertIn("verschiedene Buchstaben", reason)

    def test_one_letter_dominating_a_longer_alphabet_is_degenerate(self):
        """Enough distinct letters to clear the first rule, one swamping them."""
        text = ("u" * 180) + "abcdefghijklmnop"
        self.assertTrue(detect_degeneration(text)[0])
        self.assertIn("ein Buchstabe", detect_degeneration(text)[1])

    def test_a_short_page_is_not_degenerate(self):
        """A legitimately short page has no room for a wide alphabet."""
        self.assertFalse(detect_degeneration("Item mer ze Bern")[0])

    def test_real_german_prose_is_not_degenerate(self):
        text = (
            "Hut genennt die brief die das Closter ze künge welt haben sol "
            "und die abschuift der brief sol man keschen nach ordnung als sy "
            "gezeichen sint von eit der brief mit dem hochgeboen furstin"
        )
        self.assertFalse(detect_degeneration(text)[0])

    def test_every_real_transcription_in_the_corpus_stays_clean(self):
        """The rule must not reclassify a document that does hold text."""
        wrongly_flagged = []
        for pipeline in sorted(DOCS.glob("*/pipeline.json")):
            doc_id = pipeline.parent.name
            if doc_id in KNOWN_FINDINGS:
                continue
            import json
            data = json.loads(pipeline.read_text(encoding="utf-8"))
            body = integrity.body_text(data.get("transcription") or "")
            if not body:
                continue
            if detect_degeneration(body)[0]:
                wrongly_flagged.append(doc_id)
        self.assertEqual(
            [], wrongly_flagged,
            "these documents hold real text but were called degenerate:\n  "
            + "\n  ".join(wrongly_flagged),
        )


class AlphabetProfileTests(unittest.TestCase):

    def test_counts_distinct_letters_case_insensitively(self):
        self.assertEqual((4, 2, 0.5), alphabet_profile("AaBb"))

    def test_ignores_digits_and_punctuation(self):
        self.assertEqual((3, 3, 1 / 3), alphabet_profile("a1b2c3 .,;"))

    def test_empty_text_has_no_profile(self):
        self.assertEqual((0, 0, 0.0), alphabet_profile("   123  "))


class PublishedCorpusTests(unittest.TestCase):
    """The findings in the published corpus are a fixed, known set."""

    def setUp(self):
        self.rows = integrity.findings(DOCS)

    def test_the_report_finds_the_known_documents(self):
        found: dict[str, set[str]] = {}
        for row in self.rows:
            found.setdefault(row["doc_id"], set()).add(row["kind"])
        self.assertEqual(
            KNOWN_FINDINGS, found,
            "the set of documents with integrity findings changed. A new "
            "entry means something was published that should not have been; "
            "a missing one means it was dealt with — update KNOWN_FINDINGS "
            "in the same commit and say which.",
        )

    def test_every_finding_names_a_kind_the_report_explains(self):
        unknown = sorted({row["kind"] for row in self.rows} - set(integrity.KINDS))
        self.assertEqual([], unknown, f"undocumented finding kinds: {unknown}")

    def test_every_finding_carries_a_detail(self):
        bare = [row["doc_id"] for row in self.rows if not row["detail"].strip()]
        self.assertEqual([], bare, "a finding with no detail cannot be acted on")

    def test_withdrawn_documents_are_not_reported(self):
        """A withdrawn output is not a live publication problem."""
        withdrawn = integrity._withdrawn()
        self.assertTrue(withdrawn, "no withdrawals registry to check against")
        reported = {row["doc_id"] for row in self.rows}
        self.assertEqual(
            set(), reported & withdrawn,
            "withdrawn documents appear in the report; they are already "
            "retracted and cannot be acted on again",
        )

    def test_the_summary_names_every_document_it_found(self):
        summary = integrity.summarize(self.rows)
        for doc_id in KNOWN_FINDINGS:
            self.assertIn(doc_id, summary, f"{doc_id} is missing from the report")
        if not KNOWN_FINDINGS:
            self.assertIn("no findings", summary)

    def test_a_withdrawn_document_is_not_a_finding(self):
        """The report is about what is published, not about what was."""
        archived = sorted(p.name for p in (ROOT / "data" / "withdrawn").iterdir()
                          if p.is_dir())
        self.assertTrue(archived, "no withdrawn records to check against")
        reported = {row["doc_id"] for row in self.rows}
        self.assertEqual(
            set(), reported & set(archived),
            "withdrawn outputs are being reported as live integrity problems",
        )

    def test_an_empty_report_says_so(self):
        self.assertIn("no findings", integrity.summarize([]))


# The lineage tests that stood here asserted the state of the published
# ``u-17``/``u-17__`` pair: that the canonical record held less text than the
# one it retired, and that the facsimile mapping sat on the canonical one. Both
# documents are withdrawn (#254), so there is no published state left to
# assert.
#
# The defect they recorded is *not* fixed. ``0cf46c4`` moved the ``supersedes``
# pointer from the malformed id to the clean one without moving the content, so
# the next publication through that path will make a stub canonical again. That
# belongs upstream, where the lineage is written; see docs/source-backfill.md.

if __name__ == "__main__":
    unittest.main()
