---
layout: default
title: "Training report performance and accessibility budgets"
---

> **Internal engineering document.** This is the release contract for the
> generated training section.

# Training report budgets

Training reports remain complete without JavaScript. Curves are inline SVG and
all exact epoch values are also available in an HTML table.

## Performance budgets

- At most **250 SVG points per series**. Longer curves are sampled
  deterministically for display while the adjacent table retains every value.
- At most **128 KB of generated markup per run report**.
- At most **2 MB for the complete generated training page**. The build fails
  rather than publishing a page beyond this threshold.
- Rendering a synthetic overview table of **500 runs must take less than one
  second** in the Python test environment.
- No client-side charting dependency and no JavaScript are required for the
  curves, provenance, model card, or metrics.

Budgets are defined once in `scripts/build_training.py` as
`TRAINING_PERFORMANCE_BUDGETS` and enforced by
`tests/test_training_budgets.py`.

## Accessibility release gate

Every release must preserve:

- an SVG `role="img"` with a unique `<title>` and `<desc>`;
- labelled axes and a visible legend whose line styles do not rely on color
  alone;
- the exact curve values in a native table;
- native `details`/`summary` disclosures operable without JavaScript;
- a visible three-pixel keyboard focus indicator;
- disclosure targets at least 44 CSS pixels high;
- horizontal scrolling around wide tables without scrolling the whole page;
- single-column reflow below 38 rem and at 200% zoom;
- forced-colors styling and printable expanded report content;
- explicit empty states for missing curves and metrics—never synthetic zeros.

Run the gate with:

```sh
python3 -m unittest tests.test_training_budgets tests.test_training_reports
```
