---
layout: default
title: "Entitäten: Normdatenabgleich"
---

# Optionaler Normdatenabgleich

Der statische Build greift nie auf Wikidata oder die GND zu. Er liest
ausschließlich den versionierten Kandidatensatz
[`data/entity-reconciliation.json`](https://github.com/thodel/agentic-historian-outputs/blob/main/data/entity-reconciliation.json).
Vorschläge erscheinen ausdrücklich als **„Unverifiziert — automatisch
vorgeschlagen“** und sind keine bestätigten Identifizierungen.

Ein neuer Kandidatenlauf wird bewusst separat ausgeführt:

```bash
python3 scripts/reconcile_entities.py
```

Das Skript berücksichtigt nur nicht quarantänisierte Entitäten mit hoher
Konfidenz. Sein Ergebnis muss vor dem Commit geprüft werden. Falsche oder
unerwünschte Vorschläge werden dauerhaft unter `suppress` in
`data/entity-reconciliation-review.json` eingetragen, beispielsweise:

```json
{
  "schema_version": 1,
  "suppress": ["PLACE:thun"]
}
```

Der Schlüssel besteht aus Entitätstyp und dem normalisierten Varianten-Schlüssel.
Eine Unterdrückung entfernt weder die Entität noch ihre Belegstellen; lediglich
der automatische Normdatenvorschlag wird nicht publiziert.
