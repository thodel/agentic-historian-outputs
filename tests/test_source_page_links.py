"""Per-page source references must reach the reader (#186).

``normalize_source_reference`` has always resolved ``source_pages`` into
page/canvas/image triples, but the only consumer was the evidence viewer, which
is gated on the *document-level* source being an image or a IIIF manifest. A
document whose ``source_url`` is a landing page therefore carried a complete
page mapping that no reader could reach — it existed only inside the embedded
JSON payload.

That is the case these tests pin: a landing page plus per-page references must
still surface the references.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import build_outputs  # noqa: E402

LANDING_PAGE_WITH_PAGES = {
    "source_url": "https://archive.example/item/42",
    "source_pages": [
        {
            "page": "scan_001.jpg",
            "canvas_url": "https://archive.example/item/42/canvas/1",
            "image_url": "https://archive.example/item/42/full/1200,/0/default.jpg",
        },
        {
            "page": "scan_002.jpg",
            "image_url": "https://archive.example/item/42/full/1200,/1/default.jpg",
        },
    ],
}


class SourcePageLinkTests(unittest.TestCase):
    def test_landing_page_source_still_exposes_its_pages(self):
        """The regression this issue is about."""
        panel = build_outputs.source_panel(LANDING_PAGE_WITH_PAGES)
        self.assertIn("source-pages", panel)
        self.assertIn("scan_001.jpg", panel)
        self.assertIn("scan_002.jpg", panel)

    def test_canvas_is_preferred_over_raw_image(self):
        """A canvas is the citable view; the raw image is the fallback."""
        html = build_outputs.source_page_links(
            build_outputs.normalize_source_reference(LANDING_PAGE_WITH_PAGES)["pages"]
        )
        self.assertIn("https://archive.example/item/42/canvas/1", html)
        self.assertNotIn("/0/default.jpg", html)
        # Second page has no canvas, so its image is used instead.
        self.assertIn("/1/default.jpg", html)

    def test_no_pages_renders_nothing(self):
        self.assertEqual(build_outputs.source_page_links([]), "")

    def test_entries_without_a_usable_target_are_skipped(self):
        self.assertEqual(
            build_outputs.source_page_links([{"page": "a", "canvas_url": "", "image_url": ""}]),
            "",
        )

    def test_unsourced_document_gains_no_page_list(self):
        """Existing documents must keep working unchanged."""
        panel = build_outputs.source_panel({})
        self.assertNotIn("source-pages", panel)
        self.assertIn("Kein öffentliches Digitalisat verknüpft", panel)

    def test_labels_and_targets_are_escaped(self):
        html = build_outputs.source_page_links([
            {"page": '<script>x</script>', "canvas_url": "https://e.example/a?b=1&c=2"},
        ])
        self.assertNotIn("<script>", html)
        self.assertIn("&amp;", html)

    def test_summary_is_pluralized_in_german(self):
        one = build_outputs.source_page_links(
            [{"page": "p1", "canvas_url": "https://e.example/1"}]
        )
        two = build_outputs.source_page_links([
            {"page": "p1", "canvas_url": "https://e.example/1"},
            {"page": "p2", "canvas_url": "https://e.example/2"},
        ])
        self.assertIn("1 seitengenauer Quellenverweis", one)
        self.assertIn("2 seitengenaue Quellenverweise", two)


if __name__ == "__main__":
    unittest.main()
