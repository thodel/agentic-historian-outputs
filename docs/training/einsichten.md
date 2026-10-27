---
layout: default
title: "Training: Einsichten und Probleme im Ablauf"
---

# Einsichten und Probleme im Ablauf

*Unterseite von [Training](./). Stand: 27. Oktober 2026.*

Die [Übersicht](./) sagt, wie die Systeme abschneiden. Diese Seite sammelt das
Kleinere: Was beim Trainieren und Messen schiefging, welche Annahme sich als
falsch erwies und was daraus als Regel geblieben ist. Jeder Punkt ist kurz
gehalten. Der Beleg mit allen Zahlen steht im verlinkten Forschungstext
(englisch) oder im Trainings-Repository.

## Messen

**Die eigene Validierung schmeichelt.** Ein Validierungssatz, der nach Seiten
gezogen ist, enthält dieselben Hände wie das Training.

- Die mittelalterlichen Seitenmodelle verloren auf zurückgehaltenen
  Dokumenten rund zehn Punkte.
- Das Kraken-Modell des 19. Jahrhunderts las den eigenen Satz mit 3,12 % und
  den fremden Testsatz mit 11,18 %.
- Frühe Modelle meldeten auf dem eigenen Satz um 1 % und lagen auf dem
  Benchmark bei 25 bis 36 %.

Seither gilt nur ein Satz, dessen Dokumente nie im Training waren.
→ [Fine-tuning vision models, §8a](../vlm-finetuning.html#8a-the-held-out-boundary-and-a-ladder-that-finally-holds)

**Dieselbe Stichprobe reicht nicht, derselbe Korpusstand gehört dazu.** Zwei
Zahlen sind nur vergleichbar, wenn beides stimmt:

- dieselbe Stichprobe: Eine andere Stichprobe allein verschob eine CER um 0,6
  bis 4,7 Punkte;
- derselbe Stand der Trainingsdaten.

Der mittelalterliche Korpus vom September enthielt 3 173 Seiten, die vier Tage
später für die Messung reserviert wurden. Die Modelle darauf sind 1,6 bis 2,7
Punkte zu optimistisch. Ein Zensus über 58 Läufe fand sechs, die diese
Grenze überschreiten.
→ [§8a](../vlm-finetuning.html#8a-the-held-out-boundary-and-a-ladder-that-finally-holds),
[HELDOUT_BOUNDARY.md](https://github.com/thodel/training-atr-models/blob/main/docs/HELDOUT_BOUNDARY.md)

**Wer nicht aufhört zu schreiben, wird anders bestraft als wer falsch liest.**

- Seitenmodelle laufen auf manchen Seiten bis an die Grenze der Ausgabelänge:
  Der XVI–XIX-Qwen-Arm tut es auf 99 von 695 Seiten.
- Die volle CER mischt beides. `truncated_cer` kürzt jede Lesung auf die Länge
  der Vorlage und zeigt das Lesen allein. Beide Zahlen gehören nebeneinander.
- Eine Seite, die an der Grenze endet, sieht aus wie ein gewöhnlicher Erfolg.
  Man muss das Ende einer Lesung lesen.

**Ein Modell liest die Einheit, auf der es trainiert wurde.** Ein
Zeilenmodell, dem man eine Seite zeigt, hört nach 3 % des Textes auf. Ein
Seitenmodell, dem man eine Zeile zeigt, schreibt weiter Text, der nicht
dasteht. → [§4](../vlm-finetuning.html#4-a-model-reads-the-unit-it-was-trained-on)

**Zählweisen vertauschen sich leicht.**

- Das Trainings-Repository zählt Einfügungen und Auslassungen nach der
  Konvention von Kraken; die [Engine-Evaluation](../evaluation.html) nach der
  umgekehrten von CERberus. Mehrmals wurde eine Zahl deshalb verkehrt herum
  gelesen.
- `benchmark_samples` trug Zeichen statt Zeilen: 116 143 statt 2 749. Auf
  einer Modellkarte wäre daraus eine vierzigfach zu hohe Probenzahl geworden.

→ [§7](../vlm-finetuning.html#7-the-families-on-a-set-someone-else-can-check),
[training-atr-models#164](https://github.com/thodel/training-atr-models/issues/164)

## Trainieren

**Was beim Training gerendert wird, muss bei der Messung gleich aussehen.**

- Gemma-4-12B wurde bei der Messung aufgefordert, in einem leeren
  „Denk“-Kanal fortzufahren, den es im Training nie gesehen hatte. Ergebnis:
  22,94 % CER.
- Mit dem Render aus dem Training: 9,95 %.
- Fast fünf GPU-Tage wären beinahe in die falsche Vermutung geflossen, der Lauf
  sei durch Unterbrechungen beschädigt.

→ [§7](../vlm-finetuning.html#7-the-families-on-a-set-someone-else-can-check)

**Ein Feld im Auftrag wirkt nicht immer.** `ketos train` ignoriert die
Architekturangabe `--spec`, sobald ein Basismodell geladen wird. Vier
Kraken-Läufe wurden deshalb einer Architektur zugeschrieben, die sie nie
hatten. Gemessen wird an den Gewichten, nicht am Auftrag.
→ [training-atr-models#164](https://github.com/thodel/training-atr-models/issues/164)

**Bei Kraken entscheidet die Eingabehöhe.** Auf dichter Schrift braucht CTC
genug Bildspalten je Zeichen. Höhe 120 schlug Höhe 64 im einzigen
kontrollierten Vergleich: 13,4 % gegen 16,6 % CER, auf flämischem Material.
→ [EVAL_SETS.md](https://github.com/thodel/training-atr-models/blob/main/docs/EVAL_SETS.md)

**Abbruch erkennen statt Rechenzeit verbrennen.**

- Ein Kraken-Lauf von Grund auf lernte in 2 778 Schritten nichts und gab leere
  Zeilen aus. Die alte Untergrenze liess ihn trotzdem durch.
- Inzwischen bricht ein Lauf ab, der mehrere Epochen lang nichts lernt.

→ [training-atr-models#131](https://github.com/thodel/training-atr-models/issues/131)

**Gemma lief in 4 Bit, Qwen in bf16.** Was 4 Bit auf diesem Material kostet,
ist ungemessen. Der Abstand zwischen den Familien ist darum eine Obergrenze.

**TrOCR hat ein Backend und keinen echten Lauf.** Zwei Probeläufe (95,9 % und
97,6 % CER) prüften nur, ob die Pipeline durchläuft.
→ [training-atr-models#37](https://github.com/thodel/training-atr-models/issues/37)

## Daten

**Datensätze lesen statt erben.** `zh-regierungsratsprotokolle` hat zwei
Eigenheiten:

- Der Datensatz ist zu 38 % untranskribiert. Er liefert rund 31 statt 50
  Zeilen je Seite.
- Neben den Bänden lagen Testsätze aus demselben Archiv und derselben Zeit wie
  der Benchmark, einer davon mit „unbrauchbar“ beschriftet.

Eine Auswahl „alle Projekte“ hätte beides ins Training genommen.
→ [training-atr-models#164](https://github.com/thodel/training-atr-models/issues/164)

**Überbreite Zeilen.** Kraken polstert das ausgeschnittene Zeilenbild. Auf dem
mittelalterlichen Korpus wurde daraus ein Seitenverhältnis von 177:1, wo der
Zeilenkasten 60:1 sagte. Inzwischen schneidet das Training solche Zeilen vor
dem Lauf weg und schreibt auf, wie viele es waren.
→ [training-atr-models#145](https://github.com/thodel/training-atr-models/issues/145)

**Ein Cache, der zu viel teilt.** Beim Seitenmodell zur Berner Disputation
hatten drei von vier Läufen wegen einer Kollision im Cache dieselbe
Handschrift ein zweites Mal gelesen. Die erste Fassung der Auswertung war
deshalb falsch.
→ [Berner Disputation](../disputation-page-model/)

## Infrastruktur

**Ein Korpus zu bauen kostet mehr als das Training vorzubereiten scheint.**
2 bis 16 CPU-Stunden, meist Dateien kopieren. Inzwischen ist der kompilierte
Korpus inhaltsadressiert: Ein zweites Basismodell trainiert auf denselben
Bytes und derselben Aufteilung, ohne neu vorzubereiten.
→ [Fine-tuning vision models, „The runs“](../vlm-finetuning.html#the-runs)

**Was auf dem Scratch liegt, verschwindet.** UBELIX löscht Scratch-Dateien
nach 30 Tagen. Eine Ziehung aus einem Trainingskorpus muss vorher laufen, sonst
muss der Korpus neu gebaut werden. Der eigene Kurrent-Testsatz muss deshalb
bis Mitte November gezogen sein.

**Freigabe ohne Prüfung.**

- Das Kraken-Modell des 19. Jahrhunderts fiel durch die Freigabeprüfung, weil
  der Erkennungsdienst gerade gestoppt war (502), nicht wegen des Modells.
- Es wurde von Hand freigeschaltet. Bis der Dienst wieder lief, hätte jede
  Anfrage einen Fehler geliefert.

→ [training-atr-models#164](https://github.com/thodel/training-atr-models/issues/164)

**Welcher Container eine Zahl erzeugt hat**, ist erst seit dem 10. Oktober
nachvollziehbar.
→ [§8](../vlm-finetuning.html#which-container-produced-a-number-became-knowable-on-2026-10-10)

**Ein Lauf, der über eine Zeitgrenze hinaus muss, braucht Wiederaufnahme.**

- Auf UBELIX wird ein Lauf nach Ablauf der Zeit beendet oder verdrängt.
- Inzwischen setzt Kraken dort vom letzten Checkpoint fort (`--resume`).
- Der Trainer beendet beim Abbruch auch den Kindprozess, statt ihn als Waise
  weiterlaufen zu lassen.

→ [training-atr-models#171](https://github.com/thodel/training-atr-models/issues/171)
