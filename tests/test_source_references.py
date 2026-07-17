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


if __name__ == "__main__":
    unittest.main()
