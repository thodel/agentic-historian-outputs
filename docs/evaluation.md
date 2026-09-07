---
layout: default
title: "Recognition engine evaluation"
---

> **Internal engineering document.** This page is a working document for project contributors. It is not part of the public-facing German site and is not linked from the global navigation. See the [language policy](about.html#sprachpolitik) for context.

# Recognition engine evaluation

How well do the recognition engines behind this pipeline actually read? This page records a controlled comparison across three corpora, the error taxonomy behind the headline numbers, and what happened when a language model was asked to pick the best reading.

It records **what was measured**, and stops there. What the results argue for in the pipeline's own code is a separate document, kept separate on purpose: an experiment that also advocates for changes tends to be read as advocacy, and a pipeline that cites its own benchmark tends to stop questioning it. That agenda lives in `docs/PIPELINE_CONSEQUENCES.md` in the agentic_historian repository, and the instrument that produced these numbers in `docs/EVALUATION_HARNESS.md` beside it.

All figures are reproducible from published datasets. Where a number contradicts something stated earlier in the project, the correction is noted rather than quietly applied.

## Corpora

| Corpus | Period | Material | Extent | Source |
|---|---|---|---|---|
| Minutes of the Swiss Federal Council | 1848–1903 | German Kurrent, administrative prose | 150 lines · 5 973 characters | [Zenodo 4746342](https://doi.org/10.5281/zenodo.4746342) |
| Inzigkofen | 15th century | Upper German bastarda, two complete codices | 291 lines · 15 746 characters | [Zenodo 17978574](https://doi.org/10.5281/zenodo.17978574) |
| Valais census (German sheets) | 1870, 1880 | Handwritten tabular forms | 1 075 cells · 5 168 characters | [HTR-United](https://github.com/PonteIneptique/valais-recensement), CC0 |

Every corpus ships its own line segmentation. Lines were cut with the supplied polygons, never re-segmented, so the measurements isolate recognition from layout analysis.

## Headline results

Character Error Rate is reported corpus-wide (`errors / characters`) alongside the median and the 95th percentile over lines. The spread between those three columns carries more information than any of them alone.

### Minutes of the Swiss Federal Council, 19th century

| System | CER | median | p95 | Sub/Del/Ins |
|---|---|---|---|---|
| German Kurrent M2 · HTR+ (2021) | 3.79 % | 2.00 % | 16.7 % | 65/23/12 |
| Transkribus German Kurrent · HTR+ (2021) | 5.85 % | 4.48 % | 20.0 % | 64/25/11 |
| RRB · HTR+ (2021) | 7.40 % | 5.56 % | 28.3 % | 63/26/10 |
| German Kurrent M2 · PyLaia (2021) | 11.19 % | 6.00 % | **100.0 %** | 36/**60**/4 |
| FoNDUE-GD_v2 \* | (11.30 %) | (10.00 %) | (33.3 %) | 66/23/10 |
| trocr-kurrent-XIX | 13.90 % | 12.00 % | 42.1 % | 59/19/22 |
| trocr-kurrent-XVI-XVII | 19.37 % | 15.56 % | 52.5 % | 63/16/21 |
| kraken-bohemian_19th_v2 | 53.87 % | 57.63 % | 84.6 % | 72/19/10 |
| qwen3-vl-30b, zero-shot | 78.98 % | 56.67 % | 100.0 % | 48/9/**44** |

### Inzigkofen, 15th century

| System | CER | median | p95 | s/line |
|---|---|---|---|---|
| trocr-medieval-escriptmask | **20.0 %** | 20.0 % | 35.1 % | 0.36 |
| kraken-catmus-medieval | 25.8 % | 25.3 % | 37.0 % | **0.05** |
| FoNDUE-GD_v2 | 30.1 % | 30.6 % | 51.2 % | 0.11 |
| trocr-kurrent-XVI-XVII | 30.5 % | 29.7 % | 52.8 % | 0.33 |
| qwen3.8-27b, line by line | 38.9 % | 35.2 % | 100.0 % | 15.3 |
| trocr-essoins-middle-latin | 44.5 % | 42.9 % | 73.1 % | 0.31 |
| kraken-mccatmus | 46.4 % | 47.1 % | 64.5 % | 0.22 |
| trocr-kurrent-XIX | **56.9 %** | 56.9 % | 80.0 % | 0.30 |
| kraken-bohemian_19th_v2 | 60.8 % | 61.4 % | 80.7 % | 0.11 |

### Valais census forms, German sheets

| System | CER | exact cells | normalised | seconds |
|---|---|---|---|---|
| FoNDUE-GD_v2 \* | (34.7 %) | (35.4 %) | (35.8 %) | **7** |
| trocr-kurrent-XIX | **49.5 %** | 19.5 % | 20.3 % | 83 |
| kraken-bohemian_19th_v2 | 63.4 % | **28.6 %** | 28.6 % | **9** |
| trocr-kurrent-XVI-XVII | 73.1 % | 18.9 % | 20.7 % | 85 |
| qwen3.8-27b, cell by cell | 74.2 % | 22.0 % | — | 573 |
| kraken-mccatmus | 76.1 % | 13.5 % | 13.7 % | 8 |
| trocr-medieval-escriptmask | 78.9 % | 9.0 % | 9.2 % | 80 |

\* **Contaminated, and shown for that reason.** [FoNDUE-GD_v2](https://doi.org/10.5281/zenodo.21536798) is a multilingual kraken model aggregating 28 training datasets, two of which are corpora measured here: `zenodo.4746342`, the Federal Council minutes, and `PonteIneptique/valais-recensement`, the Valais census. Its figures on those two are memorisation, not recognition, and are given in parentheses so they are not read as a result.

Inzigkofen is not in its training list, and there it places third at 30.1 % — behind two medieval models, and eight points behind the corpus leader. That gap between a contaminated 11.3 % and a clean 30.1 % is the useful part: for a model aggregating dozens of datasets, "has it seen this test set" cannot be judged from its name or its score, only from its dataset list. It was entered here as the field's best local model and stayed that way for a quarter of an hour, until the model card was read.

One transferable observation survives: at 0.11 s/line and 1 075 form cells in seven seconds it is the fastest system measured, and it writes umlauts as a base letter plus a combining mark, so NFC normalisation improves its character error rate by 8 % relative without changing a single reading.

## Whole page or single line?

Vision models are normally driven line by line, because that is how the rest of the pipeline works. Measured with `gemini-3.7-flash` on the same eight Inzigkofen pages and 291 lines, against the same reference, that turns out to be the worst way to use them:

| Mode | CER | normalised | calls | seconds |
|---|---|---|---|---|
| **Whole page** | **20.4 %** | **14.8 %** | 8 | 171 |
| Line by line | 57.3 % | 53.6 % | 291 | 1 211 |

The page mode wins on all eight pages individually, 12.9–33.0 % against 35.1–65.5 %. It is 2.8 times more accurate and seven times faster.

At 20.4 % a commercial model with no training on this material draws level with the best fine-tuned model in the field (20.0 %). Normalising ſ→s, cz→tz and the diacritics brings it to 14.8 %, ahead of every local model — a substantial part of its residual error is modernisation rather than misreading, which under many editorial conventions is not an error at all.

The reason is visible in the outputs. Given a single line with no context, the model leaves the task and starts *analysing* letterforms — `shape: ascender loop up, descender down) Stroke 4: descend` where a transcription should be. The full page anchors it: language, hand, line sequence and the vocabulary of neighbouring lines all support each individual reading.


A second vision model, measured after the first version of this page, turns the rule into a
gradient. `qwen3.8-27b` — served locally, and the replacement for a model that was configured
but never deployed — reads the same eight pages at **27.7 %** and the same 291 lines at
**38.0 %**. The page still wins, but by 1.4× rather than 2.8×.

| Model and corpus | whole page | line or cell |
|---|---|---|
| gemini-3.7-flash, Inzigkofen | **20.4 %** | 57.3 % |
| qwen3.8-27b, Inzigkofen | **27.7 %** | 38.0 % |
| gemini-3.7-flash, Valais | **44.1 %** | 59.3 % |
| qwen3.8-27b, Valais | 98.5 % | **74.2 %** |

On the census forms the same model reverses it outright: 98.5 % for the whole sheet against
74.2 % cell by cell. The size of the page advantage tracks how well the model reads the material,
and where it cannot read it at all the added context makes things worse rather than better.

A practical note on that page run: with a 4 096-token budget two of the eight pages returned
*nothing* — the model exhausts the budget on reasoning before emitting content, and the client
sees an empty completion rather than an error. At 16 384 tokens all eight pages returned text.
A reasoning model used for recognition needs an output budget set for the reasoning, not for the
transcription.

Within the zero-shot class the gap between providers is not a nuance but a category. On the same page in the same mode, `gemini-3.7-flash` reaches 20.4 %; `internvl3-8b`, hosted locally, produces 6 832 characters for a 2 909-character page at **189.8 % CER**, the first two lines a faint echo and the rest `punc schmugelich` repeated a hundred times. Given a generic prompt it invents an essay instead. Whole-page context helps only a model that can read the script at all; it amplifies what is there, in both directions.

## Three findings that survive scrutiny

### A benchmark measures fit, not capability

The same seven models move by up to 43 percentage points between the two prose corpora, in both directions. `trocr-kurrent-XIX` is the strongest model on the 19th-century minutes at 13.9 % and the weakest TrOCR on the 15th-century manuscripts at 56.9 %. `kraken-catmus-medieval` moves the other way, 67.3 % to 25.8 %.

Only the general-purpose model varies by less than ten points. Robustness across domains and peak accuracy within one are different goals, and the difference is invisible with a single corpus.

### The metric chooses the model

On the census forms the two metrics disagree about the winner. By CER, `trocr-kurrent-XIX` wins at 49.5 % against 63.4 %. By exact cell accuracy, `kraken-bohemian_19th_v2` wins at 28.6 % against 19.5 % — 47 % better in relative terms, and ten times faster.

The reason is architectural. A generative model gets closer on average because it continues plausibly; a CTC model stays short and therefore hits exactly more often. On a four-character cell "close on average" is worthless: a name is right or it is not. For tabular records, exact cell accuracy is the operationally correct measure, and it selects the other model.

Nearly half the cells are a single character, and no model in the field is trained on isolated form cells — they all expect lines of text. Tabular records are common in archives and absent from the model catalogue.

### One line can carry twenty-five points

Generative systems occasionally collapse into repetition. Such lines are rare and they dominate the corpus figure:

| System | collapsed lines | CER | CER without them |
|---|---|---|---|
| qwen3-vl, production prompt | 2 of 149 | 96.20 % | 54.49 % |
| qwen3-vl, line prompt | 1 of 149 | 78.89 % | 53.93 % |
| kraken-catmus-medieval | 5 of 149 | 67.32 % | 67.21 % |

A CTC output is bounded by the width of the image; a generative model can write indefinitely, and every invented character counts. Five collapses move the kraken figure by a tenth of a point. One collapse moves the VLM figure by twenty-five.

The corpus figure is therefore fragile for generative recognisers in a way it is not for CTC: a handful of lines can carry it. The median moves hardly at all across the same pair of runs — 56.4 % against 56.7 % — which is what makes the two numbers worth reporting together.

## Error taxonomy

Errors were classified following [CERberus](https://github.com/WHaverals/CERberus): `CER = (Sub + Ins + Del) / len(reference)`, aligned with `editops(reference, hypothesis)`, plus per-character, per-Unicode-block and confusion-pair statistics. Note the orientation — an *insertion* is a character the hypothesis added, a *deletion* one it lost. This is the reverse of the kraken convention.

Three signatures emerge, and the boundaries follow architecture rather than quality:

- **Omitting.** PyLaia alone. Recomputed over all 2 741 lines of the archive: 73.1 % deletions against 4.4 % insertions, a ratio of 16.7 : 1, and 168 empty lines. Its substitution share, 22.5 %, is *lower* than that of the two weaker HTR+ models. Where it reads, it reads about as well; it simply stops. (An earlier version of this page gave 60 % and 13.3 : 1 for the same signature. Those values are not reproducible from the archive on either basis — all lines, or excluding the 168 empty hypotheses, which yields 63.7 % and 10.8 : 1 — and presumably came from the 150-line sample while the empty-line count was corpus-wide. The figures above are corpus-wide throughout.)
- **Misreading.** All HTR+ and all kraken models: 63–76 % substitutions, deletion-to-insertion ratios between 1.6 and 2.5. One character out for every character in, sometimes the wrong one.
- **Adding — or cutting.** Zero-shot VLMs on the 19th-century corpus: 44 % and 54 % insertions, ratios of 0.2 and 0.1. Fine-tuned TrOCR models sit between at 0.8. The signature does not generalise across corpora: on 15th-century bastarda the same architecture truncates instead. `gemini-3.7-flash` line mode reaches 72.0 % deletions at a length ratio of 0.585, `qwen3.8-27b` 41.6 % at 0.858. "Generative means over-generation" is a statement about a corpus, not about an architecture.

For an edition the distinction matters more than the rate. An omission leaves a gap that proof-reading catches. A substitution leaves a wrong word in the right place. An insertion leaves text nobody ever wrote, and it does not read differently from the transmission.

Individual observations worth recording:

- The single most frequent error of the best model is `u → ŭ` at 11.5 % of all its errors — the u-bow, a transcription convention rather than a misreading.
- The most frequent error of `trocr-kurrent-XIX` is an inserted space at 15.0 %. An eighth of its CER is output convention: normalising whitespace and punctuation improves it by 13 %.
- The same normalisation makes every kraken model *worse* by 8–12 %. The sign of that change is a diagnostic: where normalisation helps, errors are conventional; where it hurts, they are on the letter.
- Line-break characters are the hardest of the corpus for all engines: `¬` at 29–61 %, `-` at 12–63 %. Diacritics are consistently two to five times harder than plain ASCII.

## Where the errors sit

CERberus gives more than a rate: every edit operation names the character it acted on. Grouping
those by Unicode block, and normalising by how often each block occurs in the reference, localises
the difficulty. Without that normalisation Basic Latin always wins, because it is most of the text.

The Inzigkofen reference is 89.2 % Basic Latin, 4.2 % Latin Extended-A, 3.8 % Combining
Diacritical Marks, 2.8 % Latin-1 Supplement and 0.03 % Latin Extended-D.

`trocr-medieval-escriptmask`, the corpus leader at 20.0 % overall:

| Unicode block | in reference | sub | del | error rate |
|---|---|---|---|---|
| Latin Extended-A | 653 | 616 | 37 | **100.0 %** |
| Latin Extended-D | 5 | 5 | 0 | 100.0 % |
| Latin-1 Supplement | 443 | 220 | 215 | 98.2 % |
| Combining Diacritical Marks | 596 | 187 | 203 | 65.4 % |
| Basic Latin | 14 049 | 963 | 464 | **10.2 %** |

It reads the letters at 10 % error and is scored at 100 % on the block that holds the long s. One
confusion explains almost all of that block: `ſ → s`, 599 times in 291 lines. The manuscript's own
punctuation goes the same way — the middle dot is dropped 211 times here, and read as a comma 76
times by the next model down. On the 19th-century corpus the equivalent is `¬`, the edition's
line-break mark: lost or written as `-`, and 4.0 % of all edit operations of the best model there.

Small blocks are fragile. Latin Extended-D holds five characters; its 100 % is true and carries
nothing.

### How much of the error is convention

Folding one convention at a time and re-scoring the same output — nothing is recognised again:

| Step | CER | Δ |
|---|---|---|
| raw | 20.02 % | |
| + whitespace | 20.02 % | +0.00 |
| + lower case | 19.36 % | −0.66 |
| + long ſ → s | 15.34 % | **−4.03** |
| + ligatures | 15.34 % | +0.00 |
| + punctuation | 14.64 % | −0.69 |
| + diacritics folded | 11.59 % | **−3.05** |

Two fifths of this model's measured error is orthographic convention rather than misreading.
Applied to every system whose raw output was retained:

| System | raw | corrected | convention share | rank |
|---|---|---|---|---|
| trocr-medieval-escriptmask | 20.0 % | **11.6 %** | 42 % | 1 → 1 |
| gemini-3.7-flash, whole page | 20.4 % | 12.8 % | 37 % | 2 → 2 |
| qwen3.8-27b, whole page | 27.7 % | 20.5 % | 26 % | 3 → 3 |
| trocr-kurrent-XVI-XVII | 30.5 % | 23.0 % | 24 % | 4 → 4 |
| qwen3.8-27b, line by line | 38.9 % | 33.7 % | 13 % | 5 → 5 |
| trocr-essoins-middle-latin | 44.5 % | 37.2 % | 16 % | 6 → 6 |
| trocr-kurrent-XIX | 56.9 % | 51.9 % | 9 % | 7 → 7 |
| gemini-3.7-flash, line by line | 59.4 % | 54.9 % | 8 % | 8 → 8 |

Every number falls. **Not one position changes.** The raw rate orders the systems correctly and
quantifies them badly — which is the useful conclusion for anyone choosing a model from a
leaderboard, and the uncomfortable one for anyone quoting a rate.

The spread carries the information: 42 % for the domain-trained model against 8 % for a general
one driven line by line. A model that knows the conventions is charged less for them, so the raw
figure compresses the distance between specialist and generalist. Corrected, that distance widens
from 3.0× to 4.7×.

The 19th-century corpus behaves the other way, and the reason is compositional: 1.9 % of its
reference lies outside Basic Latin, and the same ladder buys only 4–9 %. Convention noise scales
with how much of the material sits outside plain ASCII.

Normalisation of this kind is a **diagnostic, not a deliverable**. An edition without long s and
diacritics is worthless. What it separates is "cannot read the hand" from "does not follow our
conventions", and the second is addressable with a mapping table rather than a better model — the
confusion pairs above are the table.

Two systems are missing from the corrected column: the raw outputs of `kraken-catmus-medieval` and
`kraken-bohemian_19th_v2` were not retained, and without the text there is no alignment to correct.
The claim that no position changes therefore holds for the eight systems listed, not for the field.

## Verifying the published 2021 results

The recognition outputs behind Hodel et al. 2021 are published, so the reported rates can be recomputed. They hold, on the right aggregation level — and the archive is mislabelled.

Table 3 of the paper averages over sample sets, not over lines; the running text says so in passing. Aggregated by group, the recomputed values track the published ones. Averaged over lines they do not. Corpus-wide CER is the usable proxy: it agrees with the group mean to two hundredths.

The directory names for the two German Kurrent M2 runs are swapped. `german_kurrent-m2_htr+` contains the PyLaia output and `german_kurrent-m2_pylaia` the HTR+ output. Two independent lines of evidence: the group means map to the table rows in reverse (3.16 ↔ 3.43 and 13.50 ↔ 18.77), and the error profile is unambiguous — 168 empty lines and a 21.9 : 1 deletion-to-insertion ratio against 1.6–2.2 for the other three. The Creator metadata is not usable as evidence; it is an accumulated processing history.

One difference remains unexplained: 2 741 lines here against 2 426 in the paper. The paper cites `zenodo.4746341` for the test set; the archive evaluated here is `4746342`.

## Asking a language model to choose

The pipeline can produce several readings of the same line. A language model was asked to rank them — the arrangement this project had been treating as an obvious improvement.

Measured against the simplest possible rule, taking the strongest single model and asking nobody, it is worse:

| Strategy | mean CER of the chosen reading |
|---|---|
| Oracle: the best reading per line | 0.110 |
| **Always `trocr-kurrent-XIX`, no judge** | **0.170** |
| The judge | 0.277 |

Its picks are statistically indistinguishable from choosing at random among the four candidates. Agreement with the CER-best reading is 55 %, and where it disagrees its choice costs 25 additional CER points. Forty-four percent of those disagreements go to the zero-shot VLM — the weakest system in the field — because that system writes fluent modern German while the accurate ones produce spaced punctuation and historical spellings.

Twice in forty lines it chose a reading with no relation to the source: `März 1848` over `werden .`, an invented date beating the correct word.

### What actually helps

| Strategy | CER | vs. no judge | calls |
|---|---|---|---|
| Gate + anti-fluency prompt | **0.131** | −0.039 | 7 of 40 |
| Gate alone | 0.151 | −0.019 | 7 of 40 |
| No judge | 0.170 | 0 | 0 |
| Prompt alone | 0.214 | +0.044 | 40 of 40 |
| The judge as first built | 0.273 | +0.103 | 40 of 40 |

What separates the two halves of that table is how often the judge was asked. The gate escalates only when the two fine-tuned recognisers disagree by more than 0.30 CER, which happens on 7 of 40 lines; on the other 33 the reliable systems already agree, and every configuration that consulted the judge there ended up behind the no-judge baseline.

Giving the judge the facsimile does not help: 0.283 with the image against 0.273 without. The model used reaches 78.9 % CER on this material itself — it cannot read the line, so it cannot check it. Handing the page to a poor reader does not make a good referee. What the image *does* reveal is self-preference: with a naive prompt the vision judge picks its own reading 14 times out of 40, against a chance value of 10.

### A second judge, and the finding reverses

The result above is a statement about one judge on one corpus. Repeating the experiment on
Inzigkofen — 40 lines, five candidates (four fine-tuned TrOCR models and `gemini-3.7-flash` line
mode), labels reshuffled per line, identical prompt for both judges:

| Strategy | CER | calls | vs. no judge |
|---|---|---|---|
| Oracle: the best reading per line | 0.205 | 0 | −0.013 |
| **Judge: `qwen3.8-27b`** | **0.209** | 40 | **−0.009** |
| Gate + `qwen3.8-27b` | 0.213 | 16 | −0.004 |
| No judge, strongest engine alone | 0.218 | 0 | 0 |
| Judge: `gpt-oss-120b` | 0.277 | 40 | +0.059 |
| Character-level vote | 0.304 | 0 | +0.086 |
| Random among the five | 0.424 | 0 | +0.206 |

Same lines, same candidates, same prompt. One judge lands 0.004 above the oracle; the other sits
0.059 behind asking nobody. The task is not unsuited to a judge — the first judge was unsuited to
the task. A judge result is a statement about that judge, in the same way a benchmark number is a
statement about that corpus.

The gate keeps two thirds of the gain at 40 % of the calls, which is the configuration worth
building. What the better judge costs is real: 24 seconds per decision against 1.2 for
`gpt-oss-120b`, because it spends a 3 000-token budget reasoning before answering with one letter.
`/no_think` is not honoured through the OpenAI-compatible interface.

Note also that the character-level vote, which helps on the 19th-century corpus, *hurts* here —
0.304 against 0.218. Where one model dominates a field of weaker ones, the vote drags the leader
down. It is free, but it is not unconditionally safe.

### Voting instead of selecting

Character-level voting across the candidates, aligned to the strongest reading, costs no model calls at all and is deterministic:

| Method | CER | vs. no judge | calls |
|---|---|---|---|
| Oracle including the vote as a candidate | 0.095 | −0.050 | — |
| Oracle over line selection | 0.103 | −0.042 | — |
| **Character-level vote, unweighted** | **0.123** | −0.022 | 0 |
| Vote weighted by reliability | 0.130 | −0.015 | 0 |
| Vote without the weakest system | 0.136 | −0.009 | 0 |
| No judge | 0.145 | 0 | 0 |

Three results run against intuition. Weighting by reliability makes it *worse*: the strongest model then outvotes everyone and the method collapses towards "always use the best model". Dropping the weakest system also makes it worse — a model at 79 % CER still gets the easy characters right and contributes to the majority, as long as its errors are uncorrelated. And gating hurts here, unlike with the language model: voting is safe everywhere, so every skipped line is a missed opportunity.

Line selection was never the ceiling. The vote produces a better reading than any single candidate on 32 of 150 lines, by 0.038 CER on average. Added as a fifth candidate it lowers the oracle from 0.103 to 0.095. A selection method can only find the best reading present; a combination method can make a better one.

## Caveats

The ground truth of the 19th-century test set names `German_Kurrent_XIX_comb-Huber_M2` as its creator — the model that leads the table produced the reference that it then matches best. It was post-edited, which is standard practice, but part of what is measured is how much the editor changed.

The language model judge is **not reproducible at temperature 0**: three runs with identical prompts returned 0.273, 0.277 and 0.297. Differences below 0.02 are not interpretable, and comparisons of judge configurations need repetitions.

The page-versus-line result holds for the census forms as well. On the same 16 sheets and 1 075 cells, `gemini-3.7-flash` reaches 44.1 % CER, 43.0 % exact cells and 41.0 % row grouping in page mode, against 59.3 %, 32.9 % and 18.7 % cell by cell — better on all three measures, at twenty times fewer calls. Its 43.0 % exact cells also lead the best local model by a wide margin (28.6 %).

That result required correcting the scoring. A first pass compared output row *i* with reference row *i* and reported the opposite conclusion, 105.7 % against 81.2 %. Gemini omits the six-row header block of the form and starts at the first data row, so almost every cell was measured against the wrong one. The content had been good throughout: `1 | Zurbriggen | Franz | Vater | 1 | 25 | März | 1830 | 1 | Grund | Wallis` against the reference `1 | Zurbriggen | Franz | Vater | 1 | 25 März 1830 | 1 | Grund | Wallis`. The prose corpus had been scored character-wise over the whole text, which tolerates an offset; the tabular corpus positionally, which does not.

Two named causes account for much of the remaining gap, and neither is a misreading: the skipped header block, and a disagreement about column boundaries — Gemini splits dates into three cells where the reference keeps one.

The vision model named in the pipeline configuration, `qwen3-vl-30b-a3b-instruct`, was not served
by GPUStack for the whole period of these measurements; every call returned HTTP 404 with no
startup check and no degraded-mode signal. It has been replaced throughout by `qwen3.8-27b`, which
is what the figures on this page record. The substitution is a finding as much as a fix: a model id
in a configuration file is a claim that can quietly stop being true.

## Reproduction

- Error taxonomy: [CERberus](https://github.com/WHaverals/CERberus) (Wouter Haverals)
- Reference: Hodel, T., Schoch, D., Schneider, C., & Purcell, J. (2021). *General Models for Handwritten Text Recognition: Feasibility and State-of-the Art. German Kurrent as an Example.* Journal of Open Humanities Data 7: 13, Table 3. [DOI 10.5334/johd.46](https://doi.org/10.5334/johd.46)
- Unless stated otherwise, no normalisation of case, whitespace or punctuation was applied.
- Unicode-block localisation and the normalisation ladder: `blocks.py`, alongside the harness described in `docs/EVALUATION_HARNESS.md`.
- Two aggregations appear on this page. Per-line sums (each line scored against its own reference) and joined-page sums (all lines of a page against the page reference) differ by about one point; tables are internally consistent, and the page-versus-line section uses the joined basis throughout.
