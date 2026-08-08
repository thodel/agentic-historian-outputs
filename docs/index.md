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
  <p class="catalogue-summary" id="catalogue-count"><strong>7</strong> Ausgaben · <span class="superseded-count">2 ersetzt</span> · 5 Testläufe</p>
</div>

<form class="catalogue-tools" role="search" aria-label="Ausgaben durchsuchen" onsubmit="return false">
  <div class="catalogue-search">
    <label for="catalogue-search">Suchen</label>
    <input id="catalogue-search" type="search" placeholder="Signatur, Sprache, Schrift oder Text …" autocomplete="off">
  </div>
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
    <summary>Weitere Filter</summary>
    <div class="catalogue-advanced__grid">
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
    </div>
  </details>
</form>

<p id="catalogue-active-filters" class="catalogue-active-filters">Keine Filter aktiv.</p>
<p id="catalogue-status" class="catalogue-status" role="status" aria-live="polite">14 Einträge, nach Erstellungsdatum absteigend sortiert.</p>
<p id="catalogue-empty" class="catalogue-empty" role="status" hidden>Keine Einträge entsprechen den aktiven Filtern. Ändern Sie die Filter oder setzen Sie sie zurück.</p>

<div id="catalogue-list" class="catalogue-list" data-enhanced="false">
<article class="catalogue-card" data-document-id="koenige" data-created="2026-07-18T22:58:42+02:00" data-kind="output" data-language="mittelhochdeutsch (oder frühneuhochdeutsch), dialekt: alemannisch oder ostschweizerisch" data-script="gothische kurrentschrift, braune tinte, schriftgrosse ca. 6 mm, abkürzungen wie &#x27;de&#x27;, &#x27;zu&#x27;, &#x27;in&#x27;, &#x27;der&#x27;, &#x27;daz&#x27;, &#x27;v&#x27; statt &#x27;w&#x27;, rasuren und korrekturen im text, keine farbige rubrizierung oder initialen" data-search="koenige drei urkunden · 1518  1518 mittelhochdeutsch (oder frühneuhochdeutsch), dialekt: alemannisch oder ostschweizerisch gothische kurrentschrift, braune tinte, schriftgroße ca. 6 mm, abkürzungen wie &#x27;de&#x27;, &#x27;zu&#x27;, &#x27;in&#x27;, &#x27;der&#x27;, &#x27;daz&#x27;, &#x27;v&#x27; statt &#x27;w&#x27;, rasuren und korrekturen im text, keine farbige rubrizierung oder initialen drei urkunden u-17_0057_r.jpg pmioe prnpma mm sim petirv s t diaridhy orea e qoicenouie qu. re us h sparer stmir mmer ene igres d e sape z crios o tre e llm rso eeieng emis onsdsem i son li e" data-superseded="false" data-recognition-provenance="current" data-recognition-total="33" data-recognition-successful="24" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="9" data-recognition-engines="kraken,trocr,vlm" data-recognition-models="10" data-recognition-pages="3" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="CARE_ACTION,ORG,PERSON,PLACE,ROLE" data-completeness="teilweise">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-18T22:58:42+02:00">18.07.2026, 22:58</time></p>
      <h2><a href="koenige/">Drei Urkunden · 1518</a></h2>
      <p class="catalogue-id">Dokument-ID <code>koenige</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span><span class="catalogue-badge catalogue-badge--quality-failed">9 problematische Kandidaten</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Datierung</dt><dd>1518</dd></div><div><dt>Seiten</dt><dd>3</dd></div><div><dt>Entitäten</dt><dd>19</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="koenige/" aria-label="Dokument öffnen: Drei Urkunden · 1518">Dokument öffnen <span aria-hidden="true">→</span></a><a class="catalogue-action catalogue-action--secondary" href="koenige/?rec=selected#recognition-selected" aria-label="Erkennungen ansehen: Drei Urkunden · 1518">Erkennungen ansehen</a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Dokumenttyp</dt><dd>Drei Urkunden</dd></div><div><dt>Sprache</dt><dd>Mittelhochdeutsch (oder Frühneuhochdeutsch), Dialekt: alemannisch oder ostschweizerisch</dd></div><div><dt>Schrift</dt><dd>Gothische Kurrentschrift, braune Tinte, Schriftgroße ca. 6 mm, Abkürzungen wie &#x27;de&#x27;, &#x27;zu&#x27;, &#x27;in&#x27;, &#x27;der&#x27;, &#x27;daz&#x27;, &#x27;v&#x27; statt &#x27;w&#x27;, Rasuren und Korrekturen im Text, keine farbige Rubrizierung oder Initialen</dd></div><div><dt>Kandidaten</dt><dd>24 erfolgreich / 33 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">9 von 33 Kandidaten problematisch</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <ul class="catalogue-engines"><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>kraken</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>trocr</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>vlm</li></ul>
        <p class="catalogue-warning"><span aria-hidden="true">⚠</span> 9 degenerierte Ergebnisse</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">U-17_0057_r.jpg PMIoe PrNPMA MM SIM PETIRV s t diaridhy orea e qoicenouie qu. re us h sparer stmir mmer ene igres d e sape z crios o tre e llm rso eeieng emis onsdsem i son li e…</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="bat" data-created="2026-07-15T21:19:05+02:00" data-kind="output" data-language="deutsch (mittelhochdeutsche und mitteldeutsche konstruktionen, alemannischer dialektraum)" data-script="gotische kurrentschrift, schwarz, zeilenhöhe ca. 4,5 mm" data-search="bat verwaltungsdokument · 15. jahrhundert (unsicher)  15. jahrhundert (unsicher) deutsch (mittelhochdeutsche und mitteldeutsche konstruktionen, alemannischer dialektraum) gotische kurrentschrift, schwarz, zeilenhöhe ca. 4,5 mm verwaltungsdokument bat_663_r_00050.jpg aimien undectetngen willegen dicust be uor lieden gnediuen hacrẽ si ucq al zut uon nat be- rent uñ ouch deñ urern lieben quedien herren ich blahen eeusthlicq" data-superseded="false" data-recognition-provenance="current" data-recognition-total="10" data-recognition-successful="6" data-recognition-failed="1" data-recognition-empty="0" data-recognition-degenerate="3" data-recognition-engines="kraken,trocr,vlm" data-recognition-models="10" data-recognition-pages="1" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="true" data-entity-types="DATE,ORG,PERSON,PLACE,SOCIAL_GROUP" data-completeness="teilweise">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-15T21:19:05+02:00">15.07.2026, 21:19</time></p>
      <h2><a href="bat/">Verwaltungsdokument · 15. Jahrhundert (unsicher)</a></h2>
      <p class="catalogue-id">Dokument-ID <code>bat</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span><span class="catalogue-badge catalogue-badge--quality-failed">4 problematische Kandidaten</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert (unsicher)</dd></div><div><dt>Seiten</dt><dd>1</dd></div><div><dt>Entitäten</dt><dd>12</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="bat/" aria-label="Dokument öffnen: Verwaltungsdokument · 15. Jahrhundert (unsicher)">Dokument öffnen <span aria-hidden="true">→</span></a><a class="catalogue-action catalogue-action--secondary" href="bat/?cmp=vlm-internvl3-8b-instruct:kraken-kraken-catmus-medieval#recognitions" aria-label="Modelle vergleichen: Verwaltungsdokument · 15. Jahrhundert (unsicher)">Modelle vergleichen</a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Dokumenttyp</dt><dd>Verwaltungsdokument</dd></div><div><dt>Sprache</dt><dd>Deutsch (mittelhochdeutsche und mitteldeutsche Konstruktionen, alemannischer Dialektraum)</dd></div><div><dt>Schrift</dt><dd>Gotische Kurrentschrift, schwarz, Zeilenhöhe ca. 4,5 mm</dd></div><div><dt>Kandidaten</dt><dd>6 erfolgreich / 10 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">4 von 10 Kandidaten problematisch</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <ul class="catalogue-engines"><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>kraken</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>trocr</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>vlm</li></ul>
        <p class="catalogue-warning"><span aria-hidden="true">⚠</span> 1 fehlgeschlagener Erkennungsversuch</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> 3 degenerierte Ergebnisse</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">BAT_663_r_00050.jpg Aimien undectetngen willegen dicust be uor lieden gnediuen hacrẽ si ucq al zut uon nat be- rent uñ ouch deñ urern lieben quedien herren ich blahen eeusthlicq…</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="order-ens" data-created="2026-07-15T19:17:36+02:00" data-kind="output" data-language="" data-script="" data-search="order-ens order-ens      p1.jpg gut lesbar hier p2.jpg gut lesbar hier" data-superseded="false" data-recognition-provenance="current" data-recognition-total="1" data-recognition-successful="1" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="kraken" data-recognition-models="1" data-recognition-pages="2" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="" data-completeness="minimal">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-15T19:17:36+02:00">15.07.2026, 19:17</time></p>
      <h2><a href="order-ens/">order-ens</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Seiten</dt><dd>2</dd></div><div><dt>Entitäten</dt><dd>0</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="order-ens/" aria-label="Dokument öffnen: order-ens">Dokument öffnen <span aria-hidden="true">→</span></a><a class="catalogue-action catalogue-action--secondary" href="order-ens/?rec=selected#recognition-selected" aria-label="Erkennungen ansehen: order-ens">Erkennungen ansehen</a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Kandidaten</dt><dd>1 erfolgreich / 1 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">Keine bekannten Erkennungsprobleme</p></div>
      </div>

      <div class="catalogue-detail-badges" aria-label="Qualitätsmetriken"><span class="catalogue-badge catalogue-badge--quality-confidence">Ø Konfidenz 80%</span></div>
      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <ul class="catalogue-engines"><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>kraken</li></ul>
        <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">p1.jpg gut lesbar hier p2.jpg gut lesbar hier…</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="u-17__" data-created="2026-07-15T16:49:41+02:00" data-kind="output" data-language="" data-script="" data-search="u-17__ staatsarchiv aargau, saa 428 e-codices: staatsarchiv aargau, saa 428     e-codices_saa-0428_015v_large.jpg seite 1 modios reina cum prato sive uysta ottovillingen dequibz hre debet forum pccenum in horum emdenaam sigilla no lsta videlicz. alhile er conu" data-superseded="true" data-recognition-provenance="current" data-recognition-total="13" data-recognition-successful="11" data-recognition-failed="2" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="kraken,trocr,vlm" data-recognition-models="5" data-recognition-pages="4" data-source-type="landing_page" data-source-available="true" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="CARE_ACTION,DATE,ORG,PERSON,PLACE,ROLE,SOCIAL_GROUP,TITLE" data-completeness="vollstaendig">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--image"><img src="https://www.e-codices.unifr.ch/loris/saa/saa-0428/saa-0428_015v.jp2/full/1200,/0/default.jpg" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer"><span class="visually-hidden">Quellenvorschau vorhanden</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-15T16:49:41+02:00">15.07.2026, 16:49</time></p>
      <h2><a href="u-17__/">Staatsarchiv Aargau, SAA 428</a></h2>
      <p class="catalogue-id">Dokument-ID <code>u-17__</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span><span class="catalogue-badge catalogue-badge--quality-failed">2 problematische Kandidaten</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Seiten</dt><dd>4</dd></div><div><dt>Entitäten</dt><dd>82</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="u-17__/" aria-label="Dokument öffnen: Staatsarchiv Aargau, SAA 428">Dokument öffnen <span aria-hidden="true">→</span></a><a class="catalogue-action catalogue-action--secondary" href="u-17__/?rec=selected#recognition-selected" aria-label="Erkennungen ansehen: Staatsarchiv Aargau, SAA 428">Erkennungen ansehen</a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Kandidaten</dt><dd>11 erfolgreich / 13 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">2 von 13 Kandidaten problematisch</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <ul class="catalogue-engines"><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>kraken</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>trocr</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>vlm</li></ul>
        <p class="catalogue-warning"><span aria-hidden="true">⚠</span> 2 fehlgeschlagene Erkennungsversuche</p>
      </div>
      <p class="catalogue-preview">e-codices_saa-0428_015v_large.jpg SEITE 1 modios reina cum prato sive uysta Ottovillingen dequibz hre debet forum pccenum in horum emdenaam sigilla no lsta videlicz. Alhile er conu…</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="u-17" data-created="2026-07-08T17:18:20+02:00" data-kind="output" data-language="" data-script="" data-search="u-17 staatsarchiv aargau, saa 428 e-codices: staatsarchiv aargau, saa 428     e-codices_saa-0428_015v_large.jpg u uuu uu uu u uu uuu uuuu u uuuuuu uuu uu iuuuu u u uuu uu uuu iuu uuu u u uuu iu uu uu u uuuuu iiiu u uu u uu uu u u uuu i uu uuu uuuuuuu u g uu " data-superseded="false" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="4" data-source-type="landing_page" data-source-available="true" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="" data-completeness="minimal">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--image"><img src="https://www.e-codices.unifr.ch/loris/saa/saa-0428/saa-0428_015v.jp2/full/1200,/0/default.jpg" alt="" loading="lazy" decoding="async" referrerpolicy="no-referrer"><span class="visually-hidden">Quellenvorschau vorhanden</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T17:18:20+02:00">08.07.2026, 17:18</time></p>
      <h2><a href="u-17/">Staatsarchiv Aargau, SAA 428</a></h2>
      <p class="catalogue-id">Dokument-ID <code>u-17</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Seiten</dt><dd>4</dd></div><div><dt>Entitäten</dt><dd>0</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="u-17/" aria-label="Dokument öffnen: Staatsarchiv Aargau, SAA 428">Dokument öffnen <span aria-hidden="true">→</span></a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">Keine Erkennungskandidaten dokumentiert</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <p class="catalogue-muted">Nicht dokumentiert</p>
        <span class="visually-hidden">Keine Warnungen</span>
      </div>
      <p class="catalogue-preview">e-codices_saa-0428_015v_large.jpg u uuu uu uu u uu uuu uuuu u uuuuuu uuu uu iuuuu u u uuu uu uuu iuu uuu u u uuu iu uu uu u uuuuu iiiu u uu u uu uu u u uuu i uu uuu uuuuuuu u g uu …</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="order-001-group" data-created="2026-07-08T09:03:38+02:00" data-kind="output" data-language="de" data-script="kurrent" data-search="order-001-group gerichtsbrief · 15. jahrhundert  15. jahrhundert de kurrent gerichtsbrief page_1.jpg page page_1.jpg page_2.jpg page page_2.jpg" data-superseded="false" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="2" data-source-type="landing_page" data-source-available="true" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="PERSON" data-completeness="teilweise">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--available" aria-label="Digitale Quelle vorhanden, keine Vorschau verfügbar"><span aria-hidden="true">◇</span><span>Quelle vorhanden</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:38+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="order-001-group/">Gerichtsbrief · 15. Jahrhundert</a></h2>
      <p class="catalogue-id">Dokument-ID <code>order-001-group</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Seiten</dt><dd>2</dd></div><div><dt>Entitäten</dt><dd>1</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="order-001-group/" aria-label="Dokument öffnen: Gerichtsbrief · 15. Jahrhundert">Dokument öffnen <span aria-hidden="true">→</span></a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">Keine Erkennungskandidaten dokumentiert</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <p class="catalogue-muted">Nicht dokumentiert</p>
        <span class="visually-hidden">Keine Warnungen</span>
      </div>
      <p class="catalogue-preview">page_1.jpg page page_1.jpg page_2.jpg page page_2.jpg…</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="saa-0005-test" data-created="2026-07-08T09:03:31+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0005-test gerichtsbrief · 15. jahrhundert  15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-superseded="false" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="landing_page" data-source-available="true" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="PERSON" data-completeness="teilweise">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--available" aria-label="Digitale Quelle vorhanden, keine Vorschau verfügbar"><span aria-hidden="true">◇</span><span>Quelle vorhanden</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:31+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0005-test/">Gerichtsbrief · 15. Jahrhundert</a></h2>
      <p class="catalogue-id">Dokument-ID <code>saa-0005-test</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Entitäten</dt><dd>1</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="saa-0005-test/" aria-label="Dokument öffnen: Gerichtsbrief · 15. Jahrhundert">Dokument öffnen <span aria-hidden="true">→</span></a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">Keine Erkennungskandidaten dokumentiert</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <p class="catalogue-muted">Nicht dokumentiert</p>
        <span class="visually-hidden">Keine Warnungen</span>
      </div>
      <p class="catalogue-preview">Hans von Bern tuend kund……</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="saa-0004-test" data-created="2026-07-08T09:03:31+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0004-test gerichtsbrief · 15. jahrhundert  15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-superseded="false" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="PERSON" data-completeness="minimal">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:31+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0004-test/">Gerichtsbrief · 15. Jahrhundert</a></h2>
      <p class="catalogue-id">Dokument-ID <code>saa-0004-test</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Entitäten</dt><dd>1</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="saa-0004-test/" aria-label="Dokument öffnen: Gerichtsbrief · 15. Jahrhundert">Dokument öffnen <span aria-hidden="true">→</span></a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">Keine Erkennungskandidaten dokumentiert</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <p class="catalogue-muted">Nicht dokumentiert</p>
        <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">Hans von Bern tuend kund……</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="saa-0003-test" data-created="2026-07-08T09:03:23+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0003-test gerichtsbrief · 15. jahrhundert  15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-superseded="false" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="PERSON" data-completeness="minimal">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:23+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0003-test/">Gerichtsbrief · 15. Jahrhundert</a></h2>
      <p class="catalogue-id">Dokument-ID <code>saa-0003-test</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Entitäten</dt><dd>1</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="saa-0003-test/" aria-label="Dokument öffnen: Gerichtsbrief · 15. Jahrhundert">Dokument öffnen <span aria-hidden="true">→</span></a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">Keine Erkennungskandidaten dokumentiert</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <p class="catalogue-muted">Nicht dokumentiert</p>
        <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">Hans von Bern tuend kund……</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="saa-0002-test" data-created="2026-07-08T09:03:23+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0002-test gerichtsbrief · 15. jahrhundert  15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-superseded="false" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="PERSON" data-completeness="minimal">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:23+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0002-test/">Gerichtsbrief · 15. Jahrhundert</a></h2>
      <p class="catalogue-id">Dokument-ID <code>saa-0002-test</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Entitäten</dt><dd>1</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="saa-0002-test/" aria-label="Dokument öffnen: Gerichtsbrief · 15. Jahrhundert">Dokument öffnen <span aria-hidden="true">→</span></a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">Keine Erkennungskandidaten dokumentiert</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <p class="catalogue-muted">Nicht dokumentiert</p>
        <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">Hans von Bern tuend kund……</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="saa-0001-test" data-created="2026-07-08T09:03:23+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0001-test gerichtsbrief · 15. jahrhundert  15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-superseded="false" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="PERSON" data-completeness="minimal">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:23+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0001-test/">Gerichtsbrief · 15. Jahrhundert</a></h2>
      <p class="catalogue-id">Dokument-ID <code>saa-0001-test</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Entitäten</dt><dd>1</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="saa-0001-test/" aria-label="Dokument öffnen: Gerichtsbrief · 15. Jahrhundert">Dokument öffnen <span aria-hidden="true">→</span></a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">Keine Erkennungskandidaten dokumentiert</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <p class="catalogue-muted">Nicht dokumentiert</p>
        <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">Hans von Bern tuend kund……</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="kf-" data-created="2026-07-07T15:47:14+02:00" data-kind="output" data-language="" data-script="" data-search="kf- kf-      0000004_478964_0001_19804829.jpg.png uuiuu uuuuuuuuuuuuuuuuuuuu uuuuuuuuuuu uuuuuuuuuuuuuuuuuu iuuuuuuuuuuuuuu uuuuuuiuuuu uuuuuuuuuuuuuuuuuuu uuuuuuuu uuuuuuuuuu uuuuuuuu uuuuuuuu" data-superseded="true" data-recognition-provenance="legacy" data-recognition-total="" data-recognition-successful="" data-recognition-failed="" data-recognition-empty="" data-recognition-degenerate="" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="" data-completeness="minimal">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-07T15:47:14+02:00">07.07.2026, 15:47</time></p>
      <h2><a href="kf-/">kf-</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Seiten</dt><dd>3</dd></div><div><dt>Entitäten</dt><dd>0</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="kf-/" aria-label="Dokument öffnen: kf-">Dokument öffnen <span aria-hidden="true">→</span></a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">Keine vollständigen Erkennungsdaten</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <p class="catalogue-muted">Nicht dokumentiert</p>
        <p class="catalogue-warning">Begrenzte Provenienz: Erkennungsversuche nicht vollständig dokumentiert.</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">0000004_478964_0001_19804829.jpg.png uuiuu uuuuuuuuuuuuuuuuuuuu uuuuuuuuuuu uuuuuuuuuuuuuuuuuu iuuuuuuuuuuuuuu uuuuuuiuuuu uuuuuuuuuuuuuuuuuuu uuuuuuuu uuuuuuuuuu uuuuuuuu uuuuuuuu…</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="kf" data-created="2026-07-07T15:29:12+02:00" data-kind="output" data-language="" data-script="" data-search="kf kf      0000004_478964_0001_19804829.jpg.png uuiuu uuuuuuuuuuuuuuuuuuuu uuuuuuuuuuu uuuuuuuuuuuuuuuuuu iuuuuuuuuuuuuuu uuuuuuiuuuu uuuuuuuuuuuuuuuuuuu uuuuuuuu uuuuuuuuuu uuuuuuuu uuuuuuuu" data-superseded="false" data-recognition-provenance="legacy" data-recognition-total="" data-recognition-successful="" data-recognition-failed="" data-recognition-empty="" data-recognition-degenerate="" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false" data-entity-types="" data-completeness="minimal">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-07T15:29:12+02:00">07.07.2026, 15:29</time></p>
      <h2><a href="kf/">kf</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Seiten</dt><dd>3</dd></div><div><dt>Entitäten</dt><dd>0</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="kf/" aria-label="Dokument öffnen: kf">Dokument öffnen <span aria-hidden="true">→</span></a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">Keine vollständigen Erkennungsdaten</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <p class="catalogue-muted">Nicht dokumentiert</p>
        <p class="catalogue-warning">Begrenzte Provenienz: Erkennungsversuche nicht vollständig dokumentiert.</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">0000004_478964_0001_19804829.jpg.png uuiuu uuuuuuuuuuuuuuuuuuuu uuuuuuuuuuu uuuuuuuuuuuuuuuuuu iuuuuuuuuuuuuuu uuuuuuiuuuu uuuuuuuuuuuuuuuuuuu uuuuuuuu uuuuuuuuuu uuuuuuuu uuuuuuuu…</p>
    </div>
  </details>
  </div>
  </div>
</article>
<article class="catalogue-card" data-document-id="bat_664_r_00027" data-created="2026-07-07T15:25:18+02:00" data-kind="output" data-language="deutsch" data-script="gotische schrift (französisch-als sächsische kursivschrift)" data-search="bat_664_r_00027 urbar · 1429  1429 deutsch gotische schrift (französisch-als sächsische kursivschrift) urbar vnser fründlich grus vor liebe getrune von der stösse wyse so daß nit zwüschent hemin , fast vnd cuͦnratoͤffen , ✳ darumb and die selbe vast im oogt vnd vil fürgannd hat vor nachta" data-superseded="false" data-recognition-provenance="current" data-recognition-total="10" data-recognition-successful="7" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="3" data-recognition-engines="kraken,trocr,vlm" data-recognition-models="10" data-recognition-pages="1" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="true" data-entity-types="DATE,ORG,PERSON,PLACE" data-completeness="teilweise">
  <div class="catalogue-card__layout">
  <div class="catalogue-source-visual catalogue-source-visual--missing" aria-label="Digitale Quelle fehlt"><span aria-hidden="true">∅</span><span>Quelle fehlt</span></div>
  <div class="catalogue-card__content">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-07T15:25:18+02:00">07.07.2026, 15:25</time></p>
      <h2><a href="BAT_664_r_00027/">Urbar · 1429</a></h2>
      <p class="catalogue-id">Dokument-ID <code>BAT_664_r_00027</code></p>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--review-machine">Maschinell erzeugt</span><span class="catalogue-badge catalogue-badge--quality-failed">3 problematische Kandidaten</span></div>
  </div>
  <dl class="catalogue-summary-facts"><div><dt>Datierung</dt><dd>1429</dd></div><div><dt>Entitäten</dt><dd>8</dd></div></dl>
  <p class="catalogue-actions"><a class="catalogue-action catalogue-action--primary" href="BAT_664_r_00027/" aria-label="Dokument öffnen: Urbar · 1429">Dokument öffnen <span aria-hidden="true">→</span></a><a class="catalogue-action catalogue-action--secondary" href="BAT_664_r_00027/?cmp=bat-664-r-00027-jpg-vlm-internvl3-8b-instruct:bat-664-r-00027-jpg-kraken-kraken-catmus-medieval&amp;page=BAT_664_r_00027.jpg#recognitions" aria-label="Modelle vergleichen: Urbar · 1429">Modelle vergleichen</a></p>
  <details class="catalogue-details">
    <summary>Details und Vorschau</summary>
    <div class="catalogue-details__body">
      <dl class="catalogue-facts"><div><dt>Dokumenttyp</dt><dd>Urbar</dd></div><div><dt>Sprache</dt><dd>Deutsch</dd></div><div><dt>Schrift</dt><dd>Gotische Schrift (französisch-als sächsische Kursivschrift)</dd></div><div><dt>Kandidaten</dt><dd>7 erfolgreich / 10 insgesamt</dd></div></dl>
      <div class="catalogue-status-groups">
        <div><p class="catalogue-provenance__label">Technischer Status</p><span class="catalogue-badge catalogue-badge--ok">Verarbeitung abgeschlossen</span></div>
        <div><p class="catalogue-provenance__label">Erkennungsqualität</p><p class="catalogue-recognition-status">3 von 10 Kandidaten problematisch</p></div>
      </div>

      <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
        <p class="catalogue-provenance__label">Engines</p>
        <ul class="catalogue-engines"><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>kraken</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>trocr</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>vlm</li></ul>
        <p class="catalogue-warning"><span aria-hidden="true">⚠</span> 3 degenerierte Ergebnisse</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
      </div>
      <p class="catalogue-preview">Vnser fründlich grus vor liebe getrune von der stösse wyse so daß nit zwüschent hemin , fast vnd Cuͦnratoͤffen , ✳ darumb and die selbe vast im oogt vnd vil fürgannd hat vor nachta…</p>
    </div>
  </details>
  </div>
  </div>
</article>
</div>

<noscript><p>Die Suche benötigt JavaScript. Alle Einträge bleiben ohne JavaScript sichtbar und sind bereits nach Erstellungsdatum sortiert.</p></noscript>
<script src="{{ '/assets/catalogue.js' | relative_url }}" defer></script>
<script src="{{ '/assets/quality-explain.js' | relative_url }}" defer></script>
