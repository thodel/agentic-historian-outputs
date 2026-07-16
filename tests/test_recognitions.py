"""Tests for build_recognitions.py (issue #4)."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the scripts/ module is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from build_recognitions import (
    _engine_label,
    _engine_icon,
    _is_selected,
    _conf_html,
    _recognition_candidate_html,
    build_recognition_section,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def make_rec(engine, model_id="test-model", confidence=None, error="", text="Sample text"):
    return {
        "engine": engine,
        "model_id": model_id,
        "confidence": confidence,
        "error": error,
        "text": text,
    }


# ── Engine labels & icons ─────────────────────────────────────────────────────

class TestEngineLabels:
    def test_vlm(self):
        assert _engine_label("vlm") == "VLM (InternVL3-8B)"

    def test_kraken(self):
        assert _engine_label("kraken") == "Kraken OCR"

    def test_trocr(self):
        assert _engine_label("trocr") == "TrOCR"

    def test_case_insensitive(self):
        assert _engine_label("VLM") == "VLM (InternVL3-8B)"
        assert _engine_label("Kraken") == "Kraken OCR"

    def test_unknown(self):
        assert _engine_label("unknown-engine") == "unknown-engine"


class TestEngineIcons:
    def test_vlm(self):
        assert _engine_icon("vlm") == "🔮"

    def test_kraken(self):
        assert _engine_icon("kraken") == "📖"

    def test_trocr(self):
        assert _engine_icon("trocr") == "🔤"

    def test_fusion(self):
        assert _engine_icon("fusion") == "🔗"

    def test_fused(self):
        assert _engine_icon("fused") == "✅"

    def test_default(self):
        assert _engine_icon("anything-else") == "🤖"


# ── _is_selected ─────────────────────────────────────────────────────────────

class TestIsSelected:
    def test_exact_match(self):
        rec = {"text": "  Hello world  "}
        assert _is_selected(rec, "Hello world") is True

    def test_strip_whitespace(self):
        rec = {"text": "  Hello world  "}
        assert _is_selected(rec, "  Hello world  ") is True

    def test_no_match(self):
        rec = {"text": "Hello"}
        assert _is_selected(rec, "Goodbye") is False

    def test_empty_text(self):
        rec = {"text": ""}
        assert _is_selected(rec, "") is True
        assert _is_selected(rec, "something") is False


# ── _conf_html ───────────────────────────────────────────────────────────────

class TestConfHtml:
    def test_float_confidence(self):
        html = _conf_html(0.82)
        assert "✅" in html
        assert "82%" in html

    def test_int_confidence(self):
        html = _conf_html(1)
        assert "✅" in html
        assert "100%" in html

    def test_zero_confidence(self):
        html = _conf_html(0.0)
        assert "✅" in html
        assert "0%" in html

    def test_none(self):
        assert _conf_html(None) == ""


# ── _recognition_candidate_html ──────────────────────────────────────────────

class TestRecognitionCandidateHtml:
    def test_success_panel(self):
        rec = make_rec("vlm", "internvl3-8b", confidence=0.8, text="Hello world")
        html = _recognition_candidate_html(rec, "bat")
        assert 'class="rec-panel"' in html
        assert "VLM (InternVL3-8B)" in html
        assert "✅ 80%" in html
        assert "internvl3-8b" in html
        assert "2,312" not in html  # bat-specific, not this fixture

    def test_error_panel(self):
        rec = make_rec("trocr", error="timed out", text="")
        html = _recognition_candidate_html(rec, "bat")
        assert 'class="rec-panel rec-panel--error"' in html
        assert "❌ Fehler" in html
        assert "timed out" in html

    def test_download_link(self):
        rec = make_rec("kraken", "kraken-catmus", confidence=0.82, text="Hello")
        html = _recognition_candidate_html(rec, "bat")
        assert 'href="recognitions/kraken-kraken-catmus.txt"' in html
        assert "rec-dl" in html

    def test_no_download_on_error(self):
        rec = make_rec("trocr", error="timeout", text="")
        html = _recognition_candidate_html(rec, "bat")
        assert "rec-dl" not in html

    def test_character_count(self):
        rec = make_rec("vlm", text="Hello")
        html = _recognition_candidate_html(rec, "bat")
        assert "5 Zeichen" in html


# ── build_recognition_section ────────────────────────────────────────────────

class TestBuildRecognitionSection:
    def test_empty_list(self):
        assert build_recognition_section([], "doc", "text") == ""

    def test_empty_recognitions(self):
        assert build_recognition_section(None, "doc", "text") == ""

    def test_single_candidate(self):
        recs = [make_rec("vlm", text="Hello world")]
        html = build_recognition_section(recs, "doc", "Hello world")
        assert "rec-viewer" in html
        assert "VLM (InternVL3-8B)" in html
        assert "rec-heading" in html

    def test_selected_default_exact_match(self):
        # transcript matches rec[1], so it should be pre-checked
        recs = [
            make_rec("kraken", text="wrong text"),
            make_rec("vlm",     text="right text"),
        ]
        html = build_recognition_section(recs, "doc", "right text")
        # The matching candidate should have its radio checked
        assert 'checked' in html
        assert 'value="cand-1-vlm-test-model"' in html

    def test_fallback_to_first_non_error_when_no_exact_match(self):
        recs = [
            make_rec("kraken", text="first"),
            make_rec("trocr",  error="fail"),
        ]
        html = build_recognition_section(recs, "doc", "unrelated text")
        # first non-error should be selected
        assert 'checked' in html
        assert 'value="cand-0-kraken-test-model"' in html

    def test_error_candidates_included(self):
        recs = [
            make_rec("trocr", error="timeout", text=""),
            make_rec("vlm",   text="ok"),
        ]
        html = build_recognition_section(recs, "doc", "ok")
        assert "rec-panel--error" in html
        assert "❌ Fehler" in html
        assert "timeout" in html

    def test_multiple_candidates_all_rendered(self):
        recs = [
            make_rec("vlm",    text="a"),
            make_rec("kraken", text="b"),
            make_rec("trocr",  error="fail"),
        ]
        html = build_recognition_section(recs, "doc", "a")
        assert html.count('class="rec-panel"') == 2  # 2 success panels
        assert html.count('class="rec-panel rec-panel--error"') == 1

    def test_radio_name_doc_scoped(self):
        recs = [make_rec("vlm")]
        html = build_recognition_section(recs, "my-doc-id", "x")
        assert 'name="rec-my-doc-id"' in html

    def test_no_recognitions_no_section(self):
        recs = []
        html = build_recognition_section(recs, "doc", "")
        assert html == ""

    def test_confidence_badge_shown_for_success(self):
        recs = [make_rec("vlm", confidence=0.8, text="Hello")]
        html = build_recognition_section(recs, "doc", "Hello")
        assert "✅ 80%" in html

    def test_doc_id_in_viewer_data_attribute(self):
        recs = [make_rec("vlm")]
        html = build_recognition_section(recs, "bat", "text")
        assert 'data-doc-id="bat"' in html
