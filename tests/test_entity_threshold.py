"""Not every mentioned entity needs its own page (#239).

Every entity gets one today, which is right for ten documents and wrong for
two thousand: at corpus scale most entities are named once and would produce
tens of thousands of single-mention pages, each a URL to keep and a sitemap
row.

The threshold is configurable rather than fixed because the right value
depends entirely on corpus size. In the present corpus 136 of 140 entities
occur exactly once — not because they are noise, but because there are only
ten documents. A threshold of 2 is correct at two thousand documents and
would gut the site at ten, so the default stays 1.

Two properties matter more than the count. Nothing may be deleted: an entity
below the threshold is still named by the documents that mention it and
counted on the index. And nothing may link to a page that was not generated,
which is the obvious way to break a site while making it smaller.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import build_outputs  # noqa: E402

ENV = "AH_ENTITY_PAGE_MIN_OCCURRENCES"


def occurrence(label, doc_id, kind="PERSON"):
    return {
        "label": label, "surface": label, "type": kind,
        "context": f"{label} im Kontext", "confidence": "high", "uri": "",
        "source_degenerate": False, "doc_id": doc_id,
    }


def index_for(*items):
    index = defaultdict(list)
    for item in items:
        index[build_outputs.entity_key(item["type"], item["label"])].append(item)
    return index


class ThresholdConfigurationTests(unittest.TestCase):
    def test_the_default_changes_nothing(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(ENV, None)
            self.assertEqual(1, build_outputs.entity_page_threshold())

    def test_the_threshold_is_configurable(self):
        with mock.patch.dict(os.environ, {ENV: "3"}):
            self.assertEqual(3, build_outputs.entity_page_threshold())

    def test_a_threshold_below_one_is_clamped(self):
        for value in ("0", "-5"):
            with self.subTest(value=value), mock.patch.dict(os.environ, {ENV: value}):
                self.assertEqual(1, build_outputs.entity_page_threshold())

    def test_a_nonsense_threshold_is_refused_loudly(self):
        with mock.patch.dict(os.environ, {ENV: "lots"}):
            with self.assertRaises(SystemExit):
                build_outputs.entity_page_threshold()

    def test_the_predicate_follows_the_threshold(self):
        self.assertTrue(build_outputs.entity_has_page(2, threshold=2))
        self.assertFalse(build_outputs.entity_has_page(1, threshold=2))


class ThresholdRenderingTests(unittest.TestCase):
    def setUp(self):
        self.original = build_outputs.DOCS
        self._tmp = tempfile.TemporaryDirectory()
        build_outputs.DOCS = Path(self._tmp.name)
        self.root = build_outputs.DOCS / "entities"
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(setattr, build_outputs, "DOCS", self.original)

    def _build(self, index, threshold):
        with mock.patch.dict(os.environ, {ENV: str(threshold)}):
            return build_outputs.build_entity_pages(index)

    def test_a_single_mention_gets_no_page_above_the_threshold(self):
        index = index_for(occurrence("Einmalig", "doc-a"),
                          occurrence("Mehrfach", "doc-a"),
                          occurrence("Mehrfach", "doc-b"))
        targets = self._build(index, threshold=2)

        self.assertEqual(1, len(targets))
        self.assertIn(build_outputs.slug("Mehrfach", "PERSON"), targets)

    def test_everything_gets_a_page_at_the_default(self):
        index = index_for(occurrence("Einmalig", "doc-a"),
                          occurrence("Mehrfach", "doc-a"),
                          occurrence("Mehrfach", "doc-b"))
        self.assertEqual(2, len(self._build(index, threshold=1)))

    def test_omitted_entities_are_declared_on_the_index(self):
        """Silently smaller is the failure mode; say what was left out."""
        index = index_for(occurrence("Einmalig", "doc-a"),
                          occurrence("Auch einmal", "doc-b"))
        self._build(index, threshold=2)

        page = (self.root / "index.md").read_text(encoding="utf-8")
        self.assertIn("entity-threshold-note", page)
        self.assertIn("2 Entitäten", page)
        self.assertIn("nicht entfernt", page)

    def test_no_note_appears_when_nothing_was_left_out(self):
        index = index_for(occurrence("Einmalig", "doc-a"))
        self._build(index, threshold=1)
        page = (self.root / "index.md").read_text(encoding="utf-8")
        self.assertNotIn("entity-threshold-note", page)


class LinkIntegrityTests(unittest.TestCase):
    """A smaller site that links to pages it did not build is a broken site."""

    def setUp(self):
        self.original = build_outputs.DOCS
        self._tmp = tempfile.TemporaryDirectory()
        build_outputs.DOCS = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(setattr, build_outputs, "DOCS", self.original)

    def test_documents_do_not_link_to_pages_below_the_threshold(self):
        import json

        docs = build_outputs.DOCS
        for doc_id, labels in (("doc-a", ["Einmalig", "Mehrfach"]),
                               ("doc-b", ["Mehrfach"])):
            directory = docs / doc_id
            directory.mkdir(parents=True)
            (directory / "pipeline.json").write_text(json.dumps({
                "doc_id": doc_id,
                "transcription": "Text",
                "description": {"source_description": "x", "source_json": {}},
                "entities": [{"name": label, "type": "PERSON",
                              "context": "c", "confidence": "high"}
                             for label in labels],
                "errors": [], "a_meta": {}, "recognitions": [],
            }), encoding="utf-8")

        index = index_for(occurrence("Einmalig", "doc-a"),
                          occurrence("Mehrfach", "doc-a"),
                          occurrence("Mehrfach", "doc-b"))

        with mock.patch.dict(os.environ, {ENV: "2"}):
            targets = build_outputs.build_entity_pages(index)
            for doc_id in ("doc-a", "doc-b"):
                build_outputs.build_document(
                    docs / doc_id / "pipeline.json", index,
                    collect_entities=False)

        for doc_id in ("doc-a", "doc-b"):
            page = (docs / doc_id / "index.md").read_text(encoding="utf-8")
            linked = set(re.findall(r'href="\.\./entities/([^"/]+)/"', page))
            with self.subTest(doc=doc_id):
                self.assertEqual(
                    set(), linked - targets,
                    "a document links to an entity page that was not generated",
                )

        below = (docs / "doc-a" / "index.md").read_text(encoding="utf-8")
        self.assertIn(
            "Einmalig", below,
            "an entity below the threshold vanished from the document that "
            "mentions it; it must still be named, just not linked",
        )
        self.assertIn("entity-unlinked", below)
        self.assertNotIn(
            f'entities/{build_outputs.slug("Einmalig", "PERSON")}/', below,
            "a below-threshold entity is still linked to a page that does "
            "not exist",
        )


if __name__ == "__main__":
    unittest.main()
