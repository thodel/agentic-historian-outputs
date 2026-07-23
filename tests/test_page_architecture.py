import json
import sys
import tempfile
import unittest
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_outputs import build_document


class StructureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings = []
        self.ids = set()
        self.sections = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.headings.append(int(tag[1]))
        if attrs.get("data-page-section"):
            self.sections.append(attrs["data-page-section"])


def recognition(text="candidate", error=""):
    return {"engine": "kraken", "model_id": "model", "text": text, "error": error}


class PageArchitectureTests(unittest.TestCase):
    def render(self, data, doc_id="research-output"):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / doc_id
            directory.mkdir()
            pipeline = directory / "pipeline.json"
            pipeline.write_text(json.dumps(data), encoding="utf-8")
            build_document(pipeline, defaultdict(list))
            return (directory / "index.md").read_text(encoding="utf-8")

    def parse(self, markup):
        parser = StructureParser(); parser.feed(markup)
        return parser

    def test_canonical_section_order_with_recognitions(self):
        page = self.parse(self.render({
            "source_url": "https://archive.org/item/1",
            "transcription": "selected",
            "recognitions": [recognition()],
        }))
        self.assertEqual(page.sections, [
            "identity", "source", "transcription", "recognitions",
            "orientation", "claims", "entities", "downloads", "citation", "history",
        ])

    def test_recognitionless_and_sourceless_variants_keep_architecture(self):
        page = self.parse(self.render({"transcription": "legacy"}, "legacy-output"))
        self.assertNotIn("recognitions", page.sections)
        self.assertEqual(page.sections[:3], ["identity", "source", "transcription"])
        self.assertIn("Kein öffentliches Digitalisat", self.render({"transcription": "legacy"}))

    def test_failed_recognition_remains_in_evidence_region(self):
        markup = self.render({
            "transcription": "selected",
            "recognitions": [recognition(text="", error="timeout")],
        })
        page = self.parse(markup)
        self.assertIn("recognitions", page.sections)
        self.assertIn("Erkennung fehlgeschlagen", markup)

    def test_stable_deep_links_and_heading_hierarchy(self):
        page = self.parse(self.render({"transcription": "text", "recognitions": [recognition()]}))
        self.assertTrue({"transcription", "claims"}.issubset(page.ids))
        self.assertEqual(page.headings[0], 1)
        self.assertTrue(all(b <= a + 1 for a, b in zip(page.headings, page.headings[1:])))

    def test_test_output_is_visibly_distinguished(self):
        markup = self.render({"transcription": "fixture"}, "sample-test")
        self.assertIn('<p class="output-kicker">Testlauf</p>', markup)


class StatusHeaderTests(unittest.TestCase):
    """Issue #21: redesigned document status header."""

    def render(self, data, doc_id="research-output"):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / doc_id
            directory.mkdir()
            pipeline = directory / "pipeline.json"
            pipeline.write_text(json.dumps(data), encoding="utf-8")
            build_document(pipeline, defaultdict(list))
            return (directory / "index.md").read_text(encoding="utf-8")

    # --- Verification status semantics ---

    def test_machine_generated_badge_present_and_typed(self):
        markup = self.render({"transcription": "text"})
        # Typed class on badge — not a raw 'QA' label
        self.assertIn('output-status-badge--machine-generated', markup)
        self.assertIn('data-review-status="machine-generated"', markup)
        # No ambiguous generic QA percentage (issue #21 acceptance criterion)
        self.assertNotIn('QA ', markup)
        self.assertNotIn('<span>QA', markup)

    def test_human_reviewed_badge_distinct_from_machine_generated(self):
        markup = self.render({"review_status": "human-reviewed", "transcription": "text"})
        self.assertIn('output-status-badge--human-reviewed', markup)
        self.assertIn('data-review-status="human-reviewed"', markup)
        self.assertNotIn('output-status-badge--machine-generated', markup)

    def test_human_verified_badge_distinct_from_others(self):
        markup = self.render({"review_status": "human-verified", "transcription": "text"})
        self.assertIn('output-status-badge--human-verified', markup)
        self.assertIn('data-review-status="human-verified"', markup)
        self.assertNotIn('output-status-badge--machine-generated', markup)
        self.assertNotIn('output-status-badge--human-reviewed', markup)
        # Verified output does NOT carry the generic machine-generated warning
        self.assertNotIn('Maschinell erzeugt:', markup)

    def test_three_review_states_are_all_distinct(self):
        states = ["machine-generated", "human-reviewed", "human-verified"]
        labels = set()
        for state in states:
            markup = self.render({"review_status": state, "transcription": "t"})
            # Each state must produce a unique badge class
            for cls in ["machine-generated", "human-reviewed", "human-verified"]:
                if state == cls:
                    self.assertIn(f'output-status-badge--{cls}', markup, f"{state} should produce --{cls}")
                else:
                    self.assertNotIn(f'output-status-badge--{cls}', markup, f"{state} must not produce --{cls}")

    # --- Accessible explanation ---

    def test_machine_generated_has_accessible_explanation_button(self):
        markup = self.render({"transcription": "text"})
        # Explanation button present for non-verified outputs
        self.assertIn('quality-explain-btn', markup)
        self.assertIn('aria-expanded="false"', markup)
        self.assertIn('aria-controls="quality-explanation-verification_needed-hdr"', markup)

    def test_human_verified_has_no_explanation_button_in_status_bar(self):
        markup = self.render({"review_status": "human-verified", "transcription": "text"})
        # Verified outputs don't need a "human review recommended" button
        self.assertNotIn('quality-explanation-verification_needed', markup)

    # --- Legacy QA badge ---

    def test_legacy_qa_is_labelled_as_legacy_not_ambiguous(self):
        markup = self.render({
            "a_meta": {"qa_score": 0.1},
            "transcription": "text",
        })
        # Legacy QA badge must be present and typed; ambiguous 'QA 10%' gone
        self.assertIn('output-status-badge--legacy', markup)
        self.assertIn('Legacy-QA', markup)
        self.assertNotIn('>QA 10%<', markup)
        self.assertNotIn('<span>QA', markup)

    def test_no_legacy_badge_when_qa_score_absent(self):
        markup = self.render({"transcription": "text"})
        self.assertNotIn('output-status-badge--legacy', markup)

    # --- Recognition-problem warnings ---

    def test_recognition_failure_warning_badge_present(self):
        markup = self.render({
            "transcription": "selected",
            "recognitions": [{"engine": "test", "model_id": "m", "text": "", "error": "timeout"}],
        })
        self.assertIn('output-status-badge--warning', markup)
        self.assertIn('Erkennungsproblem', markup)
        # Warning uses text + icon, not only colour
        self.assertIn('\u26a0', markup)  # ⚠

    def test_no_warning_badge_when_all_recognitions_clean(self):
        markup = self.render({
            "transcription": "selected",
            "recognitions": [{"engine": "kraken", "model_id": "m", "text": "clean text"}],
        })
        self.assertNotIn('output-status-badge--warning', markup)

    # --- Interpretation notice differentiated by level ---

    def test_machine_generated_notice_text(self):
        markup = self.render({"transcription": "text"})
        self.assertIn('<strong>Maschinell erzeugt:</strong>', markup)

    def test_human_reviewed_notice_text(self):
        markup = self.render({"review_status": "human-reviewed", "transcription": "text"})
        self.assertIn('<strong>Gepr\u00fcft (nicht vollst\u00e4ndig verifiziert):</strong>', markup)

    def test_human_verified_notice_text(self):
        markup = self.render({"review_status": "human-verified", "transcription": "text"})
        self.assertIn('<strong>Verifiziert:</strong>', markup)

    # --- Status bar structure ---

    def test_status_bar_has_role_group(self):
        markup = self.render({"transcription": "text"})
        self.assertIn('role="group"', markup)
        self.assertIn('aria-label="Verifikationsstatus und Qualit\u00e4t"', markup)

    def test_pages_badge_present_when_pages_known(self):
        markup = self.render({"a_meta": {"pages": "3"}, "transcription": "text"})
        self.assertIn('output-status-badge--pages', markup)
        self.assertIn('3', markup)

    def test_pages_badge_absent_when_unknown(self):
        markup = self.render({"transcription": "text"})
        self.assertNotIn('output-status-badge--pages', markup)

    # --- No regression on section order ---

    def test_identity_section_still_first(self):
        parser = StructureParser()
        markup = self.render({"transcription": "text"})
        parser.feed(markup)
        self.assertEqual(parser.sections[0], "identity")

    def test_header_always_contains_h1_with_doc_id(self):
        markup = self.render({"transcription": "text"}, "my-doc-001")
        self.assertIn('<h1>my-doc-001</h1>', markup)


class PageNavTests(unittest.TestCase):
    """Issue #22: accessible in-page navigation for long document pages."""

    def render(self, data, doc_id="nav-doc"):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / doc_id
            directory.mkdir()
            pipeline = directory / "pipeline.json"
            pipeline.write_text(json.dumps(data), encoding="utf-8")
            build_document(pipeline, defaultdict(list))
            return (directory / "index.md").read_text(encoding="utf-8")

    # --- Nav presence and role ---

    def test_page_nav_present_in_document_page(self):
        """A page-section-nav element is rendered on every document page."""
        markup = self.render({"transcription": "text"})
        self.assertIn('class="page-section-nav"', markup)

    def test_page_nav_has_accessible_label(self):
        """Nav has aria-label for screen readers."""
        markup = self.render({"transcription": "text"})
        self.assertIn('aria-label="Seitennavigation"', markup)

    def test_page_nav_has_data_attribute(self):
        """Nav carries data-page-nav for potential JS enhancement."""
        markup = self.render({"transcription": "text"})
        self.assertIn('data-page-nav', markup)

    def test_page_nav_uses_ordered_list(self):
        """Nav list is an <ol> (reflects page document order)."""
        markup = self.render({"transcription": "text"})
        self.assertIn('class="page-section-nav-list"', markup)
        # The list element used must be ol, not ul
        nav_start = markup.index('class="page-section-nav"')
        nav_slice = markup[nav_start:nav_start + 300]
        self.assertIn('<ol', nav_slice)
        self.assertNotIn('<ul', nav_slice)

    # --- Nav items target real section IDs ---

    def test_all_nav_items_target_existing_section_ids(self):
        """Every href in the nav corresponds to a section ID present in the page."""
        markup = self.render({
            "transcription": "sample",
            "recognitions": [{"engine": "k", "model_id": "m", "text": "x"}],
        })
        parser = StructureParser()
        parser.feed(markup)
        # Extract href anchors from within the nav
        import re
        nav_match = re.search(
            r'<nav[^>]*data-page-nav[^>]*>(.*?)</nav>', markup, re.DOTALL
        )
        self.assertIsNotNone(nav_match, "No page-section-nav found")
        hrefs = re.findall(r'href="#([^"]+)"', nav_match.group(1))
        self.assertGreater(len(hrefs), 0, "Nav has no links")
        for href in hrefs:
            self.assertIn(href, parser.ids, f"Nav links to #{href} but section not found")

    def test_nav_has_core_sections(self):
        """Core always-present sections appear in the nav."""
        markup = self.render({"transcription": "text"})
        for sid in ("source", "transcription", "orientation", "claims",
                    "entities", "downloads", "citation", "history"):
            self.assertIn(f'href="#{sid}"', markup, f"Nav missing link to #{sid}")

    def test_recognitions_nav_item_present_when_recognitions_exist(self):
        """#recognitions link in nav only when recognition data is present."""
        markup = self.render({
            "transcription": "text",
            "recognitions": [{"engine": "k", "model_id": "m", "text": "x"}],
        })
        self.assertIn('href="#recognitions"', markup)

    def test_recognitions_nav_item_absent_when_no_recognitions(self):
        """#recognitions nav link omitted when there are no recognitions."""
        markup = self.render({"transcription": "text"})
        self.assertNotIn('href="#recognitions"', markup)

    def test_no_duplicate_nav_hrefs(self):
        """Each section appears at most once in the nav."""
        import re
        markup = self.render({"transcription": "text"})
        nav_match = re.search(
            r'<nav[^>]*data-page-nav[^>]*>(.*?)</nav>', markup, re.DOTALL
        )
        self.assertIsNotNone(nav_match)
        hrefs = re.findall(r'href="#([^"]+)"', nav_match.group(1))
        self.assertEqual(len(hrefs), len(set(hrefs)), "Duplicate section links in nav")

    def test_nav_links_are_anchors(self):
        """Nav list items contain <a> tags with fragment hrefs."""
        import re
        markup = self.render({"transcription": "text"})
        nav_match = re.search(
            r'<nav[^>]*data-page-nav[^>]*>(.*?)</nav>', markup, re.DOTALL
        )
        self.assertIsNotNone(nav_match)
        anchors = re.findall(r'<a href="#', nav_match.group(1))
        self.assertGreater(len(anchors), 0)

    # --- Nav placement relative to page sections ---

    def test_nav_appears_after_header_before_evidence(self):
        """Nav is inserted between the identity header and the first evidence section."""
        markup = self.render({"transcription": "text"})
        header_pos = markup.find('data-page-section="identity"')
        nav_pos    = markup.find('data-page-nav')
        source_pos = markup.find('data-page-section="source"')
        self.assertGreater(nav_pos, header_pos,
                           "Nav should appear after identity header")
        self.assertLess(nav_pos, source_pos,
                        "Nav should appear before source section")

    # --- Regression: existing section IDs must not be removed ---

    def test_section_ids_unchanged_by_nav_addition(self):
        """Adding nav must not disturb the canonical section IDs."""
        markup = self.render({"transcription": "text"})
        parser = StructureParser()
        parser.feed(markup)
        for expected_id in ("source", "transcription", "orientation",
                            "claims", "entities", "downloads", "citation", "history"):
            self.assertIn(expected_id, parser.ids,
                          f"Section #{expected_id} missing after nav addition")


if __name__ == "__main__":
    unittest.main()
