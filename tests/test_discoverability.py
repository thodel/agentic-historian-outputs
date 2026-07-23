"""Tests for issue #119 — structured discoverability metadata.

Covers:
- Schema.org/Dataset JSON-LD on document pages
- sitemap.xml generation (catalogue, methodology, about, docs, entities)
- Atom feed generation with license and content fields
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).parent.parent
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import build_outputs  # noqa: E402
import build_index    # noqa: E402


# ---------------------------------------------------------------------------
# JSON-LD helpers
# ---------------------------------------------------------------------------

class JsonLdDatasetTests(unittest.TestCase):
    """_jsonld_dataset() must emit valid schema.org/Dataset JSON-LD."""

    def _ld(self, **kw):
        defaults = dict(
            doc_id="test-doc",
            canonical="https://example.com/test-doc/",
            source_url="",
            description_text="Sample document.",
            created_iso="2024-01-01T00:00:00+00:00",
            modified_iso="2024-06-15T00:00:00+00:00",
        )
        defaults.update(kw)
        html = build_outputs._jsonld_dataset(**defaults)
        # Extract JSON from script tag
        m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        self.assertIsNotNone(m, "No JSON-LD script tag found")
        return json.loads(m.group(1))

    def test_type_is_dataset(self):
        ld = self._ld()
        self.assertEqual(ld["@type"], "Dataset")

    def test_context_is_schema_org(self):
        ld = self._ld()
        self.assertEqual(ld["@context"], "https://schema.org/")

    def test_name_contains_doc_id(self):
        ld = self._ld(doc_id="saa-0001-test")
        self.assertIn("saa-0001-test", ld["name"])

    def test_url_is_canonical(self):
        ld = self._ld(canonical="https://example.com/my-doc/")
        self.assertEqual(ld["url"], "https://example.com/my-doc/")

    def test_license_is_cc_by_40(self):
        ld = self._ld()
        self.assertIn("creativecommons.org/licenses/by/4.0", ld["license"])

    def test_dates_present(self):
        ld = self._ld(created_iso="2024-01-01T00:00:00+00:00",
                      modified_iso="2024-06-15T00:00:00+00:00")
        self.assertEqual(ld["dateCreated"], "2024-01-01T00:00:00+00:00")
        self.assertEqual(ld["dateModified"], "2024-06-15T00:00:00+00:00")

    def test_distribution_contains_pipeline_json(self):
        ld = self._ld(canonical="https://example.com/doc/")
        urls = [d["contentUrl"] for d in ld["distribution"]]
        self.assertIn("https://example.com/doc/pipeline.json", urls)

    def test_distribution_contains_tei(self):
        ld = self._ld(canonical="https://example.com/doc/")
        urls = [d["contentUrl"] for d in ld["distribution"]]
        self.assertTrue(any("tei" in u.lower() for u in urls),
                        "No TEI distribution URL found")

    def test_distribution_contains_csv(self):
        ld = self._ld(canonical="https://example.com/doc/")
        urls = [d["contentUrl"] for d in ld["distribution"]]
        self.assertTrue(any(u.endswith(".csv") for u in urls),
                        "No CSV distribution URL found")

    def test_source_url_becomes_is_based_on(self):
        # example.com is filtered by valid_public_url; use a real-looking URL
        ld = self._ld(source_url="https://example.test/image.jpg")
        self.assertIn("isBasedOn", ld)
        self.assertEqual(ld["isBasedOn"], "https://example.test/image.jpg")

    def test_no_is_based_on_without_public_source(self):
        ld = self._ld(source_url="")
        self.assertNotIn("isBasedOn", ld)

    def test_description_included_when_provided(self):
        ld = self._ld(description_text="A medieval German document.")
        self.assertIn("description", ld)
        self.assertIn("medieval", ld["description"])


# ---------------------------------------------------------------------------
# Generated document pages
# ---------------------------------------------------------------------------

class GeneratedPageJsonLdTests(unittest.TestCase):
    """Generated index.md files must contain JSON-LD script tags."""

    def _pages(self):
        return list((REPO / "docs").glob("*/index.md"))

    def test_at_least_one_document_page_exists(self):
        self.assertGreater(len(self._pages()), 0)

    def test_document_pages_have_jsonld(self):
        missing = []
        for page in self._pages():
            if "application/ld+json" not in page.read_text(encoding="utf-8"):
                missing.append(page.name)
        # Allow entity index pages (they don't have pipeline.json)
        doc_pages = [
            p for p in self._pages()
            if (p.parent.parent / p.parent.name / "pipeline.json").exists()
            or (REPO / "docs" / p.parent.name / "pipeline.json").exists()
        ]
        for p in doc_pages:
            content = p.read_text(encoding="utf-8")
            self.assertIn(
                "application/ld+json", content,
                f"{p} is missing JSON-LD (run build_index.py)"
            )


# ---------------------------------------------------------------------------
# Sitemap
# ---------------------------------------------------------------------------

class SitemapTests(unittest.TestCase):
    """build_sitemap() must generate a valid sitemap.xml."""

    def _sitemap(self):
        return (REPO / "docs" / "sitemap.xml").read_text(encoding="utf-8")

    def test_sitemap_exists(self):
        self.assertTrue((REPO / "docs" / "sitemap.xml").exists(),
                        "sitemap.xml not found — run build_index.py")

    def test_sitemap_is_valid_xml(self):
        import xml.etree.ElementTree as ET  # noqa: PLC0415
        ET.fromstring(self._sitemap())  # raises if malformed

    def test_sitemap_contains_root_url(self):
        self.assertIn("thodel.github.io/agentic-historian-outputs/</loc>",
                      self._sitemap())

    def test_sitemap_contains_methodology(self):
        self.assertIn("methodology", self._sitemap())

    def test_sitemap_contains_about(self):
        self.assertIn("about", self._sitemap())

    def test_sitemap_contains_document_urls(self):
        sm = self._sitemap()
        # At least one non-test document must be listed
        self.assertRegex(sm, r"<loc>https://thodel\.github\.io/agentic-historian-outputs/[^<]+/</loc>")

    def test_sitemap_contains_entities(self):
        self.assertIn("/entities/", self._sitemap())

    def test_build_sitemap_function_exists(self):
        self.assertTrue(callable(getattr(build_index, "build_sitemap", None)))


# ---------------------------------------------------------------------------
# Atom feed
# ---------------------------------------------------------------------------

class AtomFeedTests(unittest.TestCase):
    """build_atom_feed() must generate a valid Atom 1.0 feed."""

    def _feed(self):
        return (REPO / "docs" / "feed.xml").read_text(encoding="utf-8")

    def test_feed_exists(self):
        self.assertTrue((REPO / "docs" / "feed.xml").exists(),
                        "feed.xml not found — run build_index.py")

    def test_feed_is_valid_xml(self):
        import xml.etree.ElementTree as ET  # noqa: PLC0415
        ET.fromstring(self._feed())

    def test_feed_is_atom(self):
        self.assertIn('xmlns="http://www.w3.org/2005/Atom"', self._feed())

    def test_feed_has_title(self):
        self.assertIn("<title>", self._feed())

    def test_feed_has_updated(self):
        self.assertIn("<updated>", self._feed())

    def test_feed_has_entries(self):
        self.assertIn("<entry>", self._feed())

    def test_feed_entries_have_license(self):
        feed = self._feed()
        self.assertIn("CC BY 4.0", feed)

    def test_feed_excludes_test_records(self):
        feed = self._feed()
        # Test entries should not appear in the feed
        # (saa-0001-test etc. are test runs)
        self.assertNotIn("saa-0001-test", feed)

    def test_build_atom_feed_function_exists(self):
        self.assertTrue(callable(getattr(build_index, "build_atom_feed", None)))
