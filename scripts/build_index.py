#!/usr/bin/env python3
"""Build the accessible, date-ordered catalogue in ``docs/index.md``.

The publisher has emitted more than one pipeline JSON schema.  This builder
normalises those variants and derives a stable creation date from explicit
metadata or, as a fallback, the commit that first introduced pipeline.json.
It uses only the Python standard library.
"""

from __future__ import annotations

import html
import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DOCS = Path("docs")


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
    )


def _badge(text: str, kind: str = "") -> str:
    classes = "catalogue-badge" + (f" catalogue-badge--{kind}" if kind else "")
    return f'<span class="{classes}">{html.escape(text)}</span>'


def _card(record: Record) -> str:
    created_iso = record.created.isoformat()
    created_label = record.created.strftime("%d.%m.%Y, %H:%M")
    badges = []
    if record.is_test:
        badges.append(_badge("Testlauf", "test"))
    badges.append(_badge(record.review_status, "ok" if record.review_status == "human-verified" else "test"))
    badges.append(_badge("Ohne Fehler" if not record.errors else f"{record.errors} Fehler", "ok" if not record.errors else "error"))
    if record.qa_score is not None:
        badges.append(_badge(f"QA {record.qa_score:.0%}"))

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
    return f'''<article class="catalogue-card" data-kind="{kind}" data-language="{html.escape(record.language.casefold(), quote=True)}" data-script="{html.escape(record.script.casefold(), quote=True)}" data-search="{html.escape(search, quote=True)}">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="{created_iso}">{created_label}</time></p>
      <h2><a href="{html.escape(record.doc_id)}/">{html.escape(record.doc_id)}</a></h2>
    </div>
    <div class="catalogue-badges">{"".join(badges)}</div>
  </div>
  <dl class="catalogue-facts">{fact_html}</dl>
  {preview}
  <p class="catalogue-actions"><a href="{html.escape(record.doc_id)}/" aria-label="Ausgabe {html.escape(record.doc_id)} öffnen">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
</article>'''


def build() -> int:
    records = [_record(path) for path in DOCS.glob("*/pipeline.json")]
    records.sort(key=lambda item: (item.created, item.doc_id.lower()), reverse=True)
    output_count = sum(not record.is_test for record in records)
    test_count = len(records) - output_count

    cards = "\n".join(_card(record) for record in records)
    page = f'''---
layout: default
title: Agentic Historian — Outputs
---

<link rel="stylesheet" href="{{{{ '/assets/catalogue.css' | relative_url }}}}">

<div class="catalogue-intro">
  <p class="catalogue-kicker">Forschungsdaten · automatisch erzeugt</p>
  <h1>Verarbeitete Dokumente</h1>
  <p>Transkriptionen, Quellenbeschreibungen und erkannte Entitäten. Die neuesten Ausgaben stehen zuerst. Automatisch erzeugte Angaben sind Forschungsangebote und müssen am Original überprüft werden.</p>
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
</form>

<p id="catalogue-status" class="catalogue-status" role="status" aria-live="polite">{len(records)} Einträge, nach Erstellungsdatum absteigend sortiert.</p>

<div id="catalogue-list" class="catalogue-list">
{cards}
</div>

<noscript><p>Die Suche benötigt JavaScript. Alle Einträge bleiben ohne JavaScript sichtbar und sind bereits nach Erstellungsdatum sortiert.</p></noscript>
<script src="{{{{ '/assets/catalogue.js' | relative_url }}}}" defer></script>
'''
    (DOCS / "index.md").write_text(page, encoding="utf-8")
    from build_outputs import build as build_outputs
    build_outputs()
    print(f"Wrote docs/index.md with {len(records)} record(s), newest first")
    return len(records)


if __name__ == "__main__":
    build()
