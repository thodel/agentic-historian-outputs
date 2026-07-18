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
    <p>Jede Ausgabe zeigt bis zu vier Qualitätsmetriken:</p>
    <dl>
      <div><dt>Ø Konfidenz</dt><dd>Durchschnittliche Engine-Konfidenz aller Erkennungskandidaten (niedrig = unsicherer). Nicht zwischen Engines vergleichbar.</dd></div>
      <div><dt>CER / WER</dt><dd>Character/Word Error Rate gegen eine bekannte Referenz (niedrig = weniger Fehler). Nur vorhanden wenn Referenz verfügbar.</dd></div>
      <div><dt>Erkennungsfehler</dt><dd>Anzahl der Kandidaten, die fehlgeschlagen oder degeneriert sind.</dd></div>
      <div><dt>Legacy-QA</dt><dd>QA-Wert aus älterem System ohne definierte Bedeutung. Ersetzen Sie durch eine der oben genannten Metriken.</dd></div>
    </dl>
  </details>
  <p><a href="entities/">Entitäten durchsuchen</a> · <a href="tests/">Testläufe separat anzeigen</a></p>
  <p class="catalogue-summary"><strong>14</strong> Einträge · 8 Ausgaben · 6 Testläufe</p>
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
<p id="catalogue-status" class="catalogue-status" role="status" aria-live="polite">14 Einträge, nach Erstellungsdatum absteigend sortiert.</p>
<p id="catalogue-empty" class="catalogue-empty" role="status" hidden>Keine Einträge entsprechen den aktiven Filtern. Ändern Sie die Filter oder setzen Sie sie zurück.</p>

<div id="catalogue-list" class="catalogue-list" data-enhanced="false">
<article class="catalogue-card" data-document-id="bat" data-created="2026-07-15T21:19:05+02:00" data-kind="output" data-language="deutsch (mittelhochdeutsche und mitteldeutsche konstruktionen, alemannischer dialektraum)" data-script="gotische kurrentschrift, schwarz, zeilenhöhe ca. 4,5 mm" data-search="bat 15. jahrhundert (unsicher) deutsch (mittelhochdeutsche und mitteldeutsche konstruktionen, alemannischer dialektraum) gotische kurrentschrift, schwarz, zeilenhöhe ca. 4,5 mm  bat_663_r_00050.jpg aimien undectetngen willegen dicust be uor lieden gnediuen hacrẽ si ucq al zut uon nat be- rent uñ ouch deñ urern lieben quedien herren ich blahen eeusthlicq" data-recognition-provenance="current" data-recognition-total="10" data-recognition-successful="6" data-recognition-failed="1" data-recognition-empty="0" data-recognition-degenerate="3" data-recognition-engines="kraken,trocr,vlm" data-recognition-models="10" data-recognition-pages="1" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="true">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-15T21:19:05+02:00">15.07.2026, 21:19</time></p>
      <h2><a href="bat/">bat</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--quality-failed">4 Erkennungsfehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 0%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert (unsicher)</dd></div><div><dt>Sprache</dt><dd>Deutsch (mittelhochdeutsche und mitteldeutsche Konstruktionen, alemannischer Dialektraum)</dd></div><div><dt>Schrift</dt><dd>Gotische Kurrentschrift, schwarz, Zeilenhöhe ca. 4,5 mm</dd></div><div><dt>Entitäten</dt><dd>12</dd></div><div><dt>Seiten</dt><dd>1</dd></div><div><dt>Kandidaten</dt><dd>6 erfolgreich / 10 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <ul class="catalogue-engines"><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>kraken</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>trocr</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>vlm</li></ul>
    <p class="catalogue-warning"><span aria-hidden="true">⚠</span> 1 fehlgeschlagene Erkennungsversuche</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> 3 degenerierte Ergebnisse</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">BAT_663_r_00050.jpg Aimien undectetngen willegen dicust be uor lieden gnediuen hacrẽ si ucq al zut uon nat be- rent uñ ouch deñ urern lieben quedien herren ich blahen eeusthlicq…</p>
  <p class="catalogue-actions"><a href="bat/?cmp=vlm-internvl3-8b-instruct:kraken-kraken-catmus-medieval#recognitions" aria-label="Modelle vergleichen: bat">Modelle vergleichen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="order-ens" data-created="2026-07-15T19:17:36+02:00" data-kind="output" data-language="" data-script="" data-search="order-ens     p1.jpg gut lesbar hier p2.jpg gut lesbar hier" data-recognition-provenance="current" data-recognition-total="1" data-recognition-successful="1" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="kraken" data-recognition-models="1" data-recognition-pages="2" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-15T19:17:36+02:00">15.07.2026, 19:17</time></p>
      <h2><a href="order-ens/">order-ens</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--quality-confidence">Ø Konfidenz 80%</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 90%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Entitäten</dt><dd>0</dd></div><div><dt>Seiten</dt><dd>2</dd></div><div><dt>Kandidaten</dt><dd>1 erfolgreich / 1 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <ul class="catalogue-engines"><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>kraken</li></ul>
    <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">p1.jpg gut lesbar hier p2.jpg gut lesbar hier…</p>
  <p class="catalogue-actions"><a href="order-ens/?rec=selected#recognition-selected" aria-label="Erkennungen ansehen: order-ens">Erkennungen ansehen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="u-17__" data-created="2026-07-15T16:49:41+02:00" data-kind="output" data-language="" data-script="" data-search="u-17__     e-codices_saa-0428_015v_large.jpg seite 1 modios reina cum prato sive uysta ottovillingen dequibz hre debet forum pccenum in horum emdenaam sigilla no lsta videlicz. alhile er conu" data-recognition-provenance="current" data-recognition-total="13" data-recognition-successful="11" data-recognition-failed="2" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="kraken,trocr,vlm" data-recognition-models="5" data-recognition-pages="4" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-15T16:49:41+02:00">15.07.2026, 16:49</time></p>
      <h2><a href="u-17__/">u-17__</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--quality-failed">2 Erkennungsfehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 48%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Entitäten</dt><dd>82</dd></div><div><dt>Seiten</dt><dd>4</dd></div><div><dt>Kandidaten</dt><dd>11 erfolgreich / 13 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <ul class="catalogue-engines"><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>kraken</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>trocr</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>vlm</li></ul>
    <p class="catalogue-warning"><span aria-hidden="true">⚠</span> 2 fehlgeschlagene Erkennungsversuche</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">e-codices_saa-0428_015v_large.jpg SEITE 1 modios reina cum prato sive uysta Ottovillingen dequibz hre debet forum pccenum in horum emdenaam sigilla no lsta videlicz. Alhile er conu…</p>
  <p class="catalogue-actions"><a href="u-17__/?rec=selected#recognition-selected" aria-label="Erkennungen ansehen: u-17__">Erkennungen ansehen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="u-17" data-created="2026-07-08T17:18:20+02:00" data-kind="output" data-language="" data-script="" data-search="u-17     e-codices_saa-0428_015v_large.jpg u uuu uu uu u uu uuu uuuu u uuuuuu uuu uu iuuuu u u uuu uu uuu iuu uuu u u uuu iu uu uu u uuuuu iiiu u uu u uu uu u u uuu i uu uuu uuuuuuu u g uu " data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="4" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T17:18:20+02:00">08.07.2026, 17:18</time></p>
      <h2><a href="u-17/">u-17</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 80%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Entitäten</dt><dd>0</dd></div><div><dt>Seiten</dt><dd>4</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <p class="catalogue-muted">Nicht dokumentiert</p>
    <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">e-codices_saa-0428_015v_large.jpg u uuu uu uu u uu uuu uuuu u uuuuuu uuu uu iuuuu u u uuu uu uuu iuu uuu u u uuu iu uu uu u uuuuu iiiu u uu u uu uu u u uuu i uu uuu uuuuuuu u g uu …</p>
  <p class="catalogue-actions"><a href="u-17/" aria-label="Ausgabe öffnen: u-17">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="order-001-group" data-created="2026-07-08T09:03:38+02:00" data-kind="output" data-language="de" data-script="kurrent" data-search="order-001-group 15. jahrhundert de kurrent gerichtsbrief page_1.jpg page page_1.jpg page_2.jpg page page_2.jpg" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="2" data-source-type="landing_page" data-source-available="true" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:38+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="order-001-group/">order-001-group</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 90%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Entitäten</dt><dd>1</dd></div><div><dt>Seiten</dt><dd>2</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <p class="catalogue-muted">Nicht dokumentiert</p>
    <span class="visually-hidden">Keine Warnungen</span>
  </div>
  <p class="catalogue-preview">page_1.jpg page page_1.jpg page_2.jpg page page_2.jpg…</p>
  <p class="catalogue-actions"><a href="order-001-group/" aria-label="Ausgabe öffnen: order-001-group">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="saa-0005-test" data-created="2026-07-08T09:03:31+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0005-test 15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="landing_page" data-source-available="true" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:31+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0005-test/">saa-0005-test</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 85%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Entitäten</dt><dd>1</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <p class="catalogue-muted">Nicht dokumentiert</p>
    <span class="visually-hidden">Keine Warnungen</span>
  </div>
  <p class="catalogue-preview">Hans von Bern tuend kund……</p>
  <p class="catalogue-actions"><a href="saa-0005-test/" aria-label="Ausgabe öffnen: saa-0005-test">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="saa-0004-test" data-created="2026-07-08T09:03:31+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0004-test 15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:31+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0004-test/">saa-0004-test</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 85%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Entitäten</dt><dd>1</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <p class="catalogue-muted">Nicht dokumentiert</p>
    <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">Hans von Bern tuend kund……</p>
  <p class="catalogue-actions"><a href="saa-0004-test/" aria-label="Ausgabe öffnen: saa-0004-test">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="saa-0006-test" data-created="2026-07-08T09:03:23+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0006-test 15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:23+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0006-test/">saa-0006-test</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 85%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Entitäten</dt><dd>1</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <p class="catalogue-muted">Nicht dokumentiert</p>
    <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">Hans von Bern tuend kund……</p>
  <p class="catalogue-actions"><a href="saa-0006-test/" aria-label="Ausgabe öffnen: saa-0006-test">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="saa-0003-test" data-created="2026-07-08T09:03:23+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0003-test 15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:23+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0003-test/">saa-0003-test</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 85%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Entitäten</dt><dd>1</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <p class="catalogue-muted">Nicht dokumentiert</p>
    <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">Hans von Bern tuend kund……</p>
  <p class="catalogue-actions"><a href="saa-0003-test/" aria-label="Ausgabe öffnen: saa-0003-test">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="saa-0002-test" data-created="2026-07-08T09:03:23+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0002-test 15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:23+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0002-test/">saa-0002-test</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 85%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Entitäten</dt><dd>1</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <p class="catalogue-muted">Nicht dokumentiert</p>
    <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">Hans von Bern tuend kund……</p>
  <p class="catalogue-actions"><a href="saa-0002-test/" aria-label="Ausgabe öffnen: saa-0002-test">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="saa-0001-test" data-created="2026-07-08T09:03:23+02:00" data-kind="test" data-language="de" data-script="kurrent" data-search="saa-0001-test 15. jahrhundert de kurrent gerichtsbrief hans von bern tuend kund…" data-recognition-provenance="current" data-recognition-total="0" data-recognition-successful="0" data-recognition-failed="0" data-recognition-empty="0" data-recognition-degenerate="0" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="0" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-08T09:03:23+02:00">08.07.2026, 09:03</time></p>
      <h2><a href="saa-0001-test/">saa-0001-test</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">Testlauf</span><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 85%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Datierung</dt><dd>15. Jahrhundert</dd></div><div><dt>Dokumenttyp</dt><dd>Gerichtsbrief</dd></div><div><dt>Sprache</dt><dd>de</dd></div><div><dt>Schrift</dt><dd>Kurrent</dd></div><div><dt>Entitäten</dt><dd>1</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 0 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <p class="catalogue-muted">Nicht dokumentiert</p>
    <p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">Hans von Bern tuend kund……</p>
  <p class="catalogue-actions"><a href="saa-0001-test/" aria-label="Ausgabe öffnen: saa-0001-test">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="kf-" data-created="2026-07-07T15:47:14+02:00" data-kind="output" data-language="" data-script="" data-search="kf-     0000004_478964_0001_19804829.jpg.png uuiuu uuuuuuuuuuuuuuuuuuuu uuuuuuuuuuu uuuuuuuuuuuuuuuuuu iuuuuuuuuuuuuuu uuuuuuiuuuu uuuuuuuuuuuuuuuuuuu uuuuuuuu uuuuuuuuuu uuuuuuuu uuuuuuuu" data-recognition-provenance="legacy" data-recognition-total="" data-recognition-successful="" data-recognition-failed="" data-recognition-empty="" data-recognition-degenerate="" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-07T15:47:14+02:00">07.07.2026, 15:47</time></p>
      <h2><a href="kf-/">kf-</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 80%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Entitäten</dt><dd>0</dd></div><div><dt>Seiten</dt><dd>3</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <p class="catalogue-muted">Nicht dokumentiert</p>
    <p class="catalogue-warning">Begrenzte Provenienz: Erkennungsversuche nicht vollständig dokumentiert.</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">0000004_478964_0001_19804829.jpg.png uuiuu uuuuuuuuuuuuuuuuuuuu uuuuuuuuuuu uuuuuuuuuuuuuuuuuu iuuuuuuuuuuuuuu uuuuuuiuuuu uuuuuuuuuuuuuuuuuuu uuuuuuuu uuuuuuuuuu uuuuuuuu uuuuuuuu…</p>
  <p class="catalogue-actions"><a href="kf-/" aria-label="Ausgabe öffnen: kf-">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="kf" data-created="2026-07-07T15:29:12+02:00" data-kind="output" data-language="" data-script="" data-search="kf     0000004_478964_0001_19804829.jpg.png uuiuu uuuuuuuuuuuuuuuuuuuu uuuuuuuuuuu uuuuuuuuuuuuuuuuuu iuuuuuuuuuuuuuu uuuuuuiuuuu uuuuuuuuuuuuuuuuuuu uuuuuuuu uuuuuuuuuu uuuuuuuu uuuuuuuu" data-recognition-provenance="legacy" data-recognition-total="" data-recognition-successful="" data-recognition-failed="" data-recognition-empty="" data-recognition-degenerate="" data-recognition-engines="" data-recognition-models="0" data-recognition-pages="" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-07T15:29:12+02:00">07.07.2026, 15:29</time></p>
      <h2><a href="kf/">kf</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 80%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Entitäten</dt><dd>0</dd></div><div><dt>Seiten</dt><dd>3</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <p class="catalogue-muted">Nicht dokumentiert</p>
    <p class="catalogue-warning">Begrenzte Provenienz: Erkennungsversuche nicht vollständig dokumentiert.</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">0000004_478964_0001_19804829.jpg.png uuiuu uuuuuuuuuuuuuuuuuuuu uuuuuuuuuuu uuuuuuuuuuuuuuuuuu iuuuuuuuuuuuuuu uuuuuuiuuuu uuuuuuuuuuuuuuuuuuu uuuuuuuu uuuuuuuuuu uuuuuuuu uuuuuuuu…</p>
  <p class="catalogue-actions"><a href="kf/" aria-label="Ausgabe öffnen: kf">Ausgabe öffnen <span aria-hidden="true">→</span></a></p>
  
</article>
<article class="catalogue-card" data-document-id="bat_664_r_00027" data-created="2026-07-07T15:25:18+02:00" data-kind="output" data-language="" data-script="" data-search="bat_664_r_00027     duser feunilite grus vor liebe gerrmreuon de scosse roepse di fuitsriousthont homn vast uud emraro oigon darmus ue bee selbe vast i digl cond uil furipians hat aodonoid inz esgerra" data-recognition-provenance="current" data-recognition-total="2" data-recognition-successful="0" data-recognition-failed="1" data-recognition-empty="0" data-recognition-degenerate="1" data-recognition-engines="kraken,party" data-recognition-models="2" data-recognition-pages="1" data-source-type="missing" data-source-available="false" data-review-status="machine-generated" data-comparison-ready="false">
  <div class="catalogue-card__heading">
    <div>
      <p class="catalogue-created">Erstellt <time datetime="2026-07-07T15:25:18+02:00">07.07.2026, 15:25</time></p>
      <h2><a href="BAT_664_r_00027/">BAT_664_r_00027</a></h2>
    </div>
    <div class="catalogue-badges"><span class="catalogue-badge catalogue-badge--test">machine-generated</span><span class="catalogue-badge catalogue-badge--ok">Pipeline: Ohne Fehler</span><span class="catalogue-badge catalogue-badge--quality-failed">2 Erkennungsfehler</span><span class="catalogue-badge catalogue-badge--legacy">Legacy-QA 10%</span></div>
  </div>
  <dl class="catalogue-facts"><div><dt>Entitäten</dt><dd>11</dd></div><div><dt>Kandidaten</dt><dd>0 erfolgreich / 2 insgesamt</dd></div></dl>
  <div class="catalogue-provenance" aria-label="Erkennungsprovenienz">
    <p class="catalogue-provenance__label">Engines</p>
    <ul class="catalogue-engines"><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>kraken</li><li class="catalogue-engine"><span class="visually-hidden">Erkennungsengine: </span>party</li></ul>
    <p class="catalogue-warning"><span aria-hidden="true">⚠</span> 1 fehlgeschlagene Erkennungsversuche</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> 1 degenerierte Ergebnisse</p><p class="catalogue-warning"><span aria-hidden="true">⚠</span> Keine digitale Quelle verknüpft</p>
  </div>
  <p class="catalogue-preview">duser feunilite grus vor liebe gerrmreuon de scosse roepse di fuitsriousthont homn vast uud emraro oigon darmus ue bee selbe vast i digl cond uil furipians hat aodonoid inz esgerra…</p>
  <p class="catalogue-actions"><a href="BAT_664_r_00027/?rec=selected#recognition-selected" aria-label="Erkennungen ansehen: BAT_664_r_00027">Erkennungen ansehen <span aria-hidden="true">→</span></a></p>
  
</article>
</div>

<noscript><p>Die Suche benötigt JavaScript. Alle Einträge bleiben ohne JavaScript sichtbar und sind bereits nach Erstellungsdatum sortiert.</p></noscript>
<script src="{{ '/assets/catalogue.js' | relative_url }}" defer></script>
<script src="{{ '/assets/quality-explain.js' | relative_url }}" defer></script>
