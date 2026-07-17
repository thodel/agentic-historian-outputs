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
        self.assertIn("rec-panel--error", markup)

    def test_stable_deep_links_and_heading_hierarchy(self):
        page = self.parse(self.render({"transcription": "text", "recognitions": [recognition()]}))
        self.assertTrue({"transcription", "claims"}.issubset(page.ids))
        self.assertEqual(page.headings[0], 1)
        self.assertTrue(all(b <= a + 1 for a, b in zip(page.headings, page.headings[1:])))

    def test_test_output_is_visibly_distinguished(self):
        markup = self.render({"transcription": "fixture"}, "sample-test")
        self.assertIn('<p class="output-kicker">Testlauf</p>', markup)


if __name__ == "__main__":
    unittest.main()
