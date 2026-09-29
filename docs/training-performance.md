---
layout: default
title: "Training report performance and accessibility budgets"
---

> **Internal engineering document.** This is the release contract for the
> generated training section.

# Training report budgets

Training reports remain complete without JavaScript. Curves are inline SVG with
an adjacent HTML table of exact epoch values.

## Performance budgets

- At most **250 SVG points per series**. Longer curves are reduced
  deterministically, keeping the minimum and maximum of each section so
  isolated spikes survive, and the chart's description states how many points
  of how many were drawn. Axis bounds always come from the full series.
- At most **200 exact table rows per run**. A longer run shows a disclosed
  excerpt built from the same reduction, and the complete series stays
  published verbatim in that run's `training.json`, which the report links.
- At most **128 KB of generated markup per run report**.
- At most **2 MB for the complete generated training page**. The build fails
  rather than publishing a page beyond this threshold.

The two reduction budgets exist because the byte budget alone could only
abort. A valid 2,000-epoch run rendered every table row, reached 183 KB, and
raised — taking down the build for every other document too. A budget that
can only refuse to publish is a cliff, not a budget; these bound the
presentation so a long run publishes rather than blocking the site.
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
