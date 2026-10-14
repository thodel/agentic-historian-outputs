---
layout: default
title: "Reading the Laßberg correspondence"
---

> **Research publication, in English.** This page is part of the public site and is linked from [Forschung](../forschung.html), the German research index. It is not a working document: it records what was measured. The rest of the public site is German — see the [language policy](../about.html#sprachpolitik) for why this one is not.

# Reading the Laßberg correspondence

Some 6700 digitised pages of letters to and from Joseph von Laßberg (1770–1855), held across thirteen archives and libraries, were read end to end by machine. **Eight recognition engines** then read the pages for which a human transcription exists and were scored against it. A **ninth reader**, a commercial model behind an API, read a 300-page sample in October and is the subject of its own section: it has no quality figure, because the sample was drawn from the pages nobody has transcribed. This page records what that cost, how far the readings disagree with each other, and how far each of them differs from the transcription.

It records **what was measured**, and marks clearly where a number is provisional. The engine comparison is a measurement of quality, because one side of it is a human transcription; the run figures measure cost, and the disagreement figures measure neither. Where a figure contradicts something this project said earlier, the correction is stated rather than quietly applied — ten of them contradict a figure this page itself used to carry — one of those within a day of publishing it — and the sections below record several more that never made it this far.

**What this page was not, until 5 October 2026.** It said, in this place, that it was not an engine comparison, because seven of the eight candidates had no quality figure. They have one now.

## The corpus

| | |
|---|---|
| Material | German Kurrent, c. 1808–1855, letters and enclosures |
| Extent | 6722 pages · 73.98 GB uncompressed TIFF (5 October 2026) |
| Holdings | Aarau, Basel, Donaueschingen, Freiburg i. Br., Karlsruhe (blb), Appenzell, Luzern, Marbach, St. Gallen, Stuttgart (wlb), Thurgau, Weimar, Winterthur, Zürich |
| Access | GWDG Nextcloud public share, read in place |

The share is one folder per holding institution, then one per letter. A folder name is therefore the **archive that holds the letter, not the hand that wrote it** — a distinction that matters below, and which this project initially got wrong.

**The corpus is not stable, and this page previously gave its extent as fixed.** On 2 October the share held 6742 files and 73.87 GB; on 4 October, 6722 and 73.98 GB. Two folders had gone, each answering 404 as a whole rather than losing individual files: `Briefe UB Freiburg/` and `Donaueschingen/Photos-1-001/`. Between them they held the images of **35 pages for which hand-corrected text exists** — six letters and a set of photographs — so those pages can no longer be measured or published. The transcriptions are untouched in Transkribus; it is the digitisations that are absent, and whether they were deleted, moved or renamed is a question for the share's custodians. The engine comparison below therefore ran over 241 reachable pages where the ground-truth harvest had located 276.

## What the runs cost

| Run | Engine(s) | Pages | chars/page | s/page | Wall | Empty |
|---|---|---:|---:|---:|---:|---:|
| `atr_corpus_qwen35_line` | `qwen3.5-4b-german-xix-v2` | 6719 | 1088 | 19.3 | 79.6 h | 625 (9.3 %) |
| `atr_trocr_corpus` | `trocr-kurrent` | 899 | 844 | 38.0 | 8.7 h | 77 (8.6 %) |
| `atr_gt_candidates` | seven candidates | 241 each | — | ~40 | 16.5 h | — |
| `gemini-300-strict` | `gemini-3.8-flash` (API) | 300 | — | 6.4 | 32.4 min | 28 (9.3 %) |
| `gemini-300-final` | `gemini-3.8-flash`, 3 attempts merged | 300 | 883 | — | — | 19 (6.3 %) |

The candidate run is 1687 page-engine pairs with **no failures and no source errors**, and it was the first time four of the kraken engines had read a page in this stack at all. It read only the pages the ground truth locates, which is why it is 16.5 hours and not the fortnight the whole corpus would have cost for seven engines.

**Every engine costs about the same per page** — 1.4 to 1.7 pages a minute — whether it is a 15.8 GiB vision-language model or a 2.6 GiB line recogniser, and whether the page cache was cold or warm. Whatever dominates the per-page cost is therefore common to all of them, request overhead or the size of a 25 MB TIFF, and not the model. *Correction:* a working estimate published here assumed the line recognisers would be some three times faster than the vision models, on the strength of a three-page smoke run. Over 241 pages they are not.

Neither corpus run was cut off at a token ceiling, which is worth stating because a page that hits one comes back as an ordinary success and stops mid-sentence.

The external reader is billed per page rather than per hour of a card that is idle anyway, and it is the cheapest reading in the table: 6.4 seconds and about 1500 input plus 250 output tokens a page, some 32 minutes and well under a dollar for 300 pages. The two local corpus runs cost nothing per page and 88 hours of one GPU.

**The empty pages are a property of the page, not of the engine.** Both runs report the same rate, and the twenty each report names are the same twenty in the same order. A page both engines return nothing for is most likely a blank verso or an envelope flap; a page one returns nothing for would have meant a segmenter that found no lines. The coincidence is evidence for the first reading — not proof, since the reports print only twenty names each.

*Correction, 11 October:* that claim holds for these two engines and does **not** generalise to a reader that is sampled. It was made without ever having run one engine twice over the same pages, and when that was finally done the empties moved: three of 25 pages empty in the first attempt came back with text in the second, under an identical prompt and an identical thinking level. One of them, `Winterthur__310-MsBRH_513-91-131`, had been empty in **four** prior runs and reads, on the fifth, as a complete 978-character letter from Justizrat Zellweger, Trogen, 27 April 1831. For a sampled reader an empty answer is partly a property of the attempt, and "empty in both engines" is a weaker statement than it looked. See [*Variance, measured too late*](#variance-measured-too-late).

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

## A ninth reader, and what a sentence in a prompt costs

Between 10 and 12 October 2026 a commercial model behind an API — `gemini-3.8-flash`, reached through an OpenAI-compatible endpoint — read **300 pages sampled from the 6466 that have no transcription at all**. The sample is deterministic (seed 20260915), so the same 300 pages come back on every re-run.

**There is no quality figure in this section, and there cannot be.** The pages were chosen because nobody has transcribed them; scoring them would need the thing that is missing. What this reader could be measured on is everything else: what it costs, what form it returns, how it fails, and how far two readings of the same page differ. Three of those turned out to be more informative than a character error rate would have been, because each of them found a defect that the eight scored engines could not have shown.

### Thinking is paid for out of the answer

The first finding is a property of this class of model rather than of this corpus. The model may reason before it answers, and its reasoning tokens are billed as output **and** spent against the same ceiling as the answer.

| Prompt | Thinking | Ceiling | Result |
|---|---|---:|---|
| `lassberg_atr @092fb6b0` | model default | 8192 | complete, 1592 characters |
| `lassberg_atr_strict @03c5a660` | model default | 8192 | **cut off**, 1153 characters |
| `lassberg_atr_strict @03c5a660` | **low** | 8192 | complete, 1375 characters, **392 output tokens** |

392 of 8192. Under the default setting roughly 7800 tokens went into deliberation until nothing was left for the page, and the page came back as an ordinary success that stops mid-word. **Transcribing what stands on a page is not a reasoning task**, and the side effect of saying so is a factor of 3.6 in speed: 6.4 seconds a page instead of 23.3.

### Three pages where the model argued with itself, in the transcription field

`gemini-300-strict` reported four pages cut off at the ceiling. Three of them carry **no text of the page**. They carry the model reasoning aloud, in English, in the field the transcription belongs in:

```
- e - n - k - t !
LOOK AT WORD 3:
g - e - s - c - h - e - n - k - t !
Wait, does it have 'sch'?
…
Entry stroke, downstroke, loop up to the right... THAT'S A 'V'!
```

**No quality column moved.** These pages are not empty, not short (816–928 characters), and not repetitive — every line differs and the longest run of one character is three. They were seen *only* because the arguing ran into the token ceiling. A page that argues for four hundred characters and then stops cleanly would have entered the corpus as a reading.

That inverts the obvious remedy. Raising the ceiling, which is right for a genuinely truncated transcription, **buys more arguing** for these three. What they need is a different prompt.

A classifier verdict now names the failure, and the separation it rests on was measured rather than assumed: the density of English self-addressed line openings ("Wait", "Look at", "Line 12:") is **0.38, 0.55 and 0.70** on the three leaked pages and **0.00** on every clean reading of the same pages. The threshold sits at 0.2, far from both. A transcription of this corpus is German and Latin and never addresses itself.

**The open question was how many pages argued without hitting the ceiling, and the answer is none.** All 300 pages of the run were reclassified under the new verdict: `ok` 249, `short` 19, `empty` 28, `deliberation` 3, `repetitive` 1 — and the three are exactly the three the ceiling had given away. No fourth. What that number does *not* say is that the 249 are read correctly; `ok` means "none of the known defects", and in this run there is no reference for anything stronger.

### A single sentence about blankness hid two letters

The stricter prompt bought its discipline with silence: 21 pages that the same model had read as text under the first prompt came back empty under the second. Reading all 28 empty pages under both prompts settled what that silence was, and it went **against the first prompt**, not the second:

| What is on the page | Pages |
|---|---:|
| **A real transcription** the strict prompt lost | **2** |
| A stamp or a registry note — text, but not the letter's hand | 3 |
| **A commentary about a blank page** ("Vakatseite", show-through, watermark) | 21 |
| Empty under both prompts | 2 |

On an unwritten leaf, **nothing** is the correct transcription. The first prompt was filling the transcription field with museum prose — `### Transkription *[Die Seite enthält keinen handschriftlichen Text / vacat. In der Papiermitte ist schwach ein Wasserzeichen erkennbar.]*` — and the quality classifier counted that prose as text, which is why the column named `empty` looked like a failure of the stricter prompt. Published, those 21 pages would be invented description presented as transcription.

The real loss was 5 pages of 28, and all five trace back to **one sentence**. `An empty page is an empty answer` was the strict prompt's only statement about blankness, and the model applied it to every page it did not want to write out. An empty answer therefore meant two different things — *this leaf is unwritten* and *this page I am not transcribing* — and in the second meaning two written pages disappeared. An empty answer is a success by every signal the runner has, so five pages hid inside a column called `empty`.

The variant `lassberg_atr_strict2 @9e0503e8` keeps the output discipline verbatim and separates the cases:

| On the page | Answer |
|---|---|
| no writing at all | an empty answer — which now **asserts** that the leaf is blank |
| writing, legible | a transcription, with `[...]` and `word[?]` where needed |
| writing, none of it legible | `[unlesbar]`, once — not 24 lines of `[...]` |
| a stamp, an accession number | `[stempel: …]` |
| foliation, a docket, a later hand | `[fremde hand: …]` |

and it names three things that are **not** text on the page and are neither transcribed nor described: show-through from the other side, watermark and paper condition, and anything inferred rather than read. Those three are precisely what the 21 commentaries were made of.

Marking a stamp rather than transcribing it bare is an editorial decision, and it is recorded as one: an unmarked "Schillermuseum 11551" in the middle of a transcription is worse than no stamp at all, because nothing downstream can remove it again.

Validated on the same 33 pages that produced the finding — the 21 blank ones as a control, the 5 losses as the probe: **22 of 22 blank pages stayed blank**, no page gained prose, 4 of the 5 losses came back (both written pages, both stamps), one docket is still missing, and two pages were newly found. Over the whole 300, the two prompts disagree by a **median of 6.6 %** on 240 comparable pages, while `arguing` falls from 3 to 0, `cut off` from 4 to 0, and the flagged total from 33 to 25.

### Variance, measured too late

A whole day of prompt comparisons had been read off differences between runs without anyone measuring what two *identical* runs differ by. Done on 11 October: the same 25 flagged pages, the same prompt, the same thinking level, a second attempt.

| | |
|---|---:|
| Pages | 25 |
| Empty in both attempts | 21 |
| **Empty in the first, read in the second** | **3** |
| The other way round | 0 |

What is in those three pages is not scrap. `Winterthur__310-MsBRH_513-91-131` is a complete 978-character letter from Justizrat Zellweger, Trogen, 27 April 1831, and it had been empty in four earlier runs, one of them under a different prompt. `StATG …1339_00101` is a 902-character letter from Pupikofer, Bischofszell, 25 July 1829 — the same page, same prompt, three attempts: text, empty, text.

**This corrected two statements made the same morning.** "22 of 22 blank pages stay blank" was the control of *one* attempt, and `Winterthur` was among those 22, booked as unwritten while a letter stands on it. "21 of the 28 are blank versos" counted the same page as blank.

On ordinary pages the scatter is small — 6.6 % median between two *different* prompts over 240 pages. **The noise does not sit in the running text; it sits on the tipping point between reading a page and answering nothing.** That is also where it does the most damage, because an empty answer is indistinguishable from a blank leaf.

A third attempt on the 19 still-empty pages recovered two more, and neither carries substance:

| Attempt | Still empty | Newly read | Of which substance |
|---|---:|---:|---|
| 1 (the 300-page run) | 24 | — | — |
| 2 | 21 | 3 | **2 complete letters** (978 + 902 characters) |
| 3 | 19 | 2 | **0** |

**The second attempt fetches the letters, the third only fragments.** Two attempts is therefore the policy this measurement supports. Counted in pages the two rows read 3 and then 2, almost no decline at all; the collapse is visible only by reading what is in them. **A count of pages is not a count of text.**

### A fourth attempt against a second reader

The sentence above used to end "nothing here shows the yield is zero after that — only that it collapses". Both halves of that have now been measured, on 13 October, over the 19 pages the published corpus still had empty.

| | Pages recovered |
|---|---:|
| A fourth attempt — same reader, same prompt, same thinking level | **0 of 19** |
| A second *reader* — two local engines from other model families, one of them segmenting lines | **1 of 19** |

So the yield curve of one reader over four attempts is **3 → 2 → 0**, and "ask again" is exhausted as a lever. The page the other engines found is `blb lassberg__K 2911,93__page_0001`. Both return **24 lines**; 14 of the 24 agree, among them the shelfmark in line 1, the number `67` in line 2, a salutation in line 3 (`Hochwolgebohrner`, which the other engine garbles to `Gottesvollgeboren`), and both end the final line with a hyphen, so the text runs on to the next leaf. **Neither reading is usable as a transcription**, and that was not the question: the question was whether there is ink on the leaf.

The same measurement carried its own negative control, which is what makes it a measurement rather than a hope. On five of the nineteen both engines also returned something, and three signals mark it as noise over a nearly blank page: **zero** shared words of five characters or more across those five pages; each engine repeating its own phrases on different leaves (`haußhaltung zu Buchstetten verschicken`, verbatim, twice); and the engine trained on sixteenth- and seventeenth-century material dating a Laßberg leaf to `1655`. **Agreement between independent readers is evidence. Output from independent readers is not.**

| | Pages | What it is |
|---|---:|---|
| Silent in three readers from three model families | **13** | blank, as far as any machine can say |
| A trace of ink, hallucinated over by both segmenters | **5** | foliation, a stamp, show-through — no letter text |
| **Written** | **1** | a letter's first page, refused four times |

For one of the five there is independent testimony that fits exactly: `UB Bern__Mss_h_h_XLIV_180_32_169` is the page the external reader described, under its first prompt, as "vollständig unbeschrieben … Durchschlagen". The strict prompt forbids transcribing show-through, so its silence there is the correct answer.

**Repeating a measurement with the same instrument estimates that instrument's noise.** It cannot separate a property of the object from a bias of the instrument; for that the instrument has to change. The policy this leaves is: two attempts of the reader you are using, then a reader from another family — 38 calls and six minutes of a GPU that is idle anyway.

*Correction:* this page said, one section above, that it is not known whether the 19 are blank. It is now known for 18 of them in the strongest sense a machine can offer, and known to be false for the nineteenth.

### The merged corpus, and a ranking that is an editorial decision

Three attempts live in three run directories, and publication takes one. A merge step writes a run that holds, per page, the best attempt — decided by verdict, never by length, with the caller's order of the inputs breaking ties:

| Verdict | Rank | |
|---|---:|---|
| `ok` | 3 | a reading of the page |
| `short` | 2 | little, but it stands on the page |
| `empty` | 1 | asserts nothing |
| `repetitive`, `deliberation` | 0 | **below `empty`** |

That last row is the actual decision and it is arguable. Those pages carry text that is not a reading of the page, and in a published edition that is invention wearing a transcription's clothes. **Nothing is better than something invented.** Deciding by length would be exactly wrong: a deliberating page carries 800 characters of self-address and wins any size comparison against the transcription it replaced.

Each merged page keeps its own attempt's payload — settings, prompt digest, gateway version, timings stay true — and gains a record of which attempt was chosen and what the others answered. One field is recomputed rather than carried: the quality verdict, because it is the only part of the payload that is a judgement rather than a fact about the call. That distinction was found the hard way, by reading a published file that carried `merged_from.verdict: ok` beside `quality.verdict: repetitive`.

**A verdict is currency inside one reader and not between two.** Having found the written page, the obvious move was to merge the other engines' run into the corpus and let this ranking pick the better reading. A dry run first: 300 pages plus 38 is 338, nothing improved, nothing compared — the merge identifies a page by *(model, key)*, not by key alone, so the two engines' readings never met the pages they were meant to repair. That is the safe side of the mistake. Keyed on the page alone, the five noise pages would have won, because their verdict is `short` and the refusals' is `empty`, and `orchecker classica` would have been published as a transcription in somebody else's edition. The ranking guards against `repetitive` and `deliberation`; a *short, fluent* invention by a foreign model walks past it. Taking one page's reading from another engine is an editorial act that has to name that engine on that page — not bookkeeping a merge can do quietly.

The result was published on 12 October 2026 into the edition's pull request ([michaelscho/lassberg#3](https://github.com/michaelscho/lassberg/pull/3)), as plain text and per-page JSON side by side:

| | |
|---|---:|
| Pages | **300** |
| With text | **281** |
| Empty after two attempts | 19 — of which **one is a written page**, see below |
| `looped` / `arguing` / `cut off` | 0 / 0 / 0 |
| Characters per page | 883 |
| Files | 602 (300 `.txt`, 300 `.json`, two reports) |
| Prompt | `lassberg_atr_strict2 @9e0503e8`, thinking `low` |

Nothing published there is false — an empty text file asserts nothing about the leaf — and no byte of it was changed when the written page was found. What that page needs is a note at the edition saying which of the nineteen it is, which is a message to the maintainer rather than an edit to the corpus.

The JSON travels with the text on purpose: for every page it records which prompt digest, which thinking level and which ceiling produced that reading, so the question "would this come out differently now?" has an answer per page rather than per run.

## Ground truth, and how a page is found at all

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

**The eight-engine run below gives this engine 16.1 % over 226 pages, and the two figures measure different things.** 17.2 % is a median over the ground-truth *files* this engine located on its own; 16.1 % is a median over distinct corpus *pages* located by eight readings in agreement. Counting pages rather than files accounts for most of the difference, and requiring eight readings to agree makes a page harder to locate, which is why 226 is fewer than 276.

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

## How the engines compare

On 5 October 2026 eight readings of the same pages were scored against the human transcription in one run: the seven candidates over the pages the ground truth locates, and the corpus reading from September. **226 corpus pages were located, each counted once** — of the 241 the candidate run could reach, since 35 pages lost their images.

| Engine | Median CER | p90 | best page | worst page |
|---|---:|---:|---:|---:|
| `qwen3.5-4b-german-xix-v2` | **16.1 %** | 34.1 % | 3.5 % | 43.8 % |
| `qwen3vl-german-xix-v2` | **16.8 %** | 37.3 % | 4.5 % | 45.9 % |
| `trocr-kurrent-xvi-xvii` | 18.7 % | 39.9 % | 6.3 % | 55.0 % |
| `trocr-kurrent` | 22.3 % | 45.7 % | 7.6 % | 75.0 % |
| `kraken-fondue_gd_v2` | 22.3 % | 38.4 % | 6.1 % | 51.4 % |
| `kraken-manu_mcfondue` | 26.9 % | 42.8 % | 6.8 % | 53.4 % |
| `kraken-bohemian_19th` | 44.1 % | 61.5 % | 14.8 % | 68.4 % |
| `kraken-mendelssohn_letters` | 53.2 % | 63.2 % | 25.0 % | 69.2 % |

**This is not a field of equals.** Between first and last there is a factor of 3.3 in the median. That settles more than an order: majority voting over several readings has been measured to win among comparable candidates whose errors are uncorrelated, and to lose where one candidate dominates weaker ones. These eight are the second case, so fusing them would be expected to make the best reading worse. The disagreement table above, which read as "comparable candidates", was the wrong instrument for that question.

**The two fine-tuned Qwen models lead**, and the one that has already read the whole corpus leads overall — so the 79.6 hours spent in September were not spent on the wrong engine. The 0.7-point gap between the two is not a decisive difference on 226 pages.

**`kraken-mendelssohn_letters` is finished as a candidate.** A median of 53.2 % and a worst page of 69.2 % put it at the chance floor for unrelated German text: on the harder pages it produces text that is German-shaped and does not correspond to the page.

**A model for the wrong century beats one named for the right one.** `trocr-kurrent-xvi-xvii`, trained on sixteenth- and seventeenth-century material, reads this nineteenth-century Kurrent better than `trocr-kurrent` (18.7 % against 22.3 %), and `kraken-fondue_gd_v2`, trained on French hands, ties with it on the median and beats it at p90 (38.4 % against 45.7 %). Training-set labels are a weak predictor here.

### Why eight readings measure more than one can

The confidence rule described above — a match counts as clear only when the best is half again better than the runner-up — caps a *single* reading's located pages at roughly 45 % CER. With eight readings the cap moves off the engine being measured: a page is located when the readings agree **and at least one** of them places it clearly, so a page that `qwen3.5` reads at 20 % can be scored for `kraken-mendelssohn_letters` at 69 %. That is why the worst-page column above reaches figures no single-engine measurement could have shown, and it is a real gain in what the table can say about weak engines.

The censoring is reduced, not removed. A page **no** engine reads well enough still cannot be located, so the located set remains bounded by the best engine rather than by the corpus. Laßberg's hardest pages are still likely to be missing, and the stratification point below is unaffected.

### Two cautions about these numbers

**The pages are not a sample of the corpus.** They are the pages that have hand-corrected text *and* were located, which is 226 of some 6700. The hand effect below is larger than the differences between most of these engines, so a figure here is a statement about which hands happened to be measured.

**The first version of this table was wrong, and the correction changed a rank.** It counted ground-truth files rather than pages: 66 corpus pages of this ground truth are described by 138 files, so 72 pages entered every median two or three times. Counting each page once moved `trocr-kurrent` from 25.6 % to 22.3 % — from behind `kraken-fondue_gd_v2` to level with it. The duplicates are not an error in the harvest but two people's corrections of one page, so they are averaged into one figure per page rather than dropped.

**And the obvious stratification key does not work.** This project proposed grouping by the first path segment, on the reasoning that it encodes provenance and provenance tracks the hand. It does not: `doc7151991` (Wackernagel, 8.1 %) and `doc4726780` (Laßberg, 34.8 %) are both held in Basel and both sit under `Basel__`. The folder is the holding archive, which holds both sides of a correspondence. Assigning a writer needs the dateline or the Transkribus document metadata, and is not yet in code — the groupings in the table above were read off the datelines by hand, and no median over them has been computed.

## Two archives, two scans of one page

Everything above reads pages. This section is about pairing a page's transcription with its *image*, which is what a line-level training set needs and a character error rate does not: the hand-corrected text carries line polygons in the pixel coordinates of **Transkribus's** copy of the scan, and the image beside it is this pipeline's working copy of the **share's** copy. If the two differ in size, every polygon crops the wrong strip of every line.

**That failure is invisible downstream.** The crops are plausible images, the text is real text, and the only symptom is a model that trains badly for no stated reason. So the export compares the XML's declared geometry against the actual image and refuses a page that disagrees. Of 552 ground-truth files, 241 were exportable and **43 were refused on geometry**.

Those 43 are not one population. Grouped by their pair of sizes — 21 distinct pairs — they are two (counted in files, which is not the same as pages; see the measured result below):

| | Pages | What the two sizes are |
|---|---:|---|
| **One factor on both axes** | **16** | the same scan at two resolutions |
| **Anything else** | **27** | two different photographs of the page |

The boundary is not in a crowded place: the sixteen agree on their factor to **0.11 % or better**, and the nearest refused pair is **0.78 %** out. Nothing is rotated and nothing is a pixel or two apart — so the tempting explanation, two renderers rounding a page's width differently, is not what this is.

**What the 27 are, read off the numbers alone:**

- **A fixed frame.** Sixteen pages land on an image of exactly 1420×1781 while their XML records three different heights against one width. A derivative that maps pages of different heights onto one format is not scaled per page: that page at width 1420 would be 1858 high, not 1781.
- **A second fixed frame**, 1296×1636, reached from four different declared sizes — and in two cases the image is *larger* than the transcription's own copy. An image bigger than the page its polygons describe is not a reduced derivative of it.
- **A scanned opening against a half leaf.** One pair has identical width and exactly half the height (factor 1.9917). The transcription describes a tall image; the share holds one half of it.
- **A landscape photograph against a portrait page.** 2479×3508 — A4 at 300 dpi — against 2968×2553. Not a rotation, which would be 3508×2479.

For the last two, "which scan is authoritative" is the wrong question. The question is which photograph shows the page, and it belongs to the archives rather than to this pipeline.

**The 16 are taken along, and they say so in their own data.** Picking one of two *different* scans is a judgement this project has no standing to make; a factor both axes agree on to a tenth of a percent is not that judgement but an arithmetic fact about one scan. So the coordinates are divided by it — outlines *and* baselines, because moving one and not the other would crop correctly and order the lines wrongly — the declared geometry is rewritten to the image, and each such page carries a comment as its first line naming the factor, both sizes, and how far the two axes disagreed. The export tree is images and XML and nothing else, so a note in a file beside it would not reach whoever reads the dataset; this one travels with the page. A page without a factor stays a byte-for-byte copy.

**What that gained, measured: 13 pages, not 16.** The run of 14 October exports **254** pages where the previous one exported 241, and the plan names each rescaled page with its factor. The sixteen are sixteen *files* describing **thirteen pages**; the other three are second copies of a page under another Transkribus document id. Both copies used to be refused on geometry, so both were counted there; now the first is exported and the second is correctly refused as a duplicate — which is why that column moved from 73 to 76 as this one moved from 43 to 27. The table adds up: 254 exported and 298 refused is 552, the number of scored files.

*Correction, same day:* this page said "16 pages on 241 is 6.6 % more training material", written from the count of files the measurement had produced. It is **13 pages, 5.4 %** — and the mistake is the thirteenth defect in the table below, *pages counted as files*, committed in a prediction about a report that prints the warning against it. The gain is real and one fifth smaller than announced.

Two things the run showed that the arithmetic did not. **The factors vary inside a single letter**: letter 2326 contributes two pages at ÷2.098 and ÷1.624, letter 2921 two at ÷1.992 and ÷1.584. So the derivatives are not even consistent per holding or per letter, which is a further nail in the reading corrected below. And **seven of the thirteen landed in `unbestimmt`** — pages whose hand no dateline names, because a rescued page is usually a continuation page. The share of unlabelled pages therefore rose from 11.2 % to 13.4 %: the rescue adds material a line model can train on and gives the hand-stratification nothing.

*A reading this project briefly held, and it was wrong.* The most frequent factor, 2.2548 on six pages, looks like 300 against 133 dpi and therefore like a systematic relationship between two derivative pipelines. The full table has seven factors — 1.58, 1.62, 1.99, 2.10, 2.26, 2.63, 3.31 — and no single relationship to name; it is nine archives delivering their own derivatives. The claim was made from the one signature the report had printed, which is the third time in a fortnight that a pattern visible in a handful of cases was written down as a rule. **The sample that shows a pattern is not the sample that establishes it.**

## Twenty defects the measurements found

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
| Keys all missing | "None of the 276 keys name a page under this source" | `--limit 3` cut the corpus to its first three pages *before* the key filter ran, so 276 correct keys matched none of them. The message read as a key-spelling problem and was not one |
| Share "down" | The same request answered 207 from a shell and 401 from a service, seconds apart | A stale password in the service's environment. A value already in `os.environ` wins over every `.env` file, so the corrected file looked innocent and three rounds of diagnosis went to the wrong half of the system |
| Waiting for deleted files | A run read fifteen pages in 140 minutes and looked merely slow | A 404 from the source was routed through the circuit built for outages: five failures in a row, pause 60 s, then 120, then 900, retrying files that had been removed from the share |
| Pages counted as files | The comparison table claimed 298 pages | It counted ground-truth files, one section below its own report's warning that 66 pages are described by 138 files. 226 is the count, and the correction moved one engine's rank |
| Arguing in the transcription field | Three pages carried the model reasoning aloud in English instead of text | No column could show it — not empty, not short, not repetitive. They were visible only because the arguing ran into the token ceiling, and the obvious remedy, a higher ceiling, buys more arguing |
| An empty answer meaning two things | Two written letters disappeared into a column named `empty` | One sentence of a prompt made "this leaf is blank" and "this page I am not writing out" the same answer. An empty answer is a success by every signal the runner has |
| A count without the names | A report said 33 pages were flagged and printed twenty of them | A count is a complaint; only the keys are a task, because the next run reads a list. The cap belonged where the report is rendered, not where the keys are collected |
| The same cap, in a second report | "43 refused on geometry", and five names printed, of which one was a geometry case | The fix above was applied where it had been noticed and nowhere else. One size pair cannot be grouped, so the cause could not be found — and "43 pages missing" invites the one remedy this check exists to prevent, exporting them unchecked |
| Hours-old code answering | A report came back in the previous version's shape from a checkout that was current | A long-lived server process is a cache of its own source. A `git pull` reaches a run started as a subprocess; it does not reach what the server computes in-process, and three deployments were reported as live without it |
| A printed rule read as filler | An archive's insert slip was flagged `repetitive` for a line of 80 underscores | Repetition was measured as the longest run of one character, with no account of **where** the run sits. A run that is a line of its own and under a quarter of the page is a rule; the same run inside a line of text is filler |
| Two verdicts on one page | A published file read `merged_from.verdict: ok` beside `quality.verdict: repetitive` | The merge copies the payload on purpose, so that settings and timings stay facts about the call it came from — and carried a stale judgement along with them. A judgement has to be recomputed where a fact must not be |

A twenty-first is not a defect in this pipeline but shaped the measurements: the share answered 401 to every request on 2 October, the mount was empty, and some 6700 pages sat on local disk in a cache that was not an admissible source. It is one now.

Eight of these are failures of diagnosis rather than of code — a filter applied after a cut, a status code read as a statement about the server rather than about the process asking, a page count that was a file count directly under its own warning, a deployment reported from the fact that a restart was ordered, a fix applied in the one report where it had been noticed. Each was settled by one observation nobody had made: the order of two operations, the length of a password in two processes, the difference between a file and a page, the commit a running process actually holds, the pair of sizes behind a count. Every report of this pipeline now carries that fourth one, as the pair *code loaded* / *code on disk*.

A ninth was entirely mine and not the code's: the number of geometry rejections was carried around for days as **27**, which is the count in a *different column* of the same report — the pages whose hand no dateline names. Two numbers from one printout, one of them misremembered, and nothing in between to check it. The same family as *pages counted as files*, one level up: not a file mistaken for a page, but one column's answer given to another column's question.

And two findings that looked like defects were artefacts of the instrument, which is the same mistake pointing the other way. A count of published files came to 276 of 300 and read as an incomplete push: `git` quotes paths containing non-ASCII, and the Laßberg keys are full of `Zürrich` and `Mülinen`, so those lines end in a quotation mark rather than in `.txt`. And a fetch into a shallow clone reports `(forced update)` for an ordinary fast-forward, because descent beyond the shallow boundary cannot be proven — which reads alarmingly like a rewritten history on a shared branch and is not one. **A count that depends on how a tool displays a thing is not a count of the thing.**

## What is not measured

- **Whether fusion helps.** The comparison now predicts that it does not for these eight, because one candidate dominates weaker ones. It has not been tried, and the prediction rests on measurements made elsewhere.
- **The French letters.** `kraken-fondue_gd_v2` has now read German pages creditably — level with `trocr-kurrent` on the median, better at p90 — and nobody has scored it on the French material it was trained for.
- **The 35 withdrawn pages.** Their transcriptions exist and their images do not. Until the share's custodians answer, they are measurable only if a copy turns up elsewhere.
- **Whether the 625 empty pages are blank.** Nobody has looked at the images. The variance measurement narrows this for a sampled reader and widens it for everything else: a page that answers empty once is not evidence of a blank leaf, and the 625 come from a single pass.
- **Whether the 13 silent pages of the published 300 are blank.** Three readers from three model families return nothing for them, which is the strongest statement a machine can make here, and it is not a look at the leaf. Of the original nineteen, five carry a trace of ink and one carries a letter — see [*A fourth attempt against a second reader*](#a-fourth-attempt-against-a-second-reader).
- **What is on the five pages with a trace of ink.** Both segmenters find something and read it as noise; whether it is foliation, a stamp or show-through is a question for the image.
- **How well the ninth reader reads.** Its 300 pages were sampled from the untranscribed part of the corpus on purpose, so there is nothing to score them against. 252 of 300 are `ok`, which means only "none of the known defects".
- **A median per hand**, for the reason given above.
- **How badly Laßberg's hand actually reads.** The confidence rule cuts the located set off at about 45 % CER, which is inside his range, so his worst pages are absent by construction. Measuring him needs a match test that does not depend on how well the page was read — the Transkribus `pageId` would do it, if the readings carried one.
- **Which doubtful pages are non-matches.** Three populations share that verdict and a CER ratio cannot separate them. The discriminator that can is each page's own length floor: the error rate a reading of its length cannot beat even when it is right. Nothing computes it yet.
- **Whether the 27 unstatused pages were corrected.** The harvest only fetches corrected pages, so they probably were, but the file does not say and the harvester records nothing.
- **Which of two scans of a page is the authoritative one.** For the 27 refused on geometry, two archives hold different photographs of the same leaf — in two cases a scanned opening and a half leaf, a landscape and a portrait. That is a question for the archives, and until it is answered those pages have a transcription and no image that matches it.
- **Whether the rescaled polygons sit on the ink.** Dividing the coordinates by a measured factor makes the XML consistent with its image, and consistency is not correctness: nobody has looked at a line crop from one of those 16 pages to confirm the box lands on the writing. The arithmetic says it must; an eye would say it does.
- **Whether a dataset trained on these 257 pages reads better.** The export tree has never been uploaded. Publishing a dataset is a public act, and the pipeline deliberately stops at the tree and prints the command.

## Reproducing

The runs, the comparison and the scoring are commands in the [`agentic_historian`](https://github.com/thodel/agentic_historian) repository; `docs/BATCH_ATR.md` there is the runbook and names the five steps in the order in which each produces what the next one reads. The ground truth is a Transkribus collection and is not public. The readings are published per page as plain text.

The prompts of the ninth reader are files in that repository under `agentic_historian/prompts/`, each identified by the first eight characters of its sha256 digest — `lassberg_atr @092fb6b0`, `lassberg_atr_strict @03c5a660`, `lassberg_atr_strict2 @9e0503e8` — and every page of every run records the digest that produced it, beside the thinking level and the token ceiling. A prompt is a parameter of the measurement, so a measurement that does not name it is not reproducible. Re-reading the same pages needs a **new run name**: output is the only state this runner keeps, so a page already on disk is skipped, and the second attempt of a page is a second run compared against the first.

Scoring 552 ground-truth files against eight readings takes about 32 minutes of one CPU, most of it spent matching each page against the 6719-page corpus reading.

The figures for the two older runs come from reports rebuilt from the files on disk rather than observed as those runs happened — which is why the *failed* column is not quoted for them: a page that failed wrote nothing, and nothing is what a rebuilt report cannot count. The candidate run's report was written at the end of the run, so its zero failures are a measurement.
