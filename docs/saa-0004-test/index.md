---
layout: default
title: "saa-0004-test"
---

<link rel="stylesheet" href="{{ '/assets/output.css' | relative_url }}">

<nav class="breadcrumbs" aria-label="Brotkrumen"><a href="../">Alle Ausgaben</a> <span aria-hidden="true">/</span> saa-0004-test</nav>
<header class="output-header">
  <p class="output-kicker">Testlauf</p><h1>saa-0004-test</h1>
  <div class="output-status"><span>machine-generated</span><span>QA 85%</span><span>Nicht angegeben Seiten</span></div>
  <p class="notice"><strong>Interpretationsstatus:</strong> Dieser Output wurde automatisch erzeugt. Nicht als Edition oder verifizierte Transkription zitieren, sofern der Status nicht ausdrücklich „human-verified“ lautet.</p>
</header>

<section aria-labelledby="source-heading"><h2 id="source-heading">Quelle und Digitalisat</h2>
<div class="notice notice--warning"><strong>Kein öffentliches Digitalisat verknüpft.</strong> Ein lokaler Verarbeitungspfad ist kein zitierbarer Quellenbeleg. Ergänzen Sie <code>source_url</code> oder <code>iiif_manifest</code> in der Pipeline-Ausgabe.</div></section>

<section aria-labelledby="orientation-heading"><h2 id="orientation-heading">Inhaltliche Orientierung</h2>
<p>Gerichtsbrief</p>
<p class="muted">Automatisch aus Beschreibungsfeldern zusammengestellt; keine unabhängige historische Interpretation. <a href="#claims">Behauptungen und Unsicherheiten prüfen</a>.</p></section>

<section id="claims" aria-labelledby="claims-heading"><h2 id="claims-heading">Metadaten, Provenienz und Unsicherheit</h2><div class="table-scroll"><table><thead><tr><th>Feld</th><th>Wert</th><th>Sicherheit</th><th>Begründung</th><th>Nachweis</th></tr></thead><tbody><tr><th scope="row">script</th><td>Kurrent</td><td>Nicht markiert</td><td>—</td><td><a href="pipeline.json">Pipeline JSON</a></td></tr><tr><th scope="row">lang</th><td>de</td><td>Nicht markiert</td><td>—</td><td><a href="pipeline.json">Pipeline JSON</a></td></tr><tr><th scope="row">century</th><td>15</td><td>Nicht markiert</td><td>—</td><td><a href="pipeline.json">Pipeline JSON</a></td></tr><tr><th scope="row">document type</th><td>Gerichtsbrief</td><td>Nicht markiert</td><td>—</td><td><a href="pipeline.json">Pipeline JSON</a></td></tr></tbody></table></div></section>

<section aria-labelledby="entities-heading"><h2 id="entities-heading">Erkannte Entitäten</h2>
<h3>PERSON</h3><ul><li><a href="../entities/hans-von-bern-cee70931/">Hans von Bern</a></li></ul>
<p><a href="entities.csv">Entitäten als CSV herunterladen</a> · <a href="../entities/">Alle Entitäten durchsuchen</a></p></section>

<section id="transcription" aria-labelledby="transcription-heading"><h2 id="transcription-heading">Transkription</h2>
<pre class="transcription" tabindex="0"><code>Hans von Bern tuend kund…</code></pre></section>

<section aria-labelledby="downloads-heading"><h2 id="downloads-heading">Downloads und Nachnutzung</h2>
<ul><li><a href="transcription.tei.xml">TEI-XML</a></li><li><a href="entities.csv">Entitäten (CSV)</a></li><li><a href="pipeline.json">Vollständige Pipeline-Ausgabe (JSON)</a></li><li><a href="CITATION.cff">CITATION.cff</a></li></ul>
<p><strong>Rechtehinweis:</strong> Für diese Forschungsdaten ist derzeit keine Nachnutzungslizenz angegeben. Rechte am Digitalisat und an zugrunde liegenden Quellen können separat bestehen. Vor einer Weiterverwendung Rechte klären.</p></section>

<section aria-labelledby="citation-heading"><h2 id="citation-heading">Zitation und stabile Adresse</h2>
<p><code>Agentic Historian. (2026). Agentic Historian output: saa-0004-test [Machine-generated dataset]. https://thodel.github.io/agentic-historian-outputs/saa-0004-test/</code></p>
<p>Stabile Seite: <a href="https://thodel.github.io/agentic-historian-outputs/saa-0004-test/">https://thodel.github.io/agentic-historian-outputs/saa-0004-test/</a> · <a href="https://github.com/thodel/agentic-historian-outputs/commits/main/docs/saa-0004-test/pipeline.json">Versionsverlauf auf GitHub</a></p></section>

<section aria-labelledby="history-heading"><h2 id="history-heading">Versionsgeschichte</h2><ol><li><a href="https://github.com/thodel/agentic-historian-outputs/commit/f3af584"><code>f3af584</code></a> · <time datetime="2026-07-08T12:44:41+02:00">2026-07-08</time> · Publish saa-0004-test</li><li><a href="https://github.com/thodel/agentic-historian-outputs/commit/2937442"><code>2937442</code></a> · <time datetime="2026-07-08T09:05:34+02:00">2026-07-08</time> · Publish saa-0004-test</li><li><a href="https://github.com/thodel/agentic-historian-outputs/commit/0426d24"><code>0426d24</code></a> · <time datetime="2026-07-08T09:04:19+02:00">2026-07-08</time> · Publish saa-0004-test</li><li><a href="https://github.com/thodel/agentic-historian-outputs/commit/578f6a7"><code>578f6a7</code></a> · <time datetime="2026-07-08T09:03:31+02:00">2026-07-08</time> · Publish saa-0004-test</li></ol></section>
// Recognition viewer — progressive enhancement (issues #2, #3)
// - Tab switching without navigation
// - URL persistence: ?rec=<candidate-id> restores selection
// - Browser back/forward support
// - Keyboard accessible
document.querySelectorAll('.rec-viewer').forEach(function(viewer) {
  var docId    = viewer.dataset.docId || '';
  var panels   = Array.from(viewer.querySelectorAll('.rec-panel'));
  var inputs   = Array.from(viewer.querySelectorAll('.rec-tab-input'));
  var paramKey = 'rec';   // URL query parameter name

  // ── helpers ──────────────────────────────────────────────────────────────
  function getCandidateId() {
    // 1. URL param takes precedence
    var val = new URLSearchParams(window.location.search).get(paramKey);
    if (val) { return val; }
    // 2. currently checked radio
    var checked = viewer.querySelector('.rec-tab-input:checked');
    return checked ? checked.value : (inputs[0] ? inputs[0].value : null);
  }

  function activate(id) {
    panels.forEach(function(p) {
      p.classList.toggle('is-active', p.id === id);
    });
    inputs.forEach(function(inp) {
      inp.checked = inp.value === id;
    });
  }

  function persist(id) {
    // Update URL without navigation
    var url = new URL(window.location.href);
    url.searchParams.set(paramKey, id);
    history.replaceState({}, '', url.toString());
  }

  // ── init ─────────────────────────────────────────────────────────────────
  viewer.classList.add('js');
  var initial = getCandidateId();
  if (initial) { activate(initial); }

  // ── keyboard / mouse selection ───────────────────────────────────────────
  inputs.forEach(function(inp) {
    inp.addEventListener('change', function() {
      activate(inp.value);
      persist(inp.value);
    });
  });
});


