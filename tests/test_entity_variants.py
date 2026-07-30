import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import build_outputs


def occurrence(label, surface, doc_id):
    return {
        "label": label, "surface": surface, "type": "SOCIAL_GROUP",
        "context": f"{surface} im Kontext", "confidence": "", "uri": "",
        "source_degenerate": False, "doc_id": doc_id,
    }


class EntityVariantKeyTests(unittest.TestCase):
    def test_case_and_diacritic_folding(self):
        self.assertEqual(
            build_outputs.folded_entity_label("JÜDEN"),
            build_outputs.folded_entity_label("juden"),
        )

    def test_long_s_folding(self):
        self.assertEqual(
            build_outputs.folded_entity_label("Conſtanz"),
            build_outputs.folded_entity_label("Constanz"),
        )

    def test_display_label_prefers_frequent_then_title_case_form(self):
        items = [
            occurrence("juden", "juden", "a"),
            occurrence("Juden", "Juden", "b"),
        ]
        self.assertEqual(build_outputs.entity_display_label(items), "Juden")


class EntityVariantRenderingTests(unittest.TestCase):
    def setUp(self):
        self.original_docs = build_outputs.DOCS
        self.temp = tempfile.TemporaryDirectory()
        build_outputs.DOCS = Path(self.temp.name)

    def tearDown(self):
        build_outputs.DOCS = self.original_docs
        self.temp.cleanup()

    def test_juden_variants_share_page_with_all_contexts(self):
        items = [
            occurrence("Juden", "Juden", "doc-a"),
            occurrence("juden", "juden", "doc-b"),
        ]
        index = defaultdict(list, {
            build_outputs.entity_key("SOCIAL_GROUP", "Juden"): items
        })
        build_outputs.build_entity_pages(index)
        pages = list((build_outputs.DOCS / "entities").glob("juden-*/index.md"))
        self.assertEqual(len(pages), 1)
        markup = pages[0].read_text()
        self.assertIn("2 Vorkommen", markup)
        self.assertIn("<code>Juden</code>", markup)
        self.assertIn("<code>juden</code>", markup)
        self.assertIn("../../doc-a/", markup)
        self.assertIn("../../doc-b/", markup)
        self.assertIn("Juden im Kontext", markup)
        self.assertIn("juden im Kontext", markup)

    def test_stale_variant_page_is_removed(self):
        stale = (
            build_outputs.DOCS / "entities"
            / build_outputs.slug("juden", "SOCIAL_GROUP")
        )
        stale.mkdir(parents=True)
        (stale / "index.md").write_text("stale")
        items = [
            occurrence("Juden", "Juden", "doc-a"),
            occurrence("juden", "juden", "doc-b"),
        ]
        build_outputs.build_entity_pages(defaultdict(list, {
            build_outputs.entity_key("SOCIAL_GROUP", "Juden"): items
        }))
        self.assertFalse(stale.exists())


if __name__ == "__main__":
    unittest.main()
