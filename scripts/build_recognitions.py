"""Accessible recognition-candidate rendering for generated output pages.

This module is the Epic 5 reference implementation for issue #29
(candidate-level confidence and failure indicators) and issue #31
(reference-based CER/WER with provenance).

It uses scripts/quality as the canonical source for all quality vocabulary,
provenance contract, degeneration detection, and explanation keys.
"""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import quote

try:
    from quality import (
        EXPLANATIONS,
        detect_degeneration,
        format_confidence,
        quality_badge,
        confidence_scope_label,
        explanation_button,
        explanation_block,
        BADGE_CLASS_MAP,
        Provenance,
    )
except ImportError:
    # Fallback when quality.py is not yet available (e.g., during initial bootstrap)
    Provenance = object

    def detect_degeneration(text, confidence=None): return False, ""
    def format_confidence(value): return "Nicht angegeben" if value is None else f"{max(0.0, min(1.0, float(value))):.0%}"
    def confidence_scope_label(engine, model, page): return engine

    BADGE_CLASS_MAP = {}
    EXPLANATIONS = {}

    def quality_badge(kind, value, unit, scope, is_legacy=False):
        if kind == "engine_confidence":
            return f'<span class="quality-badge quality-badge--{kind}">Konfidenz {format_confidence(value)}</span>'
        return f'<span class="quality-badge quality-badge--{kind}">{kind}</span>'

    def explanation_button(key): return ""
    def explanation_block(key): return ""


# Backward-compatible wrapper for test_recognitions.py (origin/main).
def _confidence(confidence: object) -> str:
    """Return a human-readable confidence string.  Matches origin/main signature."""
    return format_confidence(confidence)


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
        confidence = raw.get("confidence")
        # Empty-text check before degeneration (backward-compat with test
        # "empty_success_becomes_failure" which expects "keinen Text").
        if not error and not text.strip():
            error = "Der Erkennungsversuch lieferte keinen Text."
        # Degeneration check (#29): detect mechanically degenerate output
        # even when no technical error was reported.
        is_degenerate, deg_reason = detect_degeneration(text, confidence)
        if is_degenerate and not error:
            error = f"Degenerierte Erkennung: {deg_reason}"
        result.append({
            "id": candidate_id,
            "engine": engine,
            "model_id": model,
            "page": page,
            "text": text,
            "confidence": confidence,
            "error": error,
            "selected": False,
            "is_degenerate": is_degenerate,
            # Historical multi-page records without page attribution collide at
            # one publisher path. Never link a candidate to an ambiguous file.
            "path": (_recognition_path(raw)
                     if path_counts[_recognition_path(raw)] == 1 else ""),
        })
    return result


def _engine_confidence_dl(candidate: dict) -> str:
    """Build the confidence portion of the metadata <dl>, with scope label and explanation.

    Issue #29: label engine confidence with engine/model/page scope, show
    confidence ranges/units, preserve raw values in accessible details, and
    include an explanation button.
    """
    engine = candidate["engine"]
    model = candidate["model_id"]
    page = candidate["page"]
    confidence = candidate["confidence"]
    scope = confidence_scope_label(engine, model, page)

    explain_btn = explanation_button("engine_confidence")
    explain_block = explanation_block("engine_confidence")
    raw = (
        f'<details class="rec-confidence-raw">'
        f"<summary>Rohtext</summary>"
        f"<p>Engine: {html.escape(engine)}</p>"
        f'<p>Modell: {html.escape(model) or "—"}</p>'
        f'<p>Seite: {html.escape(page) or "Nicht zugeordnet"}</p>'
        f"<p>Konfidenz (raw): {confidence}</p>"
        f"</details>"
    )

    if confidence is None:
        conf_html = "Nicht angegeben"
    else:
        conf_html = (
            f'<span class="rec-confidence-value">{format_confidence(confidence)}</span> '
            f'<span class="rec-confidence-scope">— {html.escape(scope)}</span>'
        )

    return (
        f'<div><dt>Engine-Konfidenz</dt><dd>{conf_html} {explain_btn}'
        f'</dd></div>{explain_block}{raw}'
    )


def _build_ref_eval_html(candidate: dict) -> str:
    """Build reference evaluation (CER/WER) HTML block for a candidate.

    Issue #31: tracks reference-based CER/WER with full provenance.
    Called only when reference_eval data is present in the candidate dict.
    """
    ref_eval = candidate.get("reference_eval") or {}
    if not ref_eval:
        return ""

    cer = ref_eval.get("cer")
    wer = ref_eval.get("wer")
    ref_name = ref_eval.get("reference_name", "Unbekannte Referenz")
    ref_version = ref_eval.get("reference_version", "")
    norm = ref_eval.get("normalisation", "unspezifiziert")
    scope = ref_eval.get("scope", "document")
    explain_btn = explanation_button("reference_evaluation")
    explain_block = explanation_block("reference_evaluation")

    cer_html = ""
    if cer is not None:
        cer_pct = max(0.0, min(1.0, float(cer))) * 100
        cer_html = f'<div><dt>CER</dt><dd>{cer_pct:.1f} % <span class="muted">(niedrig = besser)</span></dd></div>'
    wer_html = ""
    if wer is not None:
        wer_pct = max(0.0, min(1.0, float(wer))) * 100
        wer_html = f'<div><dt>WER</dt><dd>{wer_pct:.1f} % <span class="muted">(niedrig = besser)</span></dd></div>'

    return (
        f'<details class="rec-ref-eval"><summary>Referenzbasierte Auswertung</summary>'
        f"<dl>"
        f"<div><dt>Referenz</dt><dd>{html.escape(ref_name)}"
        f'{f" — Version {html.escape(ref_version)}" if ref_version else ""}</dd></div>'
        f"<div><dt>Normalisierung</dt><dd>{html.escape(norm)}</dd></div>"
        f"<div><dt>Scope</dt><dd>{html.escape(scope)}</dd></div>"
        f"{cer_html}{wer_html}"
        f"</dl>{explain_btn}{explain_block}"
        f"</details>"
    )


def build_recognition_section(recognitions, doc_id: str, transcript: str,
                              directory: Path | None = None,
                              reference_eval: dict | None = None) -> str:
    """Render a no-JS-complete viewer that JavaScript enhances to switching.

    Issues implemented:
    - #29: candidate-level confidence with scope, failure states, degeneration
    - #31: reference-based CER/WER with provenance when reference_eval is provided
    - #30: accessible explanation buttons + blocks for all metric types
    """
    if not recognitions:
        return ""
    directory = Path(directory) if directory is not None else None
    candidates = _candidates(recognitions, transcript)

    # Build explanation blocks for all keys used in this section
    # (ensures they are present in the DOM even if no candidate uses them yet)
    all_explanation_keys = {
        "engine_confidence", "agreement", "degenerate",
        "failed", "reference_evaluation", "incomparable_confidence",
    }
    explanation_blocks = "".join(
        explanation_block(k) for k in all_explanation_keys if k in EXPLANATIONS
    )

    links, panels = [], []
    for candidate in candidates:
        cid = candidate["id"]
        label = _engine_label(candidate["engine"])
        if candidate["model_id"]:
            label += f" · {candidate['model_id']}"

        # Failure state: distinct from zero-confidence success (#29)
        is_failed = bool(candidate["error"])
        is_degenerate = candidate.get("is_degenerate", False)

        if is_failed:
            if is_degenerate:
                status = "Degeneriert"
                status_class = "degenerate"
            else:
                status = "Fehlgeschlagen"
                status_class = "failed"
        else:
            status = "Erfolgreich"
            status_class = "ok"

        # Issue #29: show typed status badge, not just text
        status_badge = quality_badge(
            "failed" if is_failed and not is_degenerate else
            "degenerate" if is_degenerate else
            "engine_confidence",
            candidate.get("confidence"),
            "probability",
            confidence_scope_label(
                candidate["engine"], candidate["model_id"], candidate["page"]
            ),
        )

        links.append(
            f'<li><a href="#recognition-{cid}" data-recognition-select="{cid}" '
            f'aria-controls="recognition-{cid}">{html.escape(label)}</a> '
            f'<span class="rec-status rec-status--{status_class}">{status}</span></li>'
        )
        path = candidate["path"]
        artifact_exists = bool(path) and (directory is None or (directory / path).exists())
        download = (
            f'<a class="rec-download" href="{quote(path, safe="/._-")}" download>'
            "Diese Transkription herunterladen</a>"
            if not is_failed and artifact_exists else
            '<span class="rec-download-unavailable">Kein Textdownload verfügbar</span>'
        )

        if is_failed:
            # Issue #29: failed candidates show error notice, NEVER a zero-confidence success state
            content = (
                f'<div class="notice notice--warning rec-error">'
                f'<strong>Erkennung fehlgeschlagen.</strong> '
                f'{html.escape(candidate["error"])}</div>'
            )
            confidence_dl = ""
        else:
            content = (
                '<pre class="rec-text" tabindex="0"><code>'
                f'{html.escape(candidate["text"])}</code></pre>'
            )
            confidence_dl = _engine_confidence_dl(candidate)

        # Issue #31: add reference evaluation provenance if available
        ref_eval_html = _build_ref_eval_html(candidate) if candidate.get("reference_eval") else ""

        panels.append(f'''<details class="rec-panel" id="recognition-{cid}" data-recognition-panel="{cid}" data-page="{html.escape(candidate["page"], quote=True)}"{' open' if candidate["selected"] else ''}>
<summary>{html.escape(label)}{' — ausgewählt' if candidate["selected"] else ''}</summary>
<dl class="rec-meta">
<div><dt>Engine</dt><dd>{html.escape(candidate["engine"])}</dd></div>
<div><dt>Modell</dt><dd>{html.escape(candidate["model_id"]) or '—'}</dd></div>
<div><dt>Seite</dt><dd>{html.escape(candidate["page"]) or 'Nicht zugeordnet'}</dd></div>
{confidence_dl}
<div><dt>Zeichen</dt><dd>{len(candidate["text"])}</dd></div>
<div><dt>Status</dt><dd>{status_badge}</dd></div>
</dl>
{content}
{ref_eval_html}
<p>{download}</p>
</details>''')

    return f'''<section id="recognitions" aria-labelledby="recognitions-heading">
<h2 id="recognitions-heading">Erkennungsversionen</h2>
<p class="rec-intro">
Alle maschinellen Erkennungsversuche bleiben als überprüfbare Provenienz sichtbar.
<button class="quality-explain-btn" type="button" aria-expanded="false" aria-controls="quality-explanation-incomparable_confidence">ⓘ Nicht vergleichbare Konfidenz</button>
</p>
{explanation_blocks}
<div class="rec-viewer" data-recognition-viewer data-doc-id="{html.escape(doc_id, quote=True)}">
<nav class="rec-selector" aria-label="Erkennungsversionen"><ul>{''.join(links)}</ul></nav>
<div class="rec-panels">{''.join(panels)}</div>
</div></section>'''
