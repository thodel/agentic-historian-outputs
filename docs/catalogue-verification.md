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

A fifth check runs the site as GitHub Pages builds it:

```sh
./scripts/build_styled_site.sh
node --test tests/integration/styled_site.mjs
```

Everything else in the suite tests generated markup. The behavioural fixtures
load raw HTML from `file://`, so nothing in them can see what the Jekyll theme
does to a page — which is how `/training/` came to be served as an eighty-byte
fragment with no head, no navigation and no stylesheet, on a page that is in
the public navigation. This suite opens the built site over HTTP at desktop
and phone widths and checks that every navigation page is themed, that a
document is visible without scrolling, that the catalogue works with
JavaScript disabled, and that a document's citable downloads all resolve. It
fails rather than skips when the site has not been built, because a test that
quietly does not run is worse than one that fails.

`unittest discover` is the only Python collector, so a test written in pytest's
shape — a module-level `def test_x()` or a bare `class TestX:` — is skipped in
silence and the gate still passes. `tests/test_suite_collection.py` rejects
that shape and holds the suite to a recorded case floor; treat a failure there
as tests having gone missing, not as a nuisance.

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
