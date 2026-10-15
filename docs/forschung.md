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
    <dd>Rund 6700 digitalisierte Briefseiten Joseph von Laßbergs, maschinell
      gelesen, und <strong>acht Erkennungsmodelle</strong> gegen eine
      menschliche Transkription von 226 Seiten gemessen. Zwischen dem besten
      und dem schlechtesten liegt Faktor 3,3 im Median — kein Feld von
      Gleichen, und damit ist Fusion der Lesungen nach allem, was dazu
      gemessen wurde, der falsche Weg. Der Befund, der die Zahlen begrenzt:
      die Fehlerrate spaltet sich um das Vier- bis Fünffache nach der
      <em>Hand</em>, innerhalb eines Modells auf einem Korpus. Und der Share
      hält inzwischen 35 Seiten nicht mehr, für die handkorrigierter Text
      vorliegt. Seit Oktober 2026 kommt ein <strong>neunter Leser</strong>
      hinzu, ein kommerzielles Modell hinter einer API: 300 bislang
      untranskribierte Seiten, in der Edition publiziert — und drei Befunde,
      die keine Qualitätszahl gezeigt hätte. Ein Modell, das im
      Transkriptionsfeld laut mit sich selbst ringt; <em>ein Satz</em> im
      Prompt, der zwei beschriebene Seiten in einer Spalte namens „leer“
      verschwinden liess; und die Streuung zwischen zwei identischen Läufen,
      die niemand gemessen hatte — ein vollständiger Brief von 1831 war in
      vier Läufen „leer“ und liest sich im fünften durch. Die Lehre daraus ist
      nicht „noch ein Versuch“, sondern ein zweiter Leser: ein vierter Durchgang
      desselben Modells holte 0 von 19 Seiten, zwei Modelle anderer Familien
      eine — den Anfang eines Briefes, 24 Zeilen, viermal verschwiegen. Und ein
      dritter Strang betrifft nicht das Lesen, sondern das <em>Bild</em>: von 43
      Seiten, deren Transkription nicht zu ihrem Scan passt, sind 27 zwei
      verschiedene Aufnahmen derselben Seite — darunter eine Doppelseite gegen
      ein halbiertes Blatt — und 16 dasselbe Bild in zwei Auflösungen.</dd>
  </div>
  <div>
    <dt><a href="disputation-page-model/">A page model on the Berner Disputation</a>
      <span class="research-language" lang="en">englisch</span></dt>
    <dd>Das erste Modell dieses Projekts, das auf <em>ganzen Seiten</em>
      trainiert wurde, gegen jenes, das die fünf Berner Handschriften von 1528
      zeilenweise gelesen hat — 40 Seiten aus vier Abschriften,
      <a href="disputation-page-model/readings.html">alle vollständig
      publiziert</a>. Der Befund: nicht das Modell entscheidet, sondern die
      Hand. Auf der Schlussredaktion, der Reinschrift, entartet keine einzige
      Seite, die Lesung trifft die Länge der Seite und weicht vom Zeilenmodell
      nur um 24,5 % ab; auf Schöni verliert dasselbe Modell eine Seite von zehn
      an eine Wiederholungsschleife und schreibt das 1,8-fache. Eine Sache kann
      es besser: es gibt die Abbreviaturen des Schreibers wieder (39 Zeichen
      gegen 2) — und zwar fast nur dort, wo ein Schreiber sie überhaupt
      verwendet. <strong>Die erste Fassung dieser Seite war falsch</strong>:
      drei der vier Läufe hatten wegen einer Cache-Kollision dieselbe
      Handschrift ein zweites Mal gelesen. Die Korrektur steht oben auf der
      Seite, samt dem, was sie umgestossen hat.</dd>
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
