"""Accessible recognition-candidate rendering for generated output pages.

This module is the Epic 5 reference implementation for issue #29
(candidate-level confidence and failure indicators) and issue #31
(reference-based CER/WER with provenance).

It uses scripts/quality as the canonical source for all quality vocabulary,
provenance contract, degeneration detection, and explanation keys.
It uses scripts/recognition_status as the canonical source for all error
taxonomy, public message derivation, and sanitisation (issue #49).
"""

from __future__ import annotations

import html
import hashlib
import json
import re
import zipfile
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

try:
    from recognition_status import public_error_message, normalize
except ImportError:
    # Fallback when recognition_status is not yet available (e.g., during initial bootstrap)
    def public_error_message(error):
        message = str(error or "").strip()
        lowered = message.casefold()
        if not message:
            return ""
        if "timed out" in lowered or "timeout" in lowered:
            return "Der Erkennungsdienst hat das Zeitlimit uberschritten."
        if "unavailable" in lowered or "connection" in lowered:
            return "Der Erkennungsdienst war nicht erreichbar."
        if "unsupported" in lowered or "not found" in lowered:
            return "Das angeforderte Erkennungsmodell war nicht verfügbar."
        return "Der Erkennungsversuch ist fehlgeschlagen."


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
    """Return a useful public message without endpoints, paths, or credentials.

    Delegates to ``recognition_status.public_error_message`` which applies the
    canonical status taxonomy (issue #49) and sanitisation patterns.
    """
    return public_error_message(error)


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
    return _recognition_path(candidate).removesuffix(".txt") + ".error.txt"


def write_error_record(directory: Path, candidate: dict) -> Path | None:
    error = _public_error(candidate.get("error"))
    if not error:
        return None
    path = directory / _error_path(candidate)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "engine": str(candidate.get("engine") or ""),
        "model_id": str(candidate.get("model_id") or ""),
        "page": str(candidate.get("page") or ""),
        "error": error,
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def compute_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _catalogue_data(doc_id: str, candidates: list[dict]) -> dict:
    # Issue #52: compute aggregate counts for catalogue-level filtering
    total = len(candidates)
    failed = sum(1 for c in candidates if c["error"])
    degenerate = sum(1 for c in candidates if c.get("is_degenerate"))
    successful = sum(1 for c in candidates if not c["error"] and not c.get("is_degenerate"))
    empty = sum(1 for c in candidates
                 if not c["error"] and not c.get("is_degenerate") and not c["text"])
    if failed + degenerate == total:
        run_quality = "total_failure"
    elif failed + degenerate > 0:
        run_quality = "partial_failure"
    elif empty > 0:
        run_quality = "empty"
    else:
        run_quality = "clean"
    return {
        "doc_id": doc_id,
        "version": "1.0",
        "run_quality": run_quality,
        "run_counts": {
            "total": total,
            "successful": successful,
            "failed": failed,
            "degenerate": degenerate,
            "empty": empty,
        },
        "artifacts": [{
            "id": candidate["id"],
            "engine": candidate["engine"],
            "model_id": candidate["model_id"] or None,
            "page": candidate["page"] or None,
            "status": "error" if candidate["error"] else "success",
            **({"status_code": normalize(candidate).code} if not candidate["error"] else {}),
            "error": _public_error(candidate.get("error")) or None,
            "path": candidate["path"] if candidate["path"] and not candidate["error"] else None,
            "error_path": _error_path(candidate) if candidate["error"] else None,
            "characters": len(candidate["text"]) if not candidate["error"] else None,
        } for candidate in candidates],
    }


def write_catalogue(directory: Path, doc_id: str, recognitions: list,
                    transcript: str) -> Path:
    path = directory / "recognitions" / "catalogue.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_catalogue_data(
        doc_id, _candidates(recognitions, transcript)), ensure_ascii=False,
        indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_package(directory: Path, doc_id: str, recognitions: list,
                  transcript: str) -> Path | None:
    """Write a byte-reproducible ZIP with candidate texts and safe errors."""
    candidates = _candidates(recognitions, transcript)
    artifacts = []
    entries: list[tuple[str, bytes]] = []
    for candidate in candidates:
        if candidate["selected"]:
            name = "fused.txt"
            payload = candidate["text"].encode("utf-8")
            kind = "selected"
        elif candidate["error"]:
            stem = "/".join((
                _safe_slug(candidate["page"], "unassigned"),
                _safe_slug(candidate["id"]),
            ))
            name = f"candidates/{stem}.error.txt"
            payload = json.dumps({
                "engine": candidate["engine"], "model_id": candidate["model_id"],
                "page": candidate["page"], "error": candidate["error"],
            }, ensure_ascii=False, sort_keys=True).encode("utf-8")
            kind = "error"
        else:
            stem = "/".join((
                _safe_slug(candidate["page"], "unassigned"),
                _safe_slug(candidate["id"]),
            ))
            name = f"candidates/{stem}.txt"
            payload = candidate["text"].encode("utf-8")
            kind = "candidate"
        entries.append((name, payload))
        artifacts.append({
            "file": name, "type": kind, "engine": candidate["engine"],
            "model_id": candidate["model_id"] or None,
            "page": candidate["page"] or None,
            "checksum": hashlib.sha256(payload).hexdigest(),
        })
    catalogue = json.dumps(_catalogue_data(doc_id, candidates), ensure_ascii=False,
                           indent=2, sort_keys=True).encode("utf-8")
    entries.append(("catalogue.json", catalogue))
    manifest = json.dumps({
        "doc_id": doc_id, "version": "1.0",
        "package_type": "complete_recognition", "artifacts": artifacts,
    }, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    entries.append(("manifest.json", manifest))
    package = directory / f"{_safe_slug(doc_id, 'document')}-recognition-package.zip"
    try:
        with zipfile.ZipFile(package, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, payload in sorted(entries):
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                archive.writestr(info, payload)
        write_catalogue(directory, doc_id, recognitions, transcript)
    except OSError:
        return None
    return package


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
    # Keep output deterministic: generated pages are committed and CI verifies that
    # rebuilding them leaves the tree clean.
    all_explanation_keys = (
        "engine_confidence", "agreement", "degenerate",
        "failed", "reference_evaluation", "incomparable_confidence",
    )
    explanation_blocks = "".join(
        explanation_block(k) for k in all_explanation_keys if k in EXPLANATIONS
    )

    # Issue #52: compute aggregate counts for document-level failure summary
    total = len(candidates)
    failed = sum(1 for c in candidates if c["error"])
    degenerate = sum(1 for c in candidates if c.get("is_degenerate"))
    successful = sum(1 for c in candidates if not c["error"] and not c.get("is_degenerate"))
    empty = sum(1 for c in candidates if not c["error"] and not c.get("is_degenerate") and not c["text"])

    # Derive run-quality label for document-level warning
    if failed + degenerate == total:
        run_quality = "total_failure"
        run_label = "Alle Erkennungen fehlgeschlagen"
    elif failed + degenerate > 0:
        run_quality = "partial_failure"
        run_label = f"{failed + degenerate} von {total} fehlgeschlagen"
    elif empty > 0:
        run_quality = "empty"
        run_label = f"{empty} von {total} ohne Ausgabe"
    else:
        run_quality = "clean"
        run_label = None

    summary_html = ""
    if run_label:
        css_class = {
            "total_failure": "notice--error",
            "partial_failure": "notice--warning",
            "empty": "notice--info",
        }.get(run_quality, "notice--info")
        chips_html = (
            '<span class="rec-chip rec-chip--ok">' + str(successful) + ' erfolgreich</span>'
            '<span class="rec-chip rec-chip--failed">' + str(failed) + ' fehlgeschlagen</span>'
            '<span class="rec-chip rec-chip--degenerate">' + str(degenerate) + ' degeneriert</span>'
        )
        summary_html = (
            '<div class="notice ' + css_class + ' rec-run-summary">'
            '<strong>Erkennungslauf:</strong> ' + run_label +
            ' <span class="rec-run-chips">' + chips_html + '</span></div>'
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
            f'data-page="{html.escape(candidate["page"], quote=True)}" '
            f'data-engine="{html.escape(candidate["engine"], quote=True)}" '
            f'data-model="{html.escape(candidate["model_id"], quote=True)}" '
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
            # Issue #29/#51: failed candidates show explanatory panel with sanitized public_msg
            status = normalize(candidate)
            timing_info = f' <span class="rec-timing">({status.timing_ms} ms)</span>' if status.timing_ms else ""
            methodology_note = (
                ' <a href="/docs/methodology/#recognition-failures" class="rec-methodology-link" rel="noopener">Erklaerung der Fehlerkategorien</a>'
                if status.code not in ("success", "empty") else ""
            )
            retry_info = (
                f' <span class="rec-retry-hint">— Wiederholung {["moeglich","nicht sinnvoll"][int(status.retryable is False)]}</span>'
                if status.code not in ("success", "empty") else ""
            )
            content = (
                f'<div class="notice notice--warning rec-error">'
                f'<strong>Erkennung fehlgeschlagen.{timing_info}</strong><br>'
                f'{html.escape(status.public_msg)}'
                f'{methodology_note}'
                f'{retry_info}'
                f'</div>'
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

        panels.append(f'''<details class="rec-panel" id="recognition-{cid}" data-recognition-panel="{cid}" data-page="{html.escape(candidate["page"], quote=True)}" data-engine="{html.escape(candidate["engine"], quote=True)}" data-model="{html.escape(candidate["model_id"], quote=True)}"{' open' if candidate["selected"] else ''}>
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

    def compare_options() -> str:
        options = []
        for candidate in candidates:
            label = _engine_label(candidate["engine"])
            if candidate["model_id"]:
                label += f' · {candidate["model_id"]}'
            if candidate["page"]:
                label += f' ({candidate["page"]})'
            disabled = " disabled" if candidate["error"] else ""
            options.append(
                f'<option value="{html.escape(candidate["id"], quote=True)}" '
                f'data-page="{html.escape(candidate["page"], quote=True)}"{disabled}>'
                f'{html.escape(label)}</option>'
            )
        return "".join(options)

    usable = [candidate for candidate in candidates if not candidate["error"]]
    left = usable[0]["id"] if usable else "selected"
    right = usable[1]["id"] if len(usable) > 1 else left
    options = compare_options()
    compare_section = f'''<div class="rec-compare" data-recognition-compare>
<div class="rec-compare-toolbar"><button class="btn-rec-compare" type="button" data-rec-compare-open aria-expanded="false">&#128269; Vergleichen</button></div>
<div class="rec-compare-panes" data-rec-compare-panes hidden>
<div class="rec-compare-heading" data-rec-compare-heading><span>Modellvergleich</span></div>
<div class="rec-compare-share" data-rec-compare-share>
<input class="rec-compare-share-input" type="text" data-rec-compare-share-input readonly placeholder="Vergleichs-URL" aria-label="Vergleichs-URL zum Teilen">
<button class="btn-rec-compare btn-rec-compare-share-copy" type="button" data-rec-compare-share-copy>Kopieren</button>
</div>
<div class="rec-compare-pane" data-rec-compare-pane="left" data-rec-compare-selected="{html.escape(left, quote=True)}">
<div class="rec-compare-header"><label class="rec-compare-label" for="rec-compare-select-left">Version links</label></div>
<select class="rec-compare-select" id="rec-compare-select-left" data-rec-compare-select="left">{options}</select>
<div class="rec-compare-body" data-rec-compare-body="left" tabindex="-1"></div></div>
<div class="rec-compare-pane" data-rec-compare-pane="right" data-rec-compare-selected="{html.escape(right, quote=True)}">
<div class="rec-compare-header"><label class="rec-compare-label" for="rec-compare-select-right">Version rechts</label></div>
<select class="rec-compare-select" id="rec-compare-select-right" data-rec-compare-select="right">{options}</select>
<div class="rec-compare-body" data-rec-compare-body="right" tabindex="-1"></div>
<div class="rec-compare-diff" data-rec-compare-diff hidden role="region" aria-label="Unterschiede"></div></div>
<button class="btn-rec-compare-close" type="button" data-rec-compare-close aria-label="Vergleich schliessen">&#215;</button>
</div></div>'''

    selected = candidates[0]
    selected_exists = bool(selected["path"]) and (directory is None or (directory / selected["path"]).exists())
    primary = (f'<div class="rec-primary-download"><a class="btn-rec-download" '
               f'href="{quote(selected["path"], safe="/._-")}" download '
               f'data-rec-primary-download>Aktuelle Transkription herunterladen '
               f'<span class="rec-download-format">TXT</span></a>'
               f'<span class="rec-download-provenance">{html.escape(selected["engine"])} · Seite {html.escape(selected["page"] or "nicht zugeordnet")}</span></div>'
               if selected_exists else
               '<div class="rec-primary-download rec-primary-download--unavailable"><span class="rec-download-unavailable">Kein Textdownload verfügbar</span></div>')
    inventory_rows = []
    current_page = object()
    for candidate in candidates:
        page = candidate["page"] or "Nicht zugeordnet"
        if page != current_page:
            inventory_rows.append(
                f'<tr class="rec-inv-page-header"><th colspan="6">{html.escape(page)}</th></tr>')
            current_page = page
        status = "Fehlgeschlagen" if candidate["error"] else "Erfolgreich"
        download = ("—" if candidate["error"] or not candidate["path"] else
                    f'<a href="{quote(candidate["path"], safe="/._-")}" download>{html.escape(Path(candidate["path"]).name)}</a>')
        row_class = ' class="rec-inv-error"' if candidate["error"] else ""
        dl_class = ' class="rec-inv-dl"' if download != "—" else ""
        inventory_rows.append(
            f'<tr{row_class}><td>{html.escape(candidate["engine"])}</td>'
            f'<td>{html.escape(candidate["model_id"]) or "—"}</td>'
            f'<td>{len(candidate["text"]) if not candidate["error"] else "—"}</td>'
            f'<td>{status}</td><td>{html.escape(candidate["error"] or _confidence(candidate["confidence"]))}</td>'
            f'<td{dl_class}>{download}</td></tr>')
    inventory = f'''<details class="rec-inventory"><summary>Alle Erkennungsversionen herunterladen <span class="rec-inv-count">({len(candidates)} Versionen)</span></summary>
<div class="table-scroll"><table class="rec-inv-table"><thead><tr><th>Engine</th><th>Modell</th><th>Zeichen</th><th>Status</th><th>Konfidenz/Fehler</th><th>Download</th></tr></thead><tbody>{''.join(inventory_rows)}</tbody></table></div></details>'''

    return f'''<section id="recognitions" class="page-section page-section--evidence" data-page-section="recognitions" aria-labelledby="recognitions-heading">
<h2 id="recognitions-heading">Erkennungsversionen</h2>
<p class="rec-intro">
Alle maschinellen Erkennungsversuche bleiben als überprüfbare Provenienz sichtbar.
<button class="quality-explain-btn" type="button" aria-expanded="false" aria-controls="quality-explanation-incomparable_confidence">ⓘ Nicht vergleichbare Konfidenz</button>
</p>
{explanation_blocks}
<div class="rec-viewer" data-recognition-viewer data-doc-id="{html.escape(doc_id, quote=True)}">
{primary}
{inventory}
{summary_html}
{compare_section}
<nav class="rec-selector" aria-label="Erkennungsversionen"><ul>{''.join(links)}</ul></nav>
<div class="rec-panels">{''.join(panels)}</div>
</div></section>'''
