"""Issue #25 – Harden and verify the evidence-first page hierarchy.

Covers:
- Duplicate-anchor detection across all critical page variants and all generated docs.
- Internal #link integrity (every #anchor must resolve to an existing id).
- Multi-page vs single-page structural contracts.
- Static/no-JavaScript content completeness (research content in HTML, not JS-only).
- Stable deep-link anchor preservation across all generated pages.
- Catalogue index integrity (every linked doc slug must have an index.md).
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_outputs import build_document

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DOCS_ROOT = Path(__file__).parent.parent / "docs"


class IDAndLinkParser(HTMLParser):
    """Collect all id= attributes and internal #href links from an HTML fragment."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.internal_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attr = dict(attrs)
        if attr.get("id"):
            self.ids.append(attr["id"])
        href = attr.get("href", "")
        if href.startswith("#") and len(href) > 1:
            self.internal_links.append(href[1:])


def _parse(markup: str) -> IDAndLinkParser:
    p = IDAndLinkParser()
    p.feed(markup)
    return p


def _render(data: dict, doc_id: str = "research-output") -> str:
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp) / doc_id
        directory.mkdir()
        (directory / "pipeline.json").write_text(json.dumps(data), encoding="utf-8")
        build_document(directory / "pipeline.json", defaultdict(list))
        return (directory / "index.md").read_text(encoding="utf-8")


def _rec(**kwargs) -> dict:
    base = {"engine": "kraken", "model_id": "model", "text": "sample text", "error": ""}
    base.update(kwargs)
    return base


def _collect_document_pages() -> dict[str, str]:
    """Return {doc_id: markup} for every generated document page that contains
    a page-section identity marker (i.e. is a document page, not a catalogue or
    entity index)."""
    pages: dict[str, str] = {}
    for doc_dir in DOCS_ROOT.iterdir():
        if not doc_dir.is_dir():
            continue
        index = doc_dir / "index.md"
        if index.exists():
            content = index.read_text(encoding="utf-8")
            if 'data-page-section="identity"' in content:
                pages[doc_dir.name] = content
    return pages


# ---------------------------------------------------------------------------
# Duplicate-anchor tests — synthetic fixtures
# ---------------------------------------------------------------------------


class DuplicateAnchorFixtureTests(unittest.TestCase):
    """No element may carry the same id= twice within one rendered page."""

    def _assert_no_dups(self, data: dict, doc_id: str = "dup-check") -> None:
        markup = _render(data, doc_id)
        counts = Counter(_parse(markup).ids)
        dups = {i: n for i, n in counts.items() if n > 1}
        self.assertEqual(dups, {}, f"Duplicate IDs in {doc_id}: {dups}")

    def test_no_duplicate_anchors_complete_output(self) -> None:
        self._assert_no_dups(
            {
                "source_url": "https://e-manuscripta.ch/item/1",
                "transcription": "Ich hab gesehen",
                "recognitions": [_rec()],
                "description": {
                    "source_json": {"Datum": "1380", "Ort": {"value": "Bern"}}
                },
                "entities": {
                    "persons": [
                        {"type": "Person", "label": "Karl", "context": "König"}
                    ]
                },
            },
            "complete-output",
        )

    def test_no_duplicate_anchors_sourceless_output(self) -> None:
        self._assert_no_dups({"transcription": "legacy text"}, "sourceless-output")

    def test_no_duplicate_anchors_failed_recognition(self) -> None:
        self._assert_no_dups(
            {
                "source_url": "https://e-manuscripta.ch/item/2",
                "transcription": "fallback",
                "recognitions": [_rec(text="", error="timeout")],
            },
            "failed-rec-output",
        )

    def test_no_duplicate_anchors_multi_page(self) -> None:
        self._assert_no_dups(
            {
                "source_url": "https://e-manuscripta.ch/item/3",
                "transcription": "folio text",
                "source_pages": [
                    {"page": "1r", "image_url": "https://e-manuscripta.ch/img/1r.jpg"},
                    {"page": "1v", "image_url": "https://e-manuscripta.ch/img/1v.jpg"},
                ],
                "recognitions": [_rec()],
            },
            "multi-page-output",
        )

    def test_no_duplicate_anchors_single_page(self) -> None:
        self._assert_no_dups(
            {
                "source_url": "https://e-manuscripta.ch/item/4",
                "transcription": "single folio",
                "source_pages": [
                    {"page": "1r", "image_url": "https://e-manuscripta.ch/img/1r.jpg"},
                ],
            },
            "single-page-output",
        )

    def test_no_duplicate_anchors_test_output(self) -> None:
        self._assert_no_dups(
            {"transcription": "test fixture text"},
            "saa-0099-test",
        )

    def test_no_duplicate_anchors_legacy_qa_output(self) -> None:
        self._assert_no_dups(
            {
                "transcription": "old text",
                "a_meta": {"qa_score": 0.83},
            },
            "legacy-qa-output",
        )


# ---------------------------------------------------------------------------
# Internal-link integrity — all #href must resolve to an existing id
# ---------------------------------------------------------------------------


class InternalLinkIntegrityFixtureTests(unittest.TestCase):
    """Every #anchor link in a rendered page must point to an existing id."""

    def _assert_links_resolve(self, data: dict, doc_id: str = "link-check") -> None:
        markup = _render(data, doc_id)
        parsed = _parse(markup)
        id_set = set(parsed.ids)
        broken = [lnk for lnk in parsed.internal_links if lnk not in id_set]
        self.assertEqual(
            broken, [], f"Broken internal #links in {doc_id}: {broken}"
        )

    def test_complete_output_links_resolve(self) -> None:
        self._assert_links_resolve(
            {
                "source_url": "https://e-manuscripta.ch/item/1",
                "transcription": "Ich hab gesehen",
                "recognitions": [_rec()],
                "description": {"source_json": {"Datum": "1380"}},
            },
            "complete-link-check",
        )

    def test_sourceless_output_links_resolve(self) -> None:
        self._assert_links_resolve(
            {"transcription": "legacy"}, "sourceless-link-check"
        )

    def test_failed_recognition_links_resolve(self) -> None:
        self._assert_links_resolve(
            {
                "source_url": "https://e-manuscripta.ch/item/4",
                "transcription": "fallback",
                "recognitions": [_rec(text="", error="failed")],
            },
            "failed-link-check",
        )

    def test_multi_page_links_resolve(self) -> None:
        self._assert_links_resolve(
            {
                "source_url": "https://e-manuscripta.ch/item/5",
                "transcription": "folio",
                "source_pages": [
                    {"page": "1r", "image_url": "https://e-manuscripta.ch/img/1r.jpg"},
                    {"page": "2r", "image_url": "https://e-manuscripta.ch/img/2r.jpg"},
                ],
            },
            "multi-page-link-check",
        )


# ---------------------------------------------------------------------------
# Multi-page vs single-page structural contracts
# ---------------------------------------------------------------------------


class MultiPageVariantTests(unittest.TestCase):
    """Source-page navigation rules for single vs multi-page outputs."""

    def test_multi_page_source_nav_present(self) -> None:
        # source-page-nav is rendered only for image/IIIF sources with >1 page.
        # Use an image URL so the source type resolves to "image".
        markup = _render(
            {
                "source_url": "https://e-manuscripta.ch/img/folio.jpg",
                "transcription": "folio text",
                "source_pages": [
                    {"page": "1r", "image_url": "https://e-manuscripta.ch/img/1r.jpg"},
                    {"page": "2r", "image_url": "https://e-manuscripta.ch/img/2r.jpg"},
                ],
            },
            "multi-page-nav-test",
        )
        self.assertIn("source-page-nav", markup)

    def test_single_page_source_nav_absent(self) -> None:
        # A single source page must not render the page-switching nav.
        markup = _render(
            {
                "source_url": "https://e-manuscripta.ch/img/folio.jpg",
                "transcription": "single text",
                "source_pages": [
                    {"page": "1r", "image_url": "https://e-manuscripta.ch/img/1r.jpg"},
                ],
            },
            "single-page-nav-test",
        )
        # Single-page output must not render page navigation chrome
        self.assertNotIn("source-page-nav", markup)

    def test_legacy_page_mapping_field_normalised_to_nav(self) -> None:
        # page_mapping is the legacy spelling; it is normalised by normalize_source_reference.
        markup = _render(
            {
                "source_url": "https://e-manuscripta.ch/img/folio.jpg",
                "transcription": "folio text",
                "page_mapping": [
                    {"page": "A", "image_url": "https://e-manuscripta.ch/img/a.jpg"},
                    {"page": "B", "image_url": "https://e-manuscripta.ch/img/b.jpg"},
                ],
            },
            "legacy-page-mapping-test",
        )
        self.assertIn("source-page-nav", markup)

    def test_multi_page_section_order_unchanged(self) -> None:
        """Adding source_pages must not alter the canonical page-section order."""
        markup = _render(
            {
                "source_url": "https://e-manuscripta.ch/img/folio.jpg",
                "transcription": "folio",
                "recognitions": [_rec()],
                "source_pages": [
                    {"page": "1r", "image_url": "https://e-manuscripta.ch/img/1r.jpg"},
                    {"page": "1v", "image_url": "https://e-manuscripta.ch/img/1v.jpg"},
                ],
            },
            "multi-page-order-test",
        )
        order = re.findall(r'data-page-section="([^"]+)"', markup)
        self.assertEqual(
            order,
            [
                "identity",
                "source",
                "transcription",
                "recognitions",
                "orientation",
                "claims",
                "entities",
                "downloads",
                "citation",
                "history",
            ],
        )


# ---------------------------------------------------------------------------
# Static / no-JavaScript content completeness
# ---------------------------------------------------------------------------


class StaticContentCompletenessTests(unittest.TestCase):
    """Primary research content must be present in static HTML without JS."""

    _STANDARD_DATA = {
        "source_url": "https://e-manuscripta.ch/item/1",
        "transcription": "Lorem ipsum research text that should survive.",
        "recognitions": [_rec(text="Lorem ipsum recognition candidate")],
        "description": {
            "source_json": {
                "Datum": "1380",
                "Ort": {"value": "Bern"},
            }
        },
        "entities": {
            # entities() normalises dict-of-lists using item.get("name") as the label.
            "persons": [{"name": "KarlVonTest", "context": ""}]
        },
        "a_meta": {"review_status": "machine-generated"},
    }

    def setUp(self) -> None:
        self._markup = _render(self._STANDARD_DATA, "static-content-check")

    def test_transcription_text_in_static_html(self) -> None:
        self.assertIn("Lorem ipsum research text", self._markup)

    def test_recognition_candidate_text_present(self) -> None:
        self.assertIn("Lorem ipsum recognition candidate", self._markup)

    def test_description_fields_present_in_static_html(self) -> None:
        self.assertIn("1380", self._markup)
        self.assertIn("Bern", self._markup)

    def test_entity_name_in_static_html(self) -> None:
        self.assertIn("KarlVonTest", self._markup)

    def test_stable_anchor_ids_present(self) -> None:
        for anchor in ("transcription", "citation", "downloads", "history"):
            self.assertIn(
                f'id="{anchor}"',
                self._markup,
                f"Stable deep-link #{anchor} missing from static HTML",
            )

    def test_citation_section_present_in_html(self) -> None:
        self.assertGreater(
            self._markup.find('id="citation"'),
            0,
            "Citation section missing from static HTML",
        )


# ---------------------------------------------------------------------------
# Deployment integration — all generated document pages in docs/
# ---------------------------------------------------------------------------


class DeploymentIntegrationTests(unittest.TestCase):
    """Checks against the real generated output files checked in to docs/."""

    def test_generated_pages_exist(self) -> None:
        pages = _collect_document_pages()
        self.assertGreater(len(pages), 0, "No generated document pages found in docs/")

    def test_no_duplicate_anchors_in_all_generated_pages(self) -> None:
        pages = _collect_document_pages()
        errors: dict[str, dict[str, int]] = {}
        for name, markup in pages.items():
            dups = {
                i: n
                for i, n in Counter(_parse(markup).ids).items()
                if n > 1
            }
            if dups:
                errors[name] = dups
        self.assertEqual(
            errors, {}, f"Duplicate IDs in generated pages: {errors}"
        )

    def test_all_internal_links_resolve_in_generated_pages(self) -> None:
        pages = _collect_document_pages()
        errors: dict[str, list[str]] = {}
        for name, markup in pages.items():
            parsed = _parse(markup)
            id_set = set(parsed.ids)
            broken = [lnk for lnk in parsed.internal_links if lnk not in id_set]
            if broken:
                errors[name] = broken
        self.assertEqual(
            errors, {}, f"Broken internal #links in generated pages: {errors}"
        )

    def test_stable_anchors_present_in_all_generated_pages(self) -> None:
        """Key deep-link anchors must remain present in every document page."""
        pages = _collect_document_pages()
        stable = ("transcription", "citation")
        missing: dict[str, list[str]] = {}
        for name, markup in pages.items():
            absent = [a for a in stable if f'id="{a}"' not in markup]
            if absent:
                missing[name] = absent
        self.assertEqual(
            missing, {}, f"Stable deep-link anchors missing in pages: {missing}"
        )

    def test_catalogue_index_links_to_existing_docs(self) -> None:
        index = DOCS_ROOT / "index.md"
        if not index.exists():
            self.skipTest("No catalogue index.md found")
        content = index.read_text(encoding="utf-8")
        # Match Markdown and HTML relative links to sibling doc dirs
        slugs = re.findall(r'href=["\']\.\.?/([^/"\']+)/', content)
        slugs += re.findall(r'\]\(\.\.?/([^)/"\']+)/', content)
        for s in set(slugs):
            target = DOCS_ROOT / s / "index.md"
            self.assertTrue(
                target.exists(),
                f"Catalogue links to non-existent page: {s}",
            )

    def test_print_essential_sections_in_all_generated_pages(self) -> None:
        """Transcription and citation must be present in every generated page."""
        pages = _collect_document_pages()
        errors: dict[str, list[str]] = {}
        for name, markup in pages.items():
            absent = [
                sec
                for sec in ("transcription", "citation")
                if f'id="{sec}"' not in markup
            ]
            if absent:
                errors[name] = absent
        self.assertEqual(
            errors,
            {},
            f"Print-essential sections missing in pages: {errors}",
        )


if __name__ == "__main__":
    unittest.main()
