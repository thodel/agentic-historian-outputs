---
layout: default
title: "A page model on the Berner Disputation"
---

> **Research publication, in English.** This page is part of the public site and is linked from [Forschung](../forschung.html), the German research index. It is not a working document: it records what was measured. The rest of the public site is German — see the [language policy](../about.html#sprachpolitik) for why this one is not.

# A page model on the Berner Disputation

Every handwriting model this project has fine-tuned reads **one line per call**, because one line is all it ever saw in training. That was measured rather than assumed, and the measurement was unkind: asked for a whole page, a line-trained model returns a short, fluent, wrong fragment and reports success. `qwen3.5-4b-german-kurrent-xvi-xix-page-v1` is the first fine-tune here trained at page granularity, so it is the first that may legitimately be asked for a page in one request.

On 14 October 2026 it read **40 pages** — ten each from four of the five Staatsarchiv Bern manuscripts of the Berner Disputation of 1528 — against the line model that had read all 3,666 pages of the same manuscripts in September and October. This page records what that showed.

**The short version: on this material the page model is clearly the worse reader**, and the one measurement here that points at quality says so without ambiguity. That is not a verdict on the model, which was trained for four centuries of German and measures well on its own validation split. It is a verdict on this corpus.

## What was compared

| | |
|---|---|
| Material | German Kurrent, 1528, five scribal copies of the Bern disputation, Staatsarchiv Bern A V 1443–1447 |
| Page model | [`qwen3.5-4b-german-kurrent-xvi-xix-page-v1`](https://huggingface.co/dh-unibe/qwen3.5-4b-german-kurrent-xvi-xix-page-v1) · `granularity: page` · base Qwen3.5-4B · 20 training corpora, XVI–XIX |
| Line model | `qwen3vl-medieval-german-v3` · `granularity: line` · base Qwen3-VL-4B · 4 training corpora, XV–XVII |
| Sample | 10 pages per manuscript, drawn deterministically, 40 in total |
| Reference, where one exists | the edition's existing Transkribus transcriptions — **themselves machine output**, see below |

The page model's own card reports **CER 0.2704** over 171 validation pages, and says plainly what that is: a seeded split of the training projects, so pages unseen in hands that *were* seen. Nothing on this page contradicts that figure. A 1528 Bern chancery hand is not in those projects.

## What the runs cost

| Run | Pages | Looped | Cut off | chars/page | s/page | Wall |
|---|---:|---:|---:|---:|---:|---:|
| `schoeni_page_v1` | 10 | 1 | 2 | 2008 | 34.1 | 12.8 min |
| `cyro_page_v1` | 10 | 1 | 2 | 2008 | 34.3 | 10.7 min |
| `ruemlang_page_v1` | 10 | 1 | 2 | 1908 | 35.0 | 10.8 min |
| `schlussredaktion_page_v1` | 10 | 1 | 2 | 2009 | 34.7 | 10.8 min |

No failures and no empty pages in 40 attempts. But **one page in ten degenerated into a repetition loop, and two in ten stopped only because they hit the token ceiling** — and that happened in every one of the four manuscripts, in the same proportion. The consistency is the finding: four different scribal hands, one failure rate. It is a property of the model on this kind of material, not of a difficult hand.

What degeneration looks like here:

```
page_195:  lievander ich ist un̄ un̄ un̄ un̄ un̄ un̄ un̄ un̄ un̄ un̄ …   (5,490 characters)
page_631:  Mauri ubin / und / Mauri ubin / und / Mauri ubin / und …  (7,738 characters)
```

Both carry text, both returned HTTP 200, and both would be counted as successful readings by any measure that does not look. The batch runner's `looped` and `cut off` columns are what caught them.

## How far the two readings diverge

| Manuscript | Pages compared | Median disagreement | 90th pct | chars/page, page model | chars/page, line model |
|---|---:|---:|---:|---:|---:|
| A V 1445 Schöni | 7 | 53.4 % | 96.0 % | 1515 | 849 |
| A V 1444 Cyro | 7 | 71.9 % | 95.1 % | 1523 | 912 |
| A V 1446 Rümlang | 7 | 43.3 % | 93.8 % | 1564 | 1101 |
| A V 1447 Schlussredaktion | 9 | 70.0 % | 95.6 % | 1372 | 1109 |

**This is disagreement, not quality.** Without ground truth neither column says which reading is right, and a model that hallucinates fluently disagrees exactly as much as one that reads badly. What it does say is that the two readings are not candidates for fusion: the pattern here — a wide gap in characters per page, disagreement above the no-merge threshold on nearly every page — is the case where majority voting has been measured *losing* to the better single reader.

## The one measurement that points at quality

The Schlussredaktion is the only one of the five manuscripts that carries an existing transcription for nearly every page. All ten sampled pages have one, so both models can be set against the same third reading on the same pages:

| Page | reference | page model | line model | sim. page | sim. line |
|---|---:|---:|---:|---:|---:|
| `page_29` | 998 | 868 | 949 | 0.17 | **0.85** |
| `page_82` | 1125 | 946 | 1068 | 0.71 | **0.80** |
| `page_95` | 1065 | 997 | 991 | 0.78 | **0.86** |
| `page_114` | 1191 | 839 | 1108 | 0.16 | **0.88** |
| `page_194` | 980 | 824 | 985 | 0.11 | **0.84** |
| `page_195` | 867 | 5490 | 873 | 0.06 | **0.85** |
| `page_406` | 1438 | 756 | 1392 | 0.21 | **0.80** |
| `page_631` | 1348 | 7738 | 1342 | 0.02 | **0.86** |
| `page_690` | 1151 | 760 | 1181 | 0.18 | **0.84** |
| `page_746` | 1383 | 869 | 1403 | 0.08 | **0.87** |
| **median** | | | | **0.16** | **0.85** |

The page model is behind on **ten pages out of ten**, and not narrowly. Its best page (0.78) is below the line model's worst (0.80). The line model sits between 0.80 and 0.88 on every page; the page model swings from 0.02 to 0.78.

**The reference is not ground truth, and this is where the reasoning has to be explicit.** Those transcriptions are themselves machine output — a Transkribus model's reading, not a human's. Measuring one machine against another is not a CER, and this page does not call it one. What carries the argument is that the line model's agreement with that reference is *reproducible at scale*: 0.84 median over all 665 pages of this manuscript that carry a transcription, and 0.85 over these ten. Two systems trained on entirely different material, by different people, converge. The page model agrees with neither. When two independent readers agree at 0.85 and a third agrees with both at 0.16, the third is the outlier — an inference, not a proof, but not a weak one.

The length column says the same thing twice over. Where the page model does not loop, it **under-reads**: 756–997 characters against a page holding 867–1,438. It stops early. Where it does loop, it produces five to eight thousand.

## What the page model does better

One thing, and it is not nothing. On the eight Schöni pages that did not degenerate, the page model reproduced **34 scribal abbreviation marks** — `un̄`, `vˀschriben`, `ꝫ`, `hˀren`. The line model, on the same ten pages, produced **zero**. A page model sees the line in the context of the page and the scribe's system of contraction; a line model sees a crop.

For an edition that cares about what the scribe actually wrote rather than what he meant, that is the right behaviour, and no amount of accuracy elsewhere substitutes for it. It is also, at present, attached to a reader that loses control of one page in ten.

## What this does not settle

- **40 pages.** One deterministic sample per manuscript. The degeneration rate is consistent across four hands, which makes it unlikely to be sampling noise, but the similarity figures rest on ten pages of one manuscript.
- **There is still no ground truth for any of these five manuscripts.** Every number on this page is either a cost, a disagreement, or an agreement between two machines. Fifteen to twenty hand-transcribed pages would convert the third category into a CER and are the cheapest way to make any of this decidable.
- **The token ceiling was not tuned for this model.** Two pages in ten stopped at the ceiling; a higher one would let a loop run further, not read better. Nothing here was re-run at a different budget.
- **The line model is not thereby good.** It agrees with another machine. On Schöni, where the existing transcription is itself poor, both readers score around 0.4 against it and the question stays open.

## What got in the way

Recorded because the next person will hit it.

Three of the four runs first exited **instantly, with status 0**, on a card check:

```
NO qwen3.5-4b-german-kurrent-xvi-xix-page-v1: needs 15,848 MiB on card 1, 2,852 MiB free
     ours on card 1:  atr-gateway 13,498 MiB · atr-party 5,200 · atr-trocr 1,600
     not ours:         pid 3536436 (root) 22,334 MiB
```

An unrelated `ollama` server had been holding 22 GB of the serving card for seven and a half hours. The check was also over-cautious: it sized a *cold* launch while the model was already resident and serving. `--no-preflight` is the documented way past it and was the right answer here.

The sharper problem is the status code. **The runner returns 0 when it refuses to run**, so a script that chains four batches and tests their exit codes reports four successes in four seconds, having read nothing. That is how this test first appeared to finish before it had started.
