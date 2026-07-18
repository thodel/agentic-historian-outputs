# Agentic Historian — Outputs

Public research-data outputs of the **Agentic Historian** pipeline: machine-generated
transcriptions, structured source descriptions, and recognized entities for historical
documents (14th–16th century), published as a static, accessible catalogue.

**Live site:** <https://thodel.github.io/agentic-historian-outputs/>

## What this is

Agentic Historian experiments with transparent, machine-assisted processing of
historical sources. Each processed document is published with everything needed to
inspect, verify, and reuse the result:

- the **selected transcription** plus *every* recognition candidate (Kraken, TrOCR,
  VLM, fusion) — including failed, empty, and degenerate attempts, kept visible as
  provenance rather than hidden;
- a **structured source description** (dating, script, language, material, …) with
  per-field certainty and reasoning;
- automatically recognized **entities** (persons, places, organizations, roles, …);
- machine-readable exports: TEI-XML, plain text, `entities.csv`/`.json`,
  `CITATION.cff`, the full `pipeline.json`, and a recognition package (ZIP);
- the **version history** of each output, derived from the git history of its
  `pipeline.json`.

The outputs are **works in progress, not verified editions**. Every page states its
review status (machine-generated vs. human-verified), and the site's quality
vocabulary deliberately distinguishes engine confidence, ensemble agreement,
reference-based CER/WER, degeneration, and failure — no unscoped "QA score" is
presented as accuracy. See the design principles in
[`docs/epic5-quality-principles/README.md`](docs/epic5-quality-principles/README.md)
and the public methodology page (`docs/methodology.md`).

## How it works

```
pipeline.json (per document, written by the publisher)
        │
        ▼
scripts/build_index.py            ← entry point; also drives:
├── scripts/build_outputs.py      → docs/<doc_id>/index.md + TEI, TXT, CSV, CITATION.cff
├── scripts/build_recognitions.py → recognition viewer markup + per-candidate downloads
├── scripts/quality.py            → typed quality badges, explanations, normalization
├── scripts/recognition_status.py → attempt statuses and sanitized error taxonomy
├── scripts/rec_exports.py        → recognition packages (ZIP) and export manifests
└── scripts/source_references.py  → IIIF / image / landing-page source normalization
        │
        ▼
docs/  (Jekyll site, served by GitHub Pages from main:/docs)
├── index.md            ← generated catalogue (search, filters, sorting; works without JS)
├── <doc_id>/           ← one folder per published document
├── entities/           ← generated entity index and per-entity pages
├── methodology.md      ← public description of processing, uncertainty, metrics
├── about.md, tests/    ← project info; test runs kept separate from real outputs
└── assets/             ← CSS and vanilla-JS progressive enhancement
```

Everything is rendered statically by the Python standard library — no external
dependencies. JavaScript only *enhances* the pages (search/filter state in the URL,
recognition viewer, comparison pane, image viewer, page sync); every document and
primary action stays reachable with JavaScript disabled.

### Automation

- **`.github/workflows/build-index.yml`** — regenerates the catalogue whenever a new
  `docs/**/pipeline.json` lands on `main` and commits the refreshed index.
- **`.github/workflows/test.yml`** — on every push/PR: runs the Python and Node test
  suites, regenerates the whole site, and requires a clean `git diff`
  (generated output must match committed output), plus syntax checks on all
  browser scripts.

## Local development

Requires Python 3.9+ and Node 18+ (CI uses 3.12 / 22). From the repository root:

```sh
python3 -m unittest discover -s tests -v   # Python test suite
node --test tests/*.mjs                    # Node test suite
python3 scripts/build_index.py             # regenerate docs/ from all pipeline.json
git diff --exit-code                       # verify the build is clean
```

The release gate and a manual accessibility checklist are documented in
[`docs/catalogue-verification.md`](docs/catalogue-verification.md); performance
budgets in [`docs/catalogue-performance.md`](docs/catalogue-performance.md).

## Repository layout

| Path | Purpose |
| --- | --- |
| `docs/` | The published site (GitHub Pages, Jekyll `minima`) — generated pages + committed pipeline data |
| `scripts/` | Python generators and the source copies of the browser scripts |
| `tests/` | Python (`unittest`) and Node (`node --test`) suites with fixtures |
| `.github/workflows/` | Test gate and catalogue auto-rebuild |

## Document id policy

Each document's folder name (`docs/<id>/`) becomes a permanent public URL, so ids
must be stable and meaningful rather than collision-avoidance artifacts:

- an id **must start and end with a letter or digit**;
- internal `.`, `_` and `-` are allowed, so archival signatures such as
  `BAT_664_r_00027` are valid;
- **no leading or trailing separators** (`kf-`, `u-17__` are rejected).

The build (`scripts/build_outputs.py` → `validate_slugs`) fails with an actionable
message if a document violates this. When a source is re-processed, relate the new
run to its predecessor with a `supersedes` field (see the roadmap) instead of
mangling the id. Two ids that predate the policy (`kf-`, `u-17__`) are grandfathered
to keep existing links working.

## Roadmap

Work is organized as epic meta-issues with per-task issues:

- [#106](https://github.com/thodel/agentic-historian-outputs/issues/106) — repair the interactive quality layer
- [#108](https://github.com/thodel/agentic-historian-outputs/issues/108) — coherent status display and language
- [#109](https://github.com/thodel/agentic-historian-outputs/issues/109) — document lineage and data hygiene
- [#110](https://github.com/thodel/agentic-historian-outputs/issues/110) — reader experience and behavioral testing

Earlier epics (page architecture, recognition transparency, quality indicators,
reproducible/citable builds) are recorded in the closed issues and in
`docs/epic5-quality-principles/`.

## Reuse and citation

The generated research data is licensed **CC BY 4.0** (see [`LICENSE`](LICENSE) and each
`CITATION.cff`); rights to digitized source images remain with the holding
institutions. Each document page provides a citation string and a `CITATION.cff`;
version history per document is available through the git history of its
`pipeline.json`.
