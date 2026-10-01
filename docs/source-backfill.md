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
| `BAT_664_r_00027` | model-written description states "Bern, Burgerbibliothek, BAT664" with `unsicher: false`; page id `BAT_664_r_00027.jpg` | Burgerbibliothek Bern, BAT 664 |
| `bat` | page id `BAT_663_r_00050.jpg` | Burgerbibliothek Bern, BAT 663 |
| `koenige`, `kf`, `order-ens`, `order-001-group` | nothing in the record identifies an original | none |

## Inconsistencies to resolve first

Two of these need answering before any entry is written, because a ledger
entry would otherwise record a contradiction as a fact.

1. **`bat` and `BAT_664_r_00027` disagree about the institution.** The
   `BAT_664_r_00027` description says Burgerbibliothek Bern; the `bat`
   description says "Staatsarchiv des Kantons Bern (unsicher)". Both are
   model-written. At most one can be right for the BAT shelfmarks.
2. **`u-17` mixes two identifiers.** Its transcript page id is
   `U-17_0057_r.jpg`, but its mapped source pages are `e-codices_saa-0428_*`,
   and `koenige`'s transcript carries the same `U-17_0057_r.jpg` page id. So
   either `u-17` and `koenige` transcribe the same image, or the page mapping
   on `u-17` belongs to `saa-0428`. The mapping is what the evidence viewer
   shows a reader, so this decides whether the one embeddable facsimile on the
   site is attached to the right document.

Both are questions about the existing data, not about missing data, and
neither can be settled from the repository alone.
