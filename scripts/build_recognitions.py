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
            from rec_artifacts import candidate_export_filename, TEXT_MIME, TEI_MIME, MANIFEST_MIME
            page_meta = rec.get("page")
            fname_xml  = f"recognitions/{candidate_export_filename(doc_id, engine, model_id, '.xml', page=page_meta)}"
            fname_json = f"recognitions/{candidate_export_filename(doc_id, engine, model_id, '.json', page=page_meta)}"
            fname_txt  = f"recognitions/{candidate_export_filename(doc_id, engine, model_id, '.txt', page=page_meta)}"
            page_label = f", Seite {page_meta}" if page_meta else ""
            seg = f"cand-{i}-{engine}-{model_id.replace('/', '-')}"
            dl_note = (
                f'<span class="exports-list">'
                f'<a href="{fname_xml}" download data-cand="{seg}" '
                f'class="dl-link dl-link--xml" type="{TEI_MIME}" '
                f'aria-label="TEI/XML herunterladen ({engine}{page_label})">'
                f'<span class="exports-badge exports-badge--xml">TEI</span></a>'
                f'<a href="{fname_json}" download data-cand="{seg}" '
                f'class="dl-link dl-link--json" type="{MANIFEST_MIME}" '
                f'aria-label="JSON herunterladen ({engine}{page_label})">'
                f'<span class="exports-badge exports-badge--json">JSON</span></a>'
                f'<a href="{fname_txt}" download data-cand="{seg}" '
                f'class="dl-link dl-link--txt" type="{TEXT_MIME}" '
                f'aria-label="Text herunterladen ({engine}{page_label})">'
                f'<span class="exports-badge">TXT</span></a>'
                f'</span>'
            )

    status = (
        f"{icon} <strong>{label}</strong> {badge} "
        f'<span class="rec-model">{html.escape(model_id)}</span> '
        f"· {char_count:,} Zeichen"
    )
    if dl_note and not error:
        status += f" {dl_note}"

    return (
        f'<div class="{cls}" id="{cand_id}">'
        f'<div class="{summary_cls}">{status}</div>'
        f"{text_html}"
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

    # Structured exports section (issue #38)
    exports_html = render_candidate_exports_section(recognitions, doc_id)

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
        "</div></div>"
        + exports_html +
        "</section>"
    )


# ── Recognition inventory section (issue #36) ────────────────────────────────

def _recognition_inventory_section(recognitions, doc_id, artifact_metas):
    """Render a complete inventory of all recognition artifacts for a document.

    Shows every candidate .txt file with type, page, character count, and
    download link — plus the fused/selected transcription if available.

    artifact_metas: list of ArtifactMeta from rec_artifacts.collect_artifacts()
    """
    if not recognitions:
        return ""

    # Build metadata lookup: cand_index → ArtifactMeta
    meta_by_index = {m.cand_index: m for m in artifact_metas}

    rows = []
    for i, rec in enumerate(recognitions):
        engine   = rec.get("engine", "unknown")
        model_id = rec.get("model_id", "unknown")
        page_meta = rec.get("page")
        error    = rec.get("error", "")
        text     = rec.get("text", "") or ""
        char_count = len(text.replace("\r", "").replace("\n", ""))
        is_error = bool(error)
        confidence = rec.get("confidence")

        meta = meta_by_index.get(i)
        path = meta.path if meta else f"recognitions/{engine}-{model_id.replace('/', '-')}.txt"
        has_text_flag = bool(text.strip()) and not is_error

        # Type badge
        if is_error:
            type_badge = '<span class="badge badge--error">Fehler</span>'
        elif page_meta is not None:
            type_badge = f'<span class="badge badge--raw">roh · S. {page_meta}</span>'
        else:
            type_badge = '<span class="badge badge--raw">roh</span>'

        # Size
        if is_error:
            size_str = "—"
        else:
            size_str = f"{char_count:,} Z."

        # Confidence
        conf_str = f"{confidence:.0%}" if confidence is not None else "—"

        # Page label
        page_str = f"Seite {page_meta}" if page_meta is not None else "—"

        # Download link
        if has_text_flag:
            dl_link = (
                f'<a href="{path}" download class="inv-dl" '
                f'type="{meta.mime if meta else "text/plain"}" '
                f'aria-label="Herunterladen {engine} {model_id}">⬇</a>'
            )
        else:
            dl_link = ""

        rows.append(
            f'<tr>'
            f'<td>{html.escape(engine)}</td>'
            f'<td class="inv-model"><code>{html.escape(model_id)}</code></td>'
            f'<td>{page_str}</td>'
            f'<td>{type_badge}</td>'
            f'<td class="inv-right">{size_str}</td>'
            f'<td class="inv-right">{conf_str}</td>'
            f'<td class="inv-center">{dl_link}</td>'
            f'</tr>'
        )

    rows_html = "\n".join(rows)

    return (
        f'<section class="inv-section" id="rec-inventory" aria-labelledby="inv-heading">'
        f'<h2 id="inv-heading">Erkennungsdateien</h2>'
        f'<p class="inv-intro">Alle Erkennungsversionen und Download-Links.</p>'
        f'<div class="table-wrapper">'
        f'<table class="inv-table">'
        f'<thead><tr>'
        f'<th>Engine</th><th>Modell</th><th>Seite</th><th>Typ</th>'
        f'<th class="inv-right">Umfang</th><th class="inv-right">Konfidenz</th>'
        f'<th class="inv-center">DL</th>'
        f'</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div></section>'
    )


# ── Complete download package (issue #37) ────────────────────────────────────

def _complete_package_section(doc_id, num_candidates, num_error, num_success):
    """Render the complete-download package section.

    Offers a ZIP bundle containing:
    - All recognition .txt files
    - manifest.json with document and pipeline metadata
    - selected/fused transcription (fused.txt)
    """
    if num_success == 0:
        return ""

    pkg_name = f"{doc_id}-complete.zip"
    size_note = ""
    if num_error > 0:
        size_note = (
            f' <span class="inv-note">({num_error} Versuch=num fehlgeschlagen)</span>'
        )

    return (
        f'<section class="pkg-section" id="complete-package" aria-labelledby="pkg-heading">'
        f'<h2 id="pkg-heading">Vollst\u00e4ndiges Erkennungspaket herunterladen</h2>'
        f'<div class="pkg-body">'
        f'<p>Alle Erkennungsversionen, das ausgew\u00e4hlte Transkript '
        f'und die Manifest-Datei in einer ZIP-Datei.</p>'
        f'<ul>'
        f'<li>Alle {num_success} erfolgreichen Erkennungen als Textdateien</li>'
        f'<li>Ausgew\u00e4hltes Transkript (<code>fused.txt</code>)</li>'
        f'<li>Manifest-Datei (<code>manifest.json</code>) mit Pipeline-Metadaten</li>'
        f'{size_note}'
        f'</ul>'
        f'<a href="{pkg_name}" download class="pkg-btn" '
        f'type="application/zip" '
        f'aria-label="Vollst\u00e4ndiges Erkennungspaket herunterladen">'
        f'21a7 Vollst\u00e4ndiges Paket herunterladen (.zip)</a>'
        f'</div></section>'
    )


# ── Candidate structured exports (issue #38) ─────────────────────────────────

def _candidate_export_links_html(rec, cand_index, doc_id):
    """Return a <ul> of TEI/XML, JSON, and TXT export links for one candidate.

    Each link has proper type=, download=, aria-label, and a span badge.
    Returns empty string if candidate has no text or is an error record.
    """
    error = rec.get("error", "")
    text = rec.get("text", "") or ""
    if error or not text.strip():
        return ""

    engine = rec.get("engine", "unknown")
    model_id = rec.get("model_id", "unknown")
    page_meta = rec.get("page")
    page_label = f", Seite {page_meta}" if page_meta else ""

    # Build per-format path using candidate_export_filename from rec_artifacts
    from rec_artifacts import candidate_export_filename, TEXT_MIME, TEI_MIME, MANIFEST_MIME

    fname_xml  = candidate_export_filename(doc_id, engine, model_id, ".xml", page=page_meta)
    fname_json = candidate_export_filename(doc_id, engine, model_id, ".json", page=page_meta)
    fname_txt  = candidate_export_filename(doc_id, engine, model_id, ".txt", page=page_meta)
    fname_xml  = f"recognitions/{fname_xml}"
    fname_json = f"recognitions/{fname_json}"
    fname_txt  = f"recognitions/{fname_txt}"

    seg = f"cand-{cand_index}-{engine}-{model_id.replace('/', '-')}"

    badge_xml  = '<span class="exports-badge exports-badge--xml">TEI/XML</span>'
    badge_json = '<span class="exports-badge exports-badge--json">JSON</span>'
    badge_txt  = '<span class="exports-badge">TXT</span>'

    aria_xml  = f"TEI/XML-Export herunterladen ({engine}{page_label})"
    aria_json = f"JSON-Export herunterladen ({engine}{page_label})"
    aria_txt  = f"Text-Export herunterladen ({engine}{page_label})"

    items = [
        f'<li>'
        f'<a href="{fname_xml}" download data-cand="{seg}" '
        f'class="dl-link dl-link--xml" type="{TEI_MIME}" aria-label="{aria_xml}">{badge_xml}</a>'
        f'</li>',
        f'<li>'
        f'<a href="{fname_json}" download data-cand="{seg}" '
        f'class="dl-link dl-link--json" type="{MANIFEST_MIME}" aria-label="{aria_json}">{badge_json}</a>'
        f'</li>',
        f'<li>'
        f'<a href="{fname_txt}" download data-cand="{seg}" '
        f'class="dl-link dl-link--txt" type="{TEXT_MIME}" aria-label="{aria_txt}">{badge_txt}</a>'
        f'</li>',
    ]

    return (
        f'<ul class="exports-list">'
        + "".join(items)
        + '</ul>'
    )


def render_candidate_exports_section(recognitions, doc_id):
    """Render a structured-exports section listing all formats for every candidate.

    Produces a grid of candidate headings each followed by their available
    export links (TEI/XML, JSON, TXT). Error and empty candidates are skipped.

    Returns an HTML string ready to drop into a page, or "" if there are no
    downloadable candidates.
    """
    if not recognitions:
        return ""

    # Collect candidates that have downloadable content
    candidates = []
    for i, rec in enumerate(recognitions):
        error = rec.get("error", "")
        text = rec.get("text", "") or ""
        if error or not text.strip():
            continue
        engine = rec.get("engine", "unk")
        model_id = rec.get("model_id", "")
        cand_id = f"cand-{i}-{engine}-{model_id.replace('/', '-')}"
        icon = _engine_icon(engine)
        label = _engine_label(engine)
        page_meta = rec.get("page")
        if page_meta is not None:
            label += f", Seite {page_meta}"
        confidence = rec.get("confidence")
        if confidence is not None:
            label += f" · {confidence:.0%} Konfidenz"
        candidates.append({
            "index": i,
            "cand_id": cand_id,
            "label": label,
            "icon": icon,
            "engine": engine,
            "model_id": model_id,
            "rec": rec,
        })

    if not candidates:
        return ""

    rows = []
    for c in candidates:
        links = _candidate_export_links_html(c["rec"], c["index"], doc_id)
        if not links:
            continue
        rows.append(
            f'<div class="exports-cand-block">'
            f'<span class="exports-cand-heading">'
            f'{c["icon"]} {html.escape(c["label"])}'
            f'</span>'
            f'{links}'
            f'</div>'
        )

    if not rows:
        return ""

    return (
        f'<section class="exports-section" aria-labelledby="exports-heading">'
        f'<h3 id="exports-heading">Strukturierte Exporte</h3>'
        f'<p>TEI/XML für wissenschaftlichen Austausch; JSON für Nachnutzung und Integration.</p>'
        f'<div class="exports-grid">'
        + "".join(rows)
        + '</div>'
        f'</section>'
    )
