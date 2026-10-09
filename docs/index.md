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
  <p class="catalogue-summary" id="catalogue-count"><strong>1</strong> Ausgaben · <span class="superseded-count">0 ersetzt</span> · 0 Testläufe</p>
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
<p id="catalogue-status" class="catalogue-status" role="status" aria-live="polite">1 Einträge, nach Erstellungsdatum absteigend sortiert.</p>
<p id="catalogue-empty" class="catalogue-empty" role="status" hidden>Keine Einträge entsprechen den aktiven Filtern. Ändern Sie die Filter oder setzen Sie sie zurück.</p>

<div id="catalogue-list" class="catalogue-list" data-enhanced="false" data-total-records="1" data-shown-records="1">
<article class="catalogue-card" data-document-id="missiven" data-created="2026-10-09T21:00:00+02:00" data-kind="output" data-language="deutsch (mittelhochdeutsch/frühneuhochdeutsch), alemannischer dialektraum" data-script="gotische kursive (cursiva), schwarze tinte" data-search="missiven missive / brief  15. jahrhundert (explizite datierung im text: &#x27;anno ... vier hundert&#x27;, montag nach sankt margareta) deutsch (mittelhochdeutsch/frühneuhochdeutsch), alemannischer dialektraum gotische kursive (cursiva), schwarze tinte missive / brief stadtasg_missive_49_97.jpg euer fründlich willig dienst ~xoran~ lieb vnd güten fründ vnd güt furbrüder ertz offencell ~vnd~ appocelle enfer lantman sine sae in rane gschriben über " data-superseded="false" data-recognition-provenance="current" data-recognition-total="20" data-recognition-successful="4" data-recognition-failed="16" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="kraken,trocr,vlm" data-recognition-models="9" data-recognition-pages="2" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="DATE,ORG,PERSON,PLACE,ROLE" data-completeness="teilweise">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-10-09T21:00:00+02:00">09.10.2026, 21:00</time></p>
      <h2><a href="missiven/">Missive / Brief</a></h2>
      <p class="catalogue-id">Dokument-ID <code>missiven</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span><span class="catalogue-badge catalogue-badge--quality-failed">16 problematische Kandidaten</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert (explizite Datierung im Text: &#x27;Anno ... vier hundert&#x27;, Montag nach Sankt Margareta)</dd></div><div><dt>Seiten</dt><dd>2</dd></div><div><dt>Entitäten</dt><dd>31</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="missiven/" aria-label="Dokument öffnen: Missive / Brief">Dokument öffnen <span aria-hidden="true">→</span></a><a class="catalogue-action catalogue-action--secondary" href="missiven/?rec=selected#recognition-selected" aria-label="Erkennungen ansehen: Missive / Brief">Erkennungen ansehen</a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Dokumenttyp</dt><dd>Missive / Brief</dd></div><div><dt>Sprache</dt><dd>Deutsch (Mittelhochdeutsch/Frühneuhochdeutsch), alemannischer Dialektraum</dd></div><div><dt>Schrift</dt><dd>gotische Kursive (Cursiva), schwarze Tinte</dd></div><div><dt>Kandidaten</dt><dd>4 erfolgreich / 20 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">16 von 20 Kandidaten problematisch</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <ul class="catalogue-engines"><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>kraken</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>trocr</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>vlm</li></ul>
        <p class="catalogue-warning"><span aria-hidden="true">⚠</span> 16 fehlgeschlagene Erkennungsversuche</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">StadtASG_Missive_49_97.JPG Euer fründlich willig dienst ~xoran~ lieb vnd güten fründ vnd güt furbrüder Ertz offencell ~vnd~ appocelle Enfer lantman Sine Sae in Rane gschriben über …</p>
    </div>
  </details>
  </div>
  </div>
</article>
</div>


<noscript><p>Die Suche benötigt JavaScript. Alle Einträge bleiben ohne JavaScript sichtbar und sind bereits nach Erstellungsdatum sortiert.</p></noscript>
<script src="{{ '/assets/catalogue.js' | relative_url }}" defer></script>
<script src="{{ '/assets/quality-explain.js' | relative_url }}" defer></script>
