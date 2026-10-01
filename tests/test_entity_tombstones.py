"""Entity pages outlive the evidence behind them, and must say so.

An entity page's URL is citable. When a document is re-recognised, superseded
or corrected, the entities it used to mention stop being generated — but the
pages stay on disk. Before this was reconciled, 191 of 331 committed entity
pages were supported by no current record, and every one of them was still
listed in ``sitemap.xml``. A reader arriving at one saw an ordinary entity
page citing evidence that no longer existed.

Deleting them would break existing citations, so they become tombstones: the
URL resolves, the claim is withdrawn, the evidence table is gone, and the last
published version stays in git history.

Two properties carry the whole design and are easy to lose:

* tombstoning must be **idempotent** — a tombstone re-derives its own label on
  the next build and produces identical bytes, or the clean-diff gate fails on
  every push;
* it must be **reversible** — an entity that reappears in a record gets a real
  page again, because generation runs before reconciliation.
"""

import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import build_outputs  # noqa: E402


def occurrence(label, doc_id, kind="PERSON"):
    return {
        "label": label, "surface": label, "type": kind,
        "context": f"{label} im Kontext", "confidence": "", "uri": "",
        "source_degenerate": False, "doc_id": doc_id,
    }


def index_for(*items):
    index = defaultdict(list)
    for item in items:
        index[build_outputs.entity_key(item["type"], item["label"])].append(item)
    return index


class EntityTombstoneTests(unittest.TestCase):
    def setUp(self):
        self.original_docs = build_outputs.DOCS
        self.temp = tempfile.TemporaryDirectory()
        build_outputs.DOCS = Path(self.temp.name)
        self.root = build_outputs.DOCS / "entities"
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(setattr, build_outputs, "DOCS", self.original_docs)

    def _generate(self, *items):
        """Run one build cycle and return the manifest of live slugs."""
        targets = build_outputs.build_entity_pages(index_for(*items))
        build_outputs.tombstone_orphan_entity_pages(self.root, targets)
        return targets

    def _page(self, slug):
        return (self.root / slug / "index.md").read_text(encoding="utf-8")

    def _slug_of(self, label, kind="PERSON"):
        return build_outputs.slug(label, kind)

    # ── the core behaviour ───────────────────────────────────────────────

    def test_orphan_page_survives_as_a_tombstone(self):
        gone = self._slug_of("Hans Muster")
        self._generate(occurrence("Hans Muster", "doc-a"))
        self.assertTrue((self.root / gone / "index.md").exists())

        self._generate(occurrence("Anna Beispiel", "doc-a"))

        self.assertTrue(
            (self.root / gone / "index.md").exists(),
            "the orphaned entity page was deleted; every existing citation of "
            "that URL now 404s",
        )
        self.assertTrue(
            build_outputs.is_entity_tombstone(self.root / gone / "index.md"),
            "the orphaned page survived but was not marked as a tombstone, so "
            "it still reads as a current entity page",
        )

    def test_tombstone_drops_the_evidence_it_can_no_longer_support(self):
        gone = self._slug_of("Hans Muster")
        self._generate(occurrence("Hans Muster", "doc-a"))
        self.assertIn("doc-a", self._page(gone))

        self._generate(occurrence("Anna Beispiel", "doc-a"))

        page = self._page(gone)
        self.assertNotIn(
            "../../doc-a/", page,
            "the tombstone still links to a document as evidence for a claim "
            "no current record supports",
        )
        self.assertNotIn("<table", page, "the tombstone still shows an evidence table")

    def test_tombstone_keeps_the_label_and_asks_not_to_be_indexed(self):
        gone = self._slug_of("Hans Muster")
        self._generate(occurrence("Hans Muster", "doc-a"))
        self._generate(occurrence("Anna Beispiel", "doc-a"))

        page = self._page(gone)
        self.assertIn('title: "Hans Muster"', page,
                      "the tombstone lost the label the URL was cited under")
        self.assertIn("robots: noindex", page)

    def test_live_pages_are_left_alone(self):
        kept = self._slug_of("Anna Beispiel")
        self._generate(occurrence("Anna Beispiel", "doc-a"))
        self._generate(occurrence("Anna Beispiel", "doc-a"),
                       occurrence("Hans Muster", "doc-b"))

        self.assertFalse(
            build_outputs.is_entity_tombstone(self.root / kept / "index.md"),
            "a still-supported entity page was tombstoned",
        )

    # ── the two properties that are easy to lose ─────────────────────────

    def test_tombstoning_is_idempotent(self):
        gone = self._slug_of("Hans Muster")
        self._generate(occurrence("Hans Muster", "doc-a"))
        self._generate(occurrence("Anna Beispiel", "doc-a"))
        first = self._page(gone)

        for cycle in range(3):
            self._generate(occurrence("Anna Beispiel", "doc-a"))
            self.assertEqual(
                first, self._page(gone),
                f"rebuild {cycle + 1} rewrote the tombstone; the clean-diff "
                "gate fails on every push once a page has been tombstoned",
            )

    def test_a_returning_entity_gets_a_real_page_again(self):
        slug = self._slug_of("Hans Muster")
        self._generate(occurrence("Hans Muster", "doc-a"))
        self._generate(occurrence("Anna Beispiel", "doc-a"))
        self.assertTrue(build_outputs.is_entity_tombstone(self.root / slug / "index.md"))

        self._generate(occurrence("Hans Muster", "doc-c"))

        page = self._page(slug)
        self.assertFalse(
            build_outputs.is_entity_tombstone(self.root / slug / "index.md"),
            "an entity that reappeared in a record is still tombstoned",
        )
        self.assertIn("../../doc-c/", page,
                      "the restored page does not cite its new evidence")

    def test_label_is_recovered_from_the_tombstone_itself(self):
        """What makes the rebuild stable: the label round-trips."""
        page = self.root / "x" / "index.md"
        page.parent.mkdir(parents=True)
        page.write_text(build_outputs.entity_tombstone_page('Der "Rote" Turm'),
                        encoding="utf-8")
        self.assertEqual(
            'Der "Rote" Turm',
            build_outputs.entity_page_label(page, "fallback"),
        )

    def test_label_falls_back_to_the_slug_when_unreadable(self):
        page = self.root / "y" / "index.md"
        page.parent.mkdir(parents=True)
        page.write_text("no front matter here", encoding="utf-8")
        self.assertEqual("y", build_outputs.entity_page_label(page, "y"))


class WithdrawalStillDeletesTests(unittest.TestCase):
    """Withdrawal and obsolescence are different decisions with different outcomes.

    A withdrawn output must stop existing (#194); an entity page whose only
    evidence came from one is deleted, not preserved. An entity that merely
    stopped being mentioned keeps its URL. The two cleanups therefore run in a
    fixed order: withdrawal first, while the pages it matches on still carry
    their document links. Tombstoning first would strip those links and
    silently convert a withdrawal into a tombstone.
    """

    def setUp(self):
        self.original_docs = build_outputs.DOCS
        self.temp = tempfile.TemporaryDirectory()
        build_outputs.DOCS = Path(self.temp.name)
        self.root = build_outputs.DOCS / "entities"
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(setattr, build_outputs, "DOCS", self.original_docs)

    def test_withdrawn_evidence_deletes_the_page_rather_than_tombstoning_it(self):
        withdrawn = "saa-0001-test"
        slug = build_outputs.slug("Hans Muster", "PERSON")
        build_outputs.build_entity_pages(index_for(occurrence("Hans Muster", withdrawn)))
        self.assertTrue((self.root / slug / "index.md").exists())

        # The order build() uses.
        build_outputs.remove_withdrawn_entity_pages(self.root, {withdrawn})
        build_outputs.tombstone_orphan_entity_pages(self.root, set())

        self.assertFalse(
            (self.root / slug).exists(),
            "an entity page sourced only from a withdrawn output survived as a "
            "tombstone; withdrawal means the page stops existing (#194)",
        )


class EntityTombstoneSitemapTests(unittest.TestCase):
    """A tombstone is noindex; advertising it in the sitemap contradicts that."""

    def test_tombstones_are_not_listed_in_the_sitemap(self):
        import build_index

        original = build_index.DOCS
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.addCleanup(setattr, build_index, "DOCS", original)
        build_index.DOCS = Path(temp.name)

        entities = build_index.DOCS / "entities"
        live = entities / "anna-beispiel-0000"
        dead = entities / "hans-muster-0000"
        for directory in (live, dead):
            directory.mkdir(parents=True)
        (live / "index.md").write_text("<h1>Anna</h1>", encoding="utf-8")
        (dead / "index.md").write_text(
            build_outputs.entity_tombstone_page("Hans Muster"), encoding="utf-8")

        build_index.build_sitemap([])
        sitemap = (build_index.DOCS / "sitemap.xml").read_text(encoding="utf-8")

        self.assertIn("/entities/anna-beispiel-0000/", sitemap)
        self.assertNotIn(
            "/entities/hans-muster-0000/", sitemap,
            "a tombstoned entity page is still advertised for indexing",
        )


class RobotsHeadOverrideTests(unittest.TestCase):
    """`robots: noindex` has to reach the rendered page to mean anything.

    Minima's own head emits no robots meta, so the declaration tombstones have
    carried since #194 never reached a crawler — verified by building the site
    with Jekyll and finding no such tag. `docs/_includes/head.html` overrides
    the theme's head to emit it.

    An override freezes a copy of someone else's file, so these checks also
    guard the parts of minima's head that must not be lost along the way.
    """

    HEAD = Path(__file__).parent.parent / "docs" / "_includes" / "head.html"

    def test_override_exists(self):
        self.assertTrue(
            self.HEAD.is_file(),
            "the head override is gone; every tombstone's noindex is "
            "decorative again",
        )

    def test_override_emits_the_robots_meta(self):
        head = self.HEAD.read_text(encoding="utf-8")
        self.assertIn("page.robots", head)
        self.assertIn('<meta name="robots"', head)

    def test_override_keeps_what_minima_put_there(self):
        head = self.HEAD.read_text(encoding="utf-8")
        for required in ("{%- seo -%}", "{%- feed_meta -%}",
                         "/assets/main.css", 'charset="utf-8"',
                         "width=device-width"):
            with self.subTest(required=required):
                self.assertIn(
                    required, head,
                    "the override dropped part of minima's head; the whole "
                    "site loses it, not just tombstones",
                )

    def test_tombstones_declare_noindex(self):
        """The producing side of the same contract."""
        self.assertIn("robots: noindex",
                      build_outputs.entity_tombstone_page("Irgendwer"))


if __name__ == "__main__":
    unittest.main()
