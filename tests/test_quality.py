"""Tests for Epic 5 quality indicators (issues #26–#32)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))


def test_explanations_registry_completeness():
    from quality import EXPLANATIONS, BADGE_CLASS_MAP
    badge_types = {
        "engine_confidence", "agreement", "reference_evaluation",
        "degenerate", "failed", "missing", "legacy_qa",
    }
    for btype in badge_types:
        assert btype in BADGE_CLASS_MAP, f"{btype} missing from BADGE_CLASS_MAP"
        assert btype in EXPLANATIONS, f"{btype} missing from EXPLANATIONS"
        short, body = EXPLANATIONS[btype]
        assert short, f"{btype} has no short label"
        assert body, f"{btype} has no body text"
        assert len(short) <= 80, f"{btype} short label too long: {short}"
    assert "incomparable_confidence" in EXPLANATIONS
    print("test_explanations_registry_completeness: PASS")


def test_format_confidence():
    from quality import format_confidence
    assert format_confidence(None) == "Nicht angegeben"
    assert format_confidence(0.95) == "95%"
    assert format_confidence(0.001) == "0%"
    assert format_confidence(1.0) == "100%"
    assert format_confidence(1.5) == "100%"
    assert format_confidence(-0.5) == "0%"
    assert format_confidence(0.333) == "33%"
    print("test_format_confidence: PASS")


def test_detect_degeneration():
    from quality import detect_degeneration
    assert not detect_degeneration("hello world")[0]
    assert detect_degeneration("aaaaa" * 5)[0]
    assert detect_degeneration("ababab" * 5)[0]
    assert detect_degeneration("   " * 60)[0]
    assert detect_degeneration("x" * 1_000_001)[0]
    is_deg, _ = detect_degeneration("hello", confidence=0.001)
    assert is_deg
    print("test_detect_degeneration: PASS")


def test_confidence_scope_label():
    from quality import confidence_scope_label
    assert confidence_scope_label("kraken", None, None) == "kraken"
    assert confidence_scope_label("kraken", "catmus", None) == "kraken/catmus"
    assert confidence_scope_label("kraken", "catmus", "p001") == "kraken/catmus/Seite p001"
    assert confidence_scope_label("kraken", None, "p001") == "kraken/Seite p001"
    print("test_confidence_scope_label: PASS")


def test_candidates_includes_selected_plus_raw():
    from build_recognitions import _candidates
    result = _candidates([], "fused text")
    assert len(result) == 1
    assert result[0]["id"] == "selected"
    assert result[0]["selected"] is True
    result = _candidates([{"engine": "kraken", "model_id": "catmus", "text": "hello"}], "fused text")
    assert len(result) == 2
    assert result[0]["selected"] is True
    assert result[1]["selected"] is False
    assert result[1]["engine"] == "kraken"
    print("test_candidates_includes_selected_plus_raw: PASS")


def test_candidates_failure_state():
    from build_recognitions import _candidates
    result = _candidates([{"engine": "kraken", "model_id": "catmus", "text": "", "error": "timeout"}], "")
    assert result[1]["error"] == "Der Erkennungsdienst hat das Zeitlimit überschritten."
    result = _candidates([{"engine": "kraken", "model_id": "catmus", "text": ""}], "")
    assert "keinen Text" in result[1]["error"]
    print("test_candidates_failure_state: PASS")


def test_candidates_degenerate_detection():
    from build_recognitions import _candidates
    result = _candidates([{"engine": "kraken", "model_id": "catmus", "text": "aaaaa" * 5, "confidence": 0.9}], "")
    assert "Degenerierte Erkennung" in result[1]["error"]
    print("test_candidates_degenerate_detection: PASS")


def test_build_recognition_section_produces_valid_html():
    from build_recognitions import build_recognition_section
    with tempfile.TemporaryDirectory() as tmpdir:
        rec_data = [
            {"engine": "kraken", "model_id": "catmus", "page": "p1", "text": "hello", "confidence": 0.85},
            {"engine": "vlm", "model_id": "internvl", "page": "p1", "text": "hallo", "confidence": 0.91},
        ]
        html = build_recognition_section(rec_data, "test-doc", "fused", directory=Path(tmpdir))
        assert 'id="recognitions"' in html
        assert 'aria-labelledby="recognitions-heading"' in html
        assert "<details" in html
        assert "data-recognition-viewer" in html
        assert "quality-badge" in html
        assert "rec-status" in html
        assert "quality-explain-btn" in html
        assert "quality-explanation" in html
        assert "incomparable_confidence" in html
        assert "rec-download" in html
    print("test_build_recognition_section_produces_valid_html: PASS")


def test_reference_evaluation_block():
    from build_recognitions import _build_ref_eval_html
    candidate = {
        "reference_eval": {
            "cer": 0.05, "wer": 0.12,
            "reference_name": "Königsfelden Ground Truth",
            "reference_version": "v1.2",
            "normalisation": "standardized whitespace",
            "scope": "page",
        }
    }
    html = _build_ref_eval_html(candidate)
    assert "CER" in html and "WER" in html
    assert "Königsfelden Ground Truth" in html and "v1.2" in html
    assert "rec-ref-eval" in html
    print("test_reference_evaluation_block: PASS")


def test_typed_quality_badges_in_card():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from build_index import _card, Record
    from datetime import datetime, timezone

    record = Record(
        doc_id="test-doc",
        created=datetime.now(timezone.utc),
        date_label="14. Jh.",
        language="de",
        script="Kurrent",
        document_type="Urbar",
        entities=3,
        pages=10,
        qa_score=None,
        errors=0,
        is_test=False,
        preview="test transcription",
        review_status="machine-generated",
        recognition_errors=0,
        recognition_avg_confidence=0.87,
        reference_cer=0.04,
        reference_wer=None,
    )
    card = _card(record)
    assert "Ø Konfidenz" in card
    assert "CER" in card
    assert "Legacy-QA" not in card
    print("test_typed_quality_badges_in_card: PASS")


def test_legacy_qa_badge_has_distinct_style():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from build_index import _card, Record
    from datetime import datetime, timezone

    record = Record(
        doc_id="test-doc",
        created=datetime.now(timezone.utc),
        date_label="14. Jh.",
        language="de",
        script="Kurrent",
        document_type="Urbar",
        entities=3,
        pages=10,
        qa_score=0.75,
        errors=0,
        is_test=False,
        preview="test transcription",
        review_status="machine-generated",
        recognition_errors=0,
        recognition_avg_confidence=None,
        reference_cer=None,
        reference_wer=None,
    )
    card = _card(record)
    assert "Legacy-QA" in card
    print("test_legacy_qa_badge_has_distinct_style: PASS")


def test_recognition_section_wired_in_outputs():
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
    from build_outputs import build_recognition_section
    html = build_recognition_section(None, "test", "fused")
    assert html == ""
    print("test_recognition_section_wired_in_outputs: PASS")


if __name__ == "__main__":
    test_explanations_registry_completeness()
    test_format_confidence()
    test_detect_degeneration()
    test_confidence_scope_label()
    test_candidates_includes_selected_plus_raw()
    test_candidates_failure_state()
    test_candidates_degenerate_detection()
    test_build_recognition_section_produces_valid_html()
    test_reference_evaluation_block()
    test_typed_quality_badges_in_card()
    test_legacy_qa_badge_has_distinct_style()
    test_recognition_section_wired_in_outputs()
    print("\nAll tests passed!")
