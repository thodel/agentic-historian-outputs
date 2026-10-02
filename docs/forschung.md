---
layout: default
title: Forschung
---

# Forschung

Neben den einzelnen Ausgaben im [Katalog](index.html) entstehen in diesem
Projekt Untersuchungen, die nicht ein Dokument betreffen, sondern das
Verfahren selbst: wie gut die eingesetzten Erkennungsmodelle tatsächlich
lesen, was beim Nachtrainieren eigener Modelle schiefging, und was ein
vollständig durchgelesenes Korpus über die Grenzen dieser Messungen verrät.

Alle drei Texte halten fest, **was gemessen wurde**, und trennen das bewusst
von der Frage, was daraus für die Pipeline folgen soll. Sie sind auf Englisch
verfaßt; die [Sprachpolitik](about.html#sprachpolitik) erklärt, warum sie
trotzdem hier verlinkt sind und nicht als interne Arbeitsdokumente gelten.

## Untersuchungen

<dl class="research-index">
  <div>
    <dt><a href="evaluation.html">Recognition engine evaluation</a>
      <span class="research-language" lang="en">englisch</span></dt>
    <dd>Ein kontrollierter Vergleich der Erkennungsmodelle über drei Korpora,
      die Fehlertaxonomie hinter den Kennzahlen, und was geschah, als ein
      Sprachmodell die beste Lesart auswählen sollte. Die Seite misst
      Modelle, die dieses Projekt nicht gebaut hat.</dd>
  </div>
  <div>
    <dt><a href="vlm-finetuning.html">Fine-tuning vision models</a>
      <span class="research-language" lang="en">englisch</span></dt>
    <dd>Was beim Nachtrainieren eigener Bild-Sprach-Modelle auf Schweizer und
      deutschem Material gelernt wurde. Fast keine der Lehren betrifft
      Hyperparameter — sie betreffen, was dem Modell gezeigt wurde und was
      die Zahl, an der es gemessen wurde, tatsächlich misst. Wo eine frühere
      Aussage sich als falsch erwies, steht die Korrektur im Text statt einer
      stillen Änderung.</dd>
  </div>
  <div>
    <dt><a href="lassberg-evaluation/">Reading the Laßberg correspondence</a>
      <span class="research-language" lang="en">englisch</span></dt>
    <dd>6742 digitalisierte Briefseiten Joseph von Laßbergs, maschinell
      gelesen: was der Durchlauf kostete, wie weit zwei Lesungen voneinander
      abweichen, und — für ein Modell auf 276 Seiten — wie weit sie von einer
      menschlichen Transkription abweichen. Der Befund, der alles weitere
      bestimmt: die Fehlerrate spaltet sich um das Vier- bis Fünffache nach
      der <em>Hand</em>, innerhalb eines Modells auf einem Korpus. Die Seite
      ist kein Modellvergleich — sieben der acht Kandidaten haben noch keine
      Qualitätszahl.</dd>
  </div>
</dl>

## Verhältnis zu den Ausgaben

Diese Untersuchungen sind **keine** Belege für einzelne Transkriptionen. Was
für eine bestimmte Ausgabe gilt, steht auf deren eigener Seite: die
eingesetzten Modelle, ihre Konfidenzen und die dokumentierten Probleme. Die
Forschungstexte sagen etwas über das Verfahren im Mittel, nicht über ein
einzelnes Dokument.

Maschinenlesbare Aufzeichnungen zu abgeschlossenen Trainingsläufen erscheinen
unter [Training](training/), sobald ein Lauf veröffentlicht ist.
