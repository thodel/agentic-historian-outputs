"""Passage anchors on document pages (agentic-historian#397, Q3).

`/find` in the pipeline repo returns ranked passages and deep-links each one
into this catalogue. For that the page has to carry an anchor at the place in
the transcription the passage names.

**The anchor is a contract across two repositories.** `passage_anchor` here and
`passage_find.anchor_for` there must spell it the same way. If each side
computed its own they would agree until the day they did not, and the symptom
would be a link that scrolls to the top of a long page — which looks like a
working link, so nobody would notice.

The offsets arrive in `pipeline.json` from agentic-historian#466. Every document
published before that carries entity records without them, and those pages must
keep working exactly as they did: highlighted, just not linkable.
"""
import html
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_outputs import (  # noqa: E402
    PASSAGE_ANCHOR_PREFIX,
    _highlight_entities,
    entities,
    passage_anchor,
)

TEXT = "der vogt gab almosen den armen lüten & mehr"


def ent(text, kind, start=None, end=None, **kw):
    item = {"text": text, "type": kind, "normalised": text, **kw}
    if start is not None:
        item["char_start"] = start
        item["char_end"] = end if end is not None else start + len(text)
    return item


def doc(*items):
    return {"entities": {"entities": list(items)}}


class AnchorContract(unittest.TestCase):
    """What the other repository is allowed to rely on."""

    def test_the_anchor_is_the_span(self):
        self.assertEqual(passage_anchor(ent("almosen", "CARE_ACTION", 13)),
                         "passage-13-20")

    def test_the_prefix_is_the_agreed_one(self):
        self.assertEqual(PASSAGE_ANCHOR_PREFIX, "passage-")

    def test_two_entities_over_the_same_words_share_an_anchor(self):
        """Right, not a collision: the anchor names a place in the text, which
        is what a reader following a link wants to see. Not an entity id."""
        role = ent("vogt", "ROLE", 4)
        group = ent("vogt", "SOCIAL_GROUP", 4)
        self.assertEqual(passage_anchor(role), passage_anchor(group))

    def test_no_offsets_means_no_anchor(self):
        self.assertIsNone(passage_anchor(ent("almosen", "CARE_ACTION")))
        self.assertIsNone(passage_anchor({}))

    def test_a_degenerate_span_has_no_anchor(self):
        """An empty or inverted span names no characters."""
        self.assertIsNone(passage_anchor({"char_start": 10, "char_end": 10}))
        self.assertIsNone(passage_anchor({"char_start": 10, "char_end": 4}))

    def test_a_non_integer_offset_is_refused(self):
        """A stringified offset is what a careless serialiser produces, and it
        cannot be compared with len(text)."""
        self.assertIsNone(passage_anchor({"char_start": "13", "char_end": "20"}))


class HighlightByOffset(unittest.TestCase):
    def test_each_mention_carries_its_anchor(self):
        out = _highlight_entities(TEXT, doc(
            ent("almosen", "CARE_ACTION", 13),
            ent("armen lüten", "SOCIAL_GROUP", 25)))

        self.assertIn('id="passage-13-20"', out)
        self.assertIn('id="passage-25-36"', out)

    def test_the_type_class_is_kept(self):
        """The existing styling must not be lost to the new anchors."""
        out = _highlight_entities(TEXT, doc(ent("almosen", "CARE_ACTION", 13)))

        self.assertIn('class="entity-care_action"', out)

    def test_escaping_happens_per_segment(self):
        """The offsets index the RAW transcription. Escaping the whole text
        first moves every position after the first `&` or `<` — which is the
        bug this function would have if it reused the escaped string."""
        text = "a & b almosen c"
        out = _highlight_entities(text, doc(ent("almosen", "CARE_ACTION", 6)))

        self.assertIn("&amp;", out)
        self.assertIn(">almosen</mark>", out)

    def test_an_entity_inside_a_marked_span_is_dropped_not_nested(self):
        """`<mark>` inside `<mark>` is not what the CSS or a screen reader
        expects here. The longer span wins, so "armen lüten" keeps its anchor
        over a nested "armen"."""
        out = _highlight_entities(TEXT, doc(
            ent("armen lüten", "SOCIAL_GROUP", 25),
            ent("armen", "SOCIAL_GROUP", 25)))

        self.assertIn('id="passage-25-36"', out)
        self.assertNotIn('id="passage-25-30"', out)
        self.assertEqual(out.count("<mark"), 1)

    def test_a_span_whose_characters_do_not_match_loses_its_anchor(self):
        """An offset written against a different transcription — a re-run that
        changed the reading, a record copied between documents — would mark the
        wrong words and anchor a link to them, which is worse than not linking.

        It costs the **anchor**, not the highlight: nothing can be placed, so
        the surface-based path runs and the mention is still marked. That is
        the better failure, and my first version of this test asserted the
        worse one (no mark at all).
        """
        out = _highlight_entities(TEXT, doc(ent("almosen", "CARE_ACTION", 0, 7)))

        self.assertNotIn('id="passage-', out)
        self.assertIn("<mark", out)
        self.assertIn(">almosen</mark>", out)

    def test_a_span_past_the_end_loses_its_anchor(self):
        out = _highlight_entities(TEXT, doc(ent("almosen", "CARE_ACTION",
                                                9000, 9007)))

        self.assertNotIn('id="passage-', out)
        self.assertIn("<mark", out)

    def test_the_text_itself_is_unchanged(self):
        """Marking must not lose or reorder a character."""
        import re

        out = _highlight_entities(TEXT, doc(
            ent("almosen", "CARE_ACTION", 13),
            ent("armen lüten", "SOCIAL_GROUP", 25)))
        stripped = html.unescape(re.sub(r"<[^>]+>", "", out))

        self.assertEqual(stripped, TEXT)


class LegacyDocumentsKeepWorking(unittest.TestCase):
    """Every document published before #466 has records without offsets."""

    def test_a_mention_without_offsets_is_still_highlighted(self):
        out = _highlight_entities(TEXT, doc(ent("almosen", "CARE_ACTION")))

        self.assertIn("<mark", out)
        self.assertIn("almosen", out)

    def test_but_carries_no_anchor(self):
        out = _highlight_entities(TEXT, doc(ent("almosen", "CARE_ACTION")))

        self.assertNotIn("id=\"passage-", out)

    def test_a_document_with_no_entities_is_just_escaped(self):
        self.assertEqual(_highlight_entities(TEXT, {"entities": {}}),
                         html.escape(TEXT))

    def test_the_grouped_shape_still_works(self):
        """`entities` arrives as {persons: [...], places: [...]} on older
        documents, and the type is derived from the group name."""
        out = _highlight_entities("Hans von Wiler ze Bern",
                                  {"entities": {"persons": ["Hans von Wiler"]}})

        self.assertIn('class="entity-person"', out)

    def test_a_mixed_document_prefers_the_offsets_it_has(self):
        """One record with offsets and one without: the placed one is anchored
        and the other is not silently given a position."""
        out = _highlight_entities(TEXT, doc(
            ent("almosen", "CARE_ACTION", 13),
            ent("vogt", "ROLE")))

        self.assertIn('id="passage-13-20"', out)
        self.assertEqual(out.count("<mark"), 1,
                         "the unplaced record must not be marked by surface "
                         "in the offset path")


class EntitiesCarryTheirOffsets(unittest.TestCase):
    def test_the_normaliser_keeps_them(self):
        """`entities()` built a fixed dict and dropped the positions, so the
        list on the page had nothing to link with."""
        rows = entities(doc(ent("almosen", "CARE_ACTION", 13)))

        self.assertEqual(rows[0]["char_start"], 13)
        self.assertEqual(rows[0]["char_end"], 20)

    def test_they_stay_integers(self):
        """A stringified offset cannot be compared with len(text)."""
        rows = entities(doc(ent("almosen", "CARE_ACTION", 13)))

        self.assertIsInstance(rows[0]["char_start"], int)

    def test_absent_where_there_are_none(self):
        rows = entities(doc(ent("almosen", "CARE_ACTION")))

        self.assertIsNone(rows[0]["char_start"])


if __name__ == "__main__":
    unittest.main()
