"""Accessible recognition-candidate rendering for generated output pages.

Recognition Artifact Naming and Metadata Contract (#34)
========================================================

Path Structure
--------------
  recognitions/                          root for all artifacts
    fused.txt                            selected/fused transcription
    <page_slug>/                         optional page subdirectory
      <engine>-<model>.txt               raw candidate for page
      <engine>-<model>.error.txt         error record for failed candidate
      <engine>-<model>.eval.txt          evaluation artifact (CER/WER etc.)
    <engine>-<model>.txt                 candidate without page attribution
    <engine>-<model>.error.txt           error record without page
    catalogue.json                       machine-readable inventory of all artifacts
    manifest.json                        package manifest for complete downloads

Filename Sanitisation
---------------------
- Spaces, Unicode, slashes, and special characters become underscores.
- Model IDs with slashes use "_" instead of "/".
- Result is lowercased and truncated to 100 characters.
- Collisions are resolved by path-count deduplication in _candidates.

MIME, Encoding, Line-endings
----------------------------
- charset=utf-8 for all text artifacts.
- LF line endings (Unix convention).
- Unicode normalisation: NFD (decomposed).

Artifact Types
==============
Suffix          Type             Contents
===========     ===============  ======================================
.txt            raw candidate    Raw engine transcription text only
.error.txt      error record     JSON: engine, model_id, page, error, ts
.eval.txt       evaluation       JSON: metric name, value, ref, scope
fused.txt       selected output  Fused/selected transcription
catalogue.json  inventory        JSON array of artifact metadata
manifest.json   manifest         JSON: doc_id, version, checksums, rights
===========     ===============  ======================================
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import html
import re
from collections import Counter
from pathlib import Path
from urllib.parse import quote


def _engine_label(engine: str) -> str:
    return {
        "vlm": "VLM",
        "kraken": "Kraken OCR",
        "trocr": "TrOCR",
        "fusion": "Ausgewählt / Fusion",
    }.get(str(engine).lower(), str(engine) or "Unbekannte Engine")


def _safe_slug(value: object, fallback: str = "candidate") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value).casefold()).strip("-")
    return slug[:100] or fallback


def _public_error(error: object) -> str:
    """Return a useful public message without endpoints, paths, or credentials."""
    message = str(error or "").strip()
    lowered = message.casefold()
    if not message:
        return ""
    if "timed out" in lowered or "timeout" in lowered:
        return "Der Erkennungsdienst hat das Zeitlimit überschritten."
    if "unavailable" in lowered or "connection" in lowered:
        return "Der Erkennungsdienst war nicht erreichbar."
    if "unsupported" in lowered or "not found" in lowered:
        return "Das angeforderte Erkennungsmodell war nicht verfügbar."
    return "Der Erkennungsversuch ist fehlgeschlagen."


def _confidence(confidence: object) -> str:
    if not isinstance(confidence, (int, float)):
        return "Nicht angegeben"
    return f"{max(0.0, min(1.0, float(confidence))):.0%}"


def _recognition_path(candidate: dict) -> str:
    """Mirror the publisher's page-aware candidate path contract (#284)."""
    page = str(candidate.get("page") or "").strip()
    engine = str(candidate.get("engine") or "engine").strip() or "engine"
    model = str(candidate.get("model_id") or "").strip().replace("/", "_")
    stem = f"{engine}-{model}" if model else engine
    if page:
        page_slug = re.sub(r"[^A-Za-z0-9._-]+", "_", page.rsplit(".", 1)[0])
        return f"recognitions/{page_slug}/{stem}.txt"
    return f"recognitions/{stem}.txt"



def _error_path(candidate: dict) -> str:
    """Return the canonical path for an error-record artifact."""
    raw = dict(page=candidate.get("page"), engine=candidate.get("engine"),
               model_id=candidate.get("model_id"))
    base = _recognition_path(raw)
    return base.replace(".txt", ".error.txt") if base else ""


def write_error_record(directory: Path, candidate: dict) -> Path | None:
    """Write a JSON error record for a failed recognition attempt.

    Returns the path of the written file, or None if the candidate succeeded.
    """
    error = _public_error(candidate.get("error"))
    if not error:
        return None
    path = _error_path(candidate)
    if not path:
        return None
    record = {
        "engine": str(candidate.get("engine") or ""),
        "model_id": str(candidate.get("model_id") or ""),
        "page": str(candidate.get("page") or ""),
        "error": error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    file_path = directory / path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


def compute_checksum(path: Path) -> str:
    """Return the SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def write_catalogue(directory: Path, doc_id: str, recognitions: list,
                    transcript: str) -> Path:
    """Write a machine-readable JSON inventory of all recognition artifacts.

    Includes selected/fused and every successful candidate; failed attempts
    are listed with error metadata but no text artifact path.
    """
    candidates = _candidates(recognitions, transcript)
    items = []
    for cand in candidates:
        item = {
            "id": cand["id"],
            "engine": cand["engine"],
            "model_id": cand["model_id"] or None,
            "page": cand["page"] or None,
            "status": "error" if cand["error"] else "success",
            "error": cand["error"] or None,
            "path": cand["path"] if (cand["path"] and not cand["error"]) else None,
            "error_path": _error_path(cand) if cand["error"] else None,
            "characters": len(cand["text"]) if not cand["error"] else None,
        }
        items.append(item)
    catalogue = {"doc_id": doc_id, "version": "1.0", "artifacts": items}
    path = directory / "recognitions" / "catalogue.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _candidates(recognitions, transcript: str) -> list[dict]:
    """Normalize selected output and every attempted recognition."""
    result = [{
        "id": "selected",
        "engine": "fusion",
        "model_id": "",
        "page": "",
        "text": str(transcript or ""),
        "confidence": None,
        "error": "",
        "selected": True,
        "path": "recognitions/fused.txt",
    }]
    raw_candidates = [raw for raw in (recognitions or []) if isinstance(raw, dict)]
    path_counts = Counter(_recognition_path(raw) for raw in raw_candidates)
    seen = {"selected"}
    for index, raw in enumerate(raw_candidates, start=1):
        if not isinstance(raw, dict):
            continue
        engine = str(raw.get("engine") or "unknown")
        model = str(raw.get("model_id") or "")
        page = str(raw.get("page") or "")
        base = _safe_slug(f"{page}-{engine}-{model}", f"candidate-{index}")
        candidate_id = base
        suffix = 2
        while candidate_id in seen:
            candidate_id = f"{base}-{suffix}"
            suffix += 1
        seen.add(candidate_id)
        text = str(raw.get("text") or "")
        error = _public_error(raw.get("error"))
        if not error and not text.strip():
            error = "Der Erkennungsversuch lieferte keinen Text."
        result.append({
            "id": candidate_id,
            "engine": engine,
            "model_id": model,
            "page": page,
            "text": text,
            "confidence": raw.get("confidence"),
            "error": error,
            "selected": False,
            # Historical multi-page records without page attribution collide at
            # one publisher path. Never link a candidate to an ambiguous file.
            "path": (_recognition_path(raw)
                     if path_counts[_recognition_path(raw)] == 1 else ""),
        })
    return result


def build_recognition_section(recognitions, doc_id: str, transcript: str,
                              directory: Path | None = None) -> str:
    """Render a no-JS-complete viewer that JavaScript enhances to switching."""
    if not recognitions:
        return ""
    directory = Path(directory) if directory is not None else None
    candidates = _candidates(recognitions, transcript)
    links, panels = [], []
    for candidate in candidates:
        cid = candidate["id"]
        label = _engine_label(candidate["engine"])
        if candidate["model_id"]:
            label += f" · {candidate['model_id']}"
        status = "Fehlgeschlagen" if candidate["error"] else "Erfolgreich"
        links.append(
            f'<li><a href="#recognition-{cid}" data-recognition-select="{cid}" '
            f'aria-controls="recognition-{cid}">{html.escape(label)}</a> '
            f'<span class="rec-status rec-status--{status.casefold()}">{status}</span></li>'
        )
        path = candidate["path"]
        artifact_exists = bool(path) and (directory is None or (directory / path).exists())
        download = (
            f'<a class="rec-download" href="{quote(path, safe="/._-")}" download>'
            "Diese Transkription herunterladen</a>"
            if not candidate["error"] and artifact_exists else
            '<span class="rec-download-unavailable">Kein Textdownload verfügbar</span>'
        )
        if candidate["error"]:
            content = (
                '<div class="notice notice--warning rec-error"><strong>Erkennung fehlgeschlagen.</strong> '
                f'{html.escape(candidate["error"])}</div>'
            )
        else:
            content = (
                '<pre class="rec-text" tabindex="0"><code>'
                f'{html.escape(candidate["text"])}</code></pre>'
            )
        panels.append(f'''<details class="rec-panel" id="recognition-{cid}" data-recognition-panel="{cid}" data-page="{html.escape(candidate["page"], quote=True)}"{' open' if candidate["selected"] else ''}>
<summary>{html.escape(label)}{' — ausgewählt' if candidate["selected"] else ''}</summary>
<dl class="rec-meta"><div><dt>Engine</dt><dd>{html.escape(candidate["engine"])}</dd></div><div><dt>Modell</dt><dd>{html.escape(candidate["model_id"]) or '—'}</dd></div><div><dt>Seite</dt><dd>{html.escape(candidate["page"]) or 'Nicht zugeordnet'}</dd></div><div><dt>Engine-Konfidenz</dt><dd>{_confidence(candidate["confidence"])}</dd></div><div><dt>Zeichen</dt><dd>{len(candidate["text"])}</dd></div><div><dt>Status</dt><dd>{status}</dd></div></dl>
{content}<p>{download}</p></details>''')
    return f'''<section id="recognitions" aria-labelledby="recognitions-heading">
<h2 id="recognitions-heading">Erkennungsversionen</h2>
<p class="rec-intro">Alle maschinellen Erkennungsversuche bleiben als überprüfbare Provenienz sichtbar. Konfidenzwerte verschiedener Engines sind nicht unmittelbar vergleichbar.</p>
<div class="rec-viewer" data-recognition-viewer data-doc-id="{html.escape(doc_id, quote=True)}">
<nav class="rec-selector" aria-label="Erkennungsversionen"><ul>{''.join(links)}</ul></nav>
<div class="rec-panels">{''.join(panels)}</div></div></section>'''
