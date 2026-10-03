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

DONE counts as ground truth here. A page marked DONE has been corrected by a human; this collection used the GT tag on only 19 pages, so requiring it would have discarded 96 % of the available truth. The gate is enforced once and rejects a status below DONE loudly.

The 27 pages with **no status recorded** are a different case: the gate reads `if gt.status and …`, so an unreadable status short-circuits it and the page is admitted without a warning. None of the 27 is hand-made — all 576 files carry the harvester's naming, and 23 of the 27 hold a `TranskribusMetadata` element that simply omits the status. The harvest knew it, because it only ever fetches corrected pages, and wrote the file without recording it. So 4.9 % of the ground truth is admitted on trust, and the policy is the reverse of the one the module argues for: a known-bad status is refused, an unknown one is accepted in silence.

### Matching, and the floor that is not a measurement

Transkribus shares no identifier with the page keys this pipeline uses, so each ground-truth page is located by content: its text is scored against every page of a run, and the best match wins. Every match carries its runner-up, and is called *clear* only when the best is substantially better than the second best.

That test turned out to carry most of the information. **Two unrelated German pages of this corpus score about 68 % CER against each other.** Cross-document ground truth scored against ground truth gives a 1st percentile of 68.6 % and a median of 78.5 %; the runner-up of a page that *was* located has a median of 67.2 % and never exceeds 70.6 %. Without the confidence test, 68 % would have entered the table as a quality figure for a large block of pages.

276 pages located a corpus page unambiguously.

### Two corrections to the paragraph above, found by re-reading the same run

**The test is "clear" only when the best is half again better than the second best** — `cer × 1.5 < runner_up_cer` ([`gt_score.py:92`](https://github.com/thodel/agentic_historian/blob/main/agentic_historian/gt_score.py)). Put that factor beside a runner-up that sits on the 67–69 % chance floor and it becomes an absolute ceiling: **no page can be called located if it reads worse than about 45 %**, whatever it is. The boundary is visible in the table — 43.7 % and 43.8 % are clear, 44.9 %, 45.7 % and 45.8 % are doubtful, and nothing above 46 % is ever clear. The located set is therefore **censored, not sampled**, and the verdict cannot tell "the true page is absent from the run" from "the true page is present and was read badly".

**The doubtful block is not one population, and this page previously said it was.** It is at least three, and only the first is a non-match.

| | What it is | Evidence |
|---|---|---|
| ~a fifth of scored pages | A genuine non-match. CER is noise and the matched key arbitrary | A tight cluster at 69.0–69.2 %, no alignment to any window of the ground-truth page (window-CER 74–75 %), overshooting the page's own length floor by ~41 points. Two are exact floating-point ties, broken only by alphabetical key order |
| Most of the 60–69 % band | A **correct** match of a long page that a line-trained reading only half covers | `doc1350778_page244` scores 68.6 % overall and 29.8 % against a *window* of its ground truth; page 251 scores 66.4 % / 32.3 %, page 264 68.1 % / 31.3 %. 17 of 24 sampled pages of that document match the same Winterthur shelfmark with strictly monotone ordinals — 16 of 16 steps, which chance does not produce |
| The 47–60 % end | A correct match, read badly | 10–20 points below the chance floor, runner-ups 10–20 points worse, and the matched readings are recognisable verbatim (`doc1682344_page1`, 51.0 % against a runner-up of 68.5 %) |

The missing discriminator is **length**. A 900–1400-character reading cannot score below 42–61 % against a 2000–2900-character ground-truth page however accurately it reads the part it covers. Non-matches overshoot that floor by ~41 points, correct partial matches by 9–25. A ratio between two CERs cannot separate those, which is why one rule marks a 12 % match and a correct 68.6 % match doubtful for opposite reasons.

**And 15 of 71 sampled doubtful pages read at 12–25 %.** They are doubtful only because the run holds a near-duplicate of the page they matched, so the runner-up is almost as good. Duplication in the *reading* corpus costs ground-truth pages their verdict.

One mechanism makes a page unlocatable before any of this: 625 of the 6719 readings are empty and 1349 are under 100 characters, and an empty candidate scores a CER of exactly 1.0. **A ground-truth page whose own reading came back empty can never win its own match** — it is not in the located set, and its absence is invisible there.

### What the ground truth turned out not to be

**Two documents are a printed edition, not scans.** `doc1350777` (32 pages) and `doc1350778` (53) carry 45–51 lines and 2000–2900 characters per page, their first lines are folio numbers running 231–283, and the opening page reads `BRIEFWECHSEL ZWISCHEN J VON LASZBERG UND JOHANN ADAM PUPIKOFER` above an editor's introduction. These are pages of an *edition* of the correspondence. All 85 share one scan size, 2479 × 3508; no other document in the collection has it. They are **15.4 % of the scored pages and 27.9 % of the ground-truth characters** — mean 2458 characters and 47.9 lines against 1154 and 19.7 for the rest.

*Correction:* this page previously said they account for much of the unmatched block. They do not. 85 pages are **about 31 % of the 276** that failed to locate, so they are a large distortion of the character budget and not the explanation of the split.

**A corrected status does not mean a corrected page.** Those 85 carry uncorrected PyLaia output (`model_id=39995`) under statuses `Final` and `FINAL`, so the status ladder admitted machine output as ground truth. Two of them are two OCR passes of the same printed folio and disagree in 8 of 48 lines; one carries a fully garbled Greek line. Their own error rate is only 0.1–0.5 %, so they would serve as a reference — what disqualifies them is that no page of the manuscript corpus corresponds to them at all.

**The same page appears under several document ids — 98 times, not five.** Measured over all 552 scored files: they describe **454 distinct pages**. There are 98 duplicate groups, every one of them a pair; 87 pairs are byte-identical text and 11 differ by one to four characters while sharing a Transkribus `pageId`. `doc4726754_page2` and `doc7152014_page6` are the same `pageId=86566867`. The pair `doc12542129_page2` / `doc12632012_page1` is the only kind that does *not* share a pageId: a second upload of the same images.

*Correction:* the headline "552 ground-truth pages" counts files, so it overstates the available truth by 17.8 %. And the located fraction reads better against the right denominator: **276 of 454 distinct pages, 61 %**, not half of 552. Nothing in the scorer mentions duplicates and no test covers them.

### The result

On the 276 located pages, scored against the human transcription, `qwen3.5-4b-german-xix-v2` reads at a median character error rate of **17.2 %**, with the best page at **3.5 %**.

*Correction:* this page previously gave the range as 3.5 % to about 56 %. The upper end cannot belong to a located page. The confidence rule caps a located page at roughly 45 % (see above), the clear rows in the table stop at 43.8 %, and a clear row at 56 % would need a runner-up above 84 % — which no page has. The 56 % came from a row the scorer itself marked doubtful.

That spread is not noise, and it is not a property of the model.

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

**That factor is a lower bound.** Laßberg's hand reads at 27–45 %, and 45 % is exactly where the confidence rule stops admitting pages. His hardest pages cannot enter the located set at all, so the measured range is cut off at the top by the matcher rather than by the model. Whatever his true error rate is, it is worse than this table can show, and the gap to his correspondents is wider than four to five.

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
- **How badly Laßberg's hand actually reads.** The confidence rule cuts the located set off at about 45 % CER, which is inside his range, so his worst pages are absent by construction. Measuring him needs a match test that does not depend on how well the page was read — the Transkribus `pageId` would do it, if the readings carried one.
- **Which doubtful pages are non-matches.** Three populations share that verdict and a CER ratio cannot separate them. The discriminator that can is each page's own length floor: the error rate a reading of its length cannot beat even when it is right. Nothing computes it yet.
- **Whether the 27 unstatused pages were corrected.** The harvest only fetches corrected pages, so they probably were, but the file does not say and the harvester records nothing.

## Reproducing

The runs, the comparison and the scoring are three commands in the [`agentic_historian`](https://github.com/thodel/agentic_historian) repository; `docs/BATCH_ATR.md` there is the runbook. The ground truth is a Transkribus collection and is not public. The readings are published per page as plain text.

The figures on this page come from the runs' own reports, rebuilt from the files on disk rather than observed as the runs happened — which is why the *failed* column of those reports is not quoted here: a page that failed wrote nothing, and nothing is what a rebuilt report cannot count.
