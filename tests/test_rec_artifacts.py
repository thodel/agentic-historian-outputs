"""Tests for rec_artifacts.py (issue #34) — naming and metadata contract."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from rec_artifacts import (
    ArtifactType,
    TEXT_MIME, ERROR_MIME, MANIFEST_MIME,
    _safe_name_component,
    _normalize_model_id,
    artifact_segment,
    recognition_artifact_path,
    fused_artifact_path,
    make_unique_segment,
    manifest_filename,
    package_basename,
    candidate_export_filename,
    collect_artifacts,
)


# ── _safe_name_component ─────────────────────────────────────────────────────

class TestSafeNameComponent:
    def test_lowercase(self):
        assert _safe_name_component("VLM") == "vlm"

    def test_spaces_become_hyphens(self):
        assert _safe_name_component("my model name") == "my-model-name"

    def test_slashes_collapsed(self):
        assert _safe_name_component("a/b/c") == "a-b-c"

    def test_unicode_normalized(self):
        # NFC vs NFD — both should normalize to NFC
        # é as composed (e + ́) vs decomposed (e + combining acute)
        composed  = "\u00e9"   # é
        decomposed = "e\u0301" # é
        assert _safe_name_component(composed) == _safe_name_component(decomposed)

    def test_multiple_non_alnum_to_single_hyphen(self):
        assert _safe_name_component("a  b!!!  c") == "a-b-c"

    def test_empty_string(self):
        assert _safe_name_component("") == "unnamed"

    def test_doi_like_id(self):
        # DOI-like: "thodel/kf-data" → "thodel-kf-data"
        assert _safe_name_component("thodel/kf-data") == "thodel-kf-data"

    def test_strips_leading_trailing_hyphens(self):
        assert _safe_name_component("  abc  ") == "abc"


# ── _normalize_model_id ──────────────────────────────────────────────────────

class TestNormalizeModelId:
    def test_slashes_become_hyphens(self):
        assert _normalize_model_id("anthropic/claude-3-5") == "anthropic-claude-3-5"

    def test_colons_become_hyphens(self):
        assert _normalize_model_id("model:v1") == "model-v1"

    def test_unknown(self):
        assert _normalize_model_id("") == "unknown-model"


# ── artifact_segment ─────────────────────────────────────────────────────────

class TestArtifactSegment:
    def test_basic(self):
        seg = artifact_segment("vlm", "internvl3-8b-instruct")
        assert seg == "vlm-internvl3-8b-instruct"

    def test_page_suffix(self):
        seg = artifact_segment("vlm", "internvl3-8b-instruct", page=3)
        assert seg == "vlm-internvl3-8b-instruct-p3"

    def test_error_qualifier(self):
        seg = artifact_segment("trocr", "base", ArtifactType.ERROR)
        assert seg == "trocr-base-error"

    def test_fused_qualifier(self):
        seg = artifact_segment("fusion", "ensemble", ArtifactType.FUSED)
        assert seg == "fusion-ensemble-fused"

    def test_string_page(self):
        seg = artifact_segment("vlm", "model", page="verso")
        assert "pverso" in seg

    def test_both_page_and_error(self):
        seg = artifact_segment("trocr", "kurrent", ArtifactType.ERROR, page=5)
        assert "p5" in seg
        assert "error" in seg


# ── recognition_artifact_path ────────────────────────────────────────────────

class TestRecognitionArtifactPath:
    def test_basic(self):
        path = recognition_artifact_path("bat", "vlm", "internvl3-8b-instruct")
        assert path == "recognitions/vlm-internvl3-8b-instruct.txt"

    def test_page(self):
        path = recognition_artifact_path("bat", "vlm", "model", page=2)
        assert path == "recognitions/vlm-model-p2.txt"

    def test_error(self):
        path = recognition_artifact_path("bat", "trocr", "base", ArtifactType.ERROR)
        assert path == "recognitions/trocr-base-error.txt"

    def test_custom_suffix(self):
        path = recognition_artifact_path("bat", "vlm", "model", suffix=".xml")
        assert path == "recognitions/vlm-model.xml"


# ── fused_artifact_path ──────────────────────────────────────────────────────

class TestFusedArtifactPath:
    def test_basic(self):
        assert fused_artifact_path("bat") == "recognitions/fused.txt"

    def test_custom_suffix(self):
        assert fused_artifact_path("bat", suffix=".md") == "recognitions/fused.md"


# ── make_unique_segment ──────────────────────────────────────────────────────

class TestMakeUniqueSegment:
    def test_first_occurrence_no_suffix(self):
        seen: set = set()
        seg = make_unique_segment("vlm", "model", seen)
        assert seg == "vlm-model"
        assert "vlm-model" in seen

    def test_duplicate_gets_suffix(self):
        seen: set = set()
        s1 = make_unique_segment("vlm", "model", seen)
        s2 = make_unique_segment("vlm", "model", seen)
        assert s1 == "vlm-model"
        assert s2 == "vlm-model-2"

    def test_third_duplicate(self):
        seen: set = set()
        s1 = make_unique_segment("vlm", "model", seen)
        s2 = make_unique_segment("vlm", "model", seen)
        s3 = make_unique_segment("vlm", "model", seen)
        assert s1 == "vlm-model"
        assert s2 == "vlm-model-2"
        assert s3 == "vlm-model-3"

    def test_different_engines_no_collision(self):
        seen: set = set()
        s1 = make_unique_segment("vlm", "model", seen)
        s2 = make_unique_segment("kraken", "model", seen)
        assert s1 == "vlm-model"
        assert s2 == "kraken-model"

    def test_different_models_no_collision(self):
        seen: set = set()
        s1 = make_unique_segment("vlm", "model-a", seen)
        s2 = make_unique_segment("vlm", "model-b", seen)
        assert s1 == "vlm-model-a"
        assert s2 == "vlm-model-b"

    def test_page_differentiates(self):
        seen: set = set()
        s1 = make_unique_segment("vlm", "model", seen, page=1)
        s2 = make_unique_segment("vlm", "model", seen, page=2)
        assert "p1" in s1
        assert "p2" in s2
        assert s1 != s2

    def test_error_type_different_segment(self):
        seen: set = set()
        s1 = make_unique_segment("vlm", "model", seen, ArtifactType.RAW)
        s2 = make_unique_segment("vlm", "model", seen, ArtifactType.ERROR)
        assert s1 == "vlm-model"
        assert "error" in s2


# ── Package naming ────────────────────────────────────────────────────────────

class TestPackageNaming:
    def test_manifest_filename(self):
        assert manifest_filename("bat") == "bat-manifest.json"

    def test_package_basename(self):
        assert package_basename("bat") == "bat-complete.zip"

    def test_package_custom_ext(self):
        assert package_basename("bat", ".tar.gz") == "bat-complete.tar.gz"

    def test_candidate_export_filename(self):
        fname = candidate_export_filename("bat", "vlm", "model", ".xml")
        assert fname == "bat-vlm-model.xml"

    def test_candidate_export_with_page(self):
        fname = candidate_export_filename("bat", "vlm", "model", ".xml", page=3)
        assert "p3" in fname
        assert fname.endswith(".xml")


# ── collect_artifacts ────────────────────────────────────────────────────────

class TestCollectArtifacts:
    def make_rec(self, engine, model, text="test", error="", confidence=None, page=None):
        return {"engine": engine, "model_id": model, "text": text,
                "error": error, "confidence": confidence, "page": page}

    def test_single_candidate(self):
        recs = [self.make_rec("vlm", "model", text="hello")]
        arts = collect_artifacts("bat", recs)
        assert len(arts) == 1
        assert arts[0].path == "recognitions/vlm-model.txt"
        assert arts[0].has_text is True
        assert arts[0].is_error is False

    def test_error_no_text(self):
        recs = [self.make_rec("trocr", "model", error="timeout")]
        arts = collect_artifacts("bat", recs)
        assert len(arts) == 1
        assert arts[0].is_error is True
        # error record may have error text but is not usable transcription
        assert "error" in arts[0].path

    def test_duplicate_engine_model_indexed(self):
        recs = [
            self.make_rec("vlm", "model", text="first"),
            self.make_rec("vlm", "model", text="second"),
        ]
        arts = collect_artifacts("bat", recs)
        assert arts[0].path == "recognitions/vlm-model.txt"
        assert arts[1].path == "recognitions/vlm-model-2.txt"

    def test_page_attributed(self):
        recs = [
            self.make_rec("vlm", "model", text="p1", page=1),
            self.make_rec("vlm", "model", text="p2", page=2),
        ]
        arts = collect_artifacts("bat", recs)
        assert "p1" in arts[0].path
        assert "p2" in arts[1].path

    def test_character_count(self):
        recs = [self.make_rec("vlm", "model", text="hello world")]
        arts = collect_artifacts("bat", recs)
        assert arts[0].char_count == 11

    def test_multi_page_many_candidates(self):
        # Simulate u-17__ structure: 13 candidates, some errors, some duplicates
        recs = [
            self.make_rec("vlm", "internvl3-8b-instruct", text="a", page=1),
            self.make_rec("kraken", "kraken-catmus_medieval", text="b", page=1),
            self.make_rec("trocr", "trocr-medieval-escriptmask", error="fail", page=2),
            self.make_rec("kraken", "kraken-mccatmus", text="c", page=2),
            self.make_rec("trocr", "trocr-kurrent-xvi-xvii", error="fail", page=2),
            self.make_rec("vlm", "internvl3-8b-instruct", text="d", page=3),
        ]
        arts = collect_artifacts("bat", recs)
        assert len(arts) == 6
        # All paths unique
        paths = [a.path for a in arts]
        assert len(paths) == len(set(paths)), "Duplicate paths detected!"

    def test_doi_slash_model_id(self):
        recs = [self.make_rec("vlm", "anthropic/claude-3-5-sonnet", text="test")]
        arts = collect_artifacts("bat", recs)
        import os; assert "/" not in os.path.basename(arts[0].path)
        assert "anthropic-claude-3-5-sonnet" in arts[0].path


# ── Determinism: same input → same output ─────────────────────────────────────

class TestDeterminism:
    def test_same_inputs_same_segment(self):
        seen: set = set()
        s1 = make_unique_segment("vlm", "model", seen, page=1)
        s2 = make_unique_segment("vlm", "model", seen, page=1)
        # s2 will get -2 since s1 already in seen
        assert s1 == "vlm-model-p1"
        assert s2 == "vlm-model-p1-2"

    def test_fresh_seen_each_time_gives_same_names(self):
        # Without persistent seen set, same inputs give same names
        seg1 = artifact_segment("vlm", "model", page=1)
        seg2 = artifact_segment("vlm", "model", page=1)
        assert seg1 == seg2  # same input → same segment

    def test_no_overwrites(self):
        seen: set = set()
        segs = [make_unique_segment("vlm", "model", seen) for _ in range(5)]
        assert len(segs) == len(set(segs)), "Overwrite detected!"
