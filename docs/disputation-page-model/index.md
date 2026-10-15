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
> **Unaffected:** the Schöni run, and the line model's readings of all 3,666 pages from September and October, which were checked digest by digest against their own manuscripts and are clean. **Hertwig** was read later the same day, after the fix, with its own cache and all ten digests verified; it was never touched by this.

Every handwriting model this project has fine-tuned reads **one line per call**, because one line is all it ever saw in training. That was measured rather than assumed, and the measurement was unkind: asked for a whole page, a line-trained model returns a short, fluent, wrong fragment and reports success. `qwen3.5-4b-german-kurrent-xvi-xix-page-v1` is the first fine-tune here trained at page granularity, so it is the first that may legitimately be asked for a page in one request.

It read **50 pages** — ten from each of the five Staatsarchiv Bern manuscripts of the Berner Disputation of 1528 — against the line model that had read all 3,666 pages of the same manuscripts in September and October. **[All fifty readings are published here](readings.html)**, both models side by side, with the digest of the scan each was made from.

**Two findings, and they pull apart.** The repetition loop is close to universal: **four of the five manuscripts lose exactly one page in ten to it**, and only the Schlussredaktion — the fair copy — loses none. But on the pages that do not degenerate, the page model is a perfectly ordinary reader almost everywhere: its text comes out within a few percent of the line model's length on Hertwig, Rümlang, Cyro and the Schlussredaktion, and it disagrees with it by 25–42 %. **Schöni is the exception on both counts** — there it writes 1.8 times as much text and disagrees by 53 %.

So the earlier formula — "competent on the fair copy, unreliable on the working copies" — was too neat. Degeneration is a property of the model that one manuscript happens to escape; over-writing is a property of one difficult hand.

## What was compared

| | |
|---|---|
| Material | German Kurrent, 1528, five scribal copies, Staatsarchiv Bern A V 1443–1447 |
| Page model | [`qwen3.5-4b-german-kurrent-xvi-xix-page-v1`](https://huggingface.co/dh-unibe/qwen3.5-4b-german-kurrent-xvi-xix-page-v1) · `granularity: page` · base Qwen3.5-4B · 20 training corpora, XVI–XIX |
| Line model | [`qwen3vl-medieval-german-v3`](https://huggingface.co/dh-unibe/qwen3vl-medieval-german-v3) · `granularity: line` · base Qwen3-VL-4B · 4 training corpora, XV–XVII |
| Sample | 10 pages per manuscript, drawn deterministically, 50 in total |
| Reference, where one exists | the edition's existing Transkribus transcriptions — **themselves machine output** |

The page model's own card reports **CER 0.2704** over 171 validation pages, and says plainly what that is: a seeded split of the training projects, so pages unseen in hands that *were* seen. A 1528 Bern chancery hand is not among those projects, and nothing here contradicts that figure.

## What the runs cost

| Run | Pages | Looped | Cut off | chars/page | s/page | Wall |
|---|---:|---:|---:|---:|---:|---:|
| `hertwig_page_v1` | 10 | 1 | 1 | 2216 | 26.1 | 9.4 min |
| `schoeni_page_v1` | 10 | 1 | 2 | 2008 | 34.1 | 12.8 min |
| `cyro_page_v1` | 10 | 1 | 1 | 1751 | 20.2 | 8.5 min |
| `ruemlang_page_v1` | 10 | 1 | 1 | 1639 | 24.4 | 9.1 min |
| `schlussredaktion_page_v1` | 10 | **0** | **0** | **1108** | **12.8** | 7.1 min |

No failures and no empty pages in 50 attempts. **Exactly one page in ten loops, in four manuscripts out of five** — a rate too regular to be about any one hand, and the Schlussredaktion is the only escape from it.

Characters per page is inflated in every row that contains a loop, which is most of them: Hertwig leads the column at 2216 only because one of its ten pages ran to 10,924 characters. The nine that did not average 1,248.

What degeneration looks like, from the Schöni run:

```
page_195:  lievander ich ist un̄ un̄ un̄ un̄ un̄ un̄ un̄ un̄ un̄ un̄ …   (5,490 characters)
page_631:  Mauri ubin / und / Mauri ubin / und / Mauri ubin / und …  (7,738 characters)
```

Both carry text and both returned HTTP 200. The runner's `looped` and `cut off` columns are what caught them; no measure that does not look at the text would have.

## How far the two readings diverge

| Manuscript | Pages compared | Median disagreement | 90th pct | chars/page, page model | chars/page, line model |
|---|---:|---:|---:|---:|---:|
| A V 1447 Schlussredaktion | 10 | **24.5 %** | 31.9 % | 1108 | 1133 |
| A V 1443 Hertwig | 8 | 29.4 % | 37.3 % | 1178 | 1176 |
| A V 1444 Cyro | 7 | 39.3 % | 65.2 % | 850 | 881 |
| A V 1446 Rümlang | 7 | 41.9 % | 45.9 % | 1089 | 1101 |
| A V 1445 Schöni | 7 | **53.4 %** | 96.0 % | **1515** | **849** |

**This is disagreement, not quality.** Without ground truth neither column says which reading is right. What it does say is where fusion could be worth trying at all, and the table now separates the manuscripts cleanly.

Four of the five sit between 24 % and 42 % with the two readings producing **almost exactly the same amount of text** — Hertwig is 1178 against 1176, two characters apart on average. That is the shape in which majority voting has been measured to help: comparable candidates whose errors are uncorrelated.

Schöni is the one that is not like the others. A 1.8× gap in characters per page and 96 % disagreement at the ninetieth percentile is the shape in which fusion has been measured to *hurt* — one candidate dominating a weaker one. Whatever makes that hand hard, it makes it hard for the page model specifically: the line model's output on Schöni (849 characters a page) is the shortest of the five, while the page model's (1515) is the longest.

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

It reproduces the scribe's abbreviations — `un̄`, `vˀschriben`, `ꝫ`, `hˀren`. Across the 45 pages that did not degenerate: **52 abbreviation marks from the page model against 5 from the line model.**

That total is concentrated, and the concentration is the point:

| | Schöni | Hertwig | Schlussredaktion | Cyro | Rümlang |
|---|---:|---:|---:|---:|---:|
| page model | **35** | 13 | 4 | 0 | 0 |
| line model | 0 | 3 | 0 | 1 | 1 |

Schöni's scribe contracts heavily, Hertwig's some, the other three barely at all. So this is not a general property of page models; it is a page model doing better on the manuscripts where there is something to get right — and Schöni, where it does best, is the one it is least reliable on overall.

A page model sees a line inside the scribe's system of contraction. A line model sees a crop.

## What this does not settle

- **50 pages**, one deterministic sample per manuscript, and the similarity figures rest on ten pages of one of them.
- **There is still no ground truth for any of these five manuscripts.** Every number here is a cost, a disagreement, or an agreement between two machines. Fifteen to twenty hand-transcribed pages would convert the third kind into a CER, and remain the cheapest way to make any of this decidable.
- **Why the Schlussredaktion escapes the loop, and why Schöni is hard, are both unexplained.** A more regular hand is the obvious reading for the first and an irregular one for the second, but layout, ink, line spacing and scan quality were not separated from the hand, and ten pages cannot separate them.
- **The loop rate of "one in ten" is four samples of ten.** It is strikingly regular, which is itself a reason to be careful with it: a rate that comes out identical four times on small samples may be telling us about the sample size rather than the model.
- **The token ceiling was not tuned.** Raising it would let a loop run further, not read better.

## What got in the way

Recorded because the next person will hit it.

### The cache collision
{: #the-cache-collision }

`atr-batch`'s `--cache-dir` **defaults to one shared directory**, and the working-copy cache keys a page by its path *relative to the source directory*. For `…/A_V_1444_Cyro/page_114.jpg` that key is `page_114.jpg`. The hit check then compares the basename and nothing else — not the directory, not a digest. Every manuscript here numbers its pages `page_N.jpg`, so the first run filled the cache and the next three read it back. Reported and **fixed** as [agentic_historian#663](https://github.com/thodel/agentic_historian/issues/663): the cache key now carries the corpus root, and the hit test compares the file's size as well as its name — size rather than a digest, because hashing the original would mean reading it, which is the cost the cache exists to avoid.

The damage followed the overlap exactly, which is how the cause was confirmed: Cyro drew the same ten page numbers as Schöni and got ten wrong pages; Rümlang drew five numbers Schöni had not and read precisely those five correctly; the Schlussredaktion drew two new ones and read two correctly.

Two things made it hard to see. Every run reported success — no failures, no empty pages, plausible timings. And the readings were *plausible*: early modern German in a Bern chancery hand, filed under a manuscript that looks like that. Only the recorded `sha256` of each source file gave it away, and the symptom that should have raised the alarm was the opposite of alarming — four supposedly independent samples returning **the same numbers**. A figure that reproduces exactly across independent samples is a reason to check whether they are independent.

The repeat passes `--cache-dir` per manuscript, and every one of the 50 digests was verified against its own manuscript directory before publication — a check that is now part of how these pages are published, not a thing remembered after a bad run.

### A refusal that reports success

Three runs also exited **instantly, with status 0**, on a card check:

```
NO qwen3.5-4b-german-kurrent-xvi-xix-page-v1: needs 15,848 MiB on card 1, 2,852 MiB free
     ours on card 1:  atr-gateway 13,498 MiB · atr-party 5,200 · atr-trocr 1,600
     not ours:         pid 3536436 (root) 22,334 MiB
```

An unrelated `ollama` server was holding 22 GB of the serving card. The check was also over-cautious — it sized a cold launch while the model was already resident and serving — and `--no-preflight` is the documented way past it. The sharper problem is the status code: **the runner returns 0 when it refuses to run**, so a script that chains four batches and tests their exit codes reports four successes in four seconds, having read nothing.
