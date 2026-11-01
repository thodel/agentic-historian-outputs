"""The search beyond the page answers what the page answers (#253).

The off-page search (#250, phase C) counted wrong in both directions and was not
tested, invisible because it arms itself only above 50 documents:

* the index row left out the title and the shelfmark, so ``BAT 664`` lit cards up
  and reported no further hits; and it folded with ``casefold`` while the page
  folded with ``.lower()`` and the query with ``toLocaleLowerCase`` — ``ß`` matched
  cards and never index rows;
* the off-page count checked five of twelve filters, so it counted and linked
  records the reader had filtered out — and with the language filter at its
  default ``"all"`` it matched no row at all;
* a title went into ``innerHTML`` unescaped.

These build a real catalogue beyond the page size and hold a card against its own
index row: the same search text, the same filter data, and — through node — the
same verdict from ``catalogueMatches`` under every filter, and the same folding.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import build_index  # noqa: E402
import build_outputs  # noqa: E402

CORPUS = 60
PAGE_SIZE = 25
NODE = shutil.which("node")


def _record(index: int) -> dict:
    doc = {
        "doc_id": f"Synth-{index:04d}",
        "collection": f"korpus-{index % 3}",
        "transcription": f"Text {index} über die Straße nach Bern. " + "wort " * 10,
        "description": {"source_json": {
            "Datierung": str(1400 + index), "Sprache": "Deutsch" if index % 2 else "Latein",
            "Schrift": "Kurrent"}},
        "entities": [], "errors": [], "a_meta": {"qa_score": 0.8}, "recognitions": [],
        "review_status": "human-verified" if index % 5 == 0 else "machine-generated",
    }
    if index % 4 == 0:
        doc["title"] = f"Brief an die Gemeinde {index}"
        doc["signature"] = f"StABE BAT {600 + index}"
    return doc


def _cards(markup: str) -> dict[str, dict[str, str]]:
    """``{documentId: dataset}`` of every card on the rendered page."""
    out = {}
    for tag in re.findall(r'<article class="catalogue-card"([^>]*)>', markup):
        attrs = {m.group(1): html.unescape(m.group(2))
                 for m in re.finditer(r'data-([a-z-]+)="([^"]*)"', tag)}
        data = {re.sub(r"-([a-z])", lambda m: m.group(1).upper(), k): v for k, v in attrs.items()}
        out[data["documentId"]] = data
    return out


class OffPageSearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.docs = Path(cls._tmp.name) / "docs"
        (cls.docs / "assets").mkdir(parents=True)
        for index in range(CORPUS):
            directory = cls.docs / _record(index)["doc_id"]
            directory.mkdir()
            (directory / "pipeline.json").write_text(
                json.dumps(_record(index), ensure_ascii=False), encoding="utf-8")
        originals = (build_index.DOCS, build_outputs.DOCS)
        build_index.DOCS = build_outputs.DOCS = cls.docs
        try:
            with mock.patch.dict(os.environ, {"AH_CATALOGUE_PAGE_SIZE": str(PAGE_SIZE)}):
                build_index.build()
        finally:
            build_index.DOCS, build_outputs.DOCS = originals
        cls.index = json.loads((cls.docs / "catalogue-index.json").read_text(encoding="utf-8"))
        cls.rows = {row["m"]["documentId"]: row for row in cls.index["records"]}
        cls.cards = _cards((cls.docs / "index.md").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_the_page_is_partial_so_the_off_page_search_is_armed(self):
        self.assertEqual(len(self.cards), PAGE_SIZE)
        self.assertEqual(len(self.rows), CORPUS)

    def test_a_card_and_its_index_row_search_the_same_text(self):
        for doc_id, card in self.cards.items():
            self.assertEqual(card["search"], self.rows[doc_id]["q"], doc_id)

    def test_title_and_shelfmark_are_searchable_off_the_page(self):
        off_page = [row for doc_id, row in self.rows.items() if doc_id not in self.cards]
        titled = [row for row in off_page if "brief an die gemeinde" in row["q"]]
        self.assertTrue(titled, "an off-page record with a title")
        self.assertTrue(all("stabe bat" in row["q"] for row in titled))

    def test_the_folding_is_casefold_on_both_sides(self):
        for row in self.rows.values():
            self.assertIn("strasse", row["q"])
            self.assertNotIn("ß", row["q"])

    def test_a_card_and_its_index_row_carry_the_same_filter_data(self):
        for doc_id, card in self.cards.items():
            for key, value in self.rows[doc_id]["m"].items():
                self.assertEqual(card.get(key), value, f"{doc_id}: {key}")

    @unittest.skipUnless(NODE, "node not installed")
    def test_catalogue_matches_gives_a_card_and_its_row_the_same_verdict(self):
        """Every filter the page has, through the browser's own function."""
        states = [{}, {"q": "Straße"}, {"q": "BAT 6"}, {"q": "STRASSE"},
                  {"language": "deutsch"}, {"script": "kurrent"},
                  {"review": "human-verified"}, {"review": "machine-generated"},
                  {"readiness": "legacy"}, {"failure": "issues"}, {"source": "missing"},
                  {"completeness": "minimal"}, {"kind": "test"}, {"superseded": "show"},
                  {"q": "gemeinde", "review": "human-verified"}]
        payload = {"cards": self.cards, "rows": self.rows, "states": states}
        script = (
            "const c = require(process.argv[1]);"
            "const p = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
            "const out = [];"
            "for (const s of p.states) { const st = { ...c.CATALOGUE_DEFAULTS, ...s };"
            "  for (const [id, card] of Object.entries(p.cards)) {"
            "    const a = c.catalogueMatches(card, st);"
            "    const b = c.catalogueMatches(c.catalogueIndexData(p.rows[id]), st);"
            "    if (a !== b) out.push([JSON.stringify(s), id, a, b]); } }"
            "console.log(JSON.stringify(out));")
        done = subprocess.run([NODE, "-e", script, str(ROOT / "docs/assets/catalogue.js")],
                              input=json.dumps(payload), capture_output=True, text=True,
                              check=True)
        self.assertEqual(json.loads(done.stdout), [])

    @unittest.skipUnless(NODE, "node not installed")
    def test_the_browser_folds_a_query_as_python_folds_the_text(self):
        samples = ["Straße", "STRASSE", "Maß", "ẞ", "Waſſer", "ﬁnden", "Öffnung", "Äbtissin",
                   "Gaſt", "ﬂuß", "Zürich"]
        script = ("const c = require(process.argv[1]);"
                  "const s = JSON.parse(require('fs').readFileSync(0, 'utf8'));"
                  "console.log(JSON.stringify(s.map(c.catalogueFold)));")
        done = subprocess.run([NODE, "-e", script, str(ROOT / "docs/assets/catalogue.js")],
                              input=json.dumps(samples), capture_output=True, text=True,
                              check=True)
        self.assertEqual(json.loads(done.stdout), [s.casefold() for s in samples])


class StyleTests(unittest.TestCase):
    """Five classes the pages use had no rule; the notice was a bare paragraph."""

    def test_every_class_named_in_the_issue_has_a_rule(self):
        css = ((ROOT / "docs/assets/catalogue.css").read_text(encoding="utf-8")
               + (ROOT / "docs/assets/output.css").read_text(encoding="utf-8"))
        for name in ("catalogue-offpage", "collection-list", "collection-row",
                     "research-index", "research-language"):
            # A rule for the class itself, not only for something inside it.
            self.assertRegex(css, rf"(?m)^\.{name}\s*\{{", name)


if __name__ == "__main__":
    unittest.main()
