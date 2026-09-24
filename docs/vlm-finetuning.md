---
layout: default
title: "Fine-tuning vision models: what fifteen runs taught us"
---

> **Internal engineering document.** This page is a working document for project contributors. It is not part of the public-facing German site and is not linked from the global navigation. See the [language policy](about.html#sprachpolitik) for context.

# Fine-tuning vision models: what fifteen runs taught us

The [recognition engine evaluation](evaluation.html) measures engines this project did not build: published Transkribus models, TrOCR and kraken checkpoints from the hub, commercial and local vision models used zero-shot. This page is about the other half — the fifteen vision-language models fine-tuned for this project on Swiss and German material between 2026-09-03 and 2026-09-24, and what went wrong often enough to be worth writing down.

Almost none of the lessons are about hyperparameters. Every one of them is about **what the model was shown, and what the number it was judged by actually measured**.

As on the evaluation page, this records what was measured. Where an earlier claim of ours turned out to be wrong — and several did — the correction is stated rather than quietly applied.

## The runs

Two corpora, two bases, four model sizes, four sample granularities.

| Family | Base | Corpus | Runs |
|---|---|---|---|
| `qwen3vl-medieval-german-v1…v3` | Qwen3-VL-4B | four German corpora, 1300–1600 · 306 582 training lines | 3 |
| `qwen3.5-{4b,2b,0.8b}-medieval-german-v1` | Qwen3.5 | the same | 3 |
| `qwen3vl-german-xix-v1, v2` | Qwen3-VL-4B | Zurich government minutes, federal protocols, kurrent-xix · 964 472 lines | 2 |
| `qwen3.5-{4b,2b,0.8b}-german-xix-v{1,2}` | Qwen3.5 | the same | 5 |
| `qwen3vl-german-xix-block-v1`, `-page-v1` | Qwen3-VL-4B | the same, cut into blocks of six lines / whole pages | 2 |

Each is a QLoRA adapter over a frozen base, one epoch, trained on one H100 (UBELIX) or two A40s. A 19th-century run costs 4–10 GPU-hours; building its corpus costs 2–16 CPU-hours, most of it copying files.

## 1. The ground truth decided everything

The first generation of both families was bad in a way no hyperparameter explains. The medieval model read its own validation split at **53.2 %** CER. The 19th-century models scored 25.5–36.0 % on the [Federal Council benchmark](https://doi.org/10.5281/zenodo.4746342) and, on 18–29 % of its lines, wrote **little more than the first word and stopped**.

The cause was in the corpus, not the training. Transkribus exports word segmentation as `<Word>` children, each with its own `TextEquiv/Unicode`, and those come *before* the line's own `TextEquiv` in document order. A reader taking the first `Unicode` under a `TextLine` therefore returns word one and drops the rest of the line. Two of the corpora were affected severely: after the fix, `nr-sr-vereinigte-bundesversammlung-xix` carried 6.35× the characters it had before, `parlamentsdienste-protokolle` 4.54×.

The models had learned the corpus exactly: on this kind of page, write the first word.

| Model | before the fix | after | collapsed lines, before → after |
|---|---:|---:|---|
| `qwen3.5-4b-german-xix` | 35.96 % | **6.80 %** | 807 of 2 751 (29.3 %) → **0** |
| `qwen3vl-german-xix` | 25.51 % | **7.65 %** | 507 (18.4 %) → **0** |
| `qwen3.5-2b-german-xix` | 29.37 % | **8.95 %** | 611 (22.2 %) → **0** |
| `qwen3.5-0.8b-german-xix` | — | 11.15 % | — → **0** |
| `qwen3vl-medieval-german` | 53.2 % (own split) | **11.1 %** (held-out) | — |

Retraining changed nothing but the corpus — same repositories, same seed, same page-level split, same hyperparameters. The collapse did not shrink, it **disappeared**, in four independent runs across two model families and a 5× spread in parameters.

Two things follow that are easy to miss:

**The ranking was wrong, not just the numbers.** Qwen3.5-4B was the *worst* of the three first-generation models and is the *best* of the second. A model-selection decision taken on the first grid would have picked the wrong family. The defect did not affect all models equally, so it could not be cancelled out by comparing them.

**Scaling only looks like scaling once the data is right.** After the fix: 0.8B 11.15 %, 2B 8.95 %, 4B 6.80 % — monotone. Before it, the 4B model was worse than the 2B. A corpus that truncates a third of its characters rewards a model for stopping early, and the more capable the model, the more reliably it learns to.

## 2. Three explanations, two of them wrong

Before the parser was found, two other causes were proposed, and each was dropped only because it was measured.

**Short training lines.** The medieval corpus has a long tail of one- and two-character lines, so a minimum-length filter was added. It moved the CER from 53.22 % to 49.95 % — real, and nowhere near an explanation. It treated a symptom of the parser bug: those short "lines" were truncated ones.

**Block crops.** The suspicion was that mis-segmented crops covering several lines were poisoning the training. Measured, they accounted for at most 6.5 % of the error. Dropped.

**The parser.** Proved on one page (7.2× more characters after the fix), then corpus-wide (1.47×), then definitively by retraining.

The rule this produced, and which has since caught two further wrong guesses on this page: **a fix must match the symptom.** A cause that explains a fifth of the error is not the cause, however plausible it sounds.

## 3. What the number was measured on

The first-generation models reported a validation CER around **1 %**. On the published benchmark the same models scored **25–36 %**.

Both numbers were correct. The 1 % was measured on the first 200 lines of `val.jsonl` — five pages, from documents that also appear in training, in hands the model had learned. The evaluator took the head of a file that is written one dataset after another, so for a multi-dataset job it scored the first dataset only. One run reported 97.56 % CER over 196 pages of one source and four pages of everything else.

The fixes were structural: a stratified draw with an equal share per source, per-source metrics in every report, and for the 19th century a held-out benchmark that shares no document with training. A single figure over five sources describes none of them — the same run read one source at 38 % and another at 191 %.

The general form: **an in-domain validation split measures convergence, not accuracy.** It is the right number for "did this run work" and the wrong number for "how well does this model read".

## 4. A model reads the unit it was trained on

All the models above were trained on **line crops**, and served the same way. The obvious question — can they read a whole page in one call, or at least a paragraph? — turned out to have a sharp answer.

Measured against ground truth on held-out pages:

| Input | `qwen3vl-medieval-german-v3` | `qwen3vl-german-xix-v2` |
|---|---:|---:|
| line crops | **11.1 %** | **5.2 %** |
| paragraphs (one `TextRegion`) | 196 % · 7 % of the text returned | 95 % · 5 % |
| whole pages | 100 % · length ratio 0.001 | 98 % · length ratio 0.03 |

The medieval model answered **every one of 14 pages with two characters** — "de", thirteen times, and once "te". The 19th-century model is worse in the way that matters more: it returns one fluent German line per page, often a line that is not on the page. A Zurich protocol page beginning "thur, zu einer Zuchthaus-Korrektion …" came back as "Hochzeitlich in der Stadt".

Two models were then trained on the same corpus, same seed, same split, changing only the unit: blocks of six consecutive lines, and whole pages. Measured on the same 15 pages, all four levels:

| | lines | blocks of 6 | paragraphs | whole pages |
|---|---:|---:|---:|---:|
| line-trained (`v2`) | **5.2 %** | 81 % · ratio 0.21 | 95 % | 98 % · ratio 0.03 |
| block-trained | 8.4 % | **14.5 %** | 26.8 % | 113 % · ratio 1.34 |
| page-trained | 43.5 % · ratio 1.26 | 35.7 % | **11.6 %** | **32.3 %** · ratio 1.12 |

**The failure is asymmetric, and that is the practical finding.** A line-trained model given a page **stops** — it returns 3 % of the text, which any length check catches. A page-trained model given a line **keeps writing** — fluent, plausible German that is not on the image, at a length ratio of 1.26. The loud failure is the safe one.

Three further observations:

- **A paragraph is not a `TextRegion`.** Transkribus exported these corpora with one region per page, median 21–40 lines. The intermediate unit had to be constructed: runs of consecutive lines, never crossing a region boundary and never crossing a line that is on the image without a transcription.
- **The crop beats the page.** The page-trained model reads the same text as a paragraph crop at 11.6 % and as a full scan at 32.3 %. The margins of a scan cost more than they contribute.
- **Whole pages are within reach for this material.** On its own validation split the page model reads 102 complete pages at **8.0 %**, length ratio 1.004; on the five Zurich pages of the comparison set at 4.8 %. Its corpus-wide 32.3 % is carried by two sparsely written pages where it over-generates: 485 reference characters answered with 2 420.

The block model's penalty on lines is uniform rather than an artefact of a few pages: it is worse than the line model on 14 of 15 pages, by 0.2 to 8.3 points, smallest on the easiest source and largest on the hardest.

## 5. Two more hypotheses that measurement killed

**"A page gives each line a quarter of the resolution."** Plausible arithmetic — 2 048 visual tokens for a page of 40 lines against 256 for one line — and wrong. Line crops never fill their budget, because a crop is small and is never upscaled. Measured on the image: a line inside a whole page keeps **74–77 %** of the height it has as a crop, 65–89 pixels, comfortably legible. For the 19th-century corpus resolution is not the bottleneck. (For the medieval corpus it may still be: those scans are 19.9 megapixels and are reduced to about a third.)

**"Pages are too long for the token budget."** Also wrong, and also cheap to check: the longest page in the corpus needs about 1 800 tokens against a budget of 4 096, at roughly three characters per token. Both hypotheses were about the model; the answer was again about the data — the model had simply never seen a page.

## 6. What this costs in practice

Operational lessons, recorded because each cost time or someone else's service:

- **Never evaluate against the production gateway.** One measurement run competed with a live caller for the single card the serving box has; the caller got three 502s and a 503 within a minute. Evaluation now runs on the training machine with its own server, bound to localhost.
- **Serving a new architecture is not a pip install.** Qwen3.5 needs a vLLM the serving box's driver could not run — until it turned out that only the *default* build was out of reach and the CUDA 12.9 build runs fine. The conclusion "a driver upgrade is required" had been derived from a version table rather than tested.
- **A measurement environment is 20–30 GB and three machines.** Building it by hand four times produced two self-inflicted outages and one forgotten 260 GB of leftovers. It is being automated.
- **Say what a job will take.** A scheduler that caps CPU-minutes reserves against the *declared* limit, so a 20-hour limit on a 7-hour job blocks a colleague's run for the difference.

## Open questions

- **Over-generation on sparse pages** is the page model's remaining weakness and the same failure the medieval page model shows. Neither a larger nor a smaller pixel budget addresses it.
- **A mixed run** — lines, blocks and pages in one training set, each at its own budget — is queued. It should hold the line accuracy *and* read pages; if it lands between the two on every level instead, the honest conclusion is two models rather than one.
- **There is no page-level benchmark** with ground truth that no run has seen. The published Federal Council test set is 2 751 isolated lines. Until one exists, page numbers are measured on held-out pages of our own corpora, which is weaker.

## Provenance

Every figure here comes from a stored evaluation report of a named run, on a named set of pages, and the corrections are recorded in the issue trackers of `thodel/serving-atr-inference` and `thodel/training-atr-models` rather than only in this summary. The measuring instrument for the granularity table is `scripts/eval_granularity.py` in the serving repository: it asks one model the same pages four ways and reports, besides CER, the two failure shapes an average hides — collapse (under a third of the reference) and runaway (over 1.5 times it).
