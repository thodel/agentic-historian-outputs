"""
Recognition artifact naming and metadata contract (issue #34).

Provides:
- Stable, collision-resistant artifact paths/names
- Artifact type taxonomy: raw, fused/selected, error record
- MIME type, encoding, and line-ending expectations
- Consistent publisher (build_outputs) and site-reader (HTML renderer) logic

Design principles
-----------------
- Names are deterministic: same inputs → same name across runs.
- Collision-resistant: duplicate engine/model in same doc → indexed suffix.
- Page-attributed: page metadata is included when available.
- Unicode, slashes, spaces, and DOI-like model IDs are handled safely.
- Raw vs derived labels are unambiguous.
- Publisher and reader use the same naming logic from this module.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Optional

# ── Artifact type taxonomy ───────────────────────────────────────────────────

class ArtifactType(Enum):
    """Recognition artifact types and their file semantics."""
    RAW          = "raw"           # Individual engine/model text output
    FUSED        = "fused"         # Selected/fused multi-engine transcription
    ERROR        = "error"         # Failed recognition attempt
    NORMALIZED   = "normalized"    # Raw text after light post-processing
    EVALUATION   = "evaluation"    # Pairwise/comparison record


# ── Derived-type qualifiers for segment names ────────────────────────────────

ARTIFACT_QUALIFIER: dict[ArtifactType, str] = {
    ArtifactType.RAW:        "",
    ArtifactType.FUSED:      "-fused",
    ArtifactType.ERROR:      "-error",
    ArtifactType.NORMALIZED: "-normalized",
    ArtifactType.EVALUATION: "-eval",
}


# ── Encoding and MIME type contract ─────────────────────────────────────────

TEXT_MIME     = "text/plain; charset=utf-8"
ERROR_MIME    = "text/plain; charset=utf-8"
MANIFEST_MIME = "application/json; charset=utf-8"
TEI_MIME      = "application/xml; charset=utf-8"
ZIP_MIME      = "application/zip"


# ── Safe name construction ───────────────────────────────────────────────────

def _safe_name_component(s: str) -> str:
    """Make a string safe for use inside a filename segment.

    - NFC-normalizes.
    - Lowercases.
    - Replaces runs of non-alphanumeric with a single hyphen.
    - Strips leading/trailing hyphens.
    - Collapses multiple slashes.
    - Rejects empty strings (→ "unnamed").
    """
    if not s:
        return "unnamed"
    s = unicodedata.normalize("NFC", s)
    s = s.replace("\\", "/")
    s = re.sub(r"/+", "/", s)
    s = s.strip("/")
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s)
    s = s.strip("-")
    return s or "unnamed"


def _normalize_model_id(model_id: str) -> str:
    """Normalize a model_id: slashes → hyphens, colons → hyphens."""
    if not model_id:
        return "unknown-model"
    return model_id.replace("/", "-").replace(":", "-")


# ── Core naming ─────────────────────────────────────────────────────────────

def artifact_segment(
    engine: str,
    model_id: str,
    artifact_type: ArtifactType = ArtifactType.RAW,
    *,
    page: Optional[str | int] = None,
) -> str:
    """Core name segment for an artifact, e.g. ``vlm-internvl3-8b-instruct-p3``."""
    eng   = _safe_name_component(engine)
    model = _safe_name_component(_normalize_model_id(model_id))
    seg   = f"{eng}-{model}"
    if page is not None:
        seg += f"-p{page}"
    if artifact_type != ArtifactType.RAW:
        seg += ARTIFACT_QUALIFIER[artifact_type]
    return seg


def recognition_artifact_path(
    doc_id: str,
    engine: str,
    model_id: str,
    artifact_type: ArtifactType = ArtifactType.RAW,
    *,
    page: Optional[str | int] = None,
    suffix: str = ".txt",
) -> str:
    """Relative artifact path, e.g. ``recognitions/vlm-internvl3-8b-instruct-p3.txt``."""
    seg = artifact_segment(engine, model_id, artifact_type, page=page)
    return f"recognitions/{seg}{suffix}"


def fused_artifact_path(doc_id: str, suffix: str = ".txt") -> str:
    """Relative path for the selected/fused transcription artifact."""
    return f"recognitions/fused{suffix}"


# ── Duplicate engine/model handling ─────────────────────────────────────────

def make_unique_segment(
    engine: str,
    model_id: str,
    seen: set[str],
    artifact_type: ArtifactType = ArtifactType.RAW,
    *,
    page: Optional[str | int] = None,
) -> str:
    """Return a unique segment name, appending -2, -3, … as needed."""
    base = artifact_segment(engine, model_id, artifact_type, page=page)
    if base not in seen:
        seen.add(base)
        return base
    idx = 2
    while True:
        candidate = f"{base}-{idx}"
        if candidate not in seen:
            seen.add(candidate)
            return candidate
        idx += 1


# ── Package naming ──────────────────────────────────────────────────────────

def manifest_filename(doc_id: str) -> str:
    """Machine-readable manifest filename for a complete package."""
    return f"{_safe_name_component(doc_id)}-manifest.json"


def package_basename(doc_id: str, extension: str = ".zip") -> str:
    """Complete download package basename."""
    return f"{_safe_name_component(doc_id)}-complete{extension}"


def candidate_export_filename(
    doc_id: str,
    engine: str,
    model_id: str,
    fmt: str,
    *,
    page: Optional[str | int] = None,
) -> str:
    """Structured candidate export filename with format extension."""
    base = _safe_name_component(doc_id)
    seg  = artifact_segment(engine, model_id, page=page)
    return f"{base}-{seg}{fmt}"


# ── Artifact metadata record ────────────────────────────────────────────────

@dataclass
class ArtifactMeta:
    path:           str
    engine:         str
    model_id:       str
    artifact_type:  ArtifactType
    page:           Optional[str | int] = None
    mime:           str = TEXT_MIME
    char_count:     int = 0
    has_text:       bool = False
    is_error:       bool = False
    cand_index:     int = 0
    label:          str = ""

    @property
    def segment(self) -> str:
        import os
        return os.path.splitext(os.path.basename(self.path))[0]


def collect_artifacts(
    doc_id: str,
    recognitions: list[dict],
    transcript: str = "",
    selected_index: Optional[int] = None,
) -> list[ArtifactMeta]:
    """Build artifact metadata for all recognition candidates."""
    seen_set: set[str] = set()
    artifacts: list[ArtifactMeta] = []

    for i, rec in enumerate(recognitions):
        engine   = rec.get("engine", "unknown")
        model_id = rec.get("model_id", "unknown")
        page_meta = rec.get("page")
        error    = rec.get("error", "")
        text     = rec.get("text", "") or ""
        char_count = len(text.replace("\r", "").replace("\n", ""))
        is_error  = bool(error)
        art_type  = ArtifactType.ERROR if is_error else ArtifactType.RAW
        confidence = rec.get("confidence")

        # Human label
        from build_recognitions import _engine_label
        label_parts = [_engine_label(engine)]
        if page_meta is not None:
            label_parts.append(f"Seite {page_meta}")
        if is_error:
            label_parts.append("Fehler")
        elif char_count > 0:
            label_parts.append(f"{char_count:,} Zeichen")
        if confidence is not None:
            label_parts.append(f"{confidence:.0%}")
        label = " · ".join(label_parts)

        seg = make_unique_segment(engine, model_id, seen_set, art_type, page=page_meta)
        path = f"recognitions/{seg}.txt"

        artifacts.append(ArtifactMeta(
            path=path,
            engine=engine,
            model_id=model_id,
            artifact_type=art_type,
            page=page_meta,
            mime=ERROR_MIME if is_error else TEXT_MIME,
            char_count=char_count,
            has_text=not is_error and bool(text.strip()),
            is_error=is_error,
            cand_index=i,
            label=label,
        ))

    return artifacts
