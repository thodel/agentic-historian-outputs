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
      zeilenweise gelesen hat — 40 Seiten aus vier Abschriften. Das
      Seitenmodell ist auf diesem Material der deutlich schlechtere Leser, und
      zwar eindeutig: auf den zehn Seiten der Schlussredaktion, für die eine
      ältere Lesung existiert, liegt es auf <strong>zehn von zehn</strong>
      zurück, Median 0,16 gegen 0,85. Dazu eine Entartungsrate, die in allen
      vier Handschriften dieselbe ist — eine Seite von zehn läuft in eine
      Wiederholungsschleife —, was sie zu einer Eigenschaft des Modells macht
      und nicht einer schwierigen Hand. Eine Sache kann es besser: es schreibt
      die Abbreviaturen des Schreibers (<em>un̄</em>, <em>vˀschriben</em>,
      <em>ꝫ</em>), die das Zeilenmodell auf denselben Seiten kein einziges Mal
      wiedergibt. Was die Seite nicht entscheidet, steht ausdrücklich darin:
      für keine dieser Handschriften existiert eine Ground Truth, jede Zahl
      hier vergleicht zwei Maschinen.</dd>
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
