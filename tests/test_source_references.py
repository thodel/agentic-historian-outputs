import json
import sys
import unittest
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_outputs import source_panel
from source_references import normalize_source_reference, public_url


class SourceReferenceTests(unittest.TestCase):
    def test_iiif_aliases_normalize_as_manifests(self):
        for key in ("iiif_manifest", "manifest_url"):
            source = normalize_source_reference({key: "https://iiif.archive.org/item/manifest"})
            self.assertEqual(source["type"], "iiif_manifest")
            self.assertEqual(source["manifest_url"], source["url"])

    def test_direct_image_and_landing_page_are_distinct(self):
        image = normalize_source_reference({"source_url": "https://archive.org/image.JPG"})
        landing = normalize_source_reference({"source_url": "https://archive.org/item/42"})
        self.assertEqual(image["type"], "image")
        self.assertEqual(landing["type"], "landing_page")

    def test_missing_and_partial_metadata_have_stable_shape(self):
        source = normalize_source_reference({"source_label": "Archive item"})
        self.assertEqual(
            list(source),
            ["type", "label", "attribution", "rights", "url", "manifest_url", "image_url", "pages"],
        )
        self.assertEqual(source["type"], "missing")
        self.assertEqual(source["label"], "Archive item")

    def test_private_placeholder_local_and_credential_urls_are_rejected(self):
        rejected = (
            "/data/image.jpg", "file:///data/image.jpg", "ftp://archive.org/a.jpg",
            "http://localhost/a", "http://127.0.0.1/a", "http://10.0.0.4/a",
            "https://example.com/a", "https://user:secret@archive.org/a",
        )
        for url in rejected:
            with self.subTest(url=url):
                self.assertEqual(public_url(url), "")

    def test_page_mapping_accepts_canvas_and_image_forms(self):
        source = normalize_source_reference({
            "source_url": "https://archive.org/item/42",
            "source_pages": [
                {"page": "folio-1", "canvas_url": "https://iiif.archive.org/canvas/1"},
                {"recognition_page": "folio-2", "image": "https://archive.org/folio-2.jpg"},
                {"page": "folio-3", "image": "file:///tmp/private.jpg"},
            ],
        })
        self.assertEqual(len(source["pages"]), 2)
        self.assertEqual(source["pages"][0]["page"], "folio-1")
        self.assertEqual(source["pages"][1]["image_url"], "https://archive.org/folio-2.jpg")

    def test_frontend_payload_is_small_valid_and_escaped(self):
        markup = source_panel({
            "source_url": "https://archive.org/item/42",
            "source_label": '<Archive & "catalogue">',
            "source_attribution": "State Archive",
            "source_rights": "CC BY 4.0",
        })
        raw = markup.split("data-source-reference>", 1)[1].split("</script>", 1)[0]
        payload = json.loads(unescape(raw))
        self.assertEqual(payload["type"], "landing_page")
        self.assertIn("State Archive", markup)
        self.assertNotIn('<Archive & "catalogue">', markup)



    def test_page_mapping_accepts_page_id_and_recognition_page_aliases(self):
        """Both page_id and recognition_page map to the same page field inside source_pages."""
        for field in ("page_id", "recognition_page"):
            source = normalize_source_reference({
                "source_url": "https://archive.org/item/42",
                "source_pages": [
                    {field: "folio-1", "image": "https://archive.org/folio-1.jpg"},
                ],
            })
            self.assertEqual(len(source["pages"]), 1)
            self.assertEqual(source["pages"][0]["page"], "folio-1")

    def test_page_mapping_skips_private_images(self):
        """Page entries with only private images are excluded from pages list."""
        source = normalize_source_reference({
            "source_url": "https://archive.org/item/42",
            "source_pages": [
                {"page": "public-page", "image": "https://archive.org/public.jpg"},
                {"page": "private-page", "image": "file:///tmp/private.jpg"},
            ],
        })
        self.assertEqual(len(source["pages"]), 1)
        self.assertEqual(source["pages"][0]["page"], "public-page")

    def test_workspace_source_panel_renders_minimal_html_without_source(self):
        """Without source data the source panel renders a warning notice."""
        from build_outputs import source_panel
        html = source_panel({})
        self.assertIn("notice--warning", html)
        self.assertIn("Kein öffentliches Digitalisat", html)
        self.assertNotIn("data-evidence-viewer", html)

    def test_workspace_source_panel_escapes_html_in_label(self):
        """HTML in source_label is escaped in the rendered anchor text."""
        from build_outputs import source_panel
        html = source_panel({"source_url": "https://archive.org/item/42",
                             "source_label": '<script>evil()</script>'})
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_workspace_multi_page_canvas_and_image_together(self):
        """A page entry can have both canvas_url and image_url simultaneously."""
        source = normalize_source_reference({
            "source_url": "https://archive.org/item/42",
            "source_pages": [
                {"page": "folio-1", "canvas_url": "https://iiif.archive.org/canvas/1",
                 "image_url": "https://archive.org/folio-1.jpg"},
            ],
        })
        self.assertEqual(len(source["pages"]), 1)
        self.assertEqual(source["pages"][0]["canvas_url"], "https://iiif.archive.org/canvas/1")
        self.assertEqual(source["pages"][0]["image_url"], "https://archive.org/folio-1.jpg")

    def test_workspace_page_nav_absent_for_single_page(self):
        """Source page navigation is omitted when there is only one page."""
        from build_outputs import source_panel
        html = source_panel({
            "source_url": "https://archive.org/item/42",
            "source_pages": [
                {"page": "p1", "canvas_url": "https://iiif.archive.org/canvas/1"},
            ],
        })
        self.assertNotIn("source-page-nav", html)

    def test_workspace_page_nav_present_for_multiple_pages(self):
        """Source page navigation is present when there are two or more pages."""
        from build_outputs import source_panel
        html = source_panel({
            "source_url": "https://archive.org/iiif/manifest.json",
            "source_pages": [
                {"page": "p1", "canvas_url": "https://iiif.archive.org/canvas/1"},
                {"page": "p2", "canvas_url": "https://iiif.archive.org/canvas/2"},
            ],
        })
        self.assertIn("source-page-nav", html)
        self.assertEqual(html.count("data-source-page="), 2)

    def test_workspace_source_pages_uses_source_pages_field_preferred(self):
        """normalize_source_reference prefers source_pages over legacy page_mapping."""
        source_pages = normalize_source_reference({
            "source_url": "https://archive.org/item/42",
            "source_pages": [{"page": "new", "canvas_url": "https://iiif.archive.org/c/1"}],
            "page_mapping": {"old": "https://archive.org/old.jpg"},
        })
        legacy_mapping = normalize_source_reference({
            "source_url": "https://archive.org/item/42",
            "page_mapping": {"old": "https://archive.org/old.jpg"},
        })
        self.assertEqual(source_pages["pages"][0]["page"], "new")
        self.assertEqual(legacy_mapping["pages"][0]["page"], "old")


if __name__ == "__main__":
    unittest.main()
