---
layout: default
title: "Catalogue performance budgets"
---

# Catalogue performance budgets

The catalogue is server-generated so every document link remains available without JavaScript. JavaScript only filters and reorders existing cards. Candidate texts and candidate arrays are never embedded in the compact `catalogue-summary.json` payload.

Budgets and measurement:

- compact summary payload: at most 600 bytes per record;
- generated card markup: at most 6 KB per record for the representative fixture;
- synthetic interaction fixture: 5,000 records must complete matching and sorting within 2 seconds in Node CI;
- pagination or incremental rendering must be introduced before the generated catalogue exceeds 500 cards or 2 MB of card markup;
- deferred enhancement reserves card geometry to avoid initialization layout shifts;
- `prefers-reduced-data` hides nonessential previews, while essential links and provenance remain present.

Measure payload sizes as UTF-8 bytes after generation. Run `node tests/test_catalogue.mjs` for the large interaction fixture and `python3 -m unittest tests.test_catalogue_summary` for payload/card budgets. Slow-network verification uses the server-rendered page with JavaScript disabled: all document and primary capability links must remain usable.
