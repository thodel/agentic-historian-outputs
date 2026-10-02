---
layout: default
title: "Source backfill ledger"
---

> **Internal engineering document.** This page is a working document for project contributors. It is not part of the public-facing German site and is not linked from the global navigation. See the [language policy](about.html#sprachpolitik) for context.

# Source backfill ledger (#182)

Epic #182 is not finished when every child issue is ticked. Its exit condition
is that **every current output either carries a verified source reference or
records why the original is unavailable**. This page tracks that, and says how
to add an entry.

Run `python3 scripts/source_ledger.py` for the current state.

## Why verified references live outside `pipeline.json`

A source reference is an editorial claim: somebody looked at a facsimile,
matched it against the text, and took responsibility for saying they
correspond. A recognition run cannot know that.

Holding it in `pipeline.json` had two consequences. A replacement run that
omitted `source_url` silently dropped the verification, so a page went from
checkable to unverifiable with nothing recording the loss. And the record
could not say who checked, when, or against what — a reference carried no more
weight than a guess.

Verified references therefore live in `data/source-references.json`, committed
like the withdrawal and editorial-review registries. A machine re-run cannot
touch them. A `source_url` in `pipeline.json` remains an **unverified hint**
from the pipeline and is presented as one; a ledger entry overrides it.

## Adding an entry

```json
{
  "version": 1,
  "documents": {
    "<doc_id>": {
      "institution": "Staatsarchiv Aargau",
      "shelfmark": "SAA 428",
      "rights": "See the rights statement on e-codices",
      "verified_by": "<name of the person who checked>",
      "verified_at": "2026-09-29",
      "source_url": "https://www.e-codices.unifr.ch/en/saa/0428",
      "source_pages": [
        {"page": "<recognition page id>",
         "canvas_url": "https://…/15v",
         "image_url": "https://…/saa-0428_015v.jp2/full/1200,/0/default.jpg"}
      ],
      "note": "what was checked, and how far"
    }
  }
}
```

`institution`, `shelfmark`, `rights`, `verified_by` and `verified_at` are
required, and at least one of `source_url` or `iiif_manifest`. Institution and
shelfmark are required because they are what make a reference checkable by
someone who cannot open the URL: a link rots, a shelfmark does not.

Where an original genuinely cannot be published, record
`unavailable_reason` instead of inventing a link. The coverage report counts
that as answered, because "we looked and it is not available" is a result.

## Candidates found in the committed data

These are **candidates, not verifications**. Each is derived from what the
repository already contains — an image filename, or a model-written
description — and none has been checked against a facsimile by a person. They
are listed so the backfill has a starting point, not so they can be pasted
into the ledger.

| Document | Evidence in the repository | Candidate |
| --- | --- | --- |
| `u-17` | `pipeline.json` already carries `source_url`, label "e-codices: Staatsarchiv Aargau, SAA 428", attribution, rights and four mapped page images | Staatsarchiv Aargau, SAA 428 — complete except for who verified it |
| `saa-0428` | its own transcript page ids are `e-codices_saa-0428_001r_large.jpg`; the text names the `Closter ze Königl[felden]` | the same e-codices SAA 428 as `u-17` |
| `BAT_664_r_00027` | page id `BAT_664_r_00027.jpg`; its own description is wrong, see below | Staatsarchiv Bern, A V 1443–1447 |
| `bat` | page id `BAT_663_r_00050.jpg` | Staatsarchiv Bern, A V 1443–1447 |
| `koenige`, `kf`, `order-ens`, `order-001-group` | nothing in the record identifies an original | none |

## The two inconsistencies, resolved

Both were recorded here as questions that "cannot be settled from the
repository alone". That was right about the repository and wrong about the
project: the answer to the first is written down upstream, and the second
turned out to be an error on this page.

### 1. BAT is Staatsarchiv Bern, not the Burgerbibliothek

Two model-written descriptions disagreed. `bat` said "Staatsarchiv des Kantons
Bern" and flagged itself `unsicher: true`, with a note saying the archive was
not derivable from the image and that the `BAT_663` format is characteristic of
the Staatsarchiv's holdings. `BAT_664_r_00027` said "Bern, Burgerbibliothek,
BAT664" with `unsicher: false` and **no note at all**.

The confident claim was the unsourced one, and it is the wrong one.
`serving-atr-inference/config/models.yaml` records, where it registers the
model that reads these hands:

> Registered on 2026-09-29 for the Berner Disputation manuscripts (Staatsarchiv
> Bern A V 1443-1447), which the xix models cannot read: they were trained on
> 19th-century Kurrent and this is 1528.

So the corpus is the Berner Disputation, the institution is **Staatsarchiv
Bern**, and the shelfmark is **A V 1443–1447**. `BAT_663` and `BAT_664` are
scan-batch identifiers, not shelfmarks — which is why neither description could
source them: there was nothing to source. A ledger entry keyed on "BAT 664"
would have recorded a filename as a call number.

This resolves the contradiction. It is still not a verification: a line in a
configuration file is not somebody matching a facsimile against the text, and
`verified_by` means the person who did that.

### 2. `u-17` did not mix two identifiers — this page did

The claim was that `u-17`'s transcript page id is `U-17_0057_r.jpg` while its
mapped source pages are `e-codices_saa-0428_*`. That was wrong.
`U-17_0057_r.jpg` is `koenige`'s page id. `u-17` carried no `U-17_*` id at all:
its four transcript pages were `e-codices_saa-0428_015v/016r/016v/017r`, exactly
and in the same order as its `source_pages` mapping, and always had been. Two
documents were conflated when this page was written.

What was actually wrong was worse, and it was live on the site:

| document | pages | facsimile mapping | transcription | recognitions |
| --- | --- | --- | --- | --- |
| `u-17` (canonical) | 4 | **4 — the only one on the site** | 451 alphabetic characters over 4 distinct letters | **0** |
| `u-17__` (retired) | the same 4 | none | 12,655 characters, 41 letters | 39 |
| `saa-0428` | those 4 plus 2 | none | 12,861 characters, 50 letters | 51 |

`u-17`'s published transcription was engine noise — 371 "u", 77 "i", 2 "s", one
"g" — scoring `qa_score: 0.8`. Three documents transcribed the same four
images; `u-17__` and `saa-0428` were independent readings of them, and both
held real text.

**The cause is the id cleanup in #195.** Commit `0cf46c4` moved the
`supersedes` pointer from the malformed id to the clean one without moving the
content. Before it, `u-17__` carried `supersedes: "u-17"` — the substantive
record was canonical and the stub was retired, which was correct. After it the
stub was canonical and the substantive record retired. `kf`/`kf-` is the same
swap over two records whose transcriptions are byte-identical.

So the answer to the question this page asked — whether the site's one
embeddable facsimile was attached to the right document — is: **it was attached
to the right pages on the wrong record.**

### Why nothing caught it

`detect_degeneration` existed and was good, but its patterns are anchored
across the whole string, so they only match a page that is one unbroken run of
one character. A line-based engine failing produces one short run *per line*,
and every newline breaks the anchor. It now tests the alphabet the text uses:
measured against all 140 candidate texts in the corpus, that added exactly one,
a kraken run on `bat` that emitted 350 characters of 94% "u".

More basically, the check ran only over *candidates* inside a recognition. A
document with no recognitions had no candidates, so nothing inspected its
published transcription at all. `scripts/transcription_integrity.py` now
reports per published document.

### What was decided

All ten outputs were withdrawn on 2026-10-01 (#254): every input published so
far was a test input rather than a corpus the project meant to edition. Each
URL still resolves and carries a notice saying the output must not be cited,
each machine record is archived under `data/withdrawn/`, and the entity pages
derived from them are gone.

That settles what to do with `u-17`, `kf`, `kf-` and `order-001-group`, which
this page had listed as open editorial questions. It does **not** settle the
defects they exposed:

- **The `supersedes` inversion is still in the publishing path.** Nothing has
  changed upstream, so the next publication that retires an id can make a stub
  canonical again in exactly the same way.
- ~~**Published failure records still do not exist.**~~ Fixed. The records are
  written beside the catalogue that names them, and `write_catalogue` emits an
  `error_path` only for a record it wrote, so the two cannot drift apart again.
  The content was never lost — `write_package` always put the same provenance
  in the ZIP — but `catalogue.json` is a loose published artifact whose own
  `reuse_notice` tells a reader to cite the failure record, and a citation
  needs an address that resolves. A styled-site case now fetches every
  advertised record over HTTP, because checking the generator would not have
  caught a record that the themed build drops.
- **The ledger is still empty**, which is now trivially true: there is nothing
  published to reference. The BAT provenance above stands for whenever that
  material is published properly.

The integrity report keeps its value through the empty period: it reports on
published documents, so it says nothing today, and its test holds the finding
set to empty. A re-publication of material like this fails that test rather
than passing unnoticed.

One test moved as a consequence. `tests/integration/styled_site.mjs` used
`/u-17/` as its download-resolution fixture precisely because it was the only
document with mapped pages, and five of its cases assumed a non-empty
catalogue. They now run against a two-document synthetic corpus built by
`scripts/build_styled_fixture.sh`, so they no longer depend on what happens to
be published.
