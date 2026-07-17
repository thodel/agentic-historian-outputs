"""Recognition candidate helpers — used by build_outputs.py (issues #2, #3, #35)."""
from __future__ import annotations
import html


def _engine_label(engine: str) -> str:
    return {
        "vlm": "VLM (InternVL3-8B)",
        "kraken": "Kraken OCR",
        "trocr": "TrOCR",
        "fusion": "Fusion",
        "fused": "Fused output",
    }.get(engine.lower(), engine)


def _engine_icon(engine: str) -> str:
    return {
        "vlm": "🔮",   # crystal ball
        "kraken": "📖",  # book
        "trocr": "🔤",   # abc
        "fusion": "🔗",  # link
        "fused": "✅",
    }.get(engine.lower(), "🤖")  # robot


def _is_selected(rec, transcript) -> bool:
    return rec.get("text", "").strip() == transcript.strip()


def _conf_html(conf) -> str:
    if isinstance(conf, (int, float)):
        return f'<span class="rec-badge">✅ {conf:.0%}</span>'
    return ""


def _recognition_candidate_html(rec, doc_id, i=0) -> str:
    engine = rec.get("engine", "unknown")
    model_id = rec.get("model_id", "—")
    confidence = rec.get("confidence")
    error = rec.get("error", "")
    text = rec.get("text", "")
    char_count = len(text.replace("\r", "").replace("\n", ""))
    has_text = bool(text.strip())
    icon = _engine_icon(engine)
    label = _engine_label(engine)
    cand_id = f"cand-{i}-{engine}-{model_id.replace('/', '-')}"

    if error:
        badge = '<span class="rec-badge rec-badge--error">❌ Fehler</span>'
        cls = "rec-panel rec-panel--error"
        summary_cls = "rec-summary rec-summary--error"
        text_html = f'<pre class="rec-text rec-text--error">{html.escape(error)}</pre>'
        dl_note = '<p class="rec-error-note">❗ Kein Output — dieser Versuch ist fehlgeschlagen.</p>'
    else:
        badge = _conf_html(confidence)
        cls = "rec-panel"
        summary_cls = "rec-summary"
        text_html = f'<pre class="rec-text">{html.escape(text)}</pre>'
        dl_note = ""
        if has_text:
            fname = f"recognitions/{engine}-{model_id.replace('/', '-')}.txt"
            dl_note = f'<a href="{fname}" download class="rec-dl" data-cand="cand-{i}-{engine}-{model_id.replace("/", "-")}">⬇ Text herunterladen</a>'

    status = (
        f"{icon} <strong>{label}</strong> {badge} "
        f'<span class="rec-model">{html.escape(model_id)}</span> '
        f"· {char_count:,} Zeichen"
    )
    if dl_note and not error:
        status += f" · {dl_note}"

    return (
        f'<div class="{cls}" id="{cand_id}">'
        f'<div class="{summary_cls}">{status}</div>'
        f"{text_html}"
        + dl_note +
        "</div>"
    )



def _download_formats(rec, doc_id, cand_index, artifact_meta):
    """Return HTML for available download formats for a candidate.

    rec: recognition dict
    doc_id: document ID
    cand_index: 0-based candidate index
    artifact_meta: ArtifactMeta from rec_artifacts (optional)
    """
    error = rec.get("error", "")
    text = rec.get("text", "") or ""
    engine = rec.get("engine", "unknown")
    model_id = rec.get("model_id", "unknown")
    confidence = rec.get("confidence")

    if error or not text.strip():
        return ""

    # Determine available formats
    from rec_artifacts import candidate_export_filename, TEXT_MIME

    seg = f"cand-{cand_index}-{engine}-{model_id.replace('/', '-')}"

    # Primary TXT download (always available)
    fname = f"recognitions/{engine}-{model_id.replace('/', '-')}.txt"
    # Use the artifact_meta path if available for accuracy
    if artifact_meta:
        fname = artifact_meta.path

    # Page label
    page_meta = rec.get("page")
    page_label = f", Seite {page_meta}" if page_meta else ""

    formats = [
        ("TXT", fname, TEXT_MIME, ""),
    ]

    lines = []
    for fmt, path, mime, extra in formats:
        safe_name = path.split("/")[-1]
        label = f"{fmt} herunterladen"
        lines.append(
            f'<a href="{path}" download data-cand="{seg}" '
            f'class="dl-link dl-link--{fmt.lower()}" '
            f'type="{mime}" aria-label="{label} ({engine}{page_label})">{fmt}</a>'
        )

    return " · ".join(lines)


def _active_download_section(recognitions, doc_id, transcript):
    """Primary download action for the currently selected candidate.

    No-JS fallback: uses the pre-selected candidate (matches transcript or first non-error).
    With JS: updates when active candidate changes.

    Returns HTML string or empty string if no downloadable candidate exists.
    """
    if not recognitions:
        return ""

    # Determine default selected candidate (same logic as build_recognition_section)
    default_idx = 0
    exact_match = False
    for i, r in enumerate(recognitions):
        if _is_selected(r, transcript):
            default_idx = i
            exact_match = True
            break
    else:
        for i, r in enumerate(recognitions):
            if not r.get("error") and r.get("text"):
                default_idx = i
                break

    rec = recognitions[default_idx]
    engine = rec.get("engine", "unknown")
    model_id = rec.get("model_id", "—")
    error = rec.get("error", "")
    text = rec.get("text", "") or ""
    confidence = rec.get("confidence")
    page_meta = rec.get("page")
    char_count = len(text.replace("\r", "").replace("\n", ""))

    if error or not text.strip():
        return (
            f'<div class="dl-section" id="downloads">'
            f'<h2 id="dl-heading">Transkription herunterladen</h2>'
            f'<div class="notice notice--warning">'
            f'❗ Die automatische Erkennung ist für dieses Dokument nicht '
            f'verfügbar oder fehlgeschlagen. Es steht kein Transkriptionstext '
            f'zum Download bereit.</div>'
            f'</div>'
        )

    label_parts = [_engine_label(engine)]
    if page_meta is not None:
        label_parts.append(f"Seite {page_meta}")
    if confidence is not None:
        label_parts.append(f"{confidence:.0%} Konfidenz")
    meta_str = " · ".join(label_parts)

    # Primary download link (TXT)
    fname = f"recognitions/{engine}-{model_id.replace('/', '-')}.txt"
    page_label = f", Seite {page_meta}" if page_meta else ""
    alt_text = f"Transkription {doc_id} — {engine} ({model_id}){page_label}"

    # Build candidate selector for switching
    options = []
    for i, r in enumerate(recognitions):
        r_engine = r.get("engine", "unk")
        r_model = r.get("model_id", "")
        r_error = r.get("error", "")
        r_text = r.get("text", "") or ""
        r_page = r.get("page")
        r_conf = r.get("confidence")
        r_cand_id = f"cand-{i}-{r_engine}-{r_model.replace('/', '-')}"
        disabled = 'disabled ' if (r_error or not r_text.strip()) else ''
        label = _engine_label(r_engine)
        if r_page is not None:
            label += f", Seite {r_page}"
        if r_error:
            label += " ❌"
        elif r_conf is not None:
            label += f" · {r_conf:.0%}"
        options.append(
            f'<option value="{r_cand_id}" {disabled}>{label}</option>'
        )

    return (
        f'<div class="dl-section" id="downloads">'
        f'<h2 id="dl-heading">Transkription herunterladen</h2>'
        f'<p class="dl-meta">{meta_str}</p>'
        f'<div class="dl-primary">'
        f'<a href="{fname}" download class="dl-btn dl-btn--primary" '
        f'data-default-href="{fname}" '
        f'data-cand="cand-{default_idx}-{engine}-{model_id.replace("/", "-")}" '
        f'aria-label="Aktuelle Transkription herunterladen ({engine}{page_label})">'
        f'⬇ Aktuelle Transkription herunterladen (.txt)</a>'
        f'</div>'
        # Candidate switcher (updates download target via JS)
        + (f'<div class="dl-switcher">'
           f'<label for="dl-cand-select">Andere Version wählen:</label> '
           f'<select id="dl-cand-select" class="dl-cand-select" '
           f'data-doc-id="{html.escape(doc_id)}">'
           + "\n".join(options) +
           f'</select></div>'
           if len(recognitions) > 1 else '') +
        f'</div>'
    )


def build_recognition_section(recognitions, doc_id, transcript) -> str:
    """Render the full recognition-viewer section (progressive enhancement).

    No JS: all panels visible, radio defaults to selected/fused candidate.
    With JS (added separately): only active panel shown.
    """
    if not recognitions:
        return ""

    # Pick default: first candidate matching the fused transcript, else
    # first non-error candidate
    default_idx = 0
    exact_match = False
    for i, r in enumerate(recognitions):
        if _is_selected(r, transcript):
            default_idx = i
            exact_match = True
            break
    else:
        for i, r in enumerate(recognitions):
            if not r.get("error") and r.get("text"):
                default_idx = i
                break

    tabs, panels = [], []
    for i, rec in enumerate(recognitions):
        engine = rec.get("engine", "unk")
        model_id = rec.get("model_id", "")
        cand_id = f"cand-{i}-{engine}-{model_id.replace('/', '-')}"
        icon = _engine_icon(engine)
        label = f"{icon} {_engine_label(engine)}"
        if rec.get("error"):
            label += " ❌"
        chk = " checked" if i == default_idx else ""
        marker = " ✔" if (i == default_idx and exact_match) else (" ⮕" if i == default_idx else "")
        tabs.append(
            f'<input type="radio" name="rec-{doc_id}" id="tab-{cand_id}" '
            f'value="{cand_id}"{chk} class="rec-tab-input">'
            f'<label for="tab-{cand_id}" class="rec-tab-label">{label}{marker}</label>'
        )
        panels.append(_recognition_candidate_html(rec, doc_id, i))

    return (
        "<section id=\"recognitions\" aria-labelledby=\"rec-heading\">"
        "<h2 id=\"rec-heading\">Erkennungsversionen</h2>"
        "<p class=\"rec-intro\">Es liegen mehrere Erkennungsversionen vor. "
        "W\u00e4hlen Sie eine Version zum Vergleichen; "
        "die ausgew\u00e4hlte Transkription bleibt ohne JavaScript sichtbar.</p>"
        f'<div class="rec-viewer" data-doc-id="{html.escape(doc_id)}">'
        "<div class=\"rec-tabs\" role=\"tablist\" aria-label=\"Erkennungsversionen\">"
        + "\n".join(tabs) +
        "</div>"
        "<div class=\"rec-panels\">"
        + "\n".join(panels) +
        "</div></div></section>"
    )
