"""Tests for build_recognitions.py export functions (issue #38)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from rec_artifacts import TEI_MIME, MANIFEST_MIME, TEXT_MIME

from build_recognitions import (
    _candidate_export_links_html,
    _engine_icon,
    _engine_label,
    build_recognition_section,
    render_candidate_exports_section,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def make_rec(engine, model_id="model", confidence=None, error="", text="Sample text", page=None):
    return {
        "engine": engine,
        "model_id": model_id,
        "confidence": confidence,
        "error": error,
        "text": text,
        "page": page,
    }


# ── Deterministic filenames ───────────────────────────────────────────────────

class TestExportFilenamesDeterministic:
    """Same inputs → same output (issue #38 key requirement)."""

    def test_same_doc_engine_model_gives_same_base(self):
        from rec_artifacts import candidate_export_filename
        a = candidate_export_filename("bat", "vlm", "internvl3-8b-instruct", ".xml", page=1)
        b = candidate_export_filename("bat", "vlm", "internvl3-8b-instruct", ".xml", page=1)
        assert a == b, f"Expected {a} == {b}"

    def test_different_pages_give_different_bases(self):
        from rec_artifacts import candidate_export_filename
        a = candidate_export_filename("bat", "vlm", "model", ".xml", page=1)
        b = candidate_export_filename("bat", "vlm", "model", ".xml", page=2)
        assert a != b


# ── MIME types ───────────────────────────────────────────────────────────────

class TestMimeTypes:
    def test_tei_mime(self):
        assert TEI_MIME == "application/xml; charset=utf-8"

    def test_json_mime(self):
        assert MANIFEST_MIME == "application/json; charset=utf-8"

    def test_text_mime(self):
        assert TEXT_MIME == "text/plain; charset=utf-8"


# ── _candidate_export_links_html ─────────────────────────────────────────────

class TestCandidateExportLinksHtml:
    def test_returns_empty_for_error(self):
        rec = make_rec("trocr", error="timeout", text="")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert html == ""

    def test_returns_empty_for_empty_text(self):
        rec = make_rec("vlm", text="")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert html == ""

    def test_has_ul_exports_list(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert '<ul class="exports-list">' in html

    def test_tei_link_has_correct_type(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert f'type="{TEI_MIME}"' in html

    def test_json_link_has_correct_type(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert f'type="{MANIFEST_MIME}"' in html

    def test_txt_link_has_correct_type(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert f'type="{TEXT_MIME}"' in html

    def test_all_three_links_present(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert html.count('<a href=') == 3

    def test_download_attribute_present(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert html.count('download') == 3

    def test_aria_label_includes_engine(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert 'aria-label="TEI/XML-Export herunterladen (vlm' in html
        assert 'aria-label="JSON-Export herunterladen (vlm' in html

    def test_xml_link_targets_recognitions_dir(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert 'href="recognitions/' in html
        assert '.xml"' in html

    def test_json_link_targets_recognitions_dir(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert '.json"' in html

    def test_txt_link_targets_recognitions_dir(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert '.txt"' in html

    def test_page_label_included_when_available(self):
        rec = make_rec("vlm", text="hello", page=3)
        html = _candidate_export_links_html(rec, 0, "bat")
        assert "Seite 3" in html
        assert 'aria-label="TEI/XML-Export herunterladen (vlm, Seite 3)' in html

    def test_no_page_label_when_not_available(self):
        rec = make_rec("vlm", text="hello", page=None)
        html = _candidate_export_links_html(rec, 0, "bat")
        assert "Seite" not in html

    def test_dl_link_class_used(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert 'class="dl-link dl-link--xml"' in html
        assert 'class="dl-link dl-link--json"' in html
        assert 'class="dl-link dl-link--txt"' in html

    def test_exports_badge_spans_present(self):
        rec = make_rec("vlm", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert 'exports-badge--xml' in html
        assert 'exports-badge--json' in html
        assert 'exports-badge' in html

    def test_data_cand_attribute(self):
        rec = make_rec("vlm", "model", text="hello")
        html = _candidate_export_links_html(rec, 0, "bat")
        assert 'data-cand="cand-0-vlm-model"' in html


# ── render_candidate_exports_section ─────────────────────────────────────────

class TestRenderCandidateExportsSection:
    def test_empty_list_returns_empty(self):
        assert render_candidate_exports_section([], "bat") == ""

    def test_none_returns_empty(self):
        assert render_candidate_exports_section(None, "bat") == ""

    def test_error_candidate_skipped(self):
        recs = [make_rec("trocr", error="timeout")]
        html = render_candidate_exports_section(recs, "bat")
        assert html == ""

    def test_empty_text_candidate_skipped(self):
        recs = [make_rec("vlm", text="")]
        html = render_candidate_exports_section(recs, "bat")
        assert html == ""

    def test_renders_exports_section(self):
        recs = [make_rec("vlm", text="hello")]
        html = render_candidate_exports_section(recs, "bat")
        assert "exports-section" in html
        assert 'id="exports-heading"' in html
        assert "Strukturierte Exporte" in html

    def test_all_candidates_listed(self):
        recs = [
            make_rec("vlm",    model_id="model-a", text="a"),
            make_rec("kraken", model_id="model-b", text="b"),
        ]
        html = render_candidate_exports_section(recs, "bat")
        assert "VLM (InternVL3-8B)" in html
        assert "Kraken OCR" in html

    def test_engine_icon_per_candidate(self):
        recs = [make_rec("vlm", text="hello")]
        html = render_candidate_exports_section(recs, "bat")
        assert _engine_icon("vlm") in html  # 🔮

    def test_page_metadata_included(self):
        recs = [make_rec("vlm", text="hello", page=2)]
        html = render_candidate_exports_section(recs, "bat")
        assert "Seite 2" in html

    def test_confidence_included_in_label(self):
        recs = [make_rec("vlm", text="hello", confidence=0.85)]
        html = render_candidate_exports_section(recs, "bat")
        assert "85%" in html

    def test_xml_and_json_links_present(self):
        recs = [make_rec("vlm", text="hello")]
        html = render_candidate_exports_section(recs, "bat")
        assert "application/xml" in html
        assert "application/json" in html

    def test_multiple_candidates_all_have_export_links(self):
        recs = [
            make_rec("vlm",    model_id="model-a", text="a"),
            make_rec("kraken", model_id="model-b", text="b"),
            make_rec("trocr",  error="fail"),       # skipped
        ]
        html = render_candidate_exports_section(recs, "bat")
        # Two candidates should produce two blocks
        assert html.count("exports-cand-block") == 2

    def test_exports_grid_container(self):
        recs = [make_rec("vlm", text="hello")]
        html = render_candidate_exports_section(recs, "bat")
        assert "exports-grid" in html


# ── build_recognition_section includes exports ───────────────────────────────

class TestBuildRecognitionSectionWithExports:
    def test_exports_section_appended(self):
        recs = [make_rec("vlm", text="Hello world")]
        html = build_recognition_section(recs, "bat", "Hello world")
        assert "exports-section" in html

    def test_exports_not_shown_when_all_error(self):
        recs = [make_rec("trocr", error="timeout", text="")]
        html = build_recognition_section(recs, "bat", "")
        assert "exports-section" not in html

    def test_exports_included_for_multiple_candidates(self):
        recs = [
            make_rec("vlm",    text="a"),
            make_rec("kraken", text="b"),
        ]
        html = build_recognition_section(recs, "bat", "a")
        assert "exports-section" in html

    def test_tei_xml_links_in_recognition_panel(self):
        """Per-candidate panel should also have TEI/XML and JSON export links."""
        recs = [make_rec("vlm", text="hello")]
        html = build_recognition_section(recs, "bat", "hello")
        # The panel dl_note now contains export links
        assert "exports-list" in html
        assert "exports-badge--xml" in html
        assert "exports-badge--json" in html

    def test_teardown_closes_section_properly(self):
        recs = [make_rec("vlm", text="hello")]
        html = build_recognition_section(recs, "bat", "hello")
        # The section should be properly closed
        assert html.count("</section>") >= 1

    def test_page_specific_export_filename(self):
        recs = [make_rec("vlm", text="page 1 content", page=1)]
        html = build_recognition_section(recs, "bat", "page 1 content")
        # Filename should include page indicator
        assert "p1" in html

    def test_exports_html_not_double_escaped(self):
        recs = [make_rec("vlm", model_id="test/model", text="hello")]
        html = build_recognition_section(recs, "bat", "hello")
        # Slashes in model_id should be replaced with hyphens in data-cand
        assert "cand-0-vlm-test-model" in html
