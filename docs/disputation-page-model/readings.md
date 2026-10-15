---
layout: default
title: "The forty pages, as both models read them"
---

> **Research data, in English.** The readings behind [A page model on the Berner Disputation](./). Machine output, published unedited — neither reading is an edition, and neither has been corrected by hand.

# The forty pages, as both models read them

Ten pages from each of four Staatsarchiv Bern copies of the Berner Disputation of 1528, read twice: once by [`qwen3.5-4b-german-kurrent-xvi-xix-page-v1`](https://huggingface.co/dh-unibe/qwen3.5-4b-german-kurrent-xvi-xix-page-v1), which was trained on whole pages, and once by [`qwen3vl-medieval-german-v3`](https://huggingface.co/dh-unibe/qwen3vl-medieval-german-v3), which reads one segmented line at a time and had already read all 3,666 pages of these manuscripts in September and October 2026.

Everything is here as plain text, one file per page per model, plus [`readings.json`](readings/readings.json) with the same content and its metadata in one machine-readable file.

## How to read these files

- **Neither column is a transcription of record.** Both are machine readings of a hand neither model was trained on.
- **`sha256`** is the digest of the scan each reading was made from, recorded at read time and verified against the image in its own manuscript directory before publication. That check exists because its absence let three runs read the wrong manuscript on 14 October — see the [correction](./#correction-15-october-2026--three-of-the-four-runs-read-the-wrong-manuscript).
- **`cut off`** means the reading stopped at the model's token ceiling; **`looped`** means it repeated itself until it did. Both still carry text, and both are marked rather than removed.
- **Similarity** is against the edition's existing transcription where one exists. That transcription is *itself machine output*, so the figure says how far two machines agree, not how right either is.
- **Facsimile** links open the page in the [Reformation edition](https://thodel.github.io/reformation/) viewer.

## A V 1445 — Schöni

Runs `schoeni_page_v1` (page model) and `schoeni_medieval_v3` (line model).

| Page | Facsimile | Page model | Line model | Edition transcription | sim. page | sim. line |
|---:|---|---|---|---:|---:|---:|
| 29 | [S. 29](https://thodel.github.io/reformation/#/disputation/a-v-1445/29) | [869 chars](readings/a_v_1445_schoeni/page_29.page.txt) | [1333 chars](readings/a_v_1445_schoeni/page_29.line.txt) | 945 | 0.41 | 0.47 |
| 114 | [S. 114](https://thodel.github.io/reformation/#/disputation/a-v-1445/114) | [839 chars](readings/a_v_1445_schoeni/page_114.page.txt) | [782 chars](readings/a_v_1445_schoeni/page_114.line.txt) | — | — | — |
| 194 | [S. 194](https://thodel.github.io/reformation/#/disputation/a-v-1445/194) | [824 chars](readings/a_v_1445_schoeni/page_194.page.txt) | [777 chars](readings/a_v_1445_schoeni/page_194.line.txt) | — | — | — |
| 195 | [S. 195](https://thodel.github.io/reformation/#/disputation/a-v-1445/195) | [5490 chars](readings/a_v_1445_schoeni/page_195.page.txt) **(cut off)** | [763 chars](readings/a_v_1445_schoeni/page_195.line.txt) | — | — | — |
| 406 | [S. 406](https://thodel.github.io/reformation/#/disputation/a-v-1445/406) | [756 chars](readings/a_v_1445_schoeni/page_406.page.txt) | [876 chars](readings/a_v_1445_schoeni/page_406.line.txt) | — | — | — |
| 631 | [S. 631](https://thodel.github.io/reformation/#/disputation/a-v-1445/631) | [7739 chars](readings/a_v_1445_schoeni/page_631.page.txt) **(looped, cut off)** | [923 chars](readings/a_v_1445_schoeni/page_631.line.txt) | — | — | — |
| 690 | [S. 690](https://thodel.github.io/reformation/#/disputation/a-v-1445/690) | [760 chars](readings/a_v_1445_schoeni/page_690.page.txt) | [821 chars](readings/a_v_1445_schoeni/page_690.line.txt) | — | — | — |
| 746 | [S. 746](https://thodel.github.io/reformation/#/disputation/a-v-1445/746) | [869 chars](readings/a_v_1445_schoeni/page_746.page.txt) | [1431 chars](readings/a_v_1445_schoeni/page_746.line.txt) | — | — | — |
| 762 | [S. 762](https://thodel.github.io/reformation/#/disputation/a-v-1445/762) | [1091 chars](readings/a_v_1445_schoeni/page_762.page.txt) | [1079 chars](readings/a_v_1445_schoeni/page_762.line.txt) | — | — | — |
| 775 | [S. 775](https://thodel.github.io/reformation/#/disputation/a-v-1445/775) | [845 chars](readings/a_v_1445_schoeni/page_775.page.txt) | [844 chars](readings/a_v_1445_schoeni/page_775.line.txt) | — | — | — |

## A V 1444 — Cyro

Runs `cyro_page_v1` (page model) and `cyro_medieval_v3` (line model).

| Page | Facsimile | Page model | Line model |
|---:|---|---|---|
| 29 | [S. 29](https://thodel.github.io/reformation/#/disputation/a-v-1444/29) | [898 chars](readings/a_v_1444_cyro/page_29.page.txt) | [929 chars](readings/a_v_1444_cyro/page_29.line.txt) |
| 114 | [S. 114](https://thodel.github.io/reformation/#/disputation/a-v-1444/114) | [3 chars](readings/a_v_1444_cyro/page_114.page.txt) | [4 chars](readings/a_v_1444_cyro/page_114.line.txt) |
| 194 | [S. 194](https://thodel.github.io/reformation/#/disputation/a-v-1444/194) | [873 chars](readings/a_v_1444_cyro/page_194.page.txt) | [923 chars](readings/a_v_1444_cyro/page_194.line.txt) |
| 195 | [S. 195](https://thodel.github.io/reformation/#/disputation/a-v-1444/195) | [905 chars](readings/a_v_1444_cyro/page_195.page.txt) | [922 chars](readings/a_v_1444_cyro/page_195.line.txt) |
| 406 | [S. 406](https://thodel.github.io/reformation/#/disputation/a-v-1444/406) | [878 chars](readings/a_v_1444_cyro/page_406.page.txt) | [953 chars](readings/a_v_1444_cyro/page_406.line.txt) |
| 631 | [S. 631](https://thodel.github.io/reformation/#/disputation/a-v-1444/631) | [763 chars](readings/a_v_1444_cyro/page_631.page.txt) | [764 chars](readings/a_v_1444_cyro/page_631.line.txt) |
| 690 | [S. 690](https://thodel.github.io/reformation/#/disputation/a-v-1444/690) | [651 chars](readings/a_v_1444_cyro/page_690.page.txt) | [668 chars](readings/a_v_1444_cyro/page_690.line.txt) |
| 746 | [S. 746](https://thodel.github.io/reformation/#/disputation/a-v-1444/746) | [985 chars](readings/a_v_1444_cyro/page_746.page.txt) | [1008 chars](readings/a_v_1444_cyro/page_746.line.txt) |
| 762 | [S. 762](https://thodel.github.io/reformation/#/disputation/a-v-1444/762) | [11550 chars](readings/a_v_1444_cyro/page_762.page.txt) **(looped, cut off)** | [978 chars](readings/a_v_1444_cyro/page_762.line.txt) |
| 775 | [S. 775](https://thodel.github.io/reformation/#/disputation/a-v-1444/775) | [2 chars](readings/a_v_1444_cyro/page_775.page.txt) | [1 chars](readings/a_v_1444_cyro/page_775.line.txt) |

## A V 1446 — Rümlang

Runs `ruemlang_page_v1` (page model) and `ruemlang_medieval_v3` (line model).

| Page | Facsimile | Page model | Line model | Edition transcription | sim. page | sim. line |
|---:|---|---|---|---:|---:|---:|
| 29 | [S. 29](https://thodel.github.io/reformation/#/disputation/a-v-1446/29) | [956 chars](readings/a_v_1446_ruemlang/page_29.page.txt) | [1549 chars](readings/a_v_1446_ruemlang/page_29.line.txt) | 1109 | 0.68 | 0.63 |
| 114 | [S. 114](https://thodel.github.io/reformation/#/disputation/a-v-1446/114) | [1219 chars](readings/a_v_1446_ruemlang/page_114.page.txt) | [1224 chars](readings/a_v_1446_ruemlang/page_114.line.txt) | — | — | — |
| 194 | [S. 194](https://thodel.github.io/reformation/#/disputation/a-v-1446/194) | [1374 chars](readings/a_v_1446_ruemlang/page_194.page.txt) | [1932 chars](readings/a_v_1446_ruemlang/page_194.line.txt) | — | — | — |
| 195 | [S. 195](https://thodel.github.io/reformation/#/disputation/a-v-1446/195) | [1135 chars](readings/a_v_1446_ruemlang/page_195.page.txt) | [1228 chars](readings/a_v_1446_ruemlang/page_195.line.txt) | — | — | — |
| 219 | [S. 219](https://thodel.github.io/reformation/#/disputation/a-v-1446/219) | [1271 chars](readings/a_v_1446_ruemlang/page_219.page.txt) | [1283 chars](readings/a_v_1446_ruemlang/page_219.line.txt) | — | — | — |
| 246 | [S. 246](https://thodel.github.io/reformation/#/disputation/a-v-1446/246) | [1317 chars](readings/a_v_1446_ruemlang/page_246.page.txt) | [1292 chars](readings/a_v_1446_ruemlang/page_246.line.txt) | — | — | — |
| 370 | [S. 370](https://thodel.github.io/reformation/#/disputation/a-v-1446/370) | [6436 chars](readings/a_v_1446_ruemlang/page_370.page.txt) **(looped, cut off)** | [1387 chars](readings/a_v_1446_ruemlang/page_370.line.txt) | — | — | — |
| 406 | [S. 406](https://thodel.github.io/reformation/#/disputation/a-v-1446/406) | [1404 chars](readings/a_v_1446_ruemlang/page_406.page.txt) | [1411 chars](readings/a_v_1446_ruemlang/page_406.line.txt) | — | — | — |
| 471 | [S. 471](https://thodel.github.io/reformation/#/disputation/a-v-1446/471) | [393 chars](readings/a_v_1446_ruemlang/page_471.page.txt) | [402 chars](readings/a_v_1446_ruemlang/page_471.line.txt) | — | — | — |
| 511 | [S. 511](https://thodel.github.io/reformation/#/disputation/a-v-1446/511) | [884 chars](readings/a_v_1446_ruemlang/page_511.page.txt) | [870 chars](readings/a_v_1446_ruemlang/page_511.line.txt) | — | — | — |

## A V 1447 — Schlussredaktion

Runs `schlussredaktion_page_v1` (page model) and `schlussredaktion_medieval_v3` (line model).

| Page | Facsimile | Page model | Line model | Edition transcription | sim. page | sim. line |
|---:|---|---|---|---:|---:|---:|
| 29 | [S. 29](https://thodel.github.io/reformation/#/disputation/a-v-1447/29) | [935 chars](readings/a_v_1447_schlussredaktion/page_29.page.txt) | [952 chars](readings/a_v_1447_schlussredaktion/page_29.line.txt) | 1000 | 0.75 | 0.85 |
| 82 | [S. 82](https://thodel.github.io/reformation/#/disputation/a-v-1447/82) | [946 chars](readings/a_v_1447_schlussredaktion/page_82.page.txt) | [1071 chars](readings/a_v_1447_schlussredaktion/page_82.line.txt) | 1127 | 0.71 | 0.80 |
| 95 | [S. 95](https://thodel.github.io/reformation/#/disputation/a-v-1447/95) | [997 chars](readings/a_v_1447_schlussredaktion/page_95.page.txt) | [995 chars](readings/a_v_1447_schlussredaktion/page_95.line.txt) | 1068 | 0.78 | 0.86 |
| 114 | [S. 114](https://thodel.github.io/reformation/#/disputation/a-v-1447/114) | [1145 chars](readings/a_v_1447_schlussredaktion/page_114.page.txt) | [1115 chars](readings/a_v_1447_schlussredaktion/page_114.line.txt) | 1191 | 0.80 | 0.88 |
| 194 | [S. 194](https://thodel.github.io/reformation/#/disputation/a-v-1447/194) | [977 chars](readings/a_v_1447_schlussredaktion/page_194.page.txt) | [987 chars](readings/a_v_1447_schlussredaktion/page_194.line.txt) | 981 | 0.69 | 0.84 |
| 195 | [S. 195](https://thodel.github.io/reformation/#/disputation/a-v-1447/195) | [866 chars](readings/a_v_1447_schlussredaktion/page_195.page.txt) | [876 chars](readings/a_v_1447_schlussredaktion/page_195.line.txt) | 869 | 0.76 | 0.85 |
| 406 | [S. 406](https://thodel.github.io/reformation/#/disputation/a-v-1447/406) | [1331 chars](readings/a_v_1447_schlussredaktion/page_406.page.txt) | [1398 chars](readings/a_v_1447_schlussredaktion/page_406.line.txt) | 1441 | 0.75 | 0.80 |
| 631 | [S. 631](https://thodel.github.io/reformation/#/disputation/a-v-1447/631) | [1345 chars](readings/a_v_1447_schlussredaktion/page_631.page.txt) | [1346 chars](readings/a_v_1447_schlussredaktion/page_631.line.txt) | 1350 | 0.80 | 0.86 |
| 690 | [S. 690](https://thodel.github.io/reformation/#/disputation/a-v-1447/690) | [1136 chars](readings/a_v_1447_schlussredaktion/page_690.page.txt) | [1183 chars](readings/a_v_1447_schlussredaktion/page_690.line.txt) | 1154 | 0.81 | 0.83 |
| 746 | [S. 746](https://thodel.github.io/reformation/#/disputation/a-v-1447/746) | [1401 chars](readings/a_v_1447_schlussredaktion/page_746.page.txt) | [1407 chars](readings/a_v_1447_schlussredaktion/page_746.line.txt) | 1387 | 0.84 | 0.87 |

## Provenance

Page model `dh-unibe/qwen3.5-4b-german-kurrent-xvi-xix-page-v1`, line model `dh-unibe/qwen3vl-medieval-german-v3`, both served by the ATR gateway on idhefix. The page-model runs were made on 15 October 2026 with one working-copy cache per manuscript; the line-model runs are the corpus runs of 29 September and 1 October 2026. Every one of the 40 source digests was checked against its own manuscript directory before these files were written.

