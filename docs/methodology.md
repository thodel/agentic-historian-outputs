---
layout: default
title: Methode
---

<link rel="stylesheet" href="{{ '/assets/output.css' | relative_url }}">

# Methode und Datenstatus

Agentic Historian veröffentlicht automatisch erzeugte Transkriptionen, strukturierte Quellenbeschreibungen und erkannte Entitäten. Die Ausgaben sind Forschungsdaten in Bearbeitung und keine verifizierten Editionen.

## Verarbeitung

Die Pipeline verarbeitet Digitalisate oder Bildgruppen, erzeugt eine maschinelle Transkription, leitet Beschreibungsfelder ab und erkennt Personen, Orte, Organisationen sowie weitere Entitäten. Die vollständigen Verarbeitungsergebnisse bleiben pro Dokument als `pipeline.json` verfügbar.

## Unsicherheit und Überprüfung

Jede Dokumentseite weist ihren Bearbeitungsstatus und – sofern vorhanden – den QA-Wert aus. Unsichere Beschreibungsfelder werden zusammen mit ihrer Begründung angezeigt. Ein globaler QA-Wert ersetzt keine Prüfung einzelner Lesungen oder Behauptungen am Original.

- `machine-generated`: automatisch erzeugt und nicht vollständig geprüft
- `under-review`: befindet sich in menschlicher Überprüfung
- `human-verified`: ausdrücklich fachlich geprüft

Fehlt ein öffentliches Digitalisat, weist die Seite darauf hin. Lokale Verarbeitungspfade gelten nicht als Quellenbeleg.

## Versionen und Nachnutzung

Änderungen werden über Git protokolliert. Jede Dokumentseite verlinkt ihre Versionsgeschichte und bietet TEI-XML, CSV, JSON und eine maschinenlesbare Zitation an. Eine allgemeine Nachnutzungslizenz ist derzeit nicht festgelegt; Rechte am Digitalisat und an den zugrunde liegenden Quellen sind separat zu prüfen.

## Zitierempfehlung

Verwenden Sie die stabile Adresse der Dokumentseite und geben Sie den Bearbeitungsstatus an. Für reproduzierbare Forschung sollte zusätzlich die konkrete Git-Version genannt werden.

## Erkennungsversionen

Für Dokumente mit mehreren OCR-Kandidaten zeigt die Seite einen **Auswahl-Dialog** (Radio-Tabs), der alle verfügbaren Transkriptionsversionen vergleichbar macht.

### Was angezeigt wird

- **Engine-Label** und **Modell-ID** je Kandidat, z. B. `VLM (InternVL3-8B)` oder `Kraken OCR`
- **Konfidenzwert** als Prozentzahl (wenn vom Engine angegeben)
- Bei Fehlern: Fehlertext und -grund — kein Download-Link
- **Download-Link** pro Kandidat (`.txt`, sprachabhängig kodiert)

### Auswahl und URL

- Die Vorauswahl trifft der **Exakte-Match-Algorithmus**: er prüft, welcher Kandidat exakt mit der Pipeline-Transkription übereinstimmt (via `_is_selected`).
- Stimmt kein Kandidat exakt, wird der erste fehlerfreie Kandidat vorausgewählt.
- Die Auswahl wird als **URL-Anker** gespeichert (`#cand-<engine>-<model>-<index>`). Die URL ist somit shareable — beim Aufruf wird die gewählte Version direkt angezeigt.
- Browser-Zurück funktioniert korrekt (History API).

### Verhalten ohne JavaScript

Ohne JavaScript werden Panele via CSS-Selektoren (`radio:checked ~ .rec-panel`) angezeigt — alle Kandidaten bleiben discoverable, die Auswahl funktioniert identisch.

### Anpassung am Original

Für die finale Transkription sollten die generierten Lesarten stets am **Original-Digitalisat** überprüft werden. Die angebotenen Versionen sind keine edierten Lesarten, sondern Erkennungsvarianten, die der menschlichen Kontrolle bedürfen.
