---
layout: default
title: Methode
---

<link rel="stylesheet" href="{{ '/assets/output.css' | relative_url }}">

# Methode und Datenstatus

Agentic Historian veröffentlicht automatisch erzeugte Transkriptionen, strukturierte Quellenbeschreibungen und erkannte Entitäten. Die Ausgaben sind Forschungsdaten in Bearbeitung und keine verifizierten Editionen.

## Aufbau der Dokumentseiten

Dokumentseiten folgen einer stabilen, evidenzorientierten Reihenfolge: Identität und Status; Quelle und ausgewählte Transkription samt Erkennungsvarianten; inhaltliche Orientierung und prüfbare Aussagen; strukturierte Metadaten und Entitäten; Downloads und Nachnutzung; Zitation; Versionsgeschichte. Primäre Evidenz, maschinell erzeugte Interpretation und administrative Provenienz sind semantisch sowie visuell voneinander unterschieden.

Die Anker `#transcription` und `#claims` bleiben für bestehende Links stabil. Fehlen Digitalisat, Erkennungsvarianten oder ältere Provenienzfelder, bleibt dieselbe Grundstruktur erhalten und benennt die Lücke ausdrücklich. Fehlgeschlagene Erkennungen bleiben innerhalb des Evidenzbereichs sichtbar. Testausgaben tragen weiterhin deutlich die Kennzeichnung „Testlauf“.

Ist ein öffentlich einbettbares Bild oder IIIF-Manifest vorhanden, erscheinen Quelle und Transkription auf breiten Bildschirmen in zwei beschrifteten Bereichen. Der Trenner lässt sich ziehen oder per Tastatur mit Pfeiltasten, Pos1 und Ende bedienen. Das Verhältnis wird ausschließlich lokal im Browser gespeichert und verändert keine teilbare URL. Auf schmalen Bildschirmen und bei starker Vergrößerung stehen Quelle und Transkription untereinander; ohne einbettbare Quelle bleibt die lineare Transkriptionsansicht erhalten.

Der integrierte Digitalisat-Viewer verwendet keine externe Viewer-Plattform. Bei IIIF lädt er das angegebene Presentation-Manifest direkt und zeigt den ersten Canvas; bei direkten Bildadressen lädt er ausschließlich dieses Bild. Beide Varianten bieten Vergrößern, Verkleinern, Zurücksetzen und Vollbild sowie eine per Tastatur erreichbare, verschiebbare Bildfläche. Manifest- und Bildfehler werden nach außen verständlich gemeldet, während der Link zur Originalquelle erhalten bleibt. Browser übertragen beim Manifestabruf keine expliziten Zugangsdaten; CORS-Regeln des Quellservers können die Einbettung dennoch verhindern.

Bei mehrseitigen Ausgaben teilen Digitalisat und Erkennungsviewer denselben Seitenzustand. Ein Wechsel der Quellenseite wählt nach Möglichkeit dieselbe Engine/Modell-Familie auf der neuen Seite; die Wahl einer seitengebundenen Erkennung bewegt umgekehrt das Digitalisat. Der Parameter `page` macht diesen Zustand teilbar und unterstützt die Browsernavigation. Fehlt eine Seitenzuordnung auf einer Seite, benennt die Oberfläche die Lücke ausdrücklich und lässt die manuelle Navigation verfügbar, statt Bild und Text stillschweigend falsch zuzuordnen.

## Verarbeitung

Die Pipeline verarbeitet Digitalisate oder Bildgruppen, erzeugt eine maschinelle Transkription, leitet Beschreibungsfelder ab und erkennt Personen, Orte, Organisationen sowie weitere Entitäten. Die vollständigen Verarbeitungsergebnisse bleiben pro Dokument als `pipeline.json` verfügbar.

## Unsicherheit und Überprüfung

Jede Dokumentseite weist ihren Bearbeitungsstatus und – sofern vorhanden – den QA-Wert aus. Unsichere Beschreibungsfelder werden zusammen mit ihrer Begründung angezeigt. Ein globaler QA-Wert ersetzt keine Prüfung einzelner Lesungen oder Behauptungen am Original.

- `machine-generated`: automatisch erzeugt und nicht vollständig geprüft
- `under-review`: befindet sich in menschlicher Überprüfung
- `human-verified`: ausdrücklich fachlich geprüft

Fehlt ein öffentliches Digitalisat, weist die Seite darauf hin. Lokale Verarbeitungspfade gelten nicht als Quellenbeleg.

### Öffentliche Quellenreferenzen

Publisher können eine IIIF-Quelle über `iiif_manifest` oder das ältere Alias `manifest_url` angeben. `source_url` bezeichnet entweder ein direktes öffentliches Bild oder die Landingpage eines Archivs. Optionale Felder sind `source_label`, `source_attribution` und `source_rights`. Mehrseitige Ausgaben können `source_pages` mit `page` sowie `canvas_url` oder `image_url` verwenden, um Erkennungsseiten eindeutig auf Digitalisate abzubilden.

Nur öffentliche HTTP(S)-Adressen werden veröffentlicht. Lokale Pfade, private IP-Adressen, Zugangsdaten in URLs, Platzhalter-Hosts und andere Protokolle werden verworfen. Ältere Ausgaben ohne diese Felder bleiben als reine Transkriptionsseiten nutzbar. Die normalisierte, bewusst kleine Quellenreferenz wird zusätzlich als JSON-Payload auf der Dokumentseite bereitgestellt; sie enthält keine vollständigen IIIF-Manifeste oder Erkennungstexte.

## Versionen und Nachnutzung

Änderungen werden über Git protokolliert. Jede Dokumentseite verlinkt ihre Versionsgeschichte und bietet TEI-XML, CSV, JSON und eine maschinenlesbare Zitation an. Eine allgemeine Nachnutzungslizenz ist derzeit nicht festgelegt; Rechte am Digitalisat und an den zugrunde liegenden Quellen sind separat zu prüfen.

### Strukturierte Erkennungskandidaten

Erfolgreiche textuelle Kandidaten können als TXT, JSON oder textorientiertes TEI-XML ausgegeben werden. TXT bleibt die verlustarme Grundform. JSON bewahrt Dokument-, Seiten-, Engine-, Modell-, Konfidenz- und Ableitungsprovenienz; Fehler werden nur als bereinigte öffentliche Meldungen ausgegeben. Das TEI-XML kennzeichnet die maschinelle Erzeugung im `revisionDesc` und enthält ausschliesslich den erkannten Text sowie seine Provenienz.

ALTO, PAGE-XML sowie TEI-Zeilen, -Regionen, Koordinaten und Faksimile-Verweise werden nicht erzeugt, solange der jeweilige Erkennungsdienst keine entsprechende Layoutstruktur geliefert hat. Eine solche Struktur aus einfachem Text abzuleiten würde nicht belegte räumliche Aussagen fabrizieren. Strukturierte Kandidaten bleiben maschinell erzeugte Forschungsdaten und sind nicht als verifizierte Transkriptionen zu zitieren.

<a id="recognition-failures"></a>
### Erkennungsfehler und Wiederholbarkeit

Jeder Erkennungsversuch wird als `success`, `empty`, `timeout`, `unavailable`, `unsupported_model`, `backend_error`, `invalid_response`, `cancelled`, `degenerate` oder `missing` klassifiziert. Timeout-, Dienst-, Backend- und ungültige Antwortfehler können wiederholbar sein. Degenerierte Ausgaben sind abgeschlossene, aber mechanisch unbrauchbare Ergebnisse; eine identische Wiederholung gilt nicht als sinnvoll. Leere Ausgaben werden getrennt von technischen Fehlern und Degeneration ausgewiesen.

Öffentliche Seiten und Pakete enthalten nur stabile Diagnosecodes und bereinigte Meldungen. Zugangsdaten, interne Adressen, lokale Pfade und Stacktraces werden nicht veröffentlicht. Die Kategorien beschreiben den technischen Ausgang eines Versuchs, nicht die historische Richtigkeit einer Transkription. Auch eine erfolgreiche oder zwischen Modellen übereinstimmende Ausgabe kann inhaltlich falsch sein.

## Erkennungsübersicht im Katalog

Der Katalog leitet aus jeder `pipeline.json` eine kompakte Erkennungsübersicht ab. Sie zählt Versuche als erfolgreich, fehlgeschlagen, leer oder degeneriert; listet unterschiedliche Engine-Familien; zählt unterschiedliche Engine/Modell-Paare; und hält Seitenzahl, Quellentyp, Prüfstatus sowie Vergleichsbereitschaft fest. Vergleichsbereitschaft setzt mindestens zwei nutzbare Kandidaten derselben bekannten Seite voraus. Doppelte Datensätze erhöhen nicht die Engine- oder Modellzahl.

Ausgaben ohne `recognitions`-Feld werden ausdrücklich als ältere Ausgaben mit unbekannter Versuchsprovenienz behandelt, nicht als fehlerfreie Läufe mit null Kandidaten. Die Werte stehen als stabile `data-*`-Attribute auf den Katalogkarten und gesammelt in `catalogue-summary.json`. Weder die Transkription noch Kandidatentexte werden in diese Filterdaten übernommen, sodass ihre Größe unabhängig von der Textlänge bleibt.

## Zitierempfehlung

Verwenden Sie die stabile Adresse der Dokumentseite und geben Sie den Bearbeitungsstatus an. Für reproduzierbare Forschung sollte zusätzlich die konkrete Git-Version genannt werden.

## Erkennungsversionen

Für Dokumente mit mehreren OCR-Kandidaten zeigt die Seite die ausgewählte beziehungsweise fusionierte Transkription und alle einzelnen Erkennungsversuche.

### Was angezeigt wird

- **Engine-Label**, **Modell-ID** und Seitenzuordnung je Kandidat
- **Engine-Konfidenz** als Prozentzahl, wenn sie angegeben wurde; Werte verschiedener Engines sind nicht unmittelbar vergleichbar
- Bei Fehlern: eine veröffentlichungssichere Fehlerkategorie ohne interne Endpunkte — kein Textdownload
- **Download-Link** pro erfolgreichem Kandidat, sofern das passende Artefakt veröffentlicht wurde

### Auswahl und URL

- Die ausgewählte beziehungsweise fusionierte Pipeline-Transkription ist die Vorauswahl.
- Die Auswahl wird im Query-Parameter `rec` und als Abschnittsanker gespeichert. Der Link lässt sich teilen und beim erneuten Aufruf wiederherstellen.
- Vor- und Zurücknavigation des Browsers stellt frühere Auswahlen wieder her.

### Verhalten ohne JavaScript

Ohne JavaScript bleiben alle Kandidaten als semantische, aufklappbare Bereiche (`details`) erreichbar. JavaScript reduziert die Ansicht auf den jeweils ausgewählten Bereich.

### Tastatur und assistive Technik

Die Kandidatenauswahl besteht aus gewöhnlichen Links und kann deshalb mit der Tabulatortaste erreicht und mit Eingabe aktiviert werden. Nach einer Auswahl wechselt der Fokus zur Überschrift der gewählten Erkennungsversion. Der aktive Link wird zusätzlich mit `aria-current` ausgezeichnet; Fehlerzustände werden immer als Text und nicht nur durch Farbe vermittelt. Transkriptionen sind als eigene scrollbare Bereiche mit sichtbarer Fokusmarkierung erreichbar.

### Anpassung am Original

Für die finale Transkription sollten die generierten Lesarten stets am **Original-Digitalisat** überprüft werden. Die angebotenen Versionen sind keine edierten Lesarten, sondern Erkennungsvarianten, die der menschlichen Kontrolle bedürfen.

---

<a id="quality-metrics"></a>
## Qualitätsmetriken

Agentic Historian unterscheidet mehrere Typen von Qualitätsindikatoren. Jeder Typ hat eine eigene Bedeutung, einen eigenen Geltungsbereich und eigene Grenzen. Diese Abschnitte erläutern, was jeder Indikator misst, woher er stammt und was er nicht aussagt. Die Erläuterungen werden auf Dokument-, Erkennungs- und Katalogansichten mit denselben Schlüsseln eingeblendet.

Kein Qualitätsindikator auf dieser Seite ersetzt die Überprüfung am Original. Maschinell erzeugte Transkriptionen können fehlerhaft sein, auch wenn alle Metriken unauffällig aussehen.

<a id="quality-metrics-engine-confidence"></a>
### Engine-Konfidenz

Die Engine-Konfidenz ist ein Wahrscheinlichkeitswert, den die jeweilige Erkennungs-Engine für ihren eigenen Output produziert. Er liegt üblicherweise im Bereich [0, 1] (0 = sehr unsicher, 1 = sehr sicher).

**Geltungsbereich:** pro Kandidat (eine Engine, ein Modell, eine Seite).

**Was er ausdrückt:** Wie sicher sich das Modell *laut seiner eigenen Kalibrierung* ist. Manche Modelle sind systematisch über- oder unterkalibriert.

**Was er nicht aussagt:**
- Hohe Konfidenz bedeutet nicht, dass die Transkription korrekt ist.
- Konfidenzwerte verschiedener Engines stammen aus unterschiedlichen Modellen mit unterschiedlichen Skalen und Bedeutungen. Ein höherer Wert einer Engine sagt nichts darüber aus, ob deren Transkription genauer ist als die einer anderen Engine.
- Konfidenzwerte verschiedener Engines dürfen nicht direkt verglichen oder gemittelt werden.

**Anzeigeformat:** Prozentzahl, z. B. „87 %" mit Angabe von Engine, Modell und Seite.

<a id="quality-metrics-agreement"></a>
### Engine-Übereinstimmung

Die Übereinstimmung gibt an, wie viele unabhängige Engines oder Kandidaten dieselbe Lesart für eine Textstelle erzeugt haben.

**Berechnung:** Anteil der Kandidaten mit identischer oder normalisiert übereinstimmender Ausgabe an der Gesamtzahl der genutzten Kandidaten.

**Was sie ausdrückt:** Konsens zwischen Erkennungssystemen — ein Indiz für Robustheit.

**Was sie nicht aussagt:**
- Übereinstimmung beweist keine Korrektheit. Alle Engines können sich gemeinsam irren, insbesondere bei häufigen Fehlern oder bei unklaren Schriftzeichen.
- Übereinstimmungswerte sind kein Ersatz für Genauigkeitswerte.
- Übereinstimmung ist nicht mit Engine-Konfidenz vergleichbar.

**Anzeigeformat:** Prozentzahl, z. B. „3/4 Engines (75 %)".

<a id="quality-metrics-reference-evaluation"></a>
### Referenzbasierte Auswertung (CER / WER)

CER (Character Error Rate) und WER (Word Error Rate) werden gegen eine bekannte Referenztranskription berechnet.

**Berechnung:**
- CER = (Substitutionen + Einfügungen + Löschungen auf Zeichenebene) / Länge der Referenz
- WER = entsprechend auf Wortebene
- Beide Werte liegen im Bereich [0, 1]; niedrigere Werte bedeuten weniger Abweichungen.

**Geltungsbereich:** Der Wert gilt nur für die angegebene Referenz (Name, Version, Normalisierung, Datensatz).

**Was sie ausdrückt:** Wie stark die maschinelle Ausgabe von einer manuell erstellten Vorlage abweicht — soweit diese Vorlage vorhanden und korrekt ist.

**Was sie nicht aussagen:**
- CER/WER setzen eine korrekte Referenztranskription voraus. Ist die Referenz unvollständig oder fehlerhaft, gibt die Metrik deren Abweichungen wieder, nicht die Qualität des Originals.
- Ein Wert gilt nur für die benannte Referenz und Normalisierung. Derselbe Kandidat kann gegenüber einer anderen Referenz einen anderen Wert erzielen.
- Werte auf Korpusebene dürfen nicht als Dokumentgenauigkeit interpretiert werden.

**Anzeigeformat:** Prozentzahl mit Normalisierungshinweis, z. B. „CER 4,2 % (niedrig = besser)" mit Quellenangabe.

<a id="quality-metrics-degeneration"></a>
### Degenerierte Ausgabe

Eine degenerierte Ausgabe ist eine Transkription, die mechanisch unbrauchbar ist — also z. B. ausschliesslich aus wiederholten Zeichen besteht oder ungewöhnlich lang ist — auch wenn kein technischer Fehler gemeldet wurde.

**Erkennungsregeln:**
- 20 oder mehr identische aufeinanderfolgende Zeichen
- 10 oder mehr Wiederholungen einer kurzen Zeichensequenz (bis 5 Zeichen)
- 50 oder mehr aufeinanderfolgende Leerzeichen
- Ausgabelänge über 1 Million Zeichen
- Engine-Konfidenz unter 1 % (sofern vorhanden)

**Was dies bedeutet:** Die Engine hat eine Ausgabe produziert, die mit hoher Wahrscheinlichkeit kein sinnvolles Transkriptionsergebnis enthält. Die Ausgabe wird als Fehler behandelt.

**Was dies nicht bedeutet:** Kurze, unklare oder mehrdeutige Transkriptionen gelten nicht als degeneriert — nur mechanisch erkennbare Anomalien.

<a id="quality-metrics-failure"></a>
### Fehlgeschlagene Erkennung

Eine fehlgeschlagene Erkennung ist ein Versuch, bei dem kein verwertbares Transkriptionsergebnis erzeugt wurde, weil ein technischer Fehler aufgetreten ist.

**Fehlerkategorien:** `timeout`, `unavailable`, `backend_error`, `unsupported_model`, `invalid_response`, `cancelled`, `degenerate`, `empty`, `missing`.

**Wiederholbarkeit:** Timeout-, Dienst-, Backend- und Antwortfehler können durch Wiederholung behoben werden. Degenerierte Ausgaben und `unsupported_model`-Fehler sind durch Wiederholung nicht zu beheben.

**Was öffentlich sichtbar ist:** Nur stabile Diagnosecodes und bereinigte Meldungen. Interne Endpunkte, Pfade und Zugangsdaten werden nicht veröffentlicht.

**Was dies nicht bedeutet:** Eine fehlgeschlagene Erkennung sagt nichts über den Inhalt des Originaldokuments aus.

<a id="quality-metrics-selection-score"></a>
### Ausgewählte Transkription / Fusion

Die ausgewählte Transkription ist das Ergebnis, das die Pipeline als Haupttranskription weitergegeben hat. Sie kann aus einer einzigen Engine-Ausgabe bestehen (bei einer Engine) oder aus mehreren Kandidaten fusioniert worden sein (bei mehreren Engines).

**Auswahlkriterien:** Die Pipeline wählt oder fusioniert nach Konfidenz, Übereinstimmung und Fehlerstatus; die genauen Gewichtungen können je nach Konfiguration variieren.

**Was dies ausdrückt:** Den besten verfügbaren maschinellen Versuch auf Basis der Pipeline-Kriterien zum Zeitpunkt der Verarbeitung.

**Was dies nicht aussagt:**
- Die ausgewählte Transkription ist nicht zwingend die historisch korrekte Lesart.
- Konfidenzwerte verschiedener Engines werden dabei nicht direkt summiert oder gemittelt.
- Eine Fusion erhöht nicht automatisch die Genauigkeit; sie kann Fehler konsolidieren oder verstärken.

**Überprüfung:** Das Ergebnis sollte stets am Original-Digitalisat überprüft werden.

<a id="quality-metrics-verification"></a>
### Menschliche Überprüfung und Verifikationsstatus

Der Verifikationsstatus beschreibt, wie weit eine Transkription menschlich geprüft wurde.

**Statuswerte:**
- `machine-generated` — automatisch erzeugt, nicht geprüft
- `under-review` — befindet sich in menschlicher Überprüfung
- `human-reviewed` — manuell gesichtet, aber nicht vollständig als Transkription freigegeben
- `human-verified` — ausdrücklich fachlich geprüft und als Transkription freigegeben

**Was dies ausdrückt:** Den Bearbeitungsstand der Ausgabe, nicht ihre Qualität. Eine `machine-generated`-Ausgabe kann korrekt sein; eine `human-reviewed`-Ausgabe kann Fehler enthalten.

**Was dies nicht aussagt:** Der Status ist kein numerischer Qualitätswert und nicht mit Konfidenz oder CER vergleichbar.

**Anzeige:** Verifikationsstatus ist kategorisch und wird als Text und Symbol ausgedrückt — nie ausschliesslich durch Farbe.
