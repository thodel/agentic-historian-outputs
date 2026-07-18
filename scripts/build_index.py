#!/usr/bin/env python3
"""Build the accessible, date-ordered catalogue in ``docs/index.md``.

The publisher has emitted more than one pipeline JSON schema.  This builder
normalises those variants and derives a stable creation date from explicit
metadata or, as a fallback, the commit that first introduced pipeline.json.
It uses only the Python standard library.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from source_references import normalize_source_reference

# ---------------------------------------------------------------------------
# Browser-script single source of truth (issue #117)
# ---------------------------------------------------------------------------
# scripts/*.js  — canonical hand-edited copies (snake_case naming)
# docs/assets/  — deployed copies produced by the build (kebab-case naming)
#
# The mapping below drives the copy step.  Editing docs/assets/ directly will
# be overwritten on the next build, and CI's git-diff check will catch drift.
_BROWSER_SCRIPTS: list[tuple[str, str]] = [
    ("evidence_viewer.js",   "evidence-viewer.js"),
    ("page_disclosure.js",   "page-disclosure.js"),
    ("page_sync.js",         "page-sync.js"),
    ("quality-explain.js",   "quality-explain.js"),
    ("rec_viewer.js",        "rec-viewer.js"),
    ("workspace.js",         "workspace.js"),
]
SCRIPTS_DIR = Path("scripts")
ASSETS_DIR  = Path("docs") / "assets"


def sync_browser_scripts() -> list[str]:
    """Copy canonical browser scripts from scripts/ to docs/assets/.

    Returns a list of destination filenames that were written.
    """
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for src_name, dst_name in _BROWSER_SCRIPTS:
        src = SCRIPTS_DIR / src_name
        dst = ASSETS_DIR / dst_name
        if not src.exists():
            raise FileNotFoundError(f"Canonical browser script not found: {src}")
        shutil.copy2(src, dst)
        copied.append(dst_name)
    return copied

# Epic 5 quality vocabulary (#27)
from quality import (
    EXPLANATIONS, detect_degeneration, format_confidence,
    confidence_scope_label, explanation_button, explanation_block,
    de_plural,
)

DOCS = Path("docs")

CATALOGUE_PERFORMANCE_BUDGETS = {
    "summary_bytes_per_record": 600,
    "card_bytes_per_record": 6000,
    "large_fixture_records": 5000,
    "large_fixture_interaction_ms": 2000,
}


def _val(value: object) -> str:
    if isinstance(value, dict):
        return str(value.get("wert") or value.get("value") or "")
    return "" if value is None else str(value)


def _first(mapping: dict, *keys: str) -> str:
    for key in keys:
        value = _val(mapping.get(key))
        if value:
            return value
    return ""


def _parse_datetime(value: object) -> datetime | None:
    if not value:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _git_created(path: Path) -> datetime | None:
    try:
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--follow", "--format=%aI", "--", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    dates = [line for line in result.stdout.splitlines() if line.strip()]
    return _parse_datetime(dates[-1]) if dates else None


def _entity_count(entities: object) -> int:
    if isinstance(entities, list):
        return len(entities)
    if not isinstance(entities, dict):
        return 0
    direct = entities.get("entities")
    if isinstance(direct, list):
        return len(direct)
    return sum(len(value) for value in entities.values() if isinstance(value, list))


@dataclass
class Record:
    doc_id: str
    created: datetime
    date_label: str
    language: str
    script: str
    document_type: str
    entities: int
    pages: int | None
    qa_score: float | None
    errors: int
    is_test: bool
    preview: str
    review_status: str
    # Epic 5 quality fields (#27, #28)
    recognition_errors: int = 0       # candidates that failed or are degenerate
    recognition_avg_confidence: float | None = None  # mean engine confidence
    reference_cer: float | None = None  # reference-based CER if available
    reference_wer: float | None = None
    recognition_summary: "RecognitionSummary | None" = None


@dataclass(frozen=True)
class RecognitionSummary:
    provenance: str
    total: int | None
    successful: int | None
    failed: int | None
    empty: int | None
    degenerate: int | None
    engines: tuple[str, ...]
    model_count: int
    page_count: int | None
    source_available: bool
    source_type: str
    review_status: str
    comparison_ready: bool
    comparison_pair: tuple[str, str, str] | None = None

    def as_dict(self) -> dict:
        return {
            "provenance": self.provenance,
            "total": self.total,
            "successful": self.successful,
            "failed": self.failed,
            "empty": self.empty,
            "degenerate": self.degenerate,
            "engines": list(self.engines),
            "model_count": self.model_count,
            "page_count": self.page_count,
            "source_available": self.source_available,
            "source_type": self.source_type,
            "review_status": self.review_status,
            "comparison_ready": self.comparison_ready,
            "comparison_pair": list(self.comparison_pair) if self.comparison_pair else None,
        }


def recognition_summary(data: dict) -> RecognitionSummary:
    """Derive the bounded catalogue contract directly from pipeline metadata."""
    meta = data.get("a_meta") if isinstance(data.get("a_meta"), dict) else {}
    review = _val(data.get("review_status") or meta.get("review_status") or "machine-generated")
    source = normalize_source_reference(data)
    raw = data.get("recognitions")
    if not isinstance(raw, list):
        return RecognitionSummary(
            "legacy", None, None, None, None, None, (), 0, None,
            bool(source["url"]), source["type"], review, False,
        )

    total = successful = failed = empty = degenerate = 0
    engines: set[str] = set()
    models: set[tuple[str, str]] = set()
    usable_by_page: dict[str, set[tuple[str, str, str]]] = {}
    attributed_pages: set[str] = set()
    seen_ids = {"selected"}
    for index, candidate in enumerate((item for item in raw if isinstance(item, dict)), start=1):
        total += 1
        engine = _val(candidate.get("engine") or "unknown").casefold()
        model = _val(candidate.get("model_id"))
        page = _val(candidate.get("page"))
        base = re.sub(r"[^a-z0-9]+", "-", f"{page}-{engine}-{model}".casefold()).strip("-")[:100]
        candidate_id = base or f"candidate-{index}"
        suffix = 2
        while candidate_id in seen_ids:
            candidate_id = f"{base or f'candidate-{index}'}-{suffix}"
            suffix += 1
        seen_ids.add(candidate_id)
        text = _val(candidate.get("text"))
        error = bool(_val(candidate.get("error")))
        is_degenerate, _ = detect_degeneration(text, candidate.get("confidence"))
        engines.add(engine)
        models.add((engine, model))
        if page:
            attributed_pages.add(page)
        if error:
            failed += 1
        elif not text.strip():
            empty += 1
        elif is_degenerate:
            degenerate += 1
        else:
            successful += 1
            usable_by_page.setdefault(page, []).append(candidate_id)

    declared_pages = meta.get("pages")
    try:
        page_count = int(declared_pages) if declared_pages is not None else None
    except (TypeError, ValueError):
        page_count = None
    if page_count is None:
        page_count = len(attributed_pages) or len(source["pages"]) or (1 if total else 0)
    comparable = any(len(items) >= 2 and (page or page_count == 1)
                     for page, items in usable_by_page.items())
    pair = next(((items[0], items[1], page) for page, items in usable_by_page.items()
                 if len(items) >= 2 and (page or page_count == 1)), None)
    return RecognitionSummary(
        "current", total, successful, failed, empty, degenerate,
        tuple(sorted(engines)), len(models), page_count,
        bool(source["url"]), source["type"], review, comparable, pair,
    )


def _record(path: Path) -> Record:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}

    description = data.get("description") if isinstance(data.get("description"), dict) else {}
    source = description.get("source_json") if isinstance(description.get("source_json"), dict) else {}
    meta = data.get("a_meta") if isinstance(data.get("a_meta"), dict) else {}

    explicit_created = next(
        (_parse_datetime(value) for value in (
            data.get("created_at"), data.get("creation_date"),
            meta.get("created_at"), meta.get("creation_date"), meta.get("timestamp"),
        ) if _parse_datetime(value)),
        None,
    )
    created = explicit_created or _git_created(path) or datetime.fromtimestamp(
        path.stat().st_mtime, tz=timezone.utc
    )

    date_label = _first(source, "Datierung", "datierung")
    if not date_label and source.get("century"):
        date_label = f"{_val(source['century'])}. Jahrhundert"

    transcript = _val(data.get("transcription") or meta.get("transcription"))
    compact_preview = " ".join(transcript.replace("---", " ").split())[:180]
    errors = data.get("errors") if isinstance(data.get("errors"), list) else []
    doc_id = path.parent.name
    source_url = _val(data.get("source_url"))

    pages = meta.get("pages")
    try:
        pages = int(pages) if pages is not None else None
    except (TypeError, ValueError):
        pages = None
    qa = meta.get("qa_score")
    try:
        qa = float(qa) if qa is not None else None
    except (TypeError, ValueError):
        qa = None

    # Epic 5 #28: Extract typed quality metrics from recognition data
    recognitions = data.get("recognitions") if isinstance(data, dict) else None
    rec_errors = 0
    rec_confidences = []
    ref_cer = None
    ref_wer = None
    if isinstance(recognitions, list):
        for rec in recognitions:
            if not isinstance(rec, dict):
                continue
            text = str(rec.get("text", ""))
            conf = rec.get("confidence")
            error = rec.get("error", "")
            is_deg, _ = detect_degeneration(text, conf)
            if error or is_deg:
                rec_errors += 1
            if conf is not None:
                try:
                    rec_confidences.append(float(conf))
                except (TypeError, ValueError):
                    pass
        # Reference evaluation from a_meta.reference_eval
        ref_eval = meta.get("reference_eval") if isinstance(meta, dict) else {}
        if isinstance(ref_eval, dict):
            ref_cer = ref_eval.get("cer")
            ref_wer = ref_eval.get("wer")

    rec_avg_conf = sum(rec_confidences) / len(rec_confidences) if rec_confidences else None

    summary = recognition_summary(data)
    return Record(
        doc_id=doc_id,
        created=created,
        date_label=date_label,
        language=_first(source, "Sprache", "sprache", "lang", "language"),
        script=_first(source, "Schrift", "schrift", "script"),
        document_type=_first(source, "Dokumenttyp", "document_type", "type"),
        entities=_entity_count(data.get("entities")),
        pages=pages,
        qa_score=qa,
        errors=len(errors),
        is_test="test" in doc_id.lower() or "example.com" in source_url,
        preview=compact_preview,
        review_status=_val(data.get("review_status") or meta.get("review_status") or "machine-generated"),
        # Epic 5 quality fields
        recognition_errors=rec_errors,
        recognition_avg_confidence=rec_avg_conf,
        reference_cer=ref_cer,
        reference_wer=ref_wer,
        recognition_summary=summary,
    )


def _badge(text: str, kind: str = "") -> str:
    classes = "catalogue-badge" + (f" catalogue-badge--{kind}" if kind else "")
    return f'<span class="{classes}">{html.escape(text)}</span>'


# Issue #122: canonical map from review-status enum → (German label, CSS modifier)
# CSS class carries semantic meaning; enum is preserved in data-review-status.
_REVIEW_STATUS_LABELS: dict[str, tuple[str, str]] = {
    "machine-generated": ("Maschinell erzeugt", "review-machine"),
    "human-verified":    ("Menschlich geprüft",  "review-human"),
}


def _review_badge(review_status: str) -> str:
    """Return a localized, semantically-classed badge for a review-status enum.

    The badge text is German; the enum value is preserved in data-review-status
    on the surrounding <article> element for JavaScript filtering.
    """
    label, css_mod = _REVIEW_STATUS_LABELS.get(
        review_status, (review_status, "review-unknown")
    )
    return _badge(label, css_mod)


def _card(record: Record) -> str:
    created_iso = record.created.isoformat()
    created_label = record.created.strftime("%d.%m.%Y, %H:%M")
    badges = []
    if record.is_test:
        badges.append(_badge("Testlauf", "test"))
    badges.append(_review_badge(record.review_status))
    badges.append(_badge("Pipeline: Ohne Fehler" if not record.errors else f"Pipeline: {record.errors} Fehler", "ok" if not record.errors else "error"))
    # Epic 5 #28: Typed quality badges — replace ambiguous QA label
    # Button and region must share one deterministic id.  Calling the quality
    # helpers without an explicit suffix advances their independent counter
    # and leaves aria-controls pointing at a non-existent element.
    explanation_suffix = hashlib.sha1(record.doc_id.encode("utf-8")).hexdigest()[:12]
    has_cer_wer = record.reference_cer is not None or record.reference_wer is not None
    explain_btn = explanation_button("reference_evaluation", explanation_suffix) if has_cer_wer else ""
    explain_blk = explanation_block("reference_evaluation", explanation_suffix) if has_cer_wer else ""

    if record.reference_cer is not None:
        cer_pct = max(0.0, min(1.0, float(record.reference_cer))) * 100
        badges.append(_badge(f"CER {cer_pct:.1f}%", "quality-confidence"))
    if record.reference_wer is not None:
        wer_pct = max(0.0, min(1.0, float(record.reference_wer))) * 100
        badges.append(_badge(f"WER {wer_pct:.1f}%", "quality-confidence"))
    if record.recognition_errors > 0:
        badges.append(_badge(f"{record.recognition_errors} Erkennungsfehler", "quality-failed"))
    if record.recognition_avg_confidence is not None and record.recognition_errors == 0:
        badges.append(_badge(f"Ø Konfidenz {record.recognition_avg_confidence:.0%}", "quality-confidence"))

    # Legacy qa_score — show with distinct style to signal it needs replacement
    if record.qa_score is not None:
        badges.append(_badge(f"Legacy-QA {record.qa_score:.0%}", "legacy"))

    facts = []
    if record.date_label:
        facts.append(("Datierung", record.date_label))
    if record.document_type:
        facts.append(("Dokumenttyp", record.document_type))
    if record.language:
        facts.append(("Sprache", record.language))
    if record.script:
        facts.append(("Schrift", record.script))
    facts.append(("Entitäten", str(record.entities)))
    if record.pages is not None:
        facts.append(("Seiten", str(record.pages)))

    fact_html = "".join(
        f'<div><dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd></div>'
        for label, value in facts
    )
    preview = (
        f'<p class="catalogue-preview">{html.escape(record.preview)}…</p>'
        if record.preview else '<p class="catalogue-preview catalogue-muted">Keine Vorschau verfügbar.</p>'
    )
    search = " ".join((record.doc_id, record.date_label, record.language, record.script, record.document_type, record.preview)).lower()
    kind = "test" if record.is_test else "output"
    summary = record.recognition_summary or RecognitionSummary(
        "legacy", None, None, None, None, None, (), 0, None, False,
        "missing", record.review_status, False)
    engine_chips = "".join(
        f'<li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>{html.escape(engine)}</li>'
        for engine in summary.engines
    )
    recognition_status = []
    if summary.provenance == "legacy":
        recognition_status.append('<p class="catalogue-warning">Begrenzte Provenienz: Erkennungsversuche nicht vollständig dokumentiert.</p>')
    else:
        facts.append(("Kandidaten", f"{summary.successful or 0} erfolgreich / {summary.total or 0} insgesamt"))
        if summary.failed:
            recognition_status.append(
                f'<p class="catalogue-warning"><span aria-hidden="true">⚠</span> {de_plural(summary.failed, "fehlgeschlagener Erkennungsversuch", "fehlgeschlagene Erkennungsversuche")}</p>')
        if summary.degenerate:
            recognition_status.append(
                f'<p class="catalogue-warning"><span aria-hidden="true">⚠</span> {de_plural(summary.degenerate, "degeneriertes Ergebnis", "degenerierte Ergebnisse")}</p>')
    if not summary.source_available:
        recognition_status.append('<p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>')
    status_html = "".join(recognition_status)
    fact_html = "".join(
        f'<div><dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd></div>'
        for label, value in facts
    )
    count = lambda value: "" if value is None else str(value)
    doc_href = f"{quote(record.doc_id, safe='')}/"
    if summary.comparison_pair:
        left, right, page = summary.comparison_pair
        query = f"cmp={quote(left)}:{quote(right)}"
        if page:
            query += f"&page={quote(page)}"
        action_href = f"{doc_href}?{query}#recognitions"
        action_label = "Modelle vergleichen"
    elif summary.total:
        action_href = f"{doc_href}?rec=selected#recognition-selected"
        action_label = "Erkennungen ansehen"
    else:
        action_href = doc_href
        action_label = "Ausgabe öffnen"
    summary_attrs = (
        f'data-recognition-provenance="{summary.provenance}" '
        f'data-recognition-total="{count(summary.total)}" '
        f'data-recognition-successful="{count(summary.successful)}" '
        f'data-recognition-failed="{count(summary.failed)}" '
        f'data-recognition-empty="{count(summary.empty)}" '
        f'data-recognition-degenerate="{count(summary.degenerate)}" '
        f'data-recognition-engines="{html.escape(",".join(summary.engines), quote=True)}" '
        f'data-recognition-models="{summary.model_count}" '
        f'data-recognition-pages="{count(summary.page_count)}" '
        f'data-source-type="{summary.source_type}" '
        f'data-source-available="{str(summary.source_available).lower()}" '
        f'data-review-status="{html.escape(summary.review_status, quote=True)}" '
        f'data-comparison-ready="{str(summary.comparison_ready).lower()}"'
    )
    return f'''<article class="catalogue-card" data-document-id="{html.escape(record.doc_id.casefold(), quote=True)}" data-created="{created_iso}" data-kind="{kind}" data-language="{html.escape(record.language.casefold(), quote=True)}" data-script="{html.escape(record.script.casefold(), quote=True)}" data-search="{html.escape(search, quote=True)}" {summary_attrs}>
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="{created_iso}">{created_label}</time></p>
      <h2><a href="{html.escape(record.doc_id)}/">{html.escape(record.doc_id)}</a></h2>
    </div>
    <div class="catalogue-badges">{"".join(badges)}</div>
  </div>
  <dl class="catalogue-facts">{fact_html}</dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    {f'<ul class="catalogue-engines">{engine_chips}</ul>' if engine_chips else '<p class="catalogue-muted">Nicht dokumentiert</p>'}
    {status_html if status_html else '<span class="visually-hidden">Keine Warnungen</span>'}
  </div>
  {preview}
  <p class="catalogue-actions"><a href="{html.escape(action_href, quote=True)}" aria-label="{html.escape(action_label)}: {html.escape(record.doc_id)}">{action_label} <span aria-hidden="true">→</span></a></p>
  {explain_btn}{explain_blk}
</article>'''


# ---------------------------------------------------------------------------
# Structured discoverability: sitemap.xml and Atom feed (issue #119)
# ---------------------------------------------------------------------------
SITE = "https://thodel.github.io/agentic-historian-outputs"
_RFC3339_FMT = "%Y-%m-%dT%H:%M:%S+00:00"


def _url_entry(loc: str, lastmod: str | None = None, priority: str = "0.7") -> str:
    lastmod_tag = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
    return f"<url><loc>{loc}</loc>{lastmod_tag}<priority>{priority}</priority></url>"


def build_sitemap(records: list) -> None:
    """Generate docs/sitemap.xml listing all site URLs."""
    entity_dirs = sorted(d for d in (DOCS / "entities").iterdir() if d.is_dir()) if (DOCS / "entities").exists() else []
    entries: list[str] = [
        _url_entry(f"{SITE}/",                  priority="1.0"),
        _url_entry(f"{SITE}/methodology.html",  priority="0.8"),
        _url_entry(f"{SITE}/about.html",        priority="0.6"),
        _url_entry(f"{SITE}/entities/",         priority="0.7"),
        _url_entry(f"{SITE}/tests/",            priority="0.4"),
    ]
    for record in records:
        lastmod = record.created.strftime(_RFC3339_FMT)
        entries.append(_url_entry(
            f"{SITE}/{record.doc_id}/",
            lastmod=lastmod,
            priority="0.9" if not record.is_test else "0.4",
        ))
    for d in entity_dirs:
        entries.append(_url_entry(f"{SITE}/entities/{d.name}/", priority="0.5"))
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(f"  {e}" for e in entries)
        + "\n</urlset>\n"
    )
    (DOCS / "sitemap.xml").write_text(xml, encoding="utf-8")
    print(f"Wrote docs/sitemap.xml with {len(entries)} URLs")


def build_atom_feed(records: list) -> None:
    """Generate docs/feed.xml (Atom 1.0) for newly published outputs."""
    from xml.sax.saxutils import escape as xml_escape  # noqa: PLC0415
    feed_records = [r for r in records if not r.is_test][:20]
    updated = (
        feed_records[0].created.strftime(_RFC3339_FMT)
        if feed_records else "1970-01-01T00:00:00+00:00"
    )
    entries_xml: list[str] = []
    for record in feed_records:
        entry_id = f"{SITE}/{record.doc_id}/"
        published = record.created.strftime(_RFC3339_FMT)
        title = f"Agentic Historian output: {record.doc_id}"
        summary_parts = []
        if record.document_type:
            summary_parts.append(record.document_type)
        if record.date_label:
            summary_parts.append(record.date_label)
        if record.language:
            summary_parts.append(record.language)
        if record.preview:
            summary_parts.append(record.preview[:120])
        summary = xml_escape(" \u00b7 ".join(summary_parts) or "Agentic Historian dataset")
        entries_xml.append(
            f"  <entry>\n"
            f"    <id>{xml_escape(entry_id)}</id>\n"
            f"    <title>{xml_escape(title)}</title>\n"
            f"    <link rel=\"alternate\" type=\"text/html\" href=\"{xml_escape(entry_id)}\"/>\n"
            f"    <published>{published}</published>\n"
            f"    <updated>{published}</updated>\n"
            f"    <summary type=\"text\">{summary}</summary>\n"
            f"    <rights>CC BY 4.0 https://creativecommons.org/licenses/by/4.0/</rights>\n"
            f"  </entry>"
        )
    atom = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<feed xmlns="http://www.w3.org/2005/Atom">\n'
        f'  <id>{SITE}/feed.xml</id>\n'
        f'  <title>Agentic Historian \u2014 Ver\u00f6ffentlichte Ausgaben</title>\n'
        f'  <link rel="self" type="application/atom+xml" href="{SITE}/feed.xml"/>\n'
        f'  <link rel="alternate" type="text/html" href="{SITE}/"/>\n'
        f'  <updated>{updated}</updated>\n'
        f'  <rights>CC BY 4.0 https://creativecommons.org/licenses/by/4.0/</rights>\n'
        + "\n".join(entries_xml)
        + "\n</feed>\n"
    )
    (DOCS / "feed.xml").write_text(atom, encoding="utf-8")
    print(f"Wrote docs/feed.xml with {len(entries_xml)} entries")


def build() -> int:
    records = [_record(path) for path in DOCS.glob("*/pipeline.json")]
    records.sort(key=lambda item: (item.created, item.doc_id.lower()), reverse=True)
    output_count = sum(not record.is_test for record in records)
    test_count = len(records) - output_count
    summary_payload = {
        record.doc_id: record.recognition_summary.as_dict()
        for record in records if record.recognition_summary is not None
    }
    (DOCS / "catalogue-summary.json").write_text(
        json.dumps(summary_payload, ensure_ascii=False, separators=(",", ":"),
                   sort_keys=True) + "\n",
        encoding="utf-8",
    )

    cards = "\n".join(_card(record) for record in records)
    page = f'''---
layout: default
title: Katalog
---

<link rel="stylesheet" href="{{{{ '/assets/catalogue.css' | relative_url }}}}">

<div class="catalogue-intro">
  <p class="catalogue-kicker">Forschungsdaten · automatisch erzeugt</p>
  <h1>Verarbeitete Dokumente</h1>
  <p>Transkriptionen, Quellenbeschreibungen und erkannte Entitäten. Die neuesten Ausgaben stehen zuerst. Automatisch erzeugte Angaben sind Forschungsangebote und müssen am Original überprüft werden.</p>
  <details class="quality-explanation" id="catalogue-quality-explainer">
    <summary>Qualitätsmetriken in diesem Katalog</summary>
    <p>Jede Ausgabe zeigt bis zu vier Qualitätsmetriken:</p>
    <dl>
      <div><dt>Ø Konfidenz</dt><dd>Durchschnittliche Engine-Konfidenz aller Erkennungskandidaten (niedrig = unsicherer). Nicht zwischen Engines vergleichbar.</dd></div>
      <div><dt>CER / WER</dt><dd>Character/Word Error Rate gegen eine bekannte Referenz (niedrig = weniger Fehler). Nur vorhanden wenn Referenz verfügbar.</dd></div>
      <div><dt>Erkennungsfehler</dt><dd>Anzahl der Kandidaten, die fehlgeschlagen oder degeneriert sind.</dd></div>
      <div><dt>Legacy-QA</dt><dd>QA-Wert aus älterem System ohne definierte Bedeutung. Ersetzen Sie durch eine der oben genannten Metriken.</dd></div>
    </dl>
  </details>
  <p><a href="entities/">Entitäten durchsuchen</a> · <a href="tests/">Testläufe separat anzeigen</a></p>
  <p class="catalogue-summary"><strong>{len(records)}</strong> Einträge · {output_count} Ausgaben · {test_count} Testläufe</p>
</div>

<form class="catalogue-tools" role="search" aria-label="Ausgaben durchsuchen" onsubmit="return false">
  <div>
    <label for="catalogue-search">Suchen</label>
    <input id="catalogue-search" type="search" placeholder="Signatur, Sprache, Schrift oder Text …" autocomplete="off">
  </div>
  <div>
    <label for="catalogue-filter">Anzeigen</label>
    <select id="catalogue-filter">
      <option value="all">Alle Einträge</option>
      <option value="output">Nur Ausgaben</option>
      <option value="test">Nur Testläufe</option>
    </select>
  </div>
  <div>
    <label for="catalogue-language">Sprache</label>
    <select id="catalogue-language"><option value="all">Alle Sprachen</option></select>
  </div>
  <div>
    <label for="catalogue-script">Schrift</label>
    <select id="catalogue-script"><option value="all">Alle Schriften</option></select>
  </div>
  <div>
    <label for="catalogue-engine">Erkennungsengine</label>
    <select id="catalogue-engine"><option value="all">Alle Engines</option></select>
  </div>
  <div>
    <label for="catalogue-readiness">Erkennungsdaten</label>
    <select id="catalogue-readiness">
      <option value="all">Alle Bereitschaftsstufen</option>
      <option value="comparison">Vergleich möglich</option>
      <option value="candidates">Kandidaten vorhanden</option>
      <option value="legacy">Begrenzte Legacy-Provenienz</option>
    </select>
  </div>
  <div>
    <label for="catalogue-failure">Erkennungsstatus</label>
    <select id="catalogue-failure">
      <option value="all">Alle Status</option>
      <option value="clean">Ohne bekannte Probleme</option>
      <option value="issues">Fehler, leer oder degeneriert</option>
    </select>
  </div>
  <div>
    <label for="catalogue-source">Digitale Quelle</label>
    <select id="catalogue-source">
      <option value="all">Alle Quellenlagen</option>
      <option value="available">Quelle vorhanden</option>
      <option value="missing">Quelle fehlt</option>
      <option value="iiif_manifest">IIIF</option>
      <option value="image">Direktbild</option>
      <option value="landing_page">Archivseite</option>
    </select>
  </div>
  <div>
    <label for="catalogue-sort">Sortierung</label>
    <select id="catalogue-sort">
      <option value="created-desc">Erstellung: neueste zuerst</option>
      <option value="created-asc">Erstellung: älteste zuerst</option>
      <option value="title-asc">Dokument-ID: A–Z</option>
      <option value="title-desc">Dokument-ID: Z–A</option>
      <option value="pages-desc">Seiten: viele zuerst</option>
      <option value="pages-asc">Seiten: wenige zuerst</option>
      <option value="candidates-desc">Kandidaten: viele zuerst</option>
      <option value="candidates-asc">Kandidaten: wenige zuerst</option>
      <option value="failures-desc">Fehler: viele zuerst</option>
      <option value="failures-asc">Fehler: wenige zuerst</option>
    </select>
  </div>
  <div class="catalogue-clear"><button id="catalogue-clear" type="button">Alle Filter zurücksetzen</button></div>
</form>

<p id="catalogue-active-filters" class="catalogue-active-filters">Keine Filter aktiv.</p>
<p id="catalogue-status" class="catalogue-status" role="status" aria-live="polite">{len(records)} Einträge, nach Erstellungsdatum absteigend sortiert.</p>
<p id="catalogue-empty" class="catalogue-empty" role="status" hidden>Keine Einträge entsprechen den aktiven Filtern. Ändern Sie die Filter oder setzen Sie sie zurück.</p>

<div id="catalogue-list" class="catalogue-list" data-enhanced="false">
{cards}
</div>

<noscript><p>Die Suche benötigt JavaScript. Alle Einträge bleiben ohne JavaScript sichtbar und sind bereits nach Erstellungsdatum sortiert.</p></noscript>
<script src="{{{{ '/assets/catalogue.js' | relative_url }}}}" defer></script>
<script src="{{{{ '/assets/quality-explain.js' | relative_url }}}}" defer></script>
'''
    (DOCS / "index.md").write_text(page, encoding="utf-8")
    from build_outputs import build as build_outputs
    build_outputs()
    copied = sync_browser_scripts()
    build_sitemap(records)
    build_atom_feed(records)
    print(f"Wrote docs/index.md with {len(records)} record(s), newest first")
    print(f"Synced {len(copied)} browser scripts to docs/assets/: {', '.join(copied)}")
    return len(records)


if __name__ == "__main__":
    build()
