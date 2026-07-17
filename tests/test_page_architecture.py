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


if __name__ == "__main__":
    unittest.main()
