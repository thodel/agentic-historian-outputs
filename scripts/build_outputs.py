#!/usr/bin/env python3
"""Generate accessible document, entity, test, citation, and export pages."""

from __future__ import annotations

import csv
import hashlib
import html
import io
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from build_recognitions import build_recognition_section, write_package
from source_references import normalize_source_reference, public_url
from urllib.parse import urlparse
from xml.sax.saxutils import escape as xml_escape

DOCS = Path("docs")
SITE = "https://thodel.github.io/agentic-historian-outputs"
REPO = "https://github.com/thodel/agentic-historian-outputs"


def value(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("wert") or item.get("value") or "")
    return "" if item is None else str(item)


def valid_public_url(url: str) -> bool:
    return bool(public_url(url))


def git_history(path: Path) -> list[tuple[str, str, str]]:
    try:
        # Generated pages must not embed the current PR commit: doing so makes
        # every rebuild one SHA behind its own commit.  Review builds therefore
        # use the merge base with main; after merge that base is HEAD and the
        # published history naturally advances when pipeline.json changes.
        revision = subprocess.run(
            ["git", "merge-base", "HEAD", "origin/main"],
            check=True, capture_output=True, text=True,
        ).stdout.strip() or "HEAD"
        out = subprocess.run(
            ["git", "log", revision, "--follow",
             "--format=%h%x09%aI%x09%s", "--", str(path)],
            check=True, capture_output=True, text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    rows = []
    for line in out.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3:
            # Git versions differ in rendering UTC as Z or +00:00.
            # Canonicalize it so generated pages are reproducible in CI.
            parts[1] = datetime.fromisoformat(
                parts[1].replace("Z", "+00:00")
            ).isoformat()
            rows.append(tuple(parts))
    return rows


def entities(data: dict) -> list[dict[str, str]]:
    raw = data.get("entities") or {}
    if isinstance(raw, dict) and isinstance(raw.get("entities"), list):
        raw = raw["entities"]
    elif isinstance(raw, dict):
        converted = []
        for group, items in raw.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    converted.append({**item, "type": item.get("type") or group.rstrip("s").upper()})
                else:
                    converted.append({"text": str(item), "type": group.rstrip("s").upper()})
        raw = converted
    if not isinstance(raw, list):
        return []
    result = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = value(item.get("normalised") or item.get("name") or item.get("text"))
        if label:
            result.append({
                "label": label,
                "surface": value(item.get("text") or item.get("name") or label),
                "type": value(item.get("type") or "UNSPECIFIED").upper(),
                "context": value(item.get("context")),
                "confidence": value(item.get("hub_confidence") or item.get("confidence")),
                "uri": value(item.get("uri") or item.get("url") or item.get("id")),
            })
    return result


def slug(label: str, kind: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", label.casefold()).strip("-")[:55] or "entity"
    digest = hashlib.sha1(f"{kind}:{label}".encode()).hexdigest()[:8]
    return f"{base}-{digest}"


def frontmatter(title: str) -> str:
    safe = title.replace('"', '\\"')
    return f'---\nlayout: default\ntitle: "{safe}"\n---\n\n<link rel="stylesheet" href="{{{{ \'/assets/output.css\' | relative_url }}}}">\n\n'


def write_csv(path: Path, items: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["label", "surface", "type", "context", "confidence", "uri"])
        writer.writeheader()
        writer.writerows(items)


def write_tei(path: Path, doc_id: str, transcript: str, source_url: str) -> None:
    source = f'<ref target="{xml_escape(source_url)}">Digital source</ref>' if valid_public_url(source_url) else "Source image not published"
    tei = f'''<?xml version="1.0" encoding="UTF-8"?>
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Machine transcription: {xml_escape(doc_id)}</title></titleStmt>
      <publicationStmt><p>Agentic Historian output; reuse rights not specified.</p></publicationStmt>
      <sourceDesc><p>{source}</p></sourceDesc>
    </fileDesc>
    <revisionDesc><change when="{datetime.now().date().isoformat()}">Generated from pipeline.json.</change></revisionDesc>
  </teiHeader>
  <text><body><div type="transcription"><p>{xml_escape(transcript)}</p></div></body></text>
</TEI>
'''
    path.write_text(tei, encoding="utf-8")


def source_panel(data: dict) -> str:
    source = normalize_source_reference(data)
    url = source["url"]
    payload = json.dumps(source, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    if url:
        escaped = html.escape(url, quote=True)
        if source["type"] in {"iiif_manifest", "image"}:
            page_buttons = "".join(
                f'<button type="button" data-source-page="{html.escape(page["page"], quote=True)}">{html.escape(page["page"])}</button>'
                for page in source["pages"]
            )
            page_nav = (f'<nav class="source-page-nav" aria-label="Quellenseite auswählen">{page_buttons}</nav>'
                        if len(source["pages"]) > 1 else "")
            viewer = f'''<div class="evidence-viewer" data-evidence-viewer data-source-type="{source["type"]}" data-source-url="{escaped}">
{page_nav}
<div class="evidence-toolbar" role="toolbar" aria-label="Digitalisat steuern">
<button type="button" data-evidence-action="zoom-out" aria-label="Verkleinern">−</button>
<output data-evidence-zoom aria-label="Vergrößerung">100%</output>
<button type="button" data-evidence-action="zoom-in" aria-label="Vergrößern">+</button>
<button type="button" data-evidence-action="reset">Ansicht zurücksetzen</button>
<button type="button" data-evidence-action="fullscreen">Vollbild</button></div>
<div class="evidence-stage" data-evidence-stage tabindex="0" aria-label="Digitalisat, verschiebbar bei Vergrößerung"><img data-evidence-image hidden alt="Digitalisat zu diesem Output"></div>
<p class="evidence-status" data-evidence-status role="status" aria-live="polite">Digitalisat wird geladen …</p></div>'''
        else:
            viewer = ""
        metadata = "".join(
            f'<dt>{label}</dt><dd>{html.escape(source[key])}</dd>'
            for key, label in (("attribution", "Zuschreibung"), ("rights", "Rechte"))
            if source[key]
        )
        metadata = f'<dl class="source-meta">{metadata}</dl>' if metadata else ""
        return f'''<section id="source" class="page-section page-section--evidence" data-page-section="source" aria-labelledby="source-heading"><h2 id="source-heading">Quelle und Digitalisat</h2>
<p><a href="{escaped}">{html.escape(source["label"] or "Veröffentlichte Quelle öffnen")}</a></p>{metadata}{viewer}
<script type="application/json" data-source-reference>{payload}</script></section>'''
    return '''<section id="source" class="page-section page-section--evidence" data-page-section="source" aria-labelledby="source-heading"><h2 id="source-heading">Quelle und Digitalisat</h2>
<div class="notice notice--warning"><strong>Kein öffentliches Digitalisat verknüpft.</strong> Ein lokaler Verarbeitungspfad ist kein zitierbarer Quellenbeleg. Ergänzen Sie <code>source_url</code> oder <code>iiif_manifest</code> in der Pipeline-Ausgabe.</div></section>'''


def evidence_workspace(data: dict, doc_id: str, transcription: str,
                       recognition_section: str) -> str:
    """Compose evidence panes, enhancing only embeddable image/IIIF sources."""
    source = source_panel(data)
    transcript = f'''<section id="transcription" class="page-section page-section--evidence" data-page-section="transcription" aria-labelledby="transcription-heading"><h2 id="transcription-heading">Transkription</h2>
<pre class="transcription" tabindex="0"><code>{html.escape(transcription) if transcription else 'Keine Transkription verfügbar.'}</code></pre></section>'''
    if normalize_source_reference(data)["type"] not in {"image", "iiif_manifest"}:
        return f"{source}\n\n{transcript}\n\n{recognition_section}"
    return f'''<div class="evidence-workspace" data-evidence-workspace data-doc-id="{html.escape(doc_id, quote=True)}">
<div class="evidence-pane evidence-pane--source" role="region" aria-labelledby="source-heading">{source}</div>
<div class="workspace-divider" role="separator" aria-label="Breite von Quelle und Transkription ändern" aria-orientation="vertical" aria-valuemin="25" aria-valuemax="75" aria-valuenow="50" tabindex="0" data-workspace-divider><span aria-hidden="true">⋮</span></div>
<div class="evidence-pane evidence-pane--transcription" role="region" aria-labelledby="transcription-heading">{transcript}{recognition_section}</div>
<p class="notice notice--warning page-sync-warning" data-page-sync-warning role="status" hidden></p>
</div>'''


def build_document(path: Path, entity_index: dict) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    doc_id = path.parent.name
    description = data.get("description") if isinstance(data.get("description"), dict) else {}
    fields = description.get("source_json") if isinstance(description.get("source_json"), dict) else {}
    meta = data.get("a_meta") if isinstance(data.get("a_meta"), dict) else {}
    transcript = value(data.get("transcription") or meta.get("transcription"))
    source_url = normalize_source_reference(data)["url"]
    items = entities(data)
    is_test = "test" in doc_id.lower() or "example.com" in source_url
    review = value(data.get("review_status") or meta.get("review_status") or "machine-generated")

    for item in items:
        key = (item["type"], item["label"])
        entity_index[key].append({"doc_id": doc_id, **item})

    write_csv(path.parent / "entities.csv", items)
    write_tei(path.parent / "transcription.tei.xml", doc_id, transcript, source_url)

    canonical = f"{SITE}/{doc_id}/"
    citation = f'''cff-version: 1.2.0
message: "If you use this output, cite it using these metadata."
title: "Agentic Historian output: {doc_id}"
type: dataset
authors:
  - name: "Agentic Historian"
repository-code: "{REPO}"
url: "{canonical}"
date-released: "{datetime.now().date().isoformat()}"
license: "LicenseRef-Not-Specified"
'''
    (path.parent / "CITATION.cff").write_text(citation, encoding="utf-8")

    uncertainty_rows = []
    for key, raw in fields.items():
        if isinstance(raw, dict):
            field_value = value(raw)
            uncertain = bool(raw.get("unsicher") or raw.get("uncertain"))
            note = value(raw.get("notiz") or raw.get("note"))
        else:
            field_value, uncertain, note = value(raw), False, ""
        if not field_value and not note:
            continue
        evidence = '<a href="#transcription">Transkription</a> · <a href="description.json">JSON</a>' if (path.parent / "description.json").exists() else '<a href="pipeline.json">Pipeline JSON</a>'
        uncertainty_rows.append(
            f'<tr><th scope="row">{html.escape(str(key).replace("_", " "))}</th><td>{html.escape(field_value) or "—"}</td><td>{"Unsicher" if uncertain else "Nicht markiert"}</td><td>{html.escape(note) or "—"}</td><td>{evidence}</td></tr>'
        )

    grouped = defaultdict(list)
    for item in items:
        grouped[item["type"]].append(item)
    entity_html = []
    for kind in sorted(grouped):
        links = []
        for item in grouped[kind]:
            target = slug(item["label"], kind)
            links.append(f'<li><a href="../entities/{target}/">{html.escape(item["label"])}</a>' + (f' <span class="muted">— {html.escape(item["context"])}</span>' if item["context"] else "") + '</li>')
        entity_html.append(f'<h3>{html.escape(kind)}</h3><ul>{"".join(links)}</ul>')

    source_description = value(description.get("source_description"))
    content = value(fields.get("Inhalt") or fields.get("document_type"))
    seed = content or re.sub(r"[#*_>`]", "", source_description).strip()
    interpretive = " ".join(seed.split())[:500]
    if not interpretive:
        interpretive = "Die vorhandenen Metadaten erlauben derzeit keine belastbare inhaltliche Orientierung."

    history = git_history(path)
    history_html = "".join(
        f'<li><a href="{REPO}/commit/{sha}"><code>{sha}</code></a> · <time datetime="{date}">{html.escape(date[:10])}</time> · {html.escape(subject)}</li>'
        for sha, date, subject in history
    ) or "<li>Noch keine Git-Historie verfügbar.</li>"

    qa = meta.get("qa_score")
    qa_text = f"{float(qa):.0%}" if isinstance(qa, (int, float)) else "Nicht angegeben"
    pages = value(meta.get("pages")) or "Nicht angegeben"
    state_label = "Testlauf" if is_test else "Forschungsausgabe"
    field_table = f'''<div class="table-scroll"><table><thead><tr><th>Feld</th><th>Wert</th><th>Sicherheit</th><th>Begründung</th><th>Nachweis</th></tr></thead><tbody>{''.join(uncertainty_rows) or '<tr><td colspan="5">Keine strukturierten Beschreibungsfelder verfügbar.</td></tr>'}</tbody></table></div>'''

    # Recognition viewer (progressive enhancement — issue #2)
    recognition_section = build_recognition_section(
        recognitions=data.get("recognitions", []),
        doc_id=doc_id,
        transcript=transcript,
        directory=path.parent,
    )
    package = write_package(path.parent, doc_id, data.get("recognitions", []), transcript) if data.get("recognitions") else None
    package_link = (f'<li><a href="{html.escape(package.name, quote=True)}">Vollständiges Erkennungspaket (ZIP)</a></li>'
                    if package else "")

    evidence = evidence_workspace(data, doc_id, transcript, recognition_section)

    page = frontmatter(doc_id) + f'''<nav class="breadcrumbs" aria-label="Brotkrumen"><a href="../">Alle Ausgaben</a> <span aria-hidden="true">/</span> {html.escape(doc_id)}</nav>
<header class="output-header page-section page-section--identity" data-page-section="identity">
  <p class="output-kicker">{state_label}</p><h1>{html.escape(doc_id)}</h1>
  <div class="output-status"><span>{html.escape(review)}</span><span>QA {qa_text}</span><span>{pages} Seiten</span></div>
  <p class="notice"><strong>Interpretationsstatus:</strong> Dieser Output wurde automatisch erzeugt. Nicht als Edition oder verifizierte Transkription zitieren, sofern der Status nicht ausdrücklich „human-verified“ lautet.</p>
</header>

{evidence}

<section id="orientation" class="page-section page-section--interpretation" data-page-section="orientation" aria-labelledby="orientation-heading"><h2 id="orientation-heading">Inhaltliche Orientierung</h2>
<p>{html.escape(interpretive)}</p>
<p class="muted">Automatisch aus Beschreibungsfeldern zusammengestellt; keine unabhängige historische Interpretation. <a href="#claims">Behauptungen und Unsicherheiten prüfen</a>.</p></section>

<section id="claims" class="page-section page-section--interpretation" data-page-section="claims" aria-labelledby="claims-heading"><h2 id="claims-heading">Metadaten, Provenienz und Unsicherheit</h2>{field_table}</section>

<section id="entities" class="page-section page-section--interpretation" data-page-section="entities" aria-labelledby="entities-heading"><h2 id="entities-heading">Erkannte Entitäten</h2>
{''.join(entity_html) or '<p>Keine Entitäten erkannt.</p>'}
<p><a href="entities.csv">Entitäten als CSV herunterladen</a> · <a href="../entities/">Alle Entitäten durchsuchen</a></p></section>

<section id="downloads" class="page-section page-section--administrative" data-page-section="downloads" aria-labelledby="downloads-heading"><h2 id="downloads-heading">Downloads und Nachnutzung</h2>
<ul>{package_link}<li><a href="transcription.tei.xml">TEI-XML</a></li><li><a href="entities.csv">Entitäten (CSV)</a></li><li><a href="pipeline.json">Vollständige Pipeline-Ausgabe (JSON)</a></li><li><a href="CITATION.cff">CITATION.cff</a></li></ul>
<p><strong>Rechtehinweis:</strong> Für diese Forschungsdaten ist derzeit keine Nachnutzungslizenz angegeben. Rechte am Digitalisat und an zugrunde liegenden Quellen können separat bestehen. Vor einer Weiterverwendung Rechte klären.</p></section>

<section id="citation" class="page-section page-section--administrative" data-page-section="citation" aria-labelledby="citation-heading"><h2 id="citation-heading">Zitation und stabile Adresse</h2>
<p><code>Agentic Historian. ({datetime.now().year}). Agentic Historian output: {html.escape(doc_id)} [Machine-generated dataset]. {canonical}</code></p>
<p>Stabile Seite: <a href="{canonical}">{canonical}</a> · <a href="{REPO}/commits/main/docs/{html.escape(doc_id)}/pipeline.json">Versionsverlauf auf GitHub</a></p></section>

<section id="history" class="page-section page-section--administrative" data-page-section="history" aria-labelledby="history-heading"><h2 id="history-heading">Versionsgeschichte</h2><ol>{history_html}</ol></section>
<script src="{{{{ '/assets/rec-viewer.js' | relative_url }}}}" defer></script>
<script src="{{{{ '/assets/workspace.js' | relative_url }}}}" defer></script>
<script src="{{{{ '/assets/evidence-viewer.js' | relative_url }}}}" defer></script>
<script src="{{{{ '/assets/page-sync.js' | relative_url }}}}" defer></script>
'''
    (path.parent / "index.md").write_text(page, encoding="utf-8")
    return is_test


def build_entity_pages(index: dict) -> None:
    root = DOCS / "entities"
    root.mkdir(exist_ok=True)
    summary = []
    for (kind, label), occurrences in sorted(index.items(), key=lambda x: (x[0][0], x[0][1].casefold())):
        target = slug(label, kind)
        directory = root / target
        directory.mkdir(exist_ok=True)
        rows = "".join(
            f'<tr><td><a href="../../{html.escape(item["doc_id"])}/">{html.escape(item["doc_id"])}</a></td><td>{html.escape(item["surface"])}</td><td>{html.escape(item["context"]) or "—"}</td><td>{html.escape(item["confidence"]) or "Nicht angegeben"}</td></tr>'
            for item in occurrences
        )
        external = next((item["uri"] for item in occurrences if valid_public_url(item["uri"])), "")
        external_html = f'<p>Normdatensatz: <a href="{html.escape(external, quote=True)}">{html.escape(external)}</a></p>' if external else '<p class="notice notice--warning">Nicht mit einem externen Normdatensatz verknüpft.</p>'
        page = frontmatter(label) + f'''<nav class="breadcrumbs"><a href="../">Entitäten</a> / {html.escape(label)}</nav><h1>{html.escape(label)}</h1><p><span class="entity-type">{html.escape(kind)}</span> · {len(occurrences)} Vorkommen</p>{external_html}<div class="table-scroll"><table><thead><tr><th>Ausgabe</th><th>Form</th><th>Kontext</th><th>Konfidenz</th></tr></thead><tbody>{rows}</tbody></table></div>'''
        (directory / "index.md").write_text(page, encoding="utf-8")
        summary.append(f'<tr><td><a href="{target}/">{html.escape(label)}</a></td><td>{html.escape(kind)}</td><td>{len(occurrences)}</td></tr>')
    page = frontmatter("Entitäten") + f'''<nav class="breadcrumbs"><a href="../">Alle Ausgaben</a> / Entitäten</nav><h1>Entitäten</h1><p>Automatisch erkannte Personen, Orte, Organisationen und weitere Entitätstypen. Schreibvarianten können getrennte Einträge bilden; fehlende Normdatenlinks bedeuten, dass die Identifikation nicht verifiziert wurde.</p><div class="table-scroll"><table><thead><tr><th>Entität</th><th>Typ</th><th>Vorkommen</th></tr></thead><tbody>{''.join(summary)}</tbody></table></div>'''
    (root / "index.md").write_text(page, encoding="utf-8")


def build() -> None:
    # Reset quality explanation counter so IDs are stable across runs.
    from quality import _expl_counter
    _expl_counter[0] = 0
    # Publish the progressive-enhancement asset from its single source.
    js_source = Path(__file__).with_name("rec_viewer.js")
    (DOCS / "assets" / "rec-viewer.js").write_text(
        js_source.read_text(encoding="utf-8"), encoding="utf-8")
    workspace_source = Path(__file__).with_name("workspace.js")
    (DOCS / "assets" / "workspace.js").write_text(
        workspace_source.read_text(encoding="utf-8"), encoding="utf-8")
    evidence_viewer_source = Path(__file__).with_name("evidence_viewer.js")
    (DOCS / "assets" / "evidence-viewer.js").write_text(
        evidence_viewer_source.read_text(encoding="utf-8"), encoding="utf-8")
    page_sync_source = Path(__file__).with_name("page_sync.js")
    (DOCS / "assets" / "page-sync.js").write_text(
        page_sync_source.read_text(encoding="utf-8"), encoding="utf-8")
    entity_index = defaultdict(list)
    tests = []
    for path in sorted(DOCS.glob("*/pipeline.json")):
        if build_document(path, entity_index):
            tests.append(path.parent.name)
    build_entity_pages(entity_index)
    test_root = DOCS / "tests"
    test_root.mkdir(exist_ok=True)
    links = "".join(f'<li><a href="../{html.escape(doc_id)}/">{html.escape(doc_id)}</a></li>' for doc_id in tests)
    (test_root / "index.md").write_text(frontmatter("Testläufe") + f'<nav class="breadcrumbs"><a href="../">Alle Ausgaben</a> / Testläufe</nav><h1>Testläufe</h1><p>Diese Einträge dienen der technischen Prüfung und sind keine Forschungsresultate.</p><ul>{links or "<li>Keine Testläufe.</li>"}</ul>', encoding="utf-8")
    print(f"Generated {len(list(DOCS.glob('*/pipeline.json')))} document pages and {len(entity_index)} entity pages")


if __name__ == "__main__":
    build()
