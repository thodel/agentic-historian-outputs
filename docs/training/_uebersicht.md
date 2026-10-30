*Stand: 30. Oktober 2026.* Diese Seite vergleicht die drei Systemfamilien, die
das Projekt selbst trainiert hat, **auf denselben Daten**:

- **Kraken**: ein kleiner CTC-Zeilenerkenner;
- **TrOCR**: ein Transformer-Zeilenerkenner;
- **feinjustierte Bild-Sprach-Modelle** (VLM): eine QLoRA-Schicht über einem
  eingefrorenen Basismodell, für Zeilen oder ganze Seiten.

Alle Zahlen sind Zeichenfehlerraten (CER); tiefer ist besser.
**Vergleichbar sind nur Zahlen derselben Tabelle.** Jede Tabelle beruht auf
einem einzigen Testsatz. Schon eine andere Stichprobe aus demselben Korpus
verschob eine CER um 0,6 bis 4,7 Punkte.

Wie die Messungen zustande kamen und wo sie in die Irre führten, steht auf der
Unterseite [Einsichten und Probleme im Ablauf](einsichten.html). Die
ausführlichen Belege stehen in den Forschungstexten
[Fine-tuning vision models](../vlm-finetuning.html) und
[Recognition engine evaluation](../evaluation.html), beide englisch.

## Auf einen Blick

- **Nur im 19. Jahrhundert gibt es einen Testsatz, auf dem Kraken und VLMs
  gemessen sind.** Das beste VLM liest ihn mit **6,80 %**, Kraken mit
  **11,18 %**. Kraken macht also rund 1,6-mal so viele Fehler. Dafür ist es
  etwa tausendmal kleiner: 4,1 Millionen Parameter und 16 MB Gewichte.
- **TrOCR ist bisher nicht wirklich trainiert worden.** Es gab zwei
  Probeläufe. Sie haben nur geprüft, ob das Trainings-Backend läuft. Ein
  eigenes TrOCR-Ergebnis auf gemeinsamen Daten gibt es deshalb nicht.
- **Im Mittelalter ist erst eine Seite der Frage gemessen.** Es gibt einen
  Testsatz, der nach Dokumenten zurückgehalten ist (695 Seiten). Auf ihm
  sind bisher nur Seitenmodelle gemessen; das beste liest mit **36,7 %**.
  Für Kraken und für Zeilenmodelle fehlt die Messung auf diesem Satz.
- **Zeilen vor Seiten.** Dasselbe Basismodell liest dieselben 164
  mittelalterlichen Seiten Zeile für Zeile mit **13,65 %**. Als ganze Seite
  liest es sie mit 37,61 %.
- **Laßberg-Briefe: Kraken wird durch Nachtrainieren auf dem Material
  deutlich besser.** Auf zurückgehaltenen Objekten der BLB liest das auf den
  BLB-Zeilen nachtrainierte Kraken Laßbergs eigene Hand auf ganzen Seiten
  mit **5,3 %** statt 14,5 % und die Manuskripte mit 10,1 % statt 20,6 %. Bei
  den Korrespondenten bringt es nichts (23,0 % wie vorher). Die beiden
  Seiten-VLMs auf demselben Datensatz sind dort noch nicht gemessen.
- **Die eigene Validierung schmeichelt.**
  - Kraken: 3,12 % auf dem eigenen Validierungssatz, 11,18 % auf dem fremden
    Testsatz.
  - Das beste mittelalterliche Seitenmodell: 26,6 % auf dem eigenen
    Validierungssatz, 36,7 % auf zurückgehaltenen Dokumenten.

  Zählen dürfen nur Testsätze, deren Dokumente das Modell nie gesehen hat.

## 1. 19. Jahrhundert: Protokolle des Bundesrats

Testsatz sind **2 751 Zeilen** aus den Protokollen des Schweizerischen
Bundesrats (1848–1903). Der Satz ist veröffentlicht
([doi:10.5281/zenodo.4746342](https://doi.org/10.5281/zenodo.4746342)), und
kein Lauf des Projekts hat auf ihm trainiert.

Alle Modelle der Tabelle wurden auf denselben Korpora des 19. Jahrhunderts
trainiert:

- Regierungsratsprotokolle Zürich;
- Protokolle der Bundesversammlung und der Parlamentsdienste;
- Kurrent des 19. Jahrhunderts.

Kraken lief mit einer etwas anderen Auswahl: Es hielt ganze Bände zurück
statt einzelner Seiten. Gemessen wurde Zeile für Zeile; alle VLMs erhielten
dieselbe Anweisung und dasselbe Pixelbudget.

| System | Familie | Grösse | CER | WER |
|---|---|---:|---:|---:|
| `Qwen3.5-4B` | VLM | 4,66 Mrd. | **6,80 %** | 23,4 % |
| `Qwen3-VL-4B` | VLM | 4,44 Mrd. | 7,65 % | 24,6 % |
| `Qwen3.5-2B` | VLM | 2,27 Mrd. | 8,95 % | 26,2 % |
| `Gemma-4-12B` ¹ | VLM | 11,96 Mrd. | 9,95 % | 24,2 % |
| `Gemma-4-E4B` ¹ | VLM | ≈ 4,5 Mrd. | 10,24 % | 28,7 % |
| `Qwen3.5-0.8B` | VLM | 0,87 Mrd. | 11,15 % | 30,7 % |
| `kraken-german-xix-v1` ² | Kraken | 4,1 Mio. | 11,18 % | 39,6 % |
| TrOCR | — | — | *nicht trainiert* | |

¹ Gemma wurde in 4 Bit trainiert und gemessen, die Qwen-Modelle in bf16. Der
Abstand zu Qwen ist deshalb eine Obergrenze, kein sauberer Vergleich.
² Feinjustiert von `kraken-bohemian_19th`. Auf dem eigenen Validierungssatz
lag es bei 3,12 %; der Abstand zum Testsatz ist ein Problem ungesehener Hände,
kein Konvergenzproblem.

**Zum Einordnen: Modelle von anderswo, auf einer Teilmenge derselben
Protokolle (150 Zeilen).** Diese Modelle hat das Projekt nicht trainiert; sie
lasen ohne Anpassung. Wegen der kleineren Stichprobe ist das **nicht** dieselbe
Messung wie oben.

| System | Familie | CER |
|---|---|---:|
| German Kurrent M2 (Transkribus HTR+, 2021) | HTR+ | 3,79 % |
| `trocr-kurrent-XIX` | TrOCR | 13,90 % |
| `kraken-bohemian_19th_v2` (die Basis von `kraken-german-xix-v1`) | Kraken | 53,87 % |
| `qwen3-vl-30b`, ohne Anpassung | VLM | 78,98 % |

Bemerkenswert sind zwei Dinge:

- Ein fertiges TrOCR-Modell von anderswo liest diese Protokolle ohne jedes
  Feintraining besser als das eigene Kraken-Modell nach Feintraining.
- Ein grosses VLM ohne Anpassung ist der schlechteste Leser im Feld.

## 2. Mittelalter (1300–1600): zurückgehaltene Dokumente

Testsatz ist `german-medieval-v1/test`: **695 Seiten aus 200 Dokumenten**.
Diese Dokumente wurden aus jedem Training herausgenommen. Für jedes Modell ist
geprüft, dass keines dieser Dokumente in seinen Trainingsdaten steht. Gelesen
wurden ganze Seiten.

| System | Familie | trainiert auf | CER eigene Validierung | **CER zurückgehalten** | gekürzt ³ |
|---|---|---|---:|---:|---:|
| `olmOCR-2-7B`, 4 MP, eigener Prompt | VLM (Seite) | Mittelalter | 26,59 % | **36,74 %** | 34,75 % |
| dasselbe mit kleinerer Adapterschicht (r16) | VLM (Seite) | Mittelalter | 32,14 % | 41,86 % | 37,80 % |
| `olmOCR-2-7B`, 4 MP, eigener Prompt | VLM (Seite) | Kurrent XVI–XIX | 15,71 % | 36,81 % | 33,54 % |
| `Qwen3.5-4B` | VLM (Seite) | Kurrent XVI–XIX | 27,04 % | 54,05 % | 41,68 % |

³ `truncated_cer`: Jede Lesung wird auf die Länge ihrer Vorlage gekürzt. Die
Kennzahl misst das Lesen ohne den Text, den ein Modell über das Ende der
Seite hinaus schreibt.

Drei Lesarten:

- **Bei den mittelalterlichen Modellen war die Validierung nach Seiten um rund
  zehn Punkte zu optimistisch.** Unbekannte Hände sind schwerer als die
  Seiten neben den Trainingsseiten. Bei den Kurrent-Modellen ist der Abstand
  kein solches Mass, weil dieser Satz am frühen Rand ihres Korpus liegt.
- **Das Kurrent-Modell liest diese frühen Seiten so gut wie das
  mittelalterliche** (36,81 % gegen 36,74 %). Nur vier seiner zwanzig
  Datensätze reichen ins 16. Jahrhundert zurück.
- **`Qwen3.5-4B` hört auf 99 von 695 Seiten nicht auf zu schreiben**, bis
  zur Grenze der Ausgabelänge. Rund 12 Punkte seiner CER sind Text über das
  Ende der Seite hinaus. Gekürzt liegt es 8 statt 17 Punkte hinter olmOCR.

**Was fehlt:** Kraken, TrOCR und die Zeilenmodelle sind auf diesem Satz
nicht gemessen.

## 3. Zeilen gegen Seiten: dieselben 164 mittelalterlichen Seiten

Hier wurde ein Basismodell auf beiden Einheiten trainiert und auf denselben
Seiten gemessen. Für die Zeilenmodelle wurden deren Zeilen in Lesereihenfolge
wieder zu Seiten zusammengesetzt. Die Seiten stammen aus dem
Validierungssatz und sind keine nach Dokument zurückgehaltenen Seiten.

| System | liest | CER |
|---|---|---:|
| `Qwen3.5-4B`, bf16 | Zeilen | **13,65 %** |
| `Qwen3.5-4B`, 4 Bit | Zeilen | 14,02 % |
| `olmOCR-2-7B`, 4 MP, eigener Prompt | Seiten | 26,59 % |
| `Qwen3.5-4B`, bf16 | Seiten | 37,61 % |

Das Zeilenmodell ist auf 131 von 164 Seiten besser. Lässt man die 18 Seiten
weg, auf denen das Seitenmodell zu viel oder zu wenig schreibt, bleibt es auf
114 von 146 Seiten besser.

Die Zeilenzahl ist allerdings eine Obergrenze für eine Zeilen-Pipeline. Die
Modelle lasen die bereits zerlegten Zeilen der Ground Truth; Fehler bei der
Zeilenerkennung sind darin nicht enthalten.

**Grösse bei Zeilen.** Auf einer gemeinsamen Stichprobe, alle Modelle aus
derselben Familie und in 4 Bit:

| Modell | CER |
|---|---:|
| `Qwen3.5-4B` | 15,94 % |
| `Qwen3.5-9B` | 13,75 % |
| `Qwen3.5-27B` | 12,24 % |
| `Qwen3.8-27B` | 12,15 % |

Mehr Parameter helfen, aber mit abnehmendem Ertrag. Diese Stichprobe ist
nicht dieselbe wie die 164 Seiten oben.

## 4. 19. Jahrhundert: Laßberg-Briefe, zurückgehaltene Objekte (BLB)

Testsatz ist die Eval-Seite von `image-text_lassberg-blb-gt`: Seiten aus
**40 Objekten**, die als ganze Objekte aus dem Training herausgenommen
wurden. Die Transkription stammt von der Badischen Landesbibliothek. Gelesen
wurden **ganze Seiten** über das Gateway. Die Zeilen findet dabei das
Gateway selbst, Fehler der Segmentierung zählen also mit. Jede Seite ist
unter ihrem eigenen Namen bewertet, auch wenn sie schlecht gelesen wurde.

Auf diesem Datensatz sind drei Modelle trainiert:

- `kraken-german-xix-blb-v1`: `kraken-german-xix-v1` aus Abschnitt 1,
  nachtrainiert nur auf den BLB-Zeilen (38 360 Zeilen, 136 Epochen).
- `Qwen3.5-4B` auf Seiten, mit den zwanzig Kurrent-Datensätzen und diesem.
- `olmOCR-2-7B` auf Seiten, ebenso. Es trainiert noch.

Gemessen ist bisher nur Kraken, neu gegen alt im selben Lauf:

| Eval-Projekt | Seiten | `kraken-german-xix-blb-v1` Median / gewichtet ⁴ | `kraken-german-xix-v1` Median / gewichtet |
|---|---:|---:|---:|
| Laßbergs eigene Hand | 23 | **5,3 % / 7,1 %** | 14,5 % / 15,9 % |
| Korrespondenten | 22 | 23,0 % / 25,6 % | 23,0 % / 28,1 % |
| Hand nicht bestimmt | 7 | 9,1 % / 11,0 % | 22,3 % / 22,0 % |
| Manuskripte | 105 | **10,1 % / 12,1 %** | 20,6 % / 21,9 % |

⁴ *Gewichtet* heisst: Fehler über alle Zeichen der Vorlage. Der Median sagt,
wie eine typische Seite gelesen wird; der gewichtete Wert, wie viel des
Textes falsch herauskommt.

Drei Lesarten:

- **Auf Laßbergs Hand sinkt der Fehler auf ein Drittel.** 19 von 23 Seiten
  liegen unter 8 %. Auf den Manuskripten halbiert er sich. Trainiert wurde
  dabei auf Zeilen, deren Grundlinie nicht gemessen ist: Die BLB liefert
  Rechtecke, und als Grundlinie diente deren Unterkante.
- **Bei den Korrespondenten gewinnt es nichts, aus zwei Gründen.** Sechs
  von 22 Seiten scheitern bei beiden Modellen an der Segmentierung (55 bis
  89 %), etwa eine Tabelle. Und die Hand von `K 3535` liest sich bei beiden
  mit 26 bis 36 %; sie ist im Training offenbar kaum vertreten.
- **Die Zahl des Trainers ist hier keine Schmeichelei, aber eine andere
  Grösse.** Auf seinen eigenen zurückgehaltenen Zeilen meldet er 8,7 %.
  Diese Zahl gilt Zeile für Zeile auf den Zeilen der Vorlage. Die Seiten oben
  enthalten auch die Fehler der Segmentierung, und je nach Hand liegen sie
  darunter oder deutlich darüber.

**Zum Einordnen, nicht zum Vergleichen:** Der Trainer von `Qwen3.5-4B`
meldet auf 168 Eval-Seiten 21,5 % (gekürzt 19,9 %). Seine Auswertung brach
die Ausgabe nach 1536 Tokens ab und schneidet lange Seiten damit ab. Gemessen
ist das mit einem anderen Werkzeug, und es ist keine Messung über das Gateway
auf denselben Seiten.

## 5. TrOCR

Das Trainings-Backend für TrOCR existiert. Bisher gab es aber nur **zwei
Probeläufe** auf dem Thuner Korpus, mit einer CER von 95,9 % und 97,6 %. Sie
haben geprüft, ob die Pipeline durchläuft, nicht wie gut TrOCR liest.
Kraken-Feintrainings auf demselben Korpus kamen auf 21,8 bis 39,2 %; das ist
jeweils ihr eigener Validierungssatz.

Ein ernsthafter Lauf ist offen:
[training-atr-models#37](https://github.com/thodel/training-atr-models/issues/37).

Fertige TrOCR-Modelle von anderswo lesen teils gut:

- `trocr-medieval-escriptmask` ist auf zwei Inzigkofer Codices des 15.
  Jahrhunderts mit **20,0 %** der beste lokale Leser. Das Kraken-Modell
  `kraken-catmus-medieval` kommt dort auf 25,8 %.
- `trocr-kurrent-XIX` liest die Bundesratsprotokolle mit 13,90 % (Abschnitt 1).

Ob ein eigenes Feintraining das übertrifft, ist ungemessen.

## 6. Was daraus folgt, und was noch fehlt

- **Kraken lohnt sich nachzutrainieren, wo es Zeilen-Ground-Truth gibt.**
  Auf den Laßberg-Briefen hat ein Nachtraining den Fehler auf Laßbergs Hand
  gedrittelt (Abschnitt 4). Gegen Seiten, an denen die Segmentierung
  scheitert, hilft es nicht.
- **Für Genauigkeit lohnt sich ein feinjustiertes VLM auf Zeilen**, wo die
  Zeilen schon zerlegt sind. Kraken bleibt die Wahl, wo Grösse,
  Geschwindigkeit oder Rechenkosten entscheiden.
- **Seiten nur mit einem Basismodell, das auf Seiten vortrainiert ist**
  (olmOCR), und mit hoher Auflösung. Das Pixelbudget allein war 7 Punkte wert.
- **Gemeinsame Testsätze fehlen.** Für einen vollständigen Vergleich fehlen
  drei Messungen:
  - Kraken und ein Zeilen-VLM auf `german-medieval-v1/test`;
  - die beiden Seiten-VLMs auf der BLB-Eval-Seite über das Gateway, damit
    Abschnitt 4 ein Vergleich wird;
  - ein erster echter TrOCR-Lauf;
  - ein eigener, nach Dokument zurückgehaltener Satz für Kurrent des 16. bis
    19. Jahrhunderts. Er ist seit dem 27. Oktober in Arbeit
    ([training-atr-models#301](https://github.com/thodel/training-atr-models/issues/301)).
