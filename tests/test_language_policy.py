"""Tests for the site language policy (issue #124).

Acceptance:
- A stated language policy exists in the repository (about.md).
- English-language internal pages carry an internal-document banner.
- Internal pages are absent from header_pages in _config.yml (public nav).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

_INTERNAL_PAGES = [
    "docs/catalogue-verification.md",
    "docs/catalogue-performance.md",
]

_PUBLIC_NAV_PAGES = [
    "index.md",
    "entities/index.md",
    "methodology.md",
    "about.md",
]


def test_language_policy_exists_in_about():
    """docs/about.md must contain a stated language policy."""
    about = (ROOT / "docs/about.md").read_text(encoding="utf-8")
    assert "sprachpolitik" in about.lower() or "sprach" in about.lower(), \
        "docs/about.md must state the site language policy"
    assert "deutsch" in about.lower() or "german" in about.lower(), \
        "Language policy must mention the chosen language (German)"


def test_internal_pages_have_banner():
    """Internal English pages must carry an explicit internal-document notice."""
    for rel_path in _INTERNAL_PAGES:
        path = ROOT / rel_path
        content = path.read_text(encoding="utf-8")
        assert "internal" in content.lower() or "intern" in content.lower(), \
            f"{rel_path} must carry an internal-document banner"


def test_internal_pages_not_in_public_nav():
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


def test_public_nav_pages_are_german():
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
    test_language_policy_exists_in_about()
    test_internal_pages_have_banner()
    test_internal_pages_not_in_public_nav()
    test_public_nav_pages_are_german()
    print("All tests passed!")
