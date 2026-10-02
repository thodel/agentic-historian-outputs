---
layout: default
title: "Reading the Laßberg correspondence"
---

> **Research publication, in English.** This page is part of the public site and is linked from [Forschung](../forschung.html), the German research index. It is not a working document: it records what was measured. The rest of the public site is German — see the [language policy](../about.html#sprachpolitik) for why this one is not.

# Reading the Laßberg correspondence

6742 digitised pages of letters to and from Joseph von Laßberg (1770–1855), held across thirteen archives and libraries, were read end to end by machine. This page records what that cost, how far the readings disagree with each other, and — for one engine, on 276 pages — how far they disagree with a human transcription.

It records **what was measured**, and marks clearly where a number is provisional. One result here is a measurement of quality; everything else is a measurement of cost or of disagreement, and those are not the same thing. Where a figure contradicts something this project said earlier, the correction is stated rather than quietly applied.

**What this page is not.** It is not an engine comparison. Eight candidate engines are queued against this ground truth and have not run; the single quality column below belongs to one model. Treating it as a ranking would be reading one number as a field.

## The corpus

| | |
|---|---|
| Material | German Kurrent, c. 1808–1855, letters and enclosures |
| Extent | 6742 pages · 73.87 GB uncompressed TIFF |
| Holdings | Aarau, Basel, Donaueschingen, Freiburg i. Br., Karlsruhe (blb), Appenzell, Luzern, Marbach, St. Gallen, Stuttgart (wlb), Thurgau, Weimar, Winterthur, Zürich |
| Access | GWDG Nextcloud public share, read in place |

The share is one folder per holding institution, then one per letter. A folder name is therefore the **archive that holds the letter, not the hand that wrote it** — a distinction that matters below, and which this project initially got wrong.

## What two complete runs cost

| Run | Engine | Pages | chars/page | s/page | Wall | Empty |
|---|---|---:|---:|---:|---:|---:|
| `atr_corpus_qwen35_line` | `qwen3.5-4b-german-xix-v2` | 6719 | 1088 | 19.3 | 79.6 h | 625 (9.3 %) |
| `atr_trocr_corpus` | `trocr-kurrent` | 899 | 844 | 38.0 | 8.7 h | 77 (8.6 %) |

Neither run was cut off at a token ceiling, which is worth stating because a page that hits one comes back as an ordinary success and stops mid-sentence.

**The empty pages are a property of the page, not of the engine.** Both runs report the same rate, and the twenty each report names are the same twenty in the same order. A page both engines return nothing for is most likely a blank verso or an envelope flap; a page one returns nothing for would have meant a segmenter that found no lines. The coincidence is evidence for the first reading — not proof, since the reports print only twenty names each.

## Disagreement between two readings

`compare-runs` joins two runs on the page key and reports pairwise disagreement, symmetrised so neither reading is privileged as the reference.

| | |
|---|---:|
| Pages compared (intersection) | 748 |
| Characters per page | 967 vs 991 |
| Median disagreement | 26.3 % |
| p90 | 43.2 % |
| Above the 35 % no-merge band | 30 % of pages |
| Pages empty on one side only | 0 |

**These are not quality figures.** Without a reference, nothing here says which reading is right, and an engine that hallucinates fluently disagrees exactly as much as one that reads badly. What the numbers settle is narrower: whether the readings are a field of comparable candidates, where majority voting has been measured to win, or one leader among weaker ones, where it has been measured to lose. Zero one-sided empties and a 24-character difference in page length say "comparable". The 26 % median says nothing either way.

Two corrections are built into that table.

**Fragments inflated the median.** An unfiltered comparison put it at 45.9 %, because a five-character fragment against an eight-character one disagrees by 75 % and says nothing about whether the engines can read the hand. Excluding pages under 100 characters on either side moved the median to 16.8 % on the probe pair that exposed it.

**One engine's padding moved the page-length column.** Before the quality classifier described below, the same comparison read 973 vs **1183** characters per page — a gap that reads as "the VLM transcribes more". Thirty pages account for it, each padded with thousands of repeated characters. Removing them closed the gap to 24 characters.

## Ground truth, and the one quality measurement

Hand-corrected transcriptions exist in Transkribus for part of this corpus. 552 pages at status DONE, FINAL or GT were harvested on 2 October 2026.

| Status | Pages |
|---|---:|
| FINAL / Final | 416 |
| DONE / Done | 90 |
| GT | 19 |
| no status recorded | 27 |
| **scored** | **552** |
| unusable (21 empty files, 3 below DONE) | 24 |

DONE counts as ground truth here. A page marked DONE has been corrected by a human; this collection used the GT tag on only 19 pages, so requiring it would have discarded 96 % of the available truth.

### Matching, and the floor that is not a measurement

Transkribus shares no identifier with the page keys this pipeline uses, so each ground-truth page is located by content: its text is scored against every page of a run, and the best match wins. Every match carries its runner-up, and is called *clear* only when the best is substantially better than the second best.

That test turned out to carry most of the information. **Two unrelated German pages of this corpus score about 68 % CER against each other.** A large block of ground-truth pages matched at 60–69 % with a runner-up within a percentage point of the best — the signature of a page that is not in the run at all. Without the confidence test, 68 % would have entered the table as a quality figure for every one of them.

276 pages located a corpus page unambiguously.

### What the ground truth turned out not to be

**Two documents are a printed edition, not scans.** `doc1350777` and `doc1350778` carry 45–51 lines and 2000–2900 characters per page, their first lines are page numbers running 231–293, and one reads `BRIEFE PUPIKOFERS AN JVLASZBREG`. These are pages of an *edition* of the correspondence. They cannot match a letter scan, and they account for much of the unmatched block.

**The same page appears under several document ids.** `doc7151593` and `doc4726794` hold identical text and score identically to three decimal places; so do at least five further pairs. Transkribus holds the same material under multiple document ids, and a page counted twice carries double weight in any average. The key list this harvest produces is deduplicated; the per-page table is not yet.

### The result

On the 276 located pages, scored against the human transcription, `qwen3.5-4b-german-xix-v2` reads at a character error rate ranging from **3.5 %** to about 56 %.

That range is not noise, and it is not a property of the model.

| Written by | Example | CER |
|---|---|---:|
| Wackernagel, from Basel | `doc7151938` "Basel 8/8/33" | 6.0 · 6.8 · 9.3 % |
| | `doc7151991` "Basel 30 Augst 33" | 8.1 · 8.0 · 7.9 · 6.9 % |
| | `doc7151993` "Basel 25 Apr. 1838" | 6.9 · 8.0 · 6.9 · 8.3 % |
| Laßberg, from Eppishausen | `doc4726780` "Eppishausen 21 Maerz 1834" | 34.8 · 32.6 · 34.0 % |
| | `doc4726761` "Eppishausen am 5 Juny 1834" | 34.0 · 37.4 % |
| | `doc4726758` "Wolgeborner, Hochzuvererender Herr Professor!" | 41.9 · 39.4 % |
| Laßberg, from Meersburg | `doc4726783` "Auf der alten Meersburg am 17 October 1840" | 34.7 · 31.2 · 43.8 % |

**The error rate splits by hand, by a factor of four to five, within a single engine on a single corpus.** His correspondents' hands read at 6–20 %; Laßberg's own reads at 27–45 %.

This has a consequence for everything that follows. A corpus-wide average would hide it, and an engine comparison that does not control for it would reward whichever engine's pages happen to include more correspondent letters. The comparison has to be stratified.

**And the obvious stratification key does not work.** This project proposed grouping by the first path segment, on the reasoning that it encodes provenance and provenance tracks the hand. It does not: `doc7151991` (Wackernagel, 8.1 %) and `doc4726780` (Laßberg, 34.8 %) are both held in Basel and both sit under `Basel__`. The folder is the holding archive, which holds both sides of a correspondence. Assigning a writer needs the dateline or the Transkribus document metadata, and is not yet in code — the groupings in the table above were read off the datelines by hand, and no median over them has been computed.

## Nine defects the measurements found

Measuring this corpus was mostly a matter of finding out why the measurement was wrong. Each of these was found by a number that could not be true.

| | Symptom | Cause |
|---|---|---|
| Walk aborted | Three corpus runs died mid-enumeration | A malformed listing response was not retried, and one unreadable folder ended the whole walk |
| Digit loop | One page returned 8824 characters, c. 8000 of them `0` | No signal distinguished a padded page from a read one; `truncated_by_model` was false and both files were on disk |
| Filler loop | `die / der / 1869 / der / der` down a page | Caught only by repetition *in lines too short to be lines of text*; the first loop test missed it entirely |
| Rate limit | Publishing stopped at chunk 24 of 68 with a 403 | GitHub's secondary limit answers 403, not 429, and 203 write calls per chunk tripped it |
| Checkout inventoried | A dry run offered `astronaut.png` as a Laßberg letter | `Path("")` is `Path(".")`, so an unset variable became a walk of the working directory |
| Same again | An unset `$GT_ROOT` offered a setuptools manifest as ground truth | The same trap, in a second place, after the first had been fixed |
| One empty file | A 16-page scoring run reported nothing at all | One unreadable file raised instead of being collected; 15 measured pages were discarded with it |
| Unlisted model | A smoke run spent 23 minutes to fail on its first page | An id the gateway had already said it does not have was treated as "unknown — run anyway" |
| Punctuation floor | Word-identical texts scored 3.1 % against each other | The metric strips punctuation *after* collapsing whitespace |

A tenth is not a defect in this pipeline but shaped the measurements: the share answered 401 to every request on 2 October, the mount was empty, and some 6700 pages sat on local disk in a cache that was not an admissible source. It is one now.

## What is not measured

- **Seven of eight candidate engines.** `trocr-kurrent`, `trocr-kurrent-xvi-xvii`, `kraken-bohemian_19th`, `kraken-mendelssohn_letters`, `kraken-fondue_gd_v2`, `kraken-manu_mcfondue` and `qwen3vl-german-xix-v2` have no quality figure here. Four of the kraken models have never read a page in this stack.
- **Whether fusion helps.** The symmetry signals favour trying it; the magnitude of disagreement does not settle it.
- **The French letters.** `kraken-fondue_gd_v2` is the only plausible candidate and is untested on them.
- **Whether the 625 empty pages are blank.** Nobody has looked at the images.
- **A median per hand**, for the reason given above.

## Reproducing

The runs, the comparison and the scoring are three commands in the [`agentic_historian`](https://github.com/thodel/agentic_historian) repository; `docs/BATCH_ATR.md` there is the runbook. The ground truth is a Transkribus collection and is not public. The readings are published per page as plain text.

The figures on this page come from the runs' own reports, rebuilt from the files on disk rather than observed as the runs happened — which is why the *failed* column of those reports is not quoted here: a page that failed wrote nothing, and nothing is what a rebuilt report cannot count.
