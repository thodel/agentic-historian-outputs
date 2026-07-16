---
layout: default
title: "order-001-group"
---

<link rel="stylesheet" href="{{ '/assets/output.css' | relative_url }}">

<nav class="breadcrumbs" aria-label="Brotkrumen"><a href="../">Alle Ausgaben</a> <span aria-hidden="true">/</span> order-001-group</nav>
<header class="output-header">
  <p class="output-kicker">Forschungsausgabe</p><h1>order-001-group</h1>
  <div class="output-status"><span>machine-generated</span><span>QA 90%</span><span>2 Seiten</span></div>
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
<pre class="transcription" tabindex="0"><code>--- page_1.jpg ---
page page_1.jpg

--- page_2.jpg ---
page page_2.jpg</code></pre></section>

<section aria-labelledby="downloads-heading"><h2 id="downloads-heading">Downloads und Nachnutzung</h2>
<ul><li><a href="transcription.tei.xml">TEI-XML</a></li><li><a href="entities.csv">Entitäten (CSV)</a></li><li><a href="pipeline.json">Vollständige Pipeline-Ausgabe (JSON)</a></li><li><a href="CITATION.cff">CITATION.cff</a></li></ul>
<p><strong>Rechtehinweis:</strong> Für diese Forschungsdaten ist derzeit keine Nachnutzungslizenz angegeben. Rechte am Digitalisat und an zugrunde liegenden Quellen können separat bestehen. Vor einer Weiterverwendung Rechte klären.</p></section>

<section aria-labelledby="citation-heading"><h2 id="citation-heading">Zitation und stabile Adresse</h2>
<p><code>Agentic Historian. (2026). Agentic Historian output: order-001-group [Machine-generated dataset]. https://thodel.github.io/agentic-historian-outputs/order-001-group/</code></p>
<p>Stabile Seite: <a href="https://thodel.github.io/agentic-historian-outputs/order-001-group/">https://thodel.github.io/agentic-historian-outputs/order-001-group/</a> · <a href="https://github.com/thodel/agentic-historian-outputs/commits/main/docs/order-001-group/pipeline.json">Versionsverlauf auf GitHub</a></p></section>

<section aria-labelledby="history-heading"><h2 id="history-heading">Versionsgeschichte</h2><ol><li><a href="https://github.com/thodel/agentic-historian-outputs/commit/2397cba"><code>2397cba</code></a> · <time datetime="2026-07-08T12:36:17+02:00">2026-07-08</time> · Publish order-001-group</li><li><a href="https://github.com/thodel/agentic-historian-outputs/commit/202031b"><code>202031b</code></a> · <time datetime="2026-07-08T09:03:38+02:00">2026-07-08</time> · Publish order-001-group</li></ol></section>
<script>
// Recognition viewer: progressive enhancement
document.querySelectorAll('.rec-viewer').forEach(function(viewer) {
  viewer.classList.add('js');
  var panels = viewer.querySelectorAll('.rec-panel');
  function showPanel(id) {
    panels.forEach(function(p) {
      p.classList.toggle('is-active', p.id === id);
    });
  }
  var checked = viewer.querySelector('.rec-tab-input:checked');
  if (checked) { showPanel(checked.value); }
  viewer.querySelectorAll('.rec-tab-input').forEach(function(inp) {
    inp.addEventListener('change', function() { showPanel(inp.value); });
  });
});

</script>

