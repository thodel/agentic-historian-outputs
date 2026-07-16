---
layout: default
title: "order-ens"
---

<link rel="stylesheet" href="{{ '/assets/output.css' | relative_url }}">

<nav class="breadcrumbs" aria-label="Brotkrumen"><a href="../">Alle Ausgaben</a> <span aria-hidden="true">/</span> order-ens</nav>
<header class="output-header">
  <p class="output-kicker">Forschungsausgabe</p><h1>order-ens</h1>
  <div class="output-status"><span>machine-generated</span><span>QA 90%</span><span>2 Seiten</span></div>
  <p class="notice"><strong>Interpretationsstatus:</strong> Dieser Output wurde automatisch erzeugt. Nicht als Edition oder verifizierte Transkription zitieren, sofern der Status nicht ausdrücklich „human-verified“ lautet.</p>
</header>

<section aria-labelledby="source-heading"><h2 id="source-heading">Quelle und Digitalisat</h2>
<div class="notice notice--warning"><strong>Kein öffentliches Digitalisat verknüpft.</strong> Ein lokaler Verarbeitungspfad ist kein zitierbarer Quellenbeleg. Ergänzen Sie <code>source_url</code> oder <code>iiif_manifest</code> in der Pipeline-Ausgabe.</div></section>

<section aria-labelledby="orientation-heading"><h2 id="orientation-heading">Inhaltliche Orientierung</h2>
<p>x</p>
<p class="muted">Automatisch aus Beschreibungsfeldern zusammengestellt; keine unabhängige historische Interpretation. <a href="#claims">Behauptungen und Unsicherheiten prüfen</a>.</p></section>

<section id="claims" aria-labelledby="claims-heading"><h2 id="claims-heading">Metadaten, Provenienz und Unsicherheit</h2><div class="table-scroll"><table><thead><tr><th>Feld</th><th>Wert</th><th>Sicherheit</th><th>Begründung</th><th>Nachweis</th></tr></thead><tbody><tr><td colspan="5">Keine strukturierten Beschreibungsfelder verfügbar.</td></tr></tbody></table></div></section>

<section aria-labelledby="entities-heading"><h2 id="entities-heading">Erkannte Entitäten</h2>
<p>Keine Entitäten erkannt.</p>
<p><a href="entities.csv">Entitäten als CSV herunterladen</a> · <a href="../entities/">Alle Entitäten durchsuchen</a></p></section>

<section id="transcription" aria-labelledby="transcription-heading"><h2 id="transcription-heading">Transkription</h2>
<pre class="transcription" tabindex="0"><code>--- p1.jpg ---
gut lesbar hier

--- p2.jpg ---
gut lesbar hier</code></pre></section>

<section id="recognitions" aria-labelledby="rec-heading"><h2 id="rec-heading">Erkennungsversionen</h2><p class="rec-intro">Es liegen mehrere Erkennungsversionen vor. Wählen Sie eine Version zum Vergleichen; die ausgewählte Transkription bleibt ohne JavaScript sichtbar.</p><div class="rec-viewer" data-doc-id="order-ens"><div class="rec-tabs" role="tablist" aria-label="Erkennungsversionen"><input type="radio" name="rec-order-ens" id="tab-cand-kraken-k0" value="cand-kraken-k0" checked class="rec-tab-input"><label for="tab-cand-kraken-k0" class="rec-tab-label">📖 Kraken OCR ⮕</label></div><div class="rec-panels"><div class="rec-panel" id="cand-kraken-k0"><div class="rec-summary">📖 <strong>Kraken OCR</strong> <span class="rec-badge">✅ 80%</span> <span class="rec-model">k0</span> · 15 Zeichen · <a href="recognitions/kraken-k0.txt" download class="rec-dl">⬇ Text herunterladen</a></div><pre class="rec-text">gut lesbar hier</pre><a href="recognitions/kraken-k0.txt" download class="rec-dl">⬇ Text herunterladen</a></div></div></div></section><section aria-labelledby="downloads-heading"><h2 id="downloads-heading">Downloads und Nachnutzung</h2>
<ul><li><a href="transcription.tei.xml">TEI-XML</a></li><li><a href="entities.csv">Entitäten (CSV)</a></li><li><a href="pipeline.json">Vollständige Pipeline-Ausgabe (JSON)</a></li><li><a href="CITATION.cff">CITATION.cff</a></li></ul>
<p><strong>Rechtehinweis:</strong> Für diese Forschungsdaten ist derzeit keine Nachnutzungslizenz angegeben. Rechte am Digitalisat und an zugrunde liegenden Quellen können separat bestehen. Vor einer Weiterverwendung Rechte klären.</p></section>

<section aria-labelledby="citation-heading"><h2 id="citation-heading">Zitation und stabile Adresse</h2>
<p><code>Agentic Historian. (2026). Agentic Historian output: order-ens [Machine-generated dataset]. https://thodel.github.io/agentic-historian-outputs/order-ens/</code></p>
<p>Stabile Seite: <a href="https://thodel.github.io/agentic-historian-outputs/order-ens/">https://thodel.github.io/agentic-historian-outputs/order-ens/</a> · <a href="https://github.com/thodel/agentic-historian-outputs/commits/main/docs/order-ens/pipeline.json">Versionsverlauf auf GitHub</a></p></section>

<section aria-labelledby="history-heading"><h2 id="history-heading">Versionsgeschichte</h2><ol><li><a href="https://github.com/thodel/agentic-historian-outputs/commit/570ccc2"><code>570ccc2</code></a> · <time datetime="2026-07-15T19:17:36+02:00">2026-07-15</time> · Publish order-ens</li></ol></section>
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

