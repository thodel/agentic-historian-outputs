---
layout: default
title: "A page model on the Berner Disputation"
---

> **Research publication, in English.** This page is part of the public site and is linked from [Forschung](../forschung.html), the German research index. It is not a working document: it records what was measured. The rest of the public site is German — see the [language policy](../about.html#sprachpolitik) for why this one is not.

# A page model on the Berner Disputation

> ## Correction, 15 October 2026 — three of the four runs read the wrong manuscript
> {: #correction-15-october-2026--three-of-the-four-runs-read-the-wrong-manuscript }
>
> The version published on 14 October reported a comparison across four manuscripts. **Three of those four runs never read the manuscript they were named after.** They re-read the first one, Schöni, because of a cache collision described under [the cache collision](#the-cache-collision). The runs have been repeated and every figure below now comes from the repeat; what the bad data had supported is listed here so the change is not silent.
>
> | run | pages from the right manuscript, 14 Oct | after the repeat |
> |---|---|---|
> | `schoeni_page_v1` | 10 of 10 | unchanged |
> | `cyro_page_v1` | **0 of 10** | 10 of 10 |
> | `ruemlang_page_v1` | 5 of 10 | 10 of 10 |
> | `schlussredaktion_page_v1` | 2 of 10 | 10 of 10 |
>
> **Withdrawn, and reversed by the repeat:** that the degeneration rate was identical across four hands and therefore a property of the model. It was the same ten Schöni pages four times. The corrected runs show the opposite — the rate depends strongly on the hand, and on one of the four manuscripts it is zero.
>
> **Withdrawn, and replaced:** the similarity table against the Schlussredaktion's transcription. It had scored a reading of *Schöni's* images against the *Schlussredaktion's* reference on 8 of 10 pages and produced a median of 0.16. The correct figure is **0.77**.
>
> **Unaffected:** the Schöni run, and the line model's readings of all 3,666 pages from September and October, which were checked digest by digest against their own manuscripts and are clean.

Every handwriting model this project has fine-tuned reads **one line per call**, because one line is all it ever saw in training. That was measured rather than assumed, and the measurement was unkind: asked for a whole page, a line-trained model returns a short, fluent, wrong fragment and reports success. `qwen3.5-4b-german-kurrent-xvi-xix-page-v1` is the first fine-tune here trained at page granularity, so it is the first that may legitimately be asked for a page in one request.

It read **40 pages** — ten each from four of the five Staatsarchiv Bern manuscripts of the Berner Disputation of 1528 — against the line model that had read all 3,666 pages of the same manuscripts in September and October. **[All forty readings are published here](readings.html)**, both models side by side, with the digest of the scan each was made from.

**The short version: the page model is a competent reader of the fair copy and an unreliable one of the working copies.** On the Schlussredaktion it lost no page to a loop, produced text of the same length as the page holds, and disagreed with the line model by 24.5 % at the median. On Schöni it lost one page in ten to a loop, wrote 1.8 times as much text as the line model, and disagreed by 53.4 %. The variable is the hand, not the model's general competence — which is the opposite of what this page claimed before the correction.

## What was compared

| | |
|---|---|
| Material | German Kurrent, 1528, four scribal copies, Staatsarchiv Bern A V 1444–1447 |
| Page model | [`qwen3.5-4b-german-kurrent-xvi-xix-page-v1`](https://huggingface.co/dh-unibe/qwen3.5-4b-german-kurrent-xvi-xix-page-v1) · `granularity: page` · base Qwen3.5-4B · 20 training corpora, XVI–XIX |
| Line model | [`qwen3vl-medieval-german-v3`](https://huggingface.co/dh-unibe/qwen3vl-medieval-german-v3) · `granularity: line` · base Qwen3-VL-4B · 4 training corpora, XV–XVII |
| Sample | 10 pages per manuscript, drawn deterministically, 40 in total |
| Reference, where one exists | the edition's existing Transkribus transcriptions — **themselves machine output** |

The page model's own card reports **CER 0.2704** over 171 validation pages, and says plainly what that is: a seeded split of the training projects, so pages unseen in hands that *were* seen. A 1528 Bern chancery hand is not among those projects, and nothing here contradicts that figure.

## What the runs cost

| Run | Pages | Looped | Cut off | chars/page | s/page | Wall |
|---|---:|---:|---:|---:|---:|---:|
| `schoeni_page_v1` | 10 | 1 | 2 | 2008 | 34.1 | 12.8 min |
| `cyro_page_v1` | 10 | 1 | 1 | 1751 | 20.2 | 8.5 min |
| `ruemlang_page_v1` | 10 | 1 | 1 | 1639 | 24.4 | 9.1 min |
| `schlussredaktion_page_v1` | 10 | **0** | **0** | **1108** | **12.8** | 7.1 min |

No failures and no empty pages in 40 attempts. The last row is the finding: on the Schlussredaktion — the fair copy, the most regular hand of the four — **nothing degenerated at all**, the reading came in at a length the page can actually hold, and it cost half the time per page of the worst of the others. The three working copies each lost one page in ten to a repetition loop.

What degeneration looks like, from the Schöni run:

```
page_195:  lievander ich ist un̄ un̄ un̄ un̄ un̄ un̄ un̄ un̄ un̄ un̄ …   (5,490 characters)
page_631:  Mauri ubin / und / Mauri ubin / und / Mauri ubin / und …  (7,738 characters)
```

Both carry text and both returned HTTP 200. The runner's `looped` and `cut off` columns are what caught them; no measure that does not look at the text would have.

## How far the two readings diverge

| Manuscript | Pages compared | Median disagreement | 90th pct | chars/page, page model | chars/page, line model |
|---|---:|---:|---:|---:|---:|
| A V 1445 Schöni | 7 | 53.4 % | 96.0 % | 1515 | 849 |
| A V 1444 Cyro | 7 | 39.3 % | 65.2 % | 850 | 881 |
| A V 1446 Rümlang | 7 | 41.9 % | 45.9 % | 1089 | 1101 |
| A V 1447 Schlussredaktion | **10** | **24.5 %** | **31.9 %** | 1108 | 1133 |

**This is disagreement, not quality.** Without ground truth neither column says which reading is right. What it does say is where fusion could be worth trying at all: the Schlussredaktion row — ten of ten pages comparable, lengths within 2 % of each other, only one page above the no-merge threshold — is the shape in which majority voting has been measured to help. The Schöni row, with a 1.8× gap in characters per page and 96 % disagreement at the ninetieth percentile, is the shape in which it has been measured to hurt.

## The one measurement that points at quality

All ten sampled Schlussredaktion pages carry an existing transcription, so both models can be set against the same third reading of the same pages:

| Page | reference | page model | line model | sim. page | sim. line |
|---|---:|---:|---:|---:|---:|
| `page_29` | 998 | 935 | 949 | 0.75 | **0.85** |
| `page_82` | 1125 | 946 | 1068 | 0.71 | **0.80** |
| `page_95` | 1065 | 997 | 991 | 0.78 | **0.86** |
| `page_114` | 1191 | 1142 | 1108 | 0.80 | **0.88** |
| `page_194` | 980 | 977 | 985 | 0.69 | **0.84** |
| `page_195` | 867 | 866 | 873 | 0.76 | **0.85** |
| `page_406` | 1438 | 1331 | 1392 | 0.75 | **0.80** |
| `page_631` | 1348 | 1345 | 1342 | 0.80 | **0.86** |
| `page_690` | 1151 | 1136 | 1181 | 0.81 | **0.84** |
| `page_746` | 1383 | 1401 | 1403 | 0.84 | **0.87** |
| **median** | | | | **0.77** | **0.85** |

The line model is ahead on all ten, but by a consistent and modest margin — 0.77 against 0.85 — and the page model's lengths now track the reference closely (935–1,401 characters against 998–1,438). This is two competent readers of the same page, not a reader and a failure.

**The reference is not ground truth, and the argument has to be explicit about it.** Those transcriptions are a Transkribus model's output, not a human's. What makes the comparison worth anything is that the line model's agreement with them is *reproducible at scale*: 0.84 across all 665 transcribed pages of this manuscript, 0.85 across these ten. Two systems trained on different material by different people converge; the page model sits a little below both. None of these three numbers is an accuracy.

## What the page model does better

It reproduces the scribe's abbreviations — `un̄`, `vˀschriben`, `ꝫ`, `hˀren`. Across the 36 pages that did not degenerate: **39 abbreviation marks from the page model against 2 from the line model.**

That total is concentrated, and the concentration is the point: **35 of the 39 are on Schöni**, four on the Schlussredaktion, none on Cyro or Rümlang. Schöni's scribe contracts heavily and the other three barely do. So this is not a general property of page models; it is a page model doing better on the one manuscript where there is something to get right — and that is, incidentally, the manuscript it is least reliable on overall.

A page model sees a line inside the scribe's system of contraction. A line model sees a crop.

## What this does not settle

- **40 pages**, one deterministic sample per manuscript, and the similarity figures rest on ten pages of one of them.
- **There is still no ground truth for any of these five manuscripts.** Every number here is a cost, a disagreement, or an agreement between two machines. Fifteen to twenty hand-transcribed pages would convert the third kind into a CER, and remain the cheapest way to make any of this decidable.
- **Why the fair copy is easier is not established.** A more regular hand is the obvious reading, but layout, ink and scan quality were not separated.
- **The token ceiling was not tuned.** Raising it would let a loop run further, not read better.

## What got in the way

Recorded because the next person will hit it.

### The cache collision
{: #the-cache-collision }

`atr-batch`'s `--cache-dir` **defaults to one shared directory**, and the working-copy cache keys a page by its path *relative to the source directory*. For `…/A_V_1444_Cyro/page_114.jpg` that key is `page_114.jpg`. The hit check then compares the basename and nothing else — not the directory, not a digest. Every manuscript here numbers its pages `page_N.jpg`, so the first run filled the cache and the next three read it back. Reported as [agentic_historian#663](https://github.com/thodel/agentic_historian/issues/663).

The damage followed the overlap exactly, which is how the cause was confirmed: Cyro drew the same ten page numbers as Schöni and got ten wrong pages; Rümlang drew five numbers Schöni had not and read precisely those five correctly; the Schlussredaktion drew two new ones and read two correctly.

Two things made it hard to see. Every run reported success — no failures, no empty pages, plausible timings. And the readings were *plausible*: early modern German in a Bern chancery hand, filed under a manuscript that looks like that. Only the recorded `sha256` of each source file gave it away, and the symptom that should have raised the alarm was the opposite of alarming — four supposedly independent samples returning **the same numbers**. A figure that reproduces exactly across independent samples is a reason to check whether they are independent.

The repeat passes `--cache-dir` per manuscript, and every one of the 40 digests was verified against its own manuscript directory before publication.

### A refusal that reports success

Three runs also exited **instantly, with status 0**, on a card check:

```
NO qwen3.5-4b-german-kurrent-xvi-xix-page-v1: needs 15,848 MiB on card 1, 2,852 MiB free
     ours on card 1:  atr-gateway 13,498 MiB · atr-party 5,200 · atr-trocr 1,600
     not ours:         pid 3536436 (root) 22,334 MiB
```

An unrelated `ollama` server was holding 22 GB of the serving card. The check was also over-cautious — it sized a cold launch while the model was already resident and serving — and `--no-preflight` is the documented way past it. The sharper problem is the status code: **the runner returns 0 when it refuses to run**, so a script that chains four batches and tests their exit codes reports four successes in four seconds, having read nothing.
