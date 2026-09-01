---
layout: default
title: "Recognition engine evaluation"
---

> **Internal engineering document.** This page is a working document for project contributors. It is not part of the public-facing German site and is not linked from the global navigation. See the [language policy](about.html#sprachpolitik) for context.

# Recognition engine evaluation

How well do the recognition engines behind this pipeline actually read? This page records a controlled comparison across three corpora, the error taxonomy behind the headline numbers, and what happened when a language model was asked to pick the best reading.

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
| trocr-kurrent-XIX | 13.90 % | 12.00 % | 42.1 % | 59/19/22 |
| trocr-kurrent-XVI-XVII | 19.37 % | 15.56 % | 52.5 % | 63/16/21 |
| kraken-bohemian_19th_v2 | 53.87 % | 57.63 % | 84.6 % | 72/19/10 |
| qwen3-vl-30b, zero-shot | 78.98 % | 56.67 % | 100.0 % | 48/9/**44** |

### Inzigkofen, 15th century

| System | CER | median | p95 | s/line |
|---|---|---|---|---|
| trocr-medieval-escriptmask | **20.0 %** | 20.0 % | 35.1 % | 0.36 |
| kraken-catmus-medieval | 25.8 % | 25.3 % | 37.0 % | **0.05** |
| trocr-kurrent-XVI-XVII | 30.5 % | 29.7 % | 52.8 % | 0.33 |
| trocr-essoins-middle-latin | 44.5 % | 42.9 % | 73.1 % | 0.31 |
| kraken-mccatmus | 46.4 % | 47.1 % | 64.5 % | 0.22 |
| trocr-kurrent-XIX | **56.9 %** | 56.9 % | 80.0 % | 0.30 |
| kraken-bohemian_19th_v2 | 60.8 % | 61.4 % | 80.7 % | 0.11 |

### Valais census forms, German sheets

| System | CER | exact cells | normalised | seconds |
|---|---|---|---|---|
| trocr-kurrent-XIX | **49.5 %** | 19.5 % | 20.3 % | 83 |
| kraken-bohemian_19th_v2 | 63.4 % | **28.6 %** | 28.6 % | **9** |
| trocr-kurrent-XVI-XVII | 73.1 % | 18.9 % | 20.7 % | 85 |
| kraken-mccatmus | 76.1 % | 13.5 % | 13.7 % | 8 |
| trocr-medieval-escriptmask | 78.9 % | 9.0 % | 9.2 % | 80 |

## Whole page or single line?

Vision models are normally driven line by line, because that is how the rest of the pipeline works. Measured with `gemini-3.7-flash` on the same eight Inzigkofen pages and 291 lines, against the same reference, that turns out to be the worst way to use them:

| Mode | CER | normalised | calls | seconds |
|---|---|---|---|---|
| **Whole page** | **20.4 %** | **14.8 %** | 8 | 171 |
| Line by line | 57.3 % | 53.6 % | 291 | 1 211 |

The page mode wins on all eight pages individually, 12.9–33.0 % against 35.1–65.5 %. It is 2.8 times more accurate and seven times faster.

At 20.4 % a commercial model with no training on this material draws level with the best fine-tuned model in the field (20.0 %). Normalising ſ→s, cz→tz and the diacritics brings it to 14.8 %, ahead of every local model — a substantial part of its residual error is modernisation rather than misreading, which under many editorial conventions is not an error at all.

The reason is visible in the outputs. Given a single line with no context, the model leaves the task and starts *analysing* letterforms — `shape: ascender loop up, descender down) Stroke 4: descend` where a transcription should be. The full page anchors it: language, hand, line sequence and the vocabulary of neighbouring lines all support each individual reading.

This has an uncomfortable consequence for the pipeline as built. It cuts lines and asks line by line, which is precisely the mode in which vision models perform worst.

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

Two consequences for practice: report the median alongside the mean for generative recognisers, and run a degeneration detector before evaluation rather than after.

## Error taxonomy

Errors were classified following [CERberus](https://github.com/WHaverals/CERberus): `CER = (Sub + Ins + Del) / len(reference)`, aligned with `editops(reference, hypothesis)`, plus per-character, per-Unicode-block and confusion-pair statistics. Note the orientation — an *insertion* is a character the hypothesis added, a *deletion* one it lost. This is the reverse of the kraken convention.

Three signatures emerge, and the boundaries follow architecture rather than quality:

- **Omitting.** PyLaia alone: 60 % deletions, 13.3 times as many as insertions, 168 empty lines across the full 2 741-line set. Its substitution count is *lower* than that of the two weaker HTR+ models. Where it reads, it reads about as well; it simply stops.
- **Misreading.** All HTR+ and all kraken models: 63–76 % substitutions, deletion-to-insertion ratios between 1.6 and 2.5. One character out for every character in, sometimes the wrong one.
- **Adding.** Zero-shot VLMs: 44 % and 54 % insertions, ratios of 0.2 and 0.1. Fine-tuned TrOCR models sit between at 0.8.

For an edition the distinction matters more than the rate. An omission leaves a gap that proof-reading catches. A substitution leaves a wrong word in the right place. An insertion leaves text nobody ever wrote, and it does not read differently from the transmission.

Individual observations worth recording:

- The single most frequent error of the best model is `u → ŭ` at 11.5 % of all its errors — the u-bow, a transcription convention rather than a misreading.
- The most frequent error of `trocr-kurrent-XIX` is an inserted space at 15.0 %. An eighth of its CER is output convention: normalising whitespace and punctuation improves it by 13 %.
- The same normalisation makes every kraken model *worse* by 8–12 %. The sign of that change is a diagnostic: where normalisation helps, errors are conventional; where it hurts, they are on the letter.
- Line-break characters are the hardest of the corpus for all engines: `¬` at 29–61 %, `-` at 12–63 %. Diacritics are consistently two to five times harder than plain ASCII.

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

The effective intervention is asking the judge *less often*. A gate that escalates only when the two fine-tuned recognisers disagree by more than 0.30 CER consults it on 7 of 40 lines and beats the no-judge rule for the first time. On the other 33 the reliable systems agree, and there a choice can only do harm.

Giving the judge the facsimile does not help: 0.283 with the image against 0.273 without. The model used reaches 78.9 % CER on this material itself — it cannot read the line, so it cannot check it. Handing the page to a poor reader does not make a good referee. What the image *does* reveal is self-preference: with a naive prompt the vision judge picks its own reading 14 times out of 40, against a chance value of 10.

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

The page-versus-line comparison is answered for prose (above). The equivalent for the Valais forms, where the page mode additionally has to preserve the table structure, is running; the structural score is validated against five constructed perturbations.

## Reproduction

- Error taxonomy: [CERberus](https://github.com/WHaverals/CERberus) (Wouter Haverals)
- Reference: Hodel, T., Schoch, D., Schneider, C., & Purcell, J. (2021). *General Models for Handwritten Text Recognition: Feasibility and State-of-the Art. German Kurrent as an Example.* Journal of Open Humanities Data 7: 13, Table 3. [DOI 10.5334/johd.46](https://doi.org/10.5334/johd.46)
- Unless stated otherwise, no normalisation of case, whitespace or punctuation was applied.
