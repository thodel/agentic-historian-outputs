"""The catalogue has to survive a corpus, not just a demonstration (#239).

The existing scale test benchmarks JavaScript matching over 5,000 objects in
memory. That is not the thing that breaks. What breaks is the page: every
record ships as a ~4 KB card and the browser filters that DOM, so two
thousand records is an eight-megabyte download before a reader has typed
anything.

This builds a real corpus through the real generator and asserts the three
properties that have to hold together. Any two of them are easy:

* the front page is bounded — it stops growing with the corpus;
* nothing becomes unreachable without JavaScript — every record is still
  linked from a collection page;
* search stays complete — the generated index covers every record, including
  the ones the front page no longer shows.

Dropping the third is how a bounded catalogue quietly starts lying about how
many results a query has.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import build_index  # noqa: E402
import build_outputs  # noqa: E402

#: Enough to exceed the page size several times over while keeping the build
#: inside a few seconds. The invariants do not get truer with more documents.
CORPUS = 120
PAGE_SIZE = 25


class CatalogueScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.docs = Path(cls._tmp.name) / "docs"
        (cls.docs / "assets").mkdir(parents=True)
        for index in range(CORPUS):
            doc_id = f"synth-{index:04d}"
            directory = cls.docs / doc_id
            directory.mkdir()
            (directory / "pipeline.json").write_text(json.dumps({
                "doc_id": doc_id,
                "collection": f"korpus-{index % 4}",
                "transcription": f"Synthetischer Text {index}. " + "wort " * 20,
                "description": {
                    "source_description": f"Beschreibung {index}",
                    "source_json": {"Datierung": str(1400 + index % 150),
                                    "Sprache": "Deutsch"},
                },
                "entities": [{"name": f"Person {index % 11}", "type": "PERSON",
                              "context": "Kontext", "confidence": "high"}],
                "errors": [], "a_meta": {"qa_score": 0.8}, "recognitions": [],
            }, ensure_ascii=False), encoding="utf-8")

        originals = (build_index.DOCS, build_outputs.DOCS)
        build_index.DOCS = cls.docs
        build_outputs.DOCS = cls.docs
        try:
            with mock.patch.dict(os.environ, {
                    "AH_CATALOGUE_PAGE_SIZE": str(PAGE_SIZE)}):
                build_index.build()
        finally:
            build_index.DOCS, build_outputs.DOCS = originals

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    # ── helpers ─────────────────────────────────────────────────────────

    def front_page(self) -> str:
        return (self.docs / "index.md").read_text(encoding="utf-8")

    def ids_on(self, text: str) -> set[str]:
        return set(re.findall(r'data-document-id="([^"]+)"', text))

    def search_index(self) -> dict:
        return json.loads(
            (self.docs / "catalogue-index.json").read_text(encoding="utf-8"))

    def collection_pages(self) -> list[Path]:
        return sorted((self.docs / "collections").glob("*/index.md"))

    # ── the three properties ────────────────────────────────────────────

    def test_the_front_page_is_bounded(self):
        shown = self.ids_on(self.front_page())
        self.assertEqual(
            PAGE_SIZE, len(shown),
            f"the front page rendered {len(shown)} cards for a corpus of "
            f"{CORPUS}; it grows with the corpus",
        )

    def test_nothing_is_unreachable_without_javascript(self):
        reachable = self.ids_on(self.front_page())
        for page in self.collection_pages():
            reachable |= self.ids_on(page.read_text(encoding="utf-8"))

        published = {path.parent.name
                     for path in self.docs.glob("*/pipeline.json")}
        self.assertEqual(
            set(), published - reachable,
            "documents are published but reachable only with JavaScript",
        )

    def test_search_covers_every_record_not_just_the_visible_ones(self):
        index = self.search_index()
        published = {path.parent.name
                     for path in self.docs.glob("*/pipeline.json")}
        indexed = {row["id"] for row in index["records"]}

        self.assertEqual(CORPUS, index["count"])
        self.assertEqual(
            set(), published - indexed,
            "the search index is missing records, so the search box would "
            "answer from a partial corpus without saying so",
        )

    # ── what the bound is worth ─────────────────────────────────────────

    def test_the_index_is_far_smaller_than_the_cards_it_replaces(self):
        index_bytes = (self.docs / "catalogue-index.json").stat().st_size
        page_bytes = (self.docs / "index.md").stat().st_size
        per_record = index_bytes / CORPUS
        per_card = page_bytes / PAGE_SIZE
        self.assertLess(
            per_record, per_card / 2,
            f"a search-index row costs {per_record:.0f} bytes against "
            f"{per_card:.0f} for a card; the index is not buying much",
        )

    def test_collection_pages_stay_small(self):
        for page in self.collection_pages():
            with self.subTest(page=page.name):
                self.assertLess(
                    page.stat().st_size, 100_000,
                    "a collection page is growing like the front page did",
                )

    def test_every_collection_is_linked_from_the_front_page(self):
        front = self.front_page()
        for page in self.collection_pages():
            with self.subTest(collection=page.parent.name):
                self.assertIn(f"collections/{page.parent.name}/", front)

    def test_the_page_states_how_much_it_is_showing(self):
        """A bounded page that does not say so is a page that looks complete."""
        front = self.front_page()
        self.assertIn(f'data-total-records="{CORPUS}"', front)
        self.assertIn(f'data-shown-records="{PAGE_SIZE}"', front)
        self.assertIn(f"{PAGE_SIZE} von {CORPUS} Ausgaben", front)


class PageSizeConfigurationTests(unittest.TestCase):
    def test_the_default_leaves_the_present_corpus_whole(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AH_CATALOGUE_PAGE_SIZE", None)
            self.assertGreater(build_index.catalogue_page_size(), 10)

    def test_a_nonsense_page_size_is_refused_loudly(self):
        with mock.patch.dict(os.environ, {"AH_CATALOGUE_PAGE_SIZE": "viele"}):
            with self.assertRaises(SystemExit):
                build_index.catalogue_page_size()


class CollectionAssignmentTests(unittest.TestCase):
    def _record(self, collection="", year=2026):
        from datetime import datetime, timezone
        return build_index.Record(
            doc_id="d", created=datetime(year, 1, 1, tzinfo=timezone.utc),
            date_label="", language="", script="", document_type="",
            entities=0, pages=None, qa_score=None, errors=0, is_test=False,
            preview="", review_status="machine-generated",
            collection=collection,
        )

    def test_a_curator_declared_collection_wins(self):
        self.assertEqual("kloster-koenigsfelden",
                         build_index.collection_of(
                             self._record("kloster-koenigsfelden")))

    def test_otherwise_the_publication_year_partitions(self):
        self.assertEqual("2024", build_index.collection_of(
            self._record(year=2024)))

    def test_collection_slugs_are_url_safe(self):
        """Diacritics fold; a naive filter made "Königsfelden" "k-ngsfelden"."""
        self.assertEqual(
            "kloster-konigsfelden-1400",
            build_index.slug_for_collection("Kloster Königsfelden 1400"))
        self.assertEqual("ohne-sammlung", build_index.slug_for_collection("///"))


if __name__ == "__main__":
    unittest.main()
