"""pytest configuration — browser tests only when deps are available."""
import pytest

# Only run browser-marked tests if playwright deps are present
def pytest_configure(config):
    try:
        from playwright.sync_api import sync_playwright
        sync_playwright().start()
        sync_playwright().stop()
    except Exception:
        config.addinivalue_line(
            "markers", "browser: browser tests (skipped — missing system deps)"
        )

# Make scripts/ importable for all tests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
