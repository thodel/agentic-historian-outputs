"""Tests for localized review-status badges on catalogue cards (issue #122)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _make_card(review_status: str) -> str:
    from build_index import _card, _record

    data = {
        "review_status": review_status,
        "transcription": "Test text",
        "iiif_manifest": "https://archive.example.edu/iiif/manifest.json",
    }
    with tempfile.TemporaryDirectory() as temp:
        target = Path(temp) / "fixture-review" / "pipeline.json"
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps(data), encoding="utf-8")
        record = _record(target)
        return _card(record)


def test_machine_generated_shows_german_label():
    markup = _make_card("machine-generated")
    assert "Maschinell erzeugt" in markup, "machine-generated must render as 'Maschinell erzeugt'"
    assert ">machine-generated<" not in markup, "Raw enum must not appear as visible badge text"


def test_human_verified_shows_german_label():
    markup = _make_card("human-verified")
    assert "Menschlich geprüft" in markup, "human-verified must render as 'Menschlich geprüft'"
    assert ">human-verified<" not in markup, "Raw enum must not appear as visible badge text"


def test_machine_generated_has_semantic_css_class():
    markup = _make_card("machine-generated")
    assert "catalogue-badge--review-machine" in markup, (
        "machine-generated badge must use 'catalogue-badge--review-machine' CSS class"
    )


def test_human_verified_has_semantic_css_class():
    markup = _make_card("human-verified")
    assert "catalogue-badge--review-human" in markup, (
        "human-verified badge must use 'catalogue-badge--review-human' CSS class"
    )


def test_data_review_status_preserves_enum():
    """data-review-status must still carry the raw enum for JS filtering."""
    markup = _make_card("machine-generated")
    assert 'data-review-status="machine-generated"' in markup, (
        "data-review-status attribute must preserve the raw enum value"
    )
    markup2 = _make_card("human-verified")
    assert 'data-review-status="human-verified"' in markup2


def test_no_raw_enum_in_generated_index():
    """The generated catalogue index must not show raw enum values as badge text."""
    index = (ROOT / "docs/index.md").read_text(encoding="utf-8")
    assert ">machine-generated<" not in index, "Raw 'machine-generated' must not appear as badge text"
    assert ">human-verified<" not in index, "Raw 'human-verified' must not appear as badge text"


def test_review_css_classes_in_stylesheet():
    """The catalogue CSS must define the new semantic badge classes."""
    css = (ROOT / "docs/assets/catalogue.css").read_text(encoding="utf-8")
    assert ".catalogue-badge--review-machine" in css
    assert ".catalogue-badge--review-human" in css


if __name__ == "__main__":
    test_machine_generated_shows_german_label()
    test_human_verified_shows_german_label()
    test_machine_generated_has_semantic_css_class()
    test_human_verified_has_semantic_css_class()
    test_data_review_status_preserves_enum()
    test_no_raw_enum_in_generated_index()
    test_review_css_classes_in_stylesheet()
    print("All tests passed!")
