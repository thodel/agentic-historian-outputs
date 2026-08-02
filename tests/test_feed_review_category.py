"""The Atom feed must expose review state machine-readably (#193).

The entry summary already names the review state in German prose, but a
subscriber wanting to act on "this edition has been reviewed" would have to
string-match a localized sentence. An Atom ``<category>`` carries the same fact
as data: the enum as ``term``, the rendered German as ``label``.

The feed is also parsed as XML here rather than string-matched, so a malformed
entry fails loudly instead of silently shipping a broken feed.
"""

import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

FEED = Path(__file__).resolve().parent.parent / "docs" / "feed.xml"
ATOM = {"a": "http://www.w3.org/2005/Atom"}
KNOWN_TERMS = {"machine-generated", "in-review", "human-verified"}


class FeedReviewCategoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.fromstring(FEED.read_text(encoding="utf-8"))
        cls.entries = cls.root.findall(".//a:entry", ATOM)

    def test_feed_is_well_formed_and_has_entries(self):
        self.assertTrue(self.entries, "feed contains no entries")

    def test_every_entry_carries_a_review_category(self):
        for entry in self.entries:
            title = entry.findtext("a:title", default="?", namespaces=ATOM)
            with self.subTest(entry=title):
                categories = entry.findall("a:category", ATOM)
                self.assertEqual(
                    len(categories), 1,
                    "expected exactly one review category per entry",
                )

    def test_terms_use_the_review_status_enum(self):
        for entry in self.entries:
            term = entry.find("a:category", ATOM).get("term")
            with self.subTest(term=term):
                self.assertIn(
                    term, KNOWN_TERMS,
                    "feed term must be a review-status enum value, so consumers "
                    "can match on it without parsing German prose",
                )

    def test_labels_are_present_and_localized(self):
        for entry in self.entries:
            category = entry.find("a:category", ATOM)
            with self.subTest(term=category.get("term")):
                self.assertTrue(
                    (category.get("label") or "").strip(),
                    "category needs a human-readable label",
                )

    def test_category_agrees_with_the_summary_prose(self):
        """The machine-readable fact and the prose must not disagree."""
        for entry in self.entries:
            term = entry.find("a:category", ATOM).get("term")
            summary = entry.findtext("a:summary", default="", namespaces=ATOM)
            with self.subTest(term=term):
                if term == "human-verified":
                    self.assertIn("Redaktionell geprüft", summary)
                elif term == "machine-generated":
                    self.assertIn("Maschinell erzeugt", summary)


if __name__ == "__main__":
    unittest.main()
