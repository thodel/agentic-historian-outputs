# Epic 5 — Explicit and Trustworthy Quality Indicators

**Issue:** [#26](https://github.com/thodel/agentic-historian-outputs/issues/26) meta-issue

This document records the design principles, metric vocabulary, acceptance criteria,
and implementation decisions for Epic 5 quality indicators (issues #26–#32).

---

## Quality vocabulary

Every quality signal emitted by this pipeline belongs to exactly one of the following
metric types.  There are no unnamed, unscoped, or engine-agnostic "QA scores."

### Engine confidence

- **What:** A probability-like score produced by a recognition engine.
- **Unit:** Dimensionless ratio in [0, 1], interpreted as a percentage.
- **Scope:** Always labelled with engine/model/page — never just "confidence".
- **Comparability:** Not comparable across engines.  A 90% Kraken confidence does not
  mean the same thing as a 90% VLM confidence.  Display includes an
  incomparability warning.
- **No correctness implication:** High engine confidence does NOT imply the
  transcription is correct.  Engines can be confidently wrong.

### Agreement

- **What:** Proportion of engines/candidates that produce the same reading.
- **Unit:** Ratio in [0, 1].
- **Scope:** Per-candidate-set, never per-engine.
- **Comparability:** Not a quality score.  All engines can agree on a wrong reading.
  Always accompanied by a warning that agreement ≠ correctness.

### Reference evaluation (CER / WER)

- **What:** Character Error Rate or Word Error Rate against a known ground-truth
  reference transcription.
- **Unit:** CER and WER are ratios in [0, 1]; lower = fewer errors = better.
- **Scope:** Per-document or per-page.  Always stated in the provenance block.
- **Comparability:** Only comparable when the reference, normalisation, and scope
  are identical.  Different references → different values.
- **Presence:** Only shown when a reference exists in `pipeline.json →
  a_meta.reference_eval`.

### Degenerate output

- **What:** Output that is mechanically invalid (all-same-character, empty,
  excessively long) even when no technical error was reported.
- **Detection:** Automatic pattern detection in `scripts/quality.py →
  detect_degeneration()`.
- **Display:** Treated as a failure; candidate is shown with an error notice, not
  silently with zero confidence.

### Failed recognition

- **What:** Recognition attempt that produced no usable output due to timeout,
  service unavailable, unsupported model, or degeneration.
- **Display:** Distinct from a zero-confidence success.  Always shows a typed
  `quality-badge--failed` or `quality-badge--degenerate` badge and a human-readable
  error message from `_public_error()` (sanitised of endpoints/paths/credentials).

### Legacy QA score

- **What:** A raw float stored in `a_meta.qa_score` from the previous system,
  without unit, scope, or provenance context.
- **Display:** Shown as `Legacy-QA` with distinct amber badge styling to signal it
  needs replacement.  Never treated as a quality score in the new system.

---

## Metric cardinality rules

| Metric | Per candidate | Per document | Per catalogue card |
|--------|--------------|--------------|-------------------|
| Engine confidence | ✅ Always | — | Average only |
| Agreement | ✅ | — | — |
| CER/WER | — | ✅ When reference exists | ✅ When reference exists |
| Degenerate flag | ✅ | — | Count of degenerate candidates |
| Failed flag | ✅ | — | Count of failed candidates |

---

## Provenance requirements

Every metric that appears in an output page must be accompanied by a provenance
block containing:

- **Metric type** and **value** with unit
- **Scope** (engine/model/page, document, or page)
- For CER/WER: `reference_name`, `reference_version`, `normalisation`, `scope`
- An `explanation_key` linking to a reusable explanation in `EXPLANATIONS`

Machine-readable quality data is preserved in:
- `<details class="rec-confidence-raw">` in each candidate panel (no-JS accessible)
- `data-quality-provenance` attributes on `.quality-badge` elements
- `reference_eval` block in `pipeline.json` when ground truth is available

---

## Accessibility requirements

- All quality signals are visible without JavaScript.
- Explanation disclosures use native `<button>` + `aria-expanded` + `aria-controls`.
- Explanation blocks use `role="region"` and `aria-label`.
- All badges have short text labels (no icon-only indicators).
- Focus styles use 3px solid `#f5b942` outline offset by 2px.
- All interactive elements are keyboard-navigable.

---

## CSS class naming

Quality indicator CSS classes follow a BEM-like pattern:

```
.quality-badge--{metric_type}          Typed quality badge (engine_confidence, agreement, etc.)
.quality-explain-btn                   Explanation toggle button
.quality-explanation                   Explanation disclosure block
.rec-status--{state}                   Candidate status (ok, failed, degenerate)
.rec-ref-eval                          Reference evaluation details block
```

---

## Acceptance criteria checklist

- [ ] **#27** Every quality metric has a typed vocabulary entry in `scripts/quality.py`
- [ ] **#28** Catalogue cards show typed badges (CER/WER, avg confidence, error count) instead of ambiguous "QA %"
- [ ] **#29** Each recognition candidate shows typed status badge + confidence with scope label + error notice
- [ ] **#30** Every metric type has a matching explanation in `EXPLANATIONS` with an accessible disclosure button
- [ ] **#31** CER/WER displays with reference name, version, normalisation, and scope
- [ ] **#32** Tests cover degeneration detection, legacy QA handling, confidence formatting, badge rendering, and accessibility requirements
- [ ] **#26** This document is updated to reflect final implementation decisions

---

## Files changed

```
scripts/quality.py                        Quality vocabulary, degeneration detection, explanations
scripts/build_recognitions.py             Recognition viewer HTML renderer
scripts/build_outputs.py                  Wires recognition section into document pages
scripts/build_index.py                    Catalogue card quality badges
docs/assets/output.css                    Quality indicator styles
tests/test_quality.py                     Epic 5 test suite
docs/epic5-quality-principles/README.md   This document
```

Last updated: 2026-07-17
