"""Tests for the site language policy (issue #124).

Acceptance:
- A stated language policy exists in the repository (about.md).
- English-language internal pages carry an internal-document banner.
- Internal pages are absent from header_pages in _config.yml (public nav).
"""

from __future__ import annotations

import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

#: English pages that are working documents: not in the navigation, not part
#: of the public offering.
_INTERNAL_PAGES = [
    "docs/catalogue-verification.md",
    "docs/catalogue-performance.md",
    "docs/source-backfill.md",
]

#: English pages that are *published research*, reachable from the German
#: research index. They were classified as internal engineering documents,
#: which is why substantial research sat outside the navigation entirely.
#: Forcing a translation would mean carrying measured claims across without
#: re-checking them; hiding them would mean withholding the evidence that
#: makes the method judgeable. They are listed, and marked as English.
_RESEARCH_PAGES = [
    "docs/evaluation.md",
    "docs/vlm-finetuning.md",
]

_PUBLIC_NAV_PAGES = [
    "index.md",
    "entities/index.md",
    "forschung.md",
    "methodology.md",
    "about.md",
]

_RESEARCH_INDEX = "docs/forschung.md"


class LanguagePolicyTests(unittest.TestCase):
    def test_language_policy_exists_in_about(self):
        """docs/about.md must contain a stated language policy."""
        about = (ROOT / "docs/about.md").read_text(encoding="utf-8")
        assert "sprachpolitik" in about.lower() or "sprach" in about.lower(), \
            "docs/about.md must state the site language policy"
        assert "deutsch" in about.lower() or "german" in about.lower(), \
            "Language policy must mention the chosen language (German)"


    def test_internal_pages_have_banner(self):
        """Internal English pages must carry an explicit internal-document notice."""
        for rel_path in _INTERNAL_PAGES:
            path = ROOT / rel_path
            content = path.read_text(encoding="utf-8")
            assert "internal" in content.lower() or "intern" in content.lower(), \
                f"{rel_path} must carry an internal-document banner"


    def test_internal_pages_not_in_public_nav(self):
        """Internal pages must not appear in header_pages in _config.yml."""
        config = (ROOT / "docs/_config.yml").read_text(encoding="utf-8")
        for rel_path in _INTERNAL_PAGES:
            # Extract just the filename
            fname = Path(rel_path).name
            stem = fname.replace(".md", "")
            # Check it's not in header_pages
            in_header = False
            in_section = False
            for line in config.splitlines():
                if "header_pages" in line:
                    in_section = True
                if in_section and (stem in line or fname in line):
                    in_header = True
                    break
                if in_section and line.strip() and not line.startswith(" ") and "header_pages" not in line:
                    in_section = False
            assert not in_header, \
                f"{fname} must not appear in header_pages (public nav) in _config.yml"


    def test_research_pages_are_not_labelled_as_internal(self):
        """They are published, not working documents — and were mislabelled."""
        for rel_path in _RESEARCH_PAGES:
            content = (ROOT / rel_path).read_text(encoding="utf-8")
            with self.subTest(page=rel_path):
                assert "Internal engineering document" not in content, (
                    f"{rel_path} is in the public navigation but still calls "
                    "itself an internal working document"
                )

    def test_research_pages_declare_their_language(self):
        """A German site must say when a page it links is not German."""
        for rel_path in _RESEARCH_PAGES:
            content = (ROOT / rel_path).read_text(encoding="utf-8")
            with self.subTest(page=rel_path):
                assert "in English" in content, (
                    f"{rel_path} does not tell a reader it is in English"
                )
                assert "sprachpolitik" in content.lower(), (
                    f"{rel_path} does not link the language policy"
                )

    def test_every_research_page_is_reachable_from_the_index(self):
        """Otherwise a page is "in the navigation" without being linked."""
        index = (ROOT / _RESEARCH_INDEX).read_text(encoding="utf-8")
        for rel_path in _RESEARCH_PAGES:
            target = Path(rel_path).name.replace(".md", ".html")
            with self.subTest(page=rel_path):
                assert target in index, (
                    f"{target} is not linked from {_RESEARCH_INDEX}"
                )

    def test_the_research_index_marks_the_pages_as_english(self):
        index = (ROOT / _RESEARCH_INDEX).read_text(encoding="utf-8")
        assert index.count("englisch") >= len(_RESEARCH_PAGES), (
            "the research index does not mark each English page as English"
        )

    def test_the_language_policy_covers_research_pages(self):
        """The policy is published; it has to describe what the site does."""
        about = (ROOT / "docs/about.md").read_text(encoding="utf-8")
        assert "Forschungstext" in about, (
            "about.md still promises a German-only navigation while the "
            "navigation links English research"
        )

    def test_public_nav_pages_are_german(self):
        """All pages in header_pages must be in German (not internal English docs)."""
        # This is a sanity check: the declared public pages should be German
        for page in _PUBLIC_NAV_PAGES:
            path = ROOT / "docs" / page
            if not path.exists():
                continue
            content = path.read_text(encoding="utf-8")
            # Simple heuristic: page should contain at least one German word from a short list
            german_words = ["und", "die", "der", "das", "ist", "für", "mit", "als", "bei"]
            found = any(f" {w} " in content.lower() for w in german_words)
            assert found, f"Public nav page {page} appears to lack German content"


if __name__ == "__main__":
    unittest.main()
