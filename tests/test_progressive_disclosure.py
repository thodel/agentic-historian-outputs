"""Tests for progressive disclosure of secondary research sections (issue #23).

Acceptance criteria:
- No primary evidence or critical warning is collapsed by default.
- Collapsed summaries communicate what is inside.
- Deep links reveal and focus their target content (JS behaviour; JS path tested
  by verifying the script is included and the JS file exists with key symbols).
- Browser find, copy, print, and assistive technology retain access to the full
  content (print CSS forces disclosures open; section content always in DOM).
- Long entity and metadata fixtures remain manageable on mobile (tested via
  section wrapping).
"""

import json
import re
import sys
import tempfile
import unittest
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_outputs import build_document


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class DisclosureParser(HTMLParser):
    """Collect details/summary/section structure from a rendered page."""

    def __init__(self):
        super().__init__()
        self.disclosures: list[dict] = []       # {section_id, open, summary_text}
        self.sections: list[str] = []            # data-page-section values in order
        self._in_summary: bool = False
        self._current_disclosure: dict | None = None
        self._summary_buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "details":
            sid = attrs.get("data-disclosure", "")
            is_open = "open" in attrs
            self._current_disclosure = {"section_id": sid, "open": is_open, "summary_text": ""}
            self.disclosures.append(self._current_disclosure)
        elif tag == "summary":
            self._in_summary = True
            self._summary_buf = []
        if attrs.get("data-page-section"):
            self.sections.append(attrs["data-page-section"])

    def handle_endtag(self, tag):
        if tag == "summary":
            self._in_summary = False
            if self._current_disclosure is not None:
                self._current_disclosure["summary_text"] = "".join(self._summary_buf)

    def handle_data(self, data):
        if self._in_summary:
            self._summary_buf.append(data)


def make_pipeline(tmp, data, doc_id="research-output"):
    directory = Path(tmp) / doc_id
    directory.mkdir(exist_ok=True)
    (directory / "pipeline.json").write_text(json.dumps(data), encoding="utf-8")
    build_document(directory / "pipeline.json", defaultdict(list))
    return (directory / "index.md").read_text(encoding="utf-8")


def parse_disclosure(markup: str) -> DisclosureParser:
    p = DisclosureParser()
    p.feed(markup)
    return p


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class ProgressiveDisclosureTests(unittest.TestCase):
    """Issue #23: progressive disclosure for secondary research sections."""

    def render(self, data, doc_id="research-output"):
        with tempfile.TemporaryDirectory() as tmp:
            return make_pipeline(tmp, data, doc_id)

    # ------------------------------------------------------------------ #
    # 1. Secondary sections wrapped in <details>                          #
    # ------------------------------------------------------------------ #

    def test_secondary_sections_have_disclosure_wrapper(self):
        """Each secondary section is wrapped in a data-disclosure <details>."""
        markup = self.render({"transcription": "text"})
        for sid in ("orientation", "claims", "entities", "downloads", "citation", "history"):
            self.assertIn(
                f'data-disclosure="{sid}"', markup,
                f"Section '{sid}' is missing a disclosure wrapper",
            )

    # ------------------------------------------------------------------ #
    # 2. Primary evidence sections are NOT wrapped                        #
    # ------------------------------------------------------------------ #

    def test_primary_evidence_sections_not_wrapped(self):
        """source and transcription must not be inside a disclosure widget."""
        markup = self.render({"transcription": "text"})
        for sid in ("source", "transcription"):
            self.assertNotIn(
                f'data-disclosure="{sid}"', markup,
                f"Primary section '{sid}' should not be wrapped in a disclosure",
            )

    def test_identity_header_not_wrapped(self):
        """The document identity header must not be collapsible."""
        markup = self.render({"transcription": "text"})
        self.assertNotIn('data-disclosure="identity"', markup)

    # ------------------------------------------------------------------ #
    # 3. orientation and claims are OPEN by default                       #
    # ------------------------------------------------------------------ #

    def test_orientation_open_by_default(self):
        markup = self.render({"transcription": "text"})
        m = re.search(r'<details[^>]*data-disclosure="orientation"[^>]*>', markup)
        self.assertIsNotNone(m, "orientation disclosure not found")
        self.assertIn(" open", m.group(0), "orientation should be open by default")

    def test_claims_open_by_default(self):
        markup = self.render({"transcription": "text"})
        m = re.search(r'<details[^>]*data-disclosure="claims"[^>]*>', markup)
        self.assertIsNotNone(m, "claims disclosure not found")
        self.assertIn(" open", m.group(0), "claims should be open by default")

    # ------------------------------------------------------------------ #
    # 4. entities, downloads, citation, history are CLOSED by default     #
    # ------------------------------------------------------------------ #

    def test_entities_closed_by_default(self):
        markup = self.render({"transcription": "text"})
        m = re.search(r'<details[^>]*data-disclosure="entities"[^>]*>', markup)
        self.assertIsNotNone(m)
        self.assertNotIn(" open", m.group(0), "entities should be closed by default")

    def test_downloads_closed_by_default(self):
        markup = self.render({"transcription": "text"})
        m = re.search(r'<details[^>]*data-disclosure="downloads"[^>]*>', markup)
        self.assertIsNotNone(m)
        self.assertNotIn(" open", m.group(0), "downloads should be closed by default")

    def test_citation_closed_by_default(self):
        markup = self.render({"transcription": "text"})
        m = re.search(r'<details[^>]*data-disclosure="citation"[^>]*>', markup)
        self.assertIsNotNone(m)
        self.assertNotIn(" open", m.group(0), "citation should be closed by default")

    def test_history_closed_by_default(self):
        markup = self.render({"transcription": "text"})
        m = re.search(r'<details[^>]*data-disclosure="history"[^>]*>', markup)
        self.assertIsNotNone(m)
        self.assertNotIn(" open", m.group(0), "history should be closed by default")

    # ------------------------------------------------------------------ #
    # 5. Each summary has summary-title and summary-detail                #
    # ------------------------------------------------------------------ #

    def test_each_disclosure_has_summary_title(self):
        """Every disclosure summary must include a .summary-title span."""
        markup = self.render({"transcription": "text"})
        for sid in ("orientation", "claims", "entities", "downloads", "citation", "history"):
            disc_pos = markup.find(f'data-disclosure="{sid}"')
            self.assertGreater(disc_pos, -1, f"No disclosure for {sid}")
            window = markup[disc_pos : disc_pos + 600]
            self.assertIn('class="summary-title"', window,
                          f"summary-title missing in disclosure for {sid}")

    def test_disclosures_have_summary_detail_span(self):
        """At least one disclosure should carry a .summary-detail count span."""
        markup = self.render({
            "transcription": "text",
            "entities": {"entities": [
                {"type": "PER", "text": "Karl", "normalised": "Karl"},
            ]},
        })
        self.assertIn('class="summary-detail"', markup)

    # ------------------------------------------------------------------ #
    # 6. Entity count shown in entities summary                           #
    # ------------------------------------------------------------------ #

    def test_entity_count_in_entities_summary(self):
        """The entities disclosure summary must state the entity count."""
        data = {
            "transcription": "text",
            "entities": {"entities": [
                {"type": "PER", "text": "Karl",  "normalised": "Karl"},
                {"type": "LOC", "text": "Bern",  "normalised": "Bern"},
                {"type": "ORG", "text": "Kloster", "normalised": "Kloster"},
            ]},
        }
        markup = self.render(data)
        disc_pos = markup.find('data-disclosure="entities"')
        summary_start = markup.find("<summary", disc_pos)
        summary_end   = markup.find("</summary>", summary_start)
        self.assertGreater(summary_end, summary_start)
        summary_html = markup[summary_start:summary_end]
        self.assertIn("3", summary_html, "Entity count 3 not shown in summary")
        self.assertIn("Entit", summary_html)

    def test_zero_entities_summary_label(self):
        """When there are no entities the summary must say so."""
        markup = self.render({"transcription": "text"})
        disc_pos = markup.find('data-disclosure="entities"')
        window = markup[disc_pos : disc_pos + 600]
        self.assertIn("Keine Entitäten", window)

    # ------------------------------------------------------------------ #
    # 7. Section IDs remain accessible inside closed disclosures          #
    # ------------------------------------------------------------------ #

    def test_section_ids_accessible_in_dom(self):
        """id= anchors must be present in the HTML regardless of open/closed state."""
        markup = self.render({"transcription": "text"})
        for sid in ("orientation", "claims", "entities", "downloads", "citation", "history"):
            self.assertIn(f'id="{sid}"', markup,
                          f"Anchor #{sid} missing from DOM")

    def test_closed_section_id_appears_after_its_disclosure_tag(self):
        """The section id inside a closed disclosure must follow its <details> open tag."""
        markup = self.render({"transcription": "text"})
        disc_pos = markup.find('data-disclosure="history"')
        id_pos   = markup.find('id="history"')
        self.assertGreater(id_pos, disc_pos,
                           "id='history' must appear inside its disclosure wrapper")

    # ------------------------------------------------------------------ #
    # 8. data-page-section attributes preserved (regression)             #
    # ------------------------------------------------------------------ #

    def test_section_order_preserved_with_recognitions(self):
        """Disclosure wrapping must not disturb the canonical section order."""
        from build_recognitions import build_recognition_section  # noqa: F401

        data = {"transcription": "text", "recognitions": [
            {"engine": "kraken", "model_id": "m", "text": "cand"}
        ]}
        markup = self.render(data)
        parser = DisclosureParser()
        parser.feed(markup)
        self.assertEqual(parser.sections, [
            "identity", "source", "transcription", "recognitions",
            "orientation", "claims", "entities", "downloads", "citation", "history",
        ])

    def test_section_order_without_recognitions(self):
        markup = self.render({"transcription": "text"})
        parser = DisclosureParser()
        parser.feed(markup)
        self.assertEqual(parser.sections, [
            "identity", "source", "transcription",
            "orientation", "claims", "entities", "downloads", "citation", "history",
        ])

    # ------------------------------------------------------------------ #
    # 9. Print CSS forces disclosures open                                #
    # ------------------------------------------------------------------ #

    def test_print_css_forces_disclosures_open(self):
        """output.css must include a @media print rule that shows hidden disclosure content."""
        css_path = Path(__file__).parent.parent / "docs" / "assets" / "output.css"
        css = css_path.read_text(encoding="utf-8")
        # Locate the print block
        print_block_start = css.find("@media print")
        self.assertGreater(print_block_start, -1, "@media print block not found in CSS")
        print_block = css[print_block_start : print_block_start + 400]
        self.assertIn("page-section-disclosure", print_block,
                      "Print CSS does not reference .page-section-disclosure")

    # ------------------------------------------------------------------ #
    # 10. JS file exists with required symbols                            #
    # ------------------------------------------------------------------ #

    def test_page_disclosure_js_script_exists(self):
        js_path = Path(__file__).parent.parent / "scripts" / "page_disclosure.js"
        self.assertTrue(js_path.exists(), "page_disclosure.js not found in scripts/")

    def test_page_disclosure_js_contains_hashchange_handler(self):
        js_path = Path(__file__).parent.parent / "scripts" / "page_disclosure.js"
        js = js_path.read_text(encoding="utf-8")
        self.assertIn("hashchange", js)

    def test_page_disclosure_js_references_page_section_disclosure(self):
        js_path = Path(__file__).parent.parent / "scripts" / "page_disclosure.js"
        js = js_path.read_text(encoding="utf-8")
        self.assertIn("page-section-disclosure", js)

    # ------------------------------------------------------------------ #
    # 11. Script tag for disclosure JS is injected into generated pages   #
    # ------------------------------------------------------------------ #

    def test_disclosure_script_tag_in_generated_page(self):
        markup = self.render({"transcription": "text"})
        self.assertIn("page-disclosure.js", markup,
                      "page-disclosure.js script tag not found in generated page")

    # ------------------------------------------------------------------ #
    # 12. Field count in claims summary                                   #
    # ------------------------------------------------------------------ #

    def test_field_count_in_claims_summary(self):
        data = {
            "transcription": "text",
            "description": {"source_json": {
                "Inhalt": "Urkunde",
                "Datum": {"wert": "1340", "unsicher": True},
                "Empfänger": "Kloster Königsfelden",
            }},
        }
        markup = self.render(data)
        disc_pos = markup.find('data-disclosure="claims"')
        summary_start = markup.find("<summary", disc_pos)
        summary_end   = markup.find("</summary>", summary_start)
        summary_html  = markup[summary_start:summary_end]
        self.assertIn("3", summary_html, "Field count 3 not in claims summary")
        self.assertIn("Felder", summary_html)

    # ------------------------------------------------------------------ #
    # 13. No duplicate disclosure wrappers per section                    #
    # ------------------------------------------------------------------ #

    def test_no_duplicate_disclosure_wrappers(self):
        """Each section ID must appear in exactly one disclosure wrapper."""
        markup = self.render({"transcription": "text"})
        for sid in ("orientation", "claims", "entities", "downloads", "citation", "history"):
            count = markup.count(f'data-disclosure="{sid}"')
            self.assertEqual(count, 1,
                             f"data-disclosure=\"{sid}\" appears {count} times (expected 1)")


if __name__ == "__main__":
    unittest.main()
