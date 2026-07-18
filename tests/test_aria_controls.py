"""Repo-wide test: every aria-controls value must resolve to an existing id.

Issue #112: explanation_button() and explanation_block() shared an
independent counter, so button aria-controls pointed to non-existent ids.
This test scans all generated docs/*.md pages (which embed HTML directly)
and asserts that every aria-controls value found on a page corresponds to
an id attribute present on the same page.

Run after the build scripts have generated docs/*/index.md.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"


def _extract_controls_and_ids(content: str) -> tuple[list[str], set[str]]:
    """Return (aria_controls_values, id_attribute_set) from raw page content."""
    controls = re.findall(r'aria-controls="([^"]+)"', content)
    ids = set(re.findall(r'\bid="([^"]+)"', content))
    return controls, ids


class AriaControlsResolutionTests(unittest.TestCase):
    """Every aria-controls attribute must resolve to an existing id on the same page."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.pages: list[tuple[Path, str]] = []
        for md in DOCS.rglob("*.md"):
            try:
                cls.pages.append((md, md.read_text(encoding="utf-8")))
            except OSError:
                pass

    def test_pages_exist(self) -> None:
        self.assertTrue(self.pages, "No .md pages found under docs/ — build may not have run")

    def test_no_dangling_aria_controls(self) -> None:
        """Zero dangling aria-controls references across all generated pages."""
        dangling: list[str] = []
        for path, content in self.pages:
            controls, ids = _extract_controls_and_ids(content)
            for ctrl in controls:
                if ctrl not in ids:
                    dangling.append(f"{path.relative_to(ROOT)}: aria-controls={ctrl!r} not found in page ids")
        self.assertEqual(
            dangling,
            [],
            "Dangling aria-controls found:\n" + "\n".join(dangling),
        )

    def test_quality_explanation_buttons_resolve(self) -> None:
        """All quality-explain-btn buttons must have resolvable aria-controls."""
        dangling: list[str] = []
        for path, content in self.pages:
            buttons = re.findall(
                r'<button class="quality-explain-btn"[^>]+aria-controls="([^"]+)"',
                content,
            )
            ids = set(re.findall(r'\bid="([^"]+)"', content))
            for ctrl in buttons:
                if ctrl not in ids:
                    dangling.append(
                        f"{path.relative_to(ROOT)}: quality-explain-btn "
                        f"aria-controls={ctrl!r} not found"
                    )
        self.assertEqual(
            dangling,
            [],
            "Dangling quality-explain-btn aria-controls:\n" + "\n".join(dangling),
        )


class AriaControlsUnitTests(unittest.TestCase):
    """Unit tests for the button/block ID contract in quality.py."""

    def setUp(self) -> None:
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from quality import explanation_button, explanation_block
        self.btn = explanation_button
        self.blk = explanation_block

    def test_no_suffix_button_matches_block(self) -> None:
        """Button aria-controls must resolve to block id when no suffix given."""
        key = "engine_confidence"
        btn_html = self.btn(key)
        blk_html = self.blk(key)
        controls = re.findall(r'aria-controls="([^"]+)"', btn_html)
        ids = re.findall(r'\bid="([^"]+)"', blk_html)
        self.assertEqual(len(controls), 1, "Button must have exactly one aria-controls")
        self.assertEqual(len(ids), 1, "Block must have exactly one id")
        self.assertEqual(controls[0], ids[0],
                         f"aria-controls={controls[0]!r} != block id={ids[0]!r}")

    def test_with_suffix_button_matches_block(self) -> None:
        """Button aria-controls must resolve to block id when suffix is given."""
        key = "reference_evaluation"
        suffix = "card-abc123"
        btn_html = self.btn(key, suffix)
        blk_html = self.blk(key, suffix)
        controls = re.findall(r'aria-controls="([^"]+)"', btn_html)
        ids = re.findall(r'\bid="([^"]+)"', blk_html)
        self.assertEqual(controls[0], ids[0],
                         f"aria-controls={controls[0]!r} != block id={ids[0]!r}")

    def test_no_suffix_id_is_key_based(self) -> None:
        """Without a suffix, block id should be quality-explanation-{key}."""
        key = "agreement"
        blk_html = self.blk(key)
        self.assertIn(f'id="quality-explanation-{key}"', blk_html)

    def test_different_suffixes_give_different_ids(self) -> None:
        """Two calls with different suffixes must produce different ids."""
        key = "engine_confidence"
        blk1 = self.blk(key, "s1")
        blk2 = self.blk(key, "s2")
        id1 = re.search(r'\bid="([^"]+)"', blk1).group(1)
        id2 = re.search(r'\bid="([^"]+)"', blk2).group(1)
        self.assertNotEqual(id1, id2)


if __name__ == "__main__":
    unittest.main()
