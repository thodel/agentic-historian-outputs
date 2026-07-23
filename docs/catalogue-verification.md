---
layout: default
title: "Catalogue verification"
---

> **Internal engineering document.** This page is a working document for project contributors. It is not part of the public-facing German site and is not linked from the global navigation. See the [language policy](about.html#sprachpolitik) for context.

# Recognition-aware catalogue verification

This checklist is the release gate for recognition-aware catalogue cards and controls. The catalogue is server-rendered: JavaScript enhances search, filtering, sorting, URL state, and history navigation, but every document and primary action remains available without it.

## Automated release gate

Pull requests run the complete Python and Node test suites, regenerate the catalogue and every document output, require a clean generated diff, and syntax-check all browser scripts. The hardening fixtures cover:

- multi-engine and comparison-ready outputs;
- failed, empty, and degenerate attempts;
- IIIF, direct-image, and missing-source states;
- legacy, test, machine-generated, and human-reviewed outputs;
- combined provenance filters, every sorting family, URL restoration, browser history, and empty results;
- primary action targets, comparison candidate IDs, disclosure relationships, and no-JavaScript links;
- a 5,000-record interaction fixture and bounded per-record payload/card sizes.

Run the same gate locally from the repository root:

```sh
python3 -m unittest discover -s tests -v
node --test tests/*.mjs
python3 scripts/build_index.py
git diff --exit-code
```

Performance budgets and their measurement method are recorded in [Catalogue performance budgets](catalogue-performance.html).

## Manual accessibility matrix

Before release, inspect the generated catalogue at mobile (320 px), tablet (768 px), and desktop (1440 px), plus 200% browser zoom. At each size verify readable wrapping, a visible focus indicator, 44 px controls, and that primary actions remain near their cards. Also verify:

- keyboard-only traversal and filter reset;
- touch operation without hover-dependent meaning;
- screen-reader labels, result announcements, and logical card reading order;
- forced/high-contrast colors and reduced-motion mode;
- an explicit empty-result message and recovery with “Alle Filter zurücksetzen”; and
- all cards and primary links with JavaScript disabled.

## Deployment smoke test

After merge and deployment, record the date, deployed commit, browser, and operator on issue #47. Verify the public catalogue loads without console errors; exercise one combined filter and a non-default sort; reload the resulting URL; use Back and Forward; open inspect, comparison, and legacy actions where available; and repeat one document-link check with JavaScript disabled. Confirm the public `catalogue-summary.json` is valid JSON and does not include candidate text or private diagnostics.
