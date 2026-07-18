"""Tests for issue #117 — single source of truth for browser scripts.

scripts/*.js  = canonical, hand-edited copies (snake_case)
docs/assets/  = deployed copies produced by build_index.py (kebab-case)

These tests assert:
1. Every canonical script in scripts/ has a deployed counterpart in docs/assets/
2. The deployed copy is byte-identical to the canonical source
3. No extra JS files exist in docs/assets/ that have a canonical scripts/ counterpart
   but are diverged (drift impossible after running the build)
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).parent.parent
SCRIPTS_DIR = REPO / "scripts"
ASSETS_DIR  = REPO / "docs" / "assets"

# Canonical mapping: scripts/<snake>.js -> docs/assets/<kebab>.js
BROWSER_SCRIPT_MAP = [
    ("evidence_viewer.js",  "evidence-viewer.js"),
    ("page_disclosure.js",  "page-disclosure.js"),
    ("page_sync.js",        "page-sync.js"),
    ("rec_viewer.js",       "rec-viewer.js"),
    ("workspace.js",        "workspace.js"),
]


class BrowserScriptSyncTests(unittest.TestCase):
    """docs/assets/ copies must be byte-identical to scripts/ originals."""

    def test_all_canonical_scripts_exist(self):
        """Every entry in the mapping must have a source in scripts/."""
        for src_name, _ in BROWSER_SCRIPT_MAP:
            src = SCRIPTS_DIR / src_name
            self.assertTrue(src.exists(),
                            f"Canonical browser script missing: scripts/{src_name}")

    def test_all_deployed_copies_exist(self):
        """Every entry in the mapping must have a deployed copy in docs/assets/."""
        for _, dst_name in BROWSER_SCRIPT_MAP:
            dst = ASSETS_DIR / dst_name
            self.assertTrue(dst.exists(),
                            f"Deployed copy missing: docs/assets/{dst_name} — run build_index.py")

    def test_deployed_copies_match_canonical_sources(self):
        """docs/assets/ copies must be byte-identical to their scripts/ originals.

        If this fails, either:
        - docs/assets/ was edited directly (don't — edit scripts/ instead), OR
        - build_index.py was not run after editing scripts/
        """
        for src_name, dst_name in BROWSER_SCRIPT_MAP:
            src = SCRIPTS_DIR / src_name
            dst = ASSETS_DIR / dst_name
            if not src.exists() or not dst.exists():
                self.skipTest(f"Missing file: {src_name} or {dst_name}")
            src_bytes = src.read_bytes()
            dst_bytes = dst.read_bytes()
            self.assertEqual(
                src_bytes, dst_bytes,
                f"docs/assets/{dst_name} differs from scripts/{src_name}.\n"
                f"Edit scripts/{src_name} and run build_index.py to sync."
            )

    def test_sync_browser_scripts_function_exists(self):
        """build_index.py must export sync_browser_scripts()."""
        sys.path.insert(0, str(REPO / "scripts"))
        import build_index  # noqa: PLC0415
        self.assertTrue(callable(getattr(build_index, "sync_browser_scripts", None)),
                        "sync_browser_scripts() not found in build_index.py")

    def test_sync_browser_scripts_function_copies(self):
        """sync_browser_scripts() must copy all files and return their names."""
        import tempfile, shutil  # noqa: E401
        sys.path.insert(0, str(REPO / "scripts"))
        import build_index  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Patch the module-level constants
            orig_scripts = build_index.SCRIPTS_DIR
            orig_assets  = build_index.ASSETS_DIR
            build_index.SCRIPTS_DIR = SCRIPTS_DIR
            build_index.ASSETS_DIR  = tmp_path / "assets"
            try:
                result = build_index.sync_browser_scripts()
            finally:
                build_index.SCRIPTS_DIR = orig_scripts
                build_index.ASSETS_DIR  = orig_assets

        self.assertEqual(len(result), len(BROWSER_SCRIPT_MAP))
        for _, dst_name in BROWSER_SCRIPT_MAP:
            self.assertIn(dst_name, result)

    def test_no_stale_js_in_assets_with_scripts_counterpart(self):
        """docs/assets/ must not contain hand-edited copies diverging from scripts/.

        This is the CI 'stale duplicate' check: any JS in docs/assets/ that
        corresponds to a canonical scripts/ file must be byte-identical to it.
        """
        canonical_names = {dst_name for _, dst_name in BROWSER_SCRIPT_MAP}
        for js_file in ASSETS_DIR.glob("*.js"):
            if js_file.name not in canonical_names:
                continue  # Not managed by the sync (e.g. catalogue.js)
            # Find the corresponding canonical source
            for src_name, dst_name in BROWSER_SCRIPT_MAP:
                if dst_name == js_file.name:
                    src = SCRIPTS_DIR / src_name
                    if src.exists():
                        self.assertEqual(
                            src.read_bytes(), js_file.read_bytes(),
                            f"Stale duplicate detected: docs/assets/{dst_name} "
                            f"differs from canonical scripts/{src_name}."
                        )
