---
layout: default
title: "Fine-tuning vision models: what twenty-two runs taught us"
---

> **Research publication, in English.** This page is part of the public site and is linked from [Forschung](forschung.html), the German research index. It is not a working document: it records what was measured. The rest of the public site is German — see the [language policy](about.html#sprachpolitik) for why this one is not.

# Fine-tuning vision models: what twenty-two runs taught us

The [recognition engine evaluation](evaluation.html) measures engines this project did not build: published Transkribus models, TrOCR and kraken checkpoints from the hub, commercial and local vision models used zero-shot. This page is about the other half — the nineteen vision-language models fine-tuned for this project on Swiss and German material between 2026-09-03 and 2026-09-26, and what went wrong often enough to be worth writing down.

Almost none of the lessons are about hyperparameters. Every one of them is about **what the model was shown, and what the number it was judged by actually measured**.

As on the evaluation page, this records what was measured. Where an earlier claim of ours turned out to be wrong — and several did — the correction is stated rather than quietly applied.

## The runs

Two corpora, **three** bases, six model sizes, four sample granularities.

| Family | Base | Corpus | Runs |
|---|---|---|---|
| `qwen3vl-medieval-german-v1…v3` | Qwen3-VL-4B | four German corpora, 1300–1600 · 306 582 training lines | 3 |
| `qwen3.5-{4b,2b,0.8b}-medieval-german-v1` | Qwen3.5 | the same | 3 |
| `qwen3vl-german-xix-v1, v2` | Qwen3-VL-4B | Zurich government minutes, federal protocols, kurrent-xix · 964 472 lines | 2 |
| `qwen3.5-{4b,2b,0.8b}-german-xix-v{1,2}` | Qwen3.5 | the same | 5 |
| `qwen3vl-german-xix-block-v1`, `-page-v1`, `-mixed-v1` | Qwen3-VL-4B | the same, cut into blocks of six lines / whole pages / all three mixed | 3 |
| `qwen3vl-medieval-german-page-v1`, `qwen3.5-4b-…-page-v1` | Qwen3-VL-4B, Qwen3.5-4B | the medieval corpus, whole pages | 2 |
| `gemma-4-{E4B,12B}-it` on the medieval corpus | Gemma 4 | the same, lines and whole pages | 3 |
| `gemma-4-{E4B,12B}-it` on the 19th century, `gemma-4-12B` on the medieval pages | Gemma 4 | both corpora | 2 landed 2026-10-03/04, 1 running |

Each is a QLoRA adapter over a frozen base, one epoch, trained on one H100 (UBELIX) or two A40s. A 19th-century run costs 4–10 GPU-hours; building its corpus costs 2–16 CPU-hours, most of it copying files. Later runs cost nothing to prepare at all: the compiled corpus is content-addressed and the base model is not part of its key, so a second base trains on the first one's bytes and, more importantly, on its split.

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

There is a third way to lose the draw, and it is the quietest: the run never makes one. A
compiled corpus is content-addressed and can be adopted by a later run instead of rebuilt, which
is what makes a second base free — but the cached entry carries only the counts someone thought to
put in it, and the per-source page counts were not among them. A run that adopts an entry therefore
has no idea which source a page came from, and its evaluator falls back from a stratified draw to a
random one, saying so in a single log line nobody reads: `0 source(s) could be attributed, so no
strata`. Two of the page arms below were scored that way. The numbers are sound; they are simply
not on the same 200 pages, so the small differences between them are not comparable at the
0.6-point resolution this section establishes.

**It happened a third time, on 2026-10-04, and this time the split was shared.** The 19th-century Gemma E4B arm takes its corpus from the Qwen3-VL run by symlink — `crops`, `train.jsonl` and `pages_val.lst` all point into that job's directory, so the training data and the page-level split are the same bytes. Its evaluation draw is not: the stratification is computed from `job.progress.dataset_counts`, which belongs to the **job** and not to the corpus, so an arm that adopted an artefact rather than compiling one plans a different subset out of the same pool. The four Qwen arms of that ladder share one `data/val_eval.jsonl` byte for byte; the Gemma arm wrote its own. **The check is one line** — compare the md5 of `data/val_eval.jsonl` across the arms before putting their CERs in one table — and it is now the first thing done to a ladder.

The same mistake was nearly made again a year later, in a smaller way, and it is worth recording because the fix is cheap. Two runs on the same corpus and the same split reported 14.27 % and 16.88 %, and the difference looked like a result. Each run's evaluation subset, however, is drawn at test time — and the two draws **overlapped in 4 of 200 samples**. Re-scoring the first model on the second's subset gave 13.65 %, which made the comparison real. It also produced, for the first time, an error bar: the same model on two draws from the same pool differs by **0.6 points**, so nothing smaller than that is a finding at all.

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

### The medieval corpus reads pages too, and the second family reads them worst

Everything above is the 19th century. The medieval corpus — older hands, 20-megapixel scans, many
short charters — was trained at page granularity three times, one arm per base, on one shared
corpus and one shared split:

| Arm | Base | CER | WER | length ratio | CER without truncations |
|---|---|---:|---:|---:|---:|
| `qwen3.5-4b-medieval-german-page-v1` | Qwen3.5-4B | **41.6 %** | 69.3 | 1.08 | **30.7 %** |
| `qwen3vl-medieval-german-page-v1` | Qwen3-VL-4B | 42.7 % | 76.6 | 1.13 | 31.6 % |
| `gemma4-e4b-medieval-german-page-v1` | Gemma-4-E4B | 51.8 % | 90.1 | 1.10 | 39.0 % |

The two Qwen arms are a point apart on different draws, which by §3 is not a finding. Gemma is
nine points behind, which is.

**All five page arms, re-scored onto one draw** (164 pages, 2026-10-05). The CER column above is
each arm's own draw; this one is comparable across rows, and it moves three of them:

| Arm | CER, one draw | own draw | s/step at micro-batch 2 × 8 |
|---|---:|---:|---:|
| `olmocr2-7b-medieval-german-page-v1` | **34.9 %** | — | 29.1 |
| `qwen3.5-4b-medieval-german-page-v1` | 37.6 % | 41.6 % | 24.3 |
| `qwen3vl-medieval-german-page-v1` | 42.7 % | — | 10.3 |
| `gemma4-e4b-medieval-german-page-v1` | 55.0 % | 51.8 % | 9.1 |
| `gemma4-12b-medieval-german-page-v1` | 96.2 % | — | 13.7 (micro 1 × 16) |

The draw was worth 4.0 points to one arm and −3.2 to another, so the ordering of the two Qwen arms
survives and its size does not: 5.1 points apart, not 1.1. Gemma's deficit grows from nine points to
seventeen. And the cost column changes how the winner reads: olmOCR's 2.7 points over the
next-best cost 20 % more time per step, while its 7.7 points over `qwen3vl` cost 180 % more. And it is behind for a reason that inverts the expectation the run
was submitted with: Gemma spends a fixed token budget per image whatever the image is, so a line
costs nearly what a page costs — the penalty should be *smallest* where the image really is a whole
page. It is largest there, and it survives removing the truncations, so it is not an early-stopping
artefact. It reads pages less well — and it runs into the generation cap on **30** of its 200
pages where the two Qwen arms do on 15, so it also over-generates on twice as many.

**What the page numbers mean at all** took a paired comparison to establish. The two Qwen arms'
evaluation draws overlap in 33 pages; scored on those alone, against the same ground truth, they
come out at 37.0 % and 32.9 % — and, with the truncated pages removed, at **34.07 % and 34.09 %**.
Identical. The entire measured difference between two page models on the same corpus was the
handful of pages one of them ran into the generation cap on.

That points at the same weakness from the other side. Taking the length ratio page by page on one
arm's 164 pages: the median is **1.00**, the 10th and 90th percentiles are 0.94 and 1.39, and 148
of 164 pages sit inside a factor of 1.5 either way. On a normal page the text quantity is right.
**Fifteen pages are not normal**: all fifteen ran to the generation cap, and together they answer
9 243 reference characters with 33 955 — roughly 24 700 characters that are not on any page. One
answers 19 reference characters with 1 545. The corpus-wide CER of 42.7 % is 31.6 % without them.

So the practical finding of the medieval page work is not a ranking of bases. It is that a page
model on this material is already usable on the pages that carry text, and that the remaining error
is concentrated in a failure mode — write until the cap on a nearly empty page — which no pixel
budget has moved and which a length check catches for free.

### A family whose strong granularity is the page

A sixth base was then trained on the same medieval corpus at both granularities:
`allenai/olmOCR-2-7B-1025`, which is not a general vision model but a Qwen2.5-VL fine-tuned by its
authors on document OCR. It is the first family measured here whose two granularities come out the
other way round.

| | Lines (200 samples, one draw) | Pages (164 pages, one draw) |
|---|---:|---:|
| `olmocr2-7b` | **74.6 %** | **34.9 %** |
| best other arm on that draw | 12.1 % (`qwen3.5-9b`) | 42.7 % (`qwen3vl`) |

On pages it is **7.7 points better** than the best previous arm on byte-identical samples, at a
length ratio of 1.006 — the best page number this project has. On lines it is the worst arm in the
field by a factor of six, at a length ratio of 0.649: it answers two thirds of the text and gets
most of that wrong. Same base, same corpus, same split, same instruction; only the unit differs.

**This does not contradict the heading of this section — it extends it one level down.** The other
five bases were pre-trained on general image–text pairs and fine-tuned here on lines or on pages,
and each read best what it was fine-tuned on. olmOCR arrives already fine-tuned, by someone else, on
whole document pages. Fine-tuning it on line crops asks it to unlearn that, and 306 582 lines of
QLoRA over a frozen base does not. *A model reads the unit it was trained on* turns out to mean the
unit it was trained on **first**.

Two readings are ruled out. **It is not the token budget:** olmOCR's 28-px cell spends 334 image
tokens on a line where Qwen spends 256, and 2 674 on a page where Qwen spends 2 048 — 30 % more at
both granularities, so a budget argument would have to explain a gain and a loss with the same sign.
**It is not a broken run:** both arms report `status: completed`, and the line arm's failure is
visible in the length ratio rather than in a traceback.

The practical consequence is a change to how this project picks a base. Until now the question was
which base reads best; for page work it is now **which base was pre-trained on pages**, and that is
answerable from a model card before any GPU is booked.

### The mixed run: one model can read all three, and pays for it

A fifth model was then trained on the same corpus and split with lines, blocks and pages **in one training set** — 50 % lines, 30 % blocks of six, 20 % whole pages, each at its own pixel budget, 119 850 samples. Scored on its own held-out split, 200 samples drawn evenly across the four sources:

| Input | CER | samples | length ratio |
|---|---:|---:|---:|
| blocks of 6 | **10.1 %** | 56 | 1.004 |
| line crops | 13.5 % | 113 | 0.998 |
| whole pages | 29.2 % | 31 | 0.997 |

**The finding is the last column.** Read it against the table above: a line-trained model answers a page at length ratio 0.03, a page-trained model answers a line at 1.26. This model is at 1.00 on all three. The asymmetric failure that the whole of §4 is about — stop early, or keep writing — is simply gone, and three out of 200 predictions reached the generation cap.

It is not free. On lines it reads at 13.5 % where the line-only model reads its own split at 5.3 %. So the honest reading of the question this page asked a year ago — hold the line accuracy *and* read pages, or land between the two on every level — is **the second**. One model that degrades gracefully at every granularity is a different product from one model that is excellent at one granularity and useless at the others, and which of the two is wanted is a decision about the task, not about the training.

The caveat that §3 exists for applies here too: 13.5 % and 5.3 % are in-domain validation numbers on different draws, and the published benchmark was not scored for this run.

## 5. Two more hypotheses that measurement killed

**"A page gives each line a quarter of the resolution."** Plausible arithmetic — 2 048 visual tokens for a page of 40 lines against 256 for one line — and wrong. Line crops never fill their budget, because a crop is small and is never upscaled. Measured on the image: a line inside a whole page keeps **74–77 %** of the height it has as a crop, 65–89 pixels, comfortably legible. For the 19th-century corpus resolution is not the bottleneck. (For the medieval corpus it may still be: those scans are 19.9 megapixels and are reduced to about a third.)

**"Pages are too long for the token budget."** Also wrong, and also cheap to check: the longest page in the corpus needs about 1 800 tokens against a budget of 4 096, at roughly three characters per token. Both hypotheses were about the model; the answer was again about the data — the model had simply never seen a page.

## 6. A second architecture, and what a drop-in actually costs

Every model above sits on a Qwen base. That was never a decision — it was the first thing that worked — so a second family was trained on the same corpus, the same split, the same epoch and the same effective batch, and scored on **the same 200 samples**:

| | overall | aaeb | bullinger | königsfelden | rats-u.-richteb. |
|---|---:|---:|---:|---:|---:|
| `Qwen3-VL-4B-Instruct` | **13.7 %** | 12.7 | 14.0 | 14.6 | 12.6 |
| `gemma-4-E4B-it` | 16.9 % | 14.8 | 19.3 | 18.7 | 12.9 |

Qwen reads better overall and on every one of the four sources, by 3.2 points — five times the 0.6-point selection noise established in §3. Gemma is not failing: length ratio 0.99, nothing truncated. It reads less well.

**Two things make that number smaller than it looks, and both are ours.**

The first is a size claim we got wrong. Gemma-4-E4B is advertised at 8 B parameters against Qwen's 4.4 B, and the result was first written up as "worse despite nearly double the size". Its config says otherwise: 42 layers with a per-layer embedding table of 262 144 × 256 each, so roughly 3.5 B of those 8 B are embedding lookup and about 4.5 B is transformer. The two models are the **same effective size**, and the honest statement is simply that Gemma read this material worse.

The second is that the comparison was designed to be fair in pixels and was therefore unfair in tokens. Gemma spends a fixed budget per image, on one of five permitted steps, and one of its tokens covers a 48 × 48 px cell against Qwen's 32 × 32. Matching the two on *pixels* — both models shown the same image detail — put Gemma on the 140-token step while Qwen had 256. Gemma's own default is 280. So the run that produced 16.9 % was given half the visual tokens the model ships with, by a decision that was made deliberately and documented as the honest one.

### Size, not family

A larger arm of the same family was then trained on the same corpus and the same split and scored
on the same 200 samples:

| Model | Parameters | CER | convention-normalised | WER | CER without truncations |
|---|---:|---:|---:|---:|---:|
| `gemma-4-12B-it` | 12 B | **12.2 %** | **10.7 %** | **30.4** | **9.1 %** |
| `qwen3vl-medieval-german-v3` | 4.4 B | 13.7 % | 12.3 % | 35.3 | 14.0 % |
| `gemma-4-E4B-it` | ~4.5 B transformer | 16.9 % | 15.8 % | 38.8 | 17.5 % |

Gemma now reads this material better than the model that has been our best on it since September —
1.5 points, more than twice the selection noise of §3 — and by a wider margin on words than on
characters. The last column is the strongest part of it: with the truncated predictions removed the
12B arm is at 9.1 % against 14.0 %, a third better, so its lead comes from the body of the
distribution rather than from a few easy pages.

**It is a size result, not a family result, and the distinction is the point.** The three rows are
4.5 B, 4.5 B and 12 B of transformer. At equal size Qwen reads this corpus better; the family that
looked behind overtakes when it is given three times the parameters. Writing "Gemma beats Qwen"
from the first row would repeat, one level up, exactly the mistake §3 is about: a comparison that
varies two things and is reported as if it varied one. Nothing here says a 12 B Qwen would not win
it back, and none was trained.

What the larger arm costs is not yet measured against the smaller one on the same hardware. The
data point that exists: at identical micro-batch, E4B needed 2.2× the GPU memory of a 4 B Qwen and
ran 3 % slower, and the 12 B arm was trained at micro-batch 2 with gradient accumulation because 16
does not fit. Its 12.2 % was also recovered rather than produced — see the seventh item below.

**The larger lesson is about what a "drop-in" comparison costs.** Six things had to be fixed before Gemma produced any number at all, and each one was invisible until the one before it was cleared:

1. the training container silently ran a transformers version that had never heard of the model;
2. the visual-token budget has no continuous knob, only five legal values, and the code refused the family rather than mapping onto them;
3. the assistant header was derived from a render the training never uses — Gemma's generation prompt opens an empty reasoning channel that the training text does not contain, so the token the loss mask searched for occurred in no sample;
4. the adapters were aimed at every module with a matching name, which on this family includes a vision tower whose wrapped layers the adapter library refuses outright — Qwen's tower simply does not reuse those names, so nobody had noticed the aim was that wide;
5. images were handed over as one flat list per batch, which this family reads as one sample's images;
6. and after a run had trained to completion — 19 162 of 19 162 steps — the evaluation refused it, because the tokens it stops generation on were hardcoded to one family's names.
7. and the same thing happened a second time, to the larger arm, for an unrelated reason: under
   4-bit the patch projection's weight is an integer, so the library's own "cast the pixels to the
   projection's dtype" step silently does not fire — and the encoder-free 12 B image path then hands
   32-bit pixels to a 16-bit normalisation layer. Two days of training, a complete adapter, and a
   `RuntimeError` in the first forward pass of the evaluation. The family with a vision tower never
   hit it, because its tower casts on the way in.

Only the fourth of those is a defect in the ordinary sense. The rest are places where a single family's conventions had been absorbed into code that looked general, and each was discovered by a run dying rather than by reading. The cheap part was the discovery: idle consumer GPUs on the cluster start a job in seconds, and five of the six failures arrived within ninety seconds of submission. The expensive part was the sixth, which cost a full day of training before the adapter could be scored — from an artefact that was still on disk, so the number was recovered without retraining.

**What this does not establish** is that Gemma cannot do better. Every hyperparameter in both runs was chosen for Qwen. A separate plan now collects what the model's own documentation recommends — a different adapter scope, a different token budget, trained embeddings — and the first thing it will test is the budget the comparison above took away.

### Two more arms landed, and neither answers the question it was queued for

**The 19th-century E4B arm finished after sixteen attempts across a week of preemptions**, at 11.10 % CER on its own evaluation draw and **6.44 % on the one its four Qwen siblings share**. The ladder, all five arms on one draw:

| Base | Params | CER |
|---|---:|---:|
| `Qwen/Qwen3.5-4B` | 4.66 B | **4.78 %** |
| `Qwen/Qwen3-VL-4B-Instruct` | 4.44 B | 5.33 % |
| `Qwen/Qwen3.5-2B` | 2.27 B | 5.49 % |
| `google/gemma-4-E4B-it` | ~4.5 B transformer | 6.44 % |
| `Qwen/Qwen3.5-0.8B` | 0.87 B | 7.04 % |

*Correction, and it is this page's own claim that was wrong.* When only the own-draw figure existed, this section said the arm reads the corpus "worse than a 0.87 B Qwen reads it" and that "the direction survives even though the figure does not". **The direction did not survive.** On the shared draw Gemma sits fourth of five — better than the 0.87 B Qwen, between the 2.27 B and the 0.87 B, and 1.7 points behind the 4.66 B. Gemma is behind on this corpus as it is on the medieval one, but by a third of what the uncorrected number suggested.

**The draw moved that number by 4.66 points, and that is the larger finding.** It is the same adapter, the same validation pool — the arm's `val.jsonl` is a symlink into its sibling's job directory — the same seed, and a stratification with the same source mix: both draws report `200 pages, stratified (100 per source …, seed 42) kurrent-xix=100 … zh-regierungsratsprotokolle=100`. The only difference is which 100 pages per source the plan happened to pick, because the attributable pool it picks from differed by 91 of 93 280 pages. §3 puts the resolution of this measurement at **0.6 points**, established from two overlapping draws on the medieval corpus. On the 19th-century corpus two non-overlapping draws of one pool differ by nearly **eight times** that. The 0.6-point figure is a floor for a corpus where the draws overlap, not an error bar for this one, and every single-draw comparison on the 19th century should be read with that in mind.

**The 12 B medieval page arm trained to completion and produced nothing.** Three epochs, validation loss improving 2.837 → 2.611 → 2.645, the best adapter promoted from step 1012 — and a test CER of **96.20 %**. It is not a bad reading; it is an absent one. Over 164 pages the model emitted **four distinct outputs**, the most common of them 68 times, averaging 101 characters against a reference averaging 1 226. The text it emits is the archival stamp that appears on many pages of that collection — `Königsf. 100 / Staatsarchiv / AARGAU` — so it learned the most frequent furniture of a page and ignored the image.

Two explanations are ruled out by measurement rather than by argument. **Not truncation:** the report's own `truncated_cer` of 95.83 % sits within half a point of the CER, only fifteen samples in the whole run exceeded `max_seq_len=4096` (at 4 098–4 263 tokens), and a token ceiling would have produced 164 *different* stumps rather than four identical ones. **Not the vision tower:** the warning in its log — `exclude_modules=.*\.(vision_tower|audio_tower)\..* but no modules were excluded` — looks like the defect §6 item 4 describes, but the saved adapter holds 656 tensors and **none** under a vision subtree. There was nothing there to exclude.

So the question this arm was queued to answer — whether size carries pages the way it carries lines — is still open, and now for a different reason. What the run does establish is narrower and still useful: a family can train to convergence on a page corpus, promote a best adapter on a falling validation loss, and emit a constant. **Validation loss did not detect it.** The only signal that did was counting distinct outputs, which no stage does.

## 7. The families on a set someone else can check

Everything above is measured on draws of our own. The 19th-century corpus has an alternative: the [Federal Council test set](https://doi.org/10.5281/zenodo.4746342), 2 751 published lines that no run of ours has ever trained on. Every arm trained on that corpus, scored there, lines, same instruction, same 262 144-pixel budget:

| Base | Parameters | CER | WER | length ratio | at cap |
|---|---:|---:|---:|---:|---:|
| `Qwen/Qwen3.5-4B` | 4.66 B | **6.80 %** | 23.4 | 1.000 | 0 |
| `Qwen/Qwen3-VL-4B-Instruct` | 4.44 B | 7.65 % | 24.6 | 1.002 | 1 |
| `Qwen/Qwen3.5-2B` | 2.27 B | 8.95 % | 26.2 | 1.001 | 2 |
| `google/gemma-4-12B-it` | 11.96 B | 9.95 % | 24.2 | 0.964 | 1 |
| `google/gemma-4-E4B-it` | ≈4.5 B effective | 10.24 % | 28.7 | 1.004 | 3 |
| `Qwen/Qwen3.5-0.8B` | 0.87 B | 11.15 % | 30.7 | 0.998 | 0 |

Three readings, and the third is a correction.

**Within one family, size pays and keeps paying.** 0.8 → 2 → 4 B is 11.15, 8.95, 6.80: about 2.2 points per doubling, with no sign of flattening. The ranking on a published set is the same as the one on our own split, which is the first time this project can say that.

**Across families, the generation matters as much as the size.** At an identical 4 B, `Qwen3.5-4B` reads 0.85 points better than `Qwen3-VL-4B` — most of a doubling, for changing nothing but which year the base was published. And Gemma's best arm here, at 12 B, sits below a 2 B Qwen.

**But Gemma's number was wrong until the day this was written, and the error was ours.** The 12 B arm first scored **22.94 %** on this set. Its error budget was the tell: 17 027 insertions against 4 783 deletions, where every arm that reads normally is substitution-dominated. Insertion-dominated is not a reading failure, it is a *generation* failure — and reading the two chat renders side by side found it in minutes:

| | what the model is asked to continue from |
|---|---|
| at inference | `<\|turn>model` + newline + **`<\|channel>thought` + newline + `<channel\|>`** |
| during training | `<\|turn>model` + newline + the transcription + `<turn\|>` |

The 12 B was being asked, at evaluation, to continue **inside an empty thinking channel it had never seen while training**. A model told to think writes text that is not a transcription. Asked instead to continue from the render it was trained on, the same adapter on the same 2 751 lines:

| Arm | CER | insertions | length ratio | at cap |
|---|---:|---:|---:|---:|
| 12 B, generation prompt | 22.94 % | 17 027 | 0.894 | 11 |
| 12 B, **training render** | **9.95 %** | 5 910 | 0.964 | 1 |
| E4B, generation prompt | 10.24 % | 2 039 | 1.004 | 3 |
| E4B, **training render** | 10.24 % | 2 039 | 1.004 | 3 |

**Thirteen points on the arm whose two renders differ, and byte-identical output on the arm whose renders agree.** The E4B rows match in every field — same insertions, same deletions, same hypothesis length — which is what makes this a controlled result rather than a lucky one: the mechanism was identified from the renders *before* the measurement, and the control was predicted not to move.

What it cost to find out: nothing. What was nearly spent instead was five days of GPU time on the wrong hypothesis — that the 12 B arm had been damaged by being preempted four times across five days. That guess was killed for free by reading its loss history, which runs smooth across all four attempts with no discontinuity at a single boundary. A training loss of 0.15 beside a 22.94 % CER is not a damaged run; it is a mismatch between training and inference.

**One confound remains, and it is also ours.** Every Qwen number in the table was produced in bf16; both Gemma arms trained and were scored in 4-bit, because that is what their configuration set. What 4-bit costs in accuracy on this corpus is unmeasured. So the Gemma figures are an upper bound on their deficit, not a clean comparison — and the evaluation report now records the quantisation, so the next reader does not have to find this out by digging.

## Open questions

- **Over-generation on sparse pages** is the page model's remaining weakness and the same failure the medieval page model shows. Neither a larger nor a smaller pixel budget addresses it.
- **Whether Gemma closes the gap when it is tuned for itself.** One of its three known handicaps is gone: §7's prompt mismatch cost the 12 B arm thirteen points and is now fixed by default. Two remain — both arms still ran at the 140-token visual budget where Gemma's own default is 280, and both were quantised to 4-bit against the Qwens' bf16. Until those are measured, "worse as a drop-in" stays the claim, and it is narrower than "worse".
- **Page numbers on a published set.** §7 gives the line comparison on 2 751 published lines; there is no page equivalent, so every page figure on this page is still measured on held-out pages of our own corpora.
- **Whether a page-pre-trained base beats a bigger general one.** olmOCR at 7 B reads pages better than every general base measured here, including a 12 B one. Whether that is the pre-training or the size is unseparated: no general 7 B page arm exists, and no page-pre-trained 4 B one either.
- **Whether size carries pages the way it carries lines.** At 12 B Gemma wins on lines and at ~4.5 B it loses on pages by nine points. The 12 B page arm has now landed and collapsed to a constant output (above), so it answers nothing; the question needs the run repeated, and the repeat needs a stage that fails a run whose outputs do not vary.
- **Whether a 12 B Qwen would take the lead back.** The size comparison above is one-sided: three arms, and only one of them large. Nobody has trained the obvious control.
- **Training variance is still unmeasured.** §3 establishes that drawing a different evaluation subset moves a CER by 0.6 points. What two runs of the *same* arm at different seeds do is unknown, and every ranking on this page assumes it is small.
- **There is no page-level benchmark** with ground truth that no run has seen. The published Federal Council test set is 2 751 isolated lines. Until one exists, page numbers are measured on held-out pages of our own corpora, which is weaker.

## Provenance

Every figure here comes from a stored evaluation report of a named run, on a named set of pages, and the corrections are recorded in the issue trackers of `thodel/serving-atr-inference` and `thodel/training-atr-models` rather than only in this summary. The operational side of these runs — scheduling, serving, how a measurement environment is built and taken down — is tracked there as well and deliberately not summarised here: this page is about what the models learned. Sections 3 and 6 rest on re-scoring stored adapters against another run's evaluation subset, which is why they can claim a comparison at all. The measuring instrument for the granularity table is `scripts/eval_granularity.py` in the serving repository: it asks one model the same pages four ways and reports, besides CER, the two failure shapes an average hides — collapse (under a third of the reference) and runaway (over 1.5 times it).
