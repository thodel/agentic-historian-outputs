---
layout: default
title: Katalog
---

<link rel="stylesheet" href="{{ '/assets/catalogue.css' | relative_url }}">

<div class="catalogue-intro">
  <p class="catalogue-kicker">Forschungsdaten · automatisch erzeugt</p>
  <h1>Verarbeitete Dokumente</h1>
  <p>Transkriptionen, Quellenbeschreibungen und erkannte Entitäten. Die neuesten Ausgaben stehen zuerst. Automatisch erzeugte Angaben sind Forschungsangebote und müssen am Original überprüft werden.</p>
  <details class="quality-explanation" id="catalogue-quality-explainer">
    <summary>Qualitätsmetriken in diesem Katalog</summary>
    <p>Je nach Datenlage zeigt eine Ausgabe bis zu drei Qualitätsmetriken:</p>
    <dl>
      <div><dt>Ø Konfidenz</dt><dd>Durchschnittliche Engine-Konfidenz aller Erkennungskandidaten (niedrig = unsicherer). Nicht zwischen Engines vergleichbar.</dd></div>
      <div><dt>CER / WER</dt><dd>Character/Word Error Rate gegen eine bekannte Referenz (niedrig = weniger Fehler). Nur vorhanden wenn Referenz verfügbar.</dd></div>
      <div><dt>Problematische Kandidaten</dt><dd>Anzahl der Kandidaten, die fehlgeschlagen, leer oder degeneriert sind.</dd></div>
    </dl>
  </details>
  <p><a href="entities/">Entitäten durchsuchen</a> · <a href="tests/">Testläufe separat anzeigen</a></p>
  <p class="catalogue-summary" id="catalogue-count"><strong>0</strong> Ausgaben · <span class="superseded-count">0 ersetzt</span> · 0 Testläufe</p>
</div>

<form class="catalogue-tools" role="search" aria-label="Ausgaben durchsuchen" onsubmit="return false">
  <div class="catalogue-search">
    <label for="catalogue-search">Suchen</label>
    <input id="catalogue-search" type="search" placeholder="Signatur, Sprache, Schrift oder Text …" autocomplete="off">
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
  <details class="catalogue-advanced">
    <summary>Weitere Filter (11)</summary>
    <div class="catalogue-advanced__grid">
    <div>
      <label for="catalogue-review">Redaktionsstatus</label>
      <select id="catalogue-review">
        <option value="all">Alle Redaktionsstände</option>
        <option value="human-verified">Menschlich geprüft</option>
        <option value="machine-generated">Maschinell erzeugt</option>
        <option value="in-review">In Prüfung</option>
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
        <label for="catalogue-filter">Anzeigen</label>
        <select id="catalogue-filter">
          <option value="all">Alle Einträge</option>
          <option value="output">Nur Ausgaben</option>
          <option value="test">Nur Testläufe</option>
        </select>
      </div>
      <div><label for="catalogue-language">Sprache</label><select id="catalogue-language"><option value="all">Alle Sprachen</option></select></div>
      <div><label for="catalogue-script">Schrift</label><select id="catalogue-script"><option value="all">Alle Schriften</option></select></div>
      <div><label for="catalogue-engine">Erkennungsengine</label><select id="catalogue-engine"><option value="all">Alle Engines</option></select></div>
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
        <label for="catalogue-superseded">Ersetzte Einträge</label>
        <select id="catalogue-superseded"><option value="hide">Verbergen</option><option value="show">Anzeigen</option></select>
      </div>
      <div>
        <label for="catalogue-entity-type">Entitätstyp</label>
        <select id="catalogue-entity-type">
          <option value="all">Alle Entitätstypen</option><option value="PERSON">Personen</option><option value="PLACE">Orte</option><option value="ORG">Organisationen</option><option value="DATE">Datumsangaben</option><option value="EVENT">Ereignisse</option><option value="ROLE">Rollen</option><option value="TITLE">Titel</option><option value="SOCIAL_GROUP">Sozialgruppe</option>
        </select>
      </div>
      <div>
        <label for="catalogue-completeness">Vollständigkeit</label>
        <select id="catalogue-completeness"><option value="all">Alle Stufen</option><option value="vollstaendig">Vollständig</option><option value="teilweise">Teilweise</option><option value="minimal">Minimal</option></select>
      </div>
    </div>  </details>
</form>

<p id="catalogue-active-filters" class="catalogue-active-filters">Keine Filter aktiv.</p>
<p id="catalogue-status" class="catalogue-status" role="status" aria-live="polite">0 Einträge, nach Erstellungsdatum absteigend sortiert.</p>
<p id="catalogue-empty" class="catalogue-empty" role="status" hidden>Keine Einträge entsprechen den aktiven Filtern. Ändern Sie die Filter oder setzen Sie sie zurück.</p>

<div id="catalogue-list" class="catalogue-list" data-enhanced="false" data-total-records="0" data-shown-records="0">

</div>
<section class="catalogue-no-outputs" role="status" aria-labelledby="catalogue-no-outputs-heading">
  <h2 id="catalogue-no-outputs-heading">Zurzeit keine veröffentlichten Ausgaben</h2>
  <p>Alle bisher veröffentlichten Ausgaben wurden zurückgezogen: ihre Eingaben
  waren Testeingaben und keine Korpora, die dieses Projekt editieren wollte.
  Die Begründung steht je Ausgabe auf ihrer eigenen Seite, die weiterhin
  erreichbar bleibt und sagt, dass sie nicht zitiert werden darf.</p>
  <p>Die maschinellen Datensätze sind nicht gelöscht, sondern unter
  <code>data/withdrawn/</code> im Repository archiviert. Was gemessen wurde,
  steht unverändert unter <a href="forschung.html">Forschung</a>; wie
  gearbeitet wird, unter <a href="methodology.html">Methode</a>.</p>
</section>

<noscript><p>Die Suche benötigt JavaScript. Alle Einträge bleiben ohne JavaScript sichtbar und sind bereits nach Erstellungsdatum sortiert.</p></noscript>
<script src="{{ '/assets/catalogue.js' | relative_url }}" defer></script>
<script src="{{ '/assets/quality-explain.js' | relative_url }}" defer></script>
