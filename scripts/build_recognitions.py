"""Recognition candidate helpers — used by build_outputs.py (issue #2)."""
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


def _recognition_candidate_html(rec, doc_id) -> str:
    engine = rec.get("engine", "unknown")
    model_id = rec.get("model_id", "—")
    confidence = rec.get("confidence")
    error = rec.get("error", "")
    text = rec.get("text", "")
    char_count = len(text.replace("\r", "").replace("\n", ""))
    has_text = bool(text.strip())
    icon = _engine_icon(engine)
    label = _engine_label(engine)
    cand_id = f"cand-{engine}-{model_id.replace('/', '-')}"

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
            dl_note = f'<a href="{fname}" download class="rec-dl">⬇ Text herunterladen</a>'

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
        cand_id = f"cand-{engine}-{model_id.replace('/', '-')}"
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
        panels.append(_recognition_candidate_html(rec, doc_id))

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
