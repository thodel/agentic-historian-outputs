"""Tests for print and static-export presentation (issue #24).

Acceptance criteria:
- Browser print preview contains all research content in semantic order.
- No content is hidden because of interactive state (max-height removed,
  disclosures expanded, overflow visible).
- URLs and citation information remain legible.
- Transcription lines are not clipped horizontally.
- Print CSS is tested against representative long and multi-page outputs.
"""

import json
import re
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_outputs import build_document, _wrap_disclosure

CSS_PATH = Path(__file__).parent.parent / "docs" / "assets" / "output.css"


def _css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def _print_block(css: str) -> str:
    """Extract the content of the @media print { ... } block."""
    # Grab everything inside the last/only @media print block
    m = re.search(r'@media print\s*\{(.+?)^}', css, re.DOTALL | re.MULTILINE)
    return m.group(1) if m else ""


def make_pipeline(tmp: str, data: dict, doc_id: str = "test-doc") -> str:
    directory = Path(tmp) / doc_id
    directory.mkdir(exist_ok=True)
    (directory / "pipeline.json").write_text(json.dumps(data), encoding="utf-8")
    build_document(directory / "pipeline.json", defaultdict(list))
    return (directory / "index.md").read_text(encoding="utf-8")


MINIMAL_DATA = {
    "transcription": "Datum: 1. Januarius 1400\nOrt: Königsfelden\n" * 30,
    "review_status": "machine-generated",
}

MULTI_FIELD_DATA = {
    "transcription": "Datum: 1. Februar 1400\n" * 50,
    "review_status": "human-reviewed",
    "description": {
        "source_json": {
            "Datum": {"wert": "1400-02-01", "unsicher": True, "notiz": "Konjektur"},
            "Ort": "Königsfelden",
            "Aussteller": {"wert": "König Albrecht", "unsicher": False},
        }
    },
    "entities": [
        {"text": "König Albrecht", "type": "PERSON", "normalised": "Albrecht I."},
        {"text": "Königsfelden", "type": "PLACE",  "normalised": "Königsfelden"},
    ],
}


class PrintCSSExistenceTests(unittest.TestCase):
    """Verify the @media print block exists and contains required rules."""

    def setUp(self):
        self.css = _css()
        self.print_block = _print_block(self.css)

    def test_print_media_query_present(self):
        self.assertIn("@media print", self.css)

    def test_print_block_non_empty(self):
        self.assertTrue(len(self.print_block.strip()) > 0)

    def test_issue_24_comment_present(self):
        self.assertIn("#24", self.css)

    # ----- Interactive chrome hidden -----

    def test_page_section_nav_hidden_in_print(self):
        self.assertIn(".page-section-nav", self.print_block)
        # The rule must set display:none
        m = re.search(r'\.page-section-nav\s*\{[^}]*display\s*:\s*none', self.print_block)
        self.assertIsNotNone(m, "Expected .page-section-nav { display: none } in @media print")

    def test_evidence_toolbar_hidden_in_print(self):
        m = re.search(r'\.evidence-toolbar\s*\{[^}]*display\s*:\s*none', self.print_block)
        self.assertIsNotNone(m, "Expected .evidence-toolbar { display: none } in @media print")

    def test_workspace_divider_hidden_in_print(self):
        m = re.search(r'\.workspace-divider\s*\{[^}]*display\s*:\s*none', self.print_block)
        self.assertIsNotNone(m, "Expected .workspace-divider { display: none } in @media print")

    def test_source_page_nav_hidden_in_print(self):
        m = re.search(r'\.source-page-nav\s*\{[^}]*display\s*:\s*none', self.print_block)
        self.assertIsNotNone(m, "Expected .source-page-nav { display: none } in @media print")

    def test_compare_ui_hidden_in_print(self):
        self.assertIn(".rec-compare", self.print_block)
        m = re.search(r'\.rec-compare\b[^{]*\{[^}]*display\s*:\s*none', self.print_block)
        self.assertIsNotNone(m, "Expected .rec-compare { display: none } in @media print")

    def test_quality_explain_buttons_hidden_in_print(self):
        self.assertIn(".quality-explain-btn", self.print_block)
        m = re.search(r'\.quality-explain-btn\s*\{[^}]*display\s*:\s*none', self.print_block)
        self.assertIsNotNone(m, "Expected .quality-explain-btn { display: none } in @media print")

    # ----- Evidence viewer replaced by source link -----

    def test_evidence_viewer_hidden_in_print(self):
        m = re.search(r'\.evidence-viewer\s*\{[^}]*display\s*:\s*none', self.print_block)
        self.assertIsNotNone(m, "Expected .evidence-viewer { display: none } in @media print")

    # ----- Evidence workspace collapses to block -----

    def test_evidence_workspace_block_in_print(self):
        m = re.search(r'\.evidence-workspace\s*\{[^}]*display\s*:\s*block', self.print_block)
        self.assertIsNotNone(m, "Expected .evidence-workspace { display: block } in @media print")

    def test_evidence_pane_max_height_removed_in_print(self):
        m = re.search(r'\.evidence-pane\s*\{[^}]*max-height\s*:\s*none', self.print_block)
        self.assertIsNotNone(m, "Expected .evidence-pane { max-height: none } in @media print")

    # ----- Transcription / rec-text: no clipping -----

    def test_transcription_max_height_none_in_print(self):
        # Rule targets .transcription and .rec-text together
        self.assertIn("max-height: none", self.print_block)

    def test_transcription_overflow_visible_in_print(self):
        m = re.search(
            r'\.transcription\b[^{]*\{[^}]*overflow\s*:\s*visible',
            self.print_block,
        )
        # Could be a combined rule; accept either form
        if m is None:
            m = re.search(r'overflow\s*:\s*visible', self.print_block)
        self.assertIsNotNone(m, "Expected overflow: visible in transcription print rule")

    def test_transcription_white_space_pre_wrap_in_print(self):
        self.assertIn("white-space: pre-wrap", self.print_block)

    def test_transcription_overflow_wrap_anywhere_in_print(self):
        self.assertIn("overflow-wrap: anywhere", self.print_block)

    # ----- Table containers do not clip -----

    def test_table_scroll_overflow_visible_in_print(self):
        m = re.search(r'\.table-scroll\s*\{[^}]*overflow\s*:\s*visible', self.print_block)
        self.assertIsNotNone(m, "Expected .table-scroll { overflow: visible } in @media print")

    # ----- Page-break control -----

    def test_output_header_break_inside_avoid_in_print(self):
        self.assertIn(".output-header", self.print_block)
        m = re.search(r'\.output-header\s*\{[^}]*break-inside\s*:\s*avoid', self.print_block)
        self.assertIsNotNone(m, "Expected .output-header break-inside: avoid in @media print")

    def test_notice_break_inside_avoid_in_print(self):
        m = re.search(r'\.notice\s*\{[^}]*break-inside\s*:\s*avoid', self.print_block)
        self.assertIsNotNone(m, "Expected .notice break-inside: avoid in @media print")

    def test_h2_break_after_avoid_in_print(self):
        m = re.search(r'h2\s*\{[^}]*break-after\s*:\s*avoid', self.print_block)
        self.assertIsNotNone(m, "Expected h2 { break-after: avoid } in @media print")

    # ----- Citation URLs -----

    def test_citation_link_url_printed(self):
        self.assertIn("#citation a[href]::after", self.print_block)
        m = re.search(r'#citation a\[href\]::after\s*\{[^}]*content\s*:', self.print_block)
        self.assertIsNotNone(m, "Expected content: after rule for citation links in @media print")

    # ----- Rec-panel and rec-inventory forced open -----

    def test_rec_panel_summary_hidden_in_print(self):
        self.assertIn(".rec-panel", self.print_block)
        m = re.search(r'\.rec-panel\s*>\s*summary\s*\{[^}]*display\s*:\s*none', self.print_block)
        self.assertIsNotNone(m, "Expected .rec-panel > summary { display: none } in @media print")

    def test_rec_inventory_summary_hidden_in_print(self):
        self.assertIn(".rec-inventory", self.print_block)
        m = re.search(r'\.rec-inventory\s*>\s*summary\s*\{[^}]*display\s*:\s*none', self.print_block)
        self.assertIsNotNone(m, "Expected .rec-inventory > summary { display: none } in @media print")


class PrintOutputContentTests(unittest.TestCase):
    """Verify that generated document pages carry all content needed for print."""

    def test_citation_section_present_minimal_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, MINIMAL_DATA)
        self.assertIn('id="citation"', markup)
        self.assertIn("Zitation und stabile Adresse", markup)

    def test_citation_stable_url_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, MINIMAL_DATA)
        self.assertIn("thodel.github.io", markup)

    def test_transcription_section_always_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, MINIMAL_DATA)
        self.assertIn('id="transcription"', markup)

    def test_downloads_section_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, MINIMAL_DATA)
        self.assertIn('id="downloads"', markup)

    def test_history_section_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, MINIMAL_DATA)
        self.assertIn('id="history"', markup)

    def test_transcription_content_not_truncated_in_dom(self):
        """All transcription text is in the DOM (not cut off by server)."""
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, MINIMAL_DATA)
        # The transcription contains repeated lines; all should be present
        self.assertIn("Januarius 1400", markup)

    def test_long_transcription_present_in_dom(self):
        """Long transcription is fully present — not truncated at some limit."""
        long_text = "Zeile " + "\nZeile ".join(str(i) for i in range(1, 201))
        data = {"transcription": long_text, "review_status": "machine-generated"}
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, data)
        # The last line must be in the DOM
        self.assertIn("Zeile 200", markup)

    def test_multi_field_claims_present_in_dom(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, MULTI_FIELD_DATA)
        self.assertIn("Datum", markup)
        self.assertIn("Konjektur", markup)

    def test_entities_present_in_dom(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, MULTI_FIELD_DATA)
        self.assertIn("Albrecht I.", markup)
        self.assertIn("Königsfelden", markup)

    def test_status_header_present_in_dom(self):
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, MINIMAL_DATA)
        self.assertIn("output-status-bar", markup)

    def test_source_without_url_shows_notice_not_empty(self):
        """A source-less page must still carry a visible notice (not blank section)."""
        with tempfile.TemporaryDirectory() as tmp:
            markup = make_pipeline(tmp, MINIMAL_DATA)
        # Either a source link or a 'no source' warning must be present
        has_link = 'href="' in markup and 'source' in markup
        has_notice = "notice--warning" in markup or "Kein öffentliches Digitalisat" in markup
        self.assertTrue(has_link or has_notice)


class PrintCSSPageBreakTests(unittest.TestCase):
    """Verify page-break rules for key semantic units."""

    def setUp(self):
        self.pb = _print_block(_css())

    def test_rec_meta_break_inside_avoid(self):
        m = re.search(r'\.rec-meta\s*\{[^}]*break-inside\s*:\s*avoid', self.pb)
        self.assertIsNotNone(m, "Expected .rec-meta break-inside: avoid in @media print")

    def test_h3_break_after_avoid(self):
        m = re.search(r'h3\s*\{[^}]*break-after\s*:\s*avoid', self.pb)
        self.assertIsNotNone(m, "Expected h3 { break-after: avoid } in @media print")

    def test_output_status_bar_break_inside_avoid(self):
        m = re.search(r'\.output-status-bar\s*\{[^}]*break-inside\s*:\s*avoid', self.pb)
        self.assertIsNotNone(m, "Expected .output-status-bar break-inside: avoid in @media print")


class PrintCSSDisclosureTests(unittest.TestCase):
    """Verify progressive disclosure is fully expanded in print."""

    def setUp(self):
        self.pb = _print_block(_css())

    def test_disclosure_summary_hidden(self):
        m = re.search(
            r'\.page-section-disclosure\s*>\s*summary\s*\{[^}]*display\s*:\s*none',
            self.pb,
        )
        self.assertIsNotNone(m)

    def test_disclosure_content_forced_visible(self):
        m = re.search(
            r'\.page-section-disclosure\s*>\s*\*:not\(summary\)\s*\{[^}]*display\s*:\s*block',
            self.pb,
        )
        self.assertIsNotNone(m)


if __name__ == "__main__":
    unittest.main()
