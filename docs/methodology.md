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
