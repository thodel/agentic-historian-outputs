"""Accessible recognition-candidate rendering for generated output pages."""
from __future__ import annotations

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
