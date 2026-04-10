
# Lokale Flussregeln stabilisieren keine emergente Geometrie in kausalen Wachstumsgraphen

## Zusammenfassung

Wir untersuchen, ob makroskopische geometrische Struktur aus rein lokalen, kausalen, kombinatorischen Regeln auf einem wachsenden gerichteten Graphen emergieren kann, ohne dass ein umgebender Raum vorausgesetzt wird. Das Modell kombiniert lokale Kantenplastizität, Sparsity-Druck, Redundanzunterdrückung, genealogische Diversifikation, Lastsättigung und mesoskopische Anti-Crowding-Terme. Geometrie ist dabei nicht in die Dynamik eingebaut, sondern wird ausschließlich über Diffusions-, Volumen-, Schalen-, Konzentrations- und Ankerdiagnostiken gemessen.

Wir führen ein gestuftes Diagnostik-Framework K1-K7 ein, dessen zentraler methodischer Beitrag in fixen Ankerpunkten liegt. Diese erlauben es, Patch-Heterogenität von echter zeitlicher Drift zu trennen, indem über die Zeit immer wieder gleich große BFS-induzierte Regionen um dieselben Seeds vermessen werden.

Das Basismodell stabilisiert ein nichttriviales dünnes gewichtetes Netzwerk, erzeugt aber keine stabile isotrope Makrogeometrie. Sowohl globale als auch ankerlokale Diffusionsdimensionen fallen mit der Systemgröße. Das Volumenwachstum entkoppelt sich teilweise von der Diffusion. Der Isotropiedefekt steigt im Spätlauf in den Ordnungsbereich 1. Konzentrationsmaße bleiben dagegen vergleichsweise flach, was lokale Monopolisierung als Primärmechanismus weitgehend ausschließt.

Wir testen anschließend drei lokale Erweiterungen: eine strafbasierte Branch-Balancing-Regel, eine belohnungsbasierte Ball-Integrity-Regel und eine gewichtskalibrierte Variante derselben. Branch-Balancing verschlechtert das Regime massiv durch Ausdünnung, frühere Anisotropie und Kollaps der Diffusionsgeometrie. Ball-Integrity ist deutlich weniger destruktiv und verbessert die Konnektivität, stabilisiert jedoch auch nach Gewichtskalibrierung keine Makrogeometrie. Der scheinbare Vorteil der unkorrigierten Ball-Integrity-Variante beruht zu einem erheblichen Teil auf einem Wechsel in ein höheres Gewichts- und schwächeres Pruning-Regime.

Wir schließen daraus, dass diese gesamte Klasse lokaler, kantenbezogener Fluss- und Konkurrenzregeln strukturell nicht hinreichend ist, um makroskopische Geometrie zu stabilisieren. Ihr natürlicher Output ist kein emergenter Raum, sondern ein selbststabilisiertes anisotropes diffusionsgeometrisches Patch-Medium.

---

## 1. Einleitung

Eine der grundlegendsten offenen Fragen der theoretischen Physik lautet, ob Raum selbst etwas Primäres ist oder ob er aus tieferliegenden, nicht-geometrischen Freiheitsgraden emergiert. Varianten dieser Frage tauchen in mehreren Forschungsprogrammen auf: in der Causal-Set-Theorie, in dynamischen Graphmodellen wie Quantum Graphity, in Causal Dynamical Triangulations und in wachstumsbasierten simplicialen Modellen wie Network Geometry with Flavor. Gemeinsam ist diesen Ansätzen die Idee, dass kausale Ordnung, kombinatorische Struktur oder diskrete Dynamik fundamental sein könnten, während Lokalität und Geometrie erst auf größeren Skalen auftreten. 0

Die vorliegende Arbeit untersucht eine bewusst minimale Version dieser Frage. Wir fragen nicht, ob ein vollständiges Modell der Quantengravitation konstruiert werden kann. Wir fragen nur, ob eine plausible Klasse rein lokaler, kausaler und kantenbasierter Regeln bereits ausreicht, um eine makroskopische Geometrie zu stabilisieren, deren Diffusions- und Volumeneigenschaften mit einem niedrigdimensionalen isotropen Raum verträglich sind.

Das Modell ist so gebaut, dass Geometrie nicht vorausgesetzt wird. Es gibt keinen eingebetteten euklidischen Raum, keine Triangulierungen, kein Pfadintegral, keine globale Energiefunktion, keinen Ziel-Laplacian und keine explizite Krümmungsstrafe. Stattdessen gibt es lokale Regeln, die transportartige Organisation erzeugen sollen: Kohärenzverstärkung, Redundanzvermeidung, genealogische Diversifikation, Lastverteilung, Plastizität und Sparsity. Das ist absichtlich eine strenge Hypothese. Wenn Raum tatsächlich aus lokalen Beziehungen emergieren kann, dann sollte sich zumindest ein Teil dieser Geometrie bereits unter einer sparsamen lokalen Mechanismusklasse andeuten.

Das Hauptproblem ist dabei diagnostischer Natur. Auf heterogenen wachsenden Graphen sind globale Mittelwerte notorisch schwer zu interpretieren. Ein Rückgang der Diffusionsdimension kann entweder echte zeitliche Degradation bedeuten oder nur darauf beruhen, dass zufällig andere Patches vermessen werden. Genau hier setzt unser methodischer Beitrag an. Mit dem K1-K7-Framework und insbesondere mit K7, den fixen Ankerdiagnostiken, wird diese Unterscheidung operational möglich.

Die Arbeit liefert ein strukturiertes Negativresultat. Das Basismodell erzeugt keine stabile Makrogeometrie. Eine naheliegende lokale Korrektur durch Branch-Balancing verschlechtert das Regime massiv. Eine plausiblere lokale Ergänzung über Ball-Integrity stützt zwar die Konnektivität, rettet aber die Geometrie nicht. Nach Gewichtskalibrierung bleibt auch dort dieselbe qualitative Klasse des Scheiterns bestehen.

Der Beitrag dieser Arbeit ist daher nicht die Konstruktion emergenten Raums, sondern die präzise Eingrenzung dessen, was lokale Mechanismen dieser Klasse **nicht** leisten.

---

## 2. Modell

### 2.1 Grundstruktur

Wir betrachten einen wachsenden gerichteten gewichteten Graphen $G_t=(V_t,E_t)$. In jedem diskreten Zeitschritt wird ein neuer Knoten hinzugefügt. Seine eingehenden Kanten stammen von bereits existierenden Knoten. Dadurch entsteht eine natürliche Wachstumsrichtung, die als primitive Kausalstruktur gelesen werden kann.

Jeder Knoten $j$ trägt einen binären internen Zustand $s_j\in\{0,1\}$. Jede aktive Kante $e=(i\to j)$ besitzt ein Gewicht $w_e\in[w_{\min},w_{\max}]$.

### 2.2 Parent-Selektion

Für einen Kandidatenknoten $i$ ist der Basisscore

$$
S_i^{\text{base}}
=
\exp\!\left(\alpha L_i+\beta C_i+\gamma N_i\right),
$$

wobei

- $L_i$ ein lokaler Dichtescore ist,
- $C_i$ eine exponentiell geglättete Kohärenzgröße,
- $N_i$ ein Neuheitsterm.

Der Dichtescore lautet

$$
L_i=\frac{1}{1+\left|k_i^{\text{out}}-\rho^\star(|V_t|-1)\right|},
$$

mit aktiver Out-Degree $k_i^{\text{out}}$ und Zieldichte $\rho^\star$.

Der Neuheitsterm ist

$$
N_i=\frac{1}{1+k_i^{\text{out}}}.
$$

Um genealogische Redundanz im Parent-Set zu vermeiden, wird jedem Knoten eine Ancestry-Signatur $A(i)$ zugeordnet, die über aktive eingehende Kanten bis zu einer festen Tiefe rekursiv erzeugt wird. Die Ähnlichkeit zweier Signaturen messen wir über den Jaccard-Index

$$
J(i,\ell)=\frac{|A(i)\cap A(\ell)|}{|A(i)\cup A(\ell)|}.
$$

Die Parents des neuen Knotens werden sequentiell gewählt. Ist $P$ die Menge der bereits gewählten Parents, dann ist der effektive Score

$$
S_i
=
S_i^{\text{base}}
\prod_{\ell\in P}
\max\!\left(\varepsilon_r,1-\lambda_r J(i,\ell)\right).
$$

### 2.3 Zustandsupdate

Der Zustand eines Knotens $j$ ergibt sich aus dem gewichteten Mittel seiner aktiven eingehenden Nachbarn:

$$
\bar{s}_j
=
\frac{\sum_{e=(i\to j)\in E_t^{\text{act}}} w_e s_i}
{\sum_{e=(i\to j)\in E_t^{\text{act}}} w_e}.
$$

Danach wird geschwellt:

$$
s_j=
\begin{cases}
1,& \bar{s}_j\ge \tfrac12,\\
0,& \bar{s}_j<\tfrac12.
\end{cases}
$$

### 2.4 Baseline-Kantenupdate

Für eine aktive Kante $e=(i\to j)$ wird das Gewicht lokal angepasst. Die Kohärenz ist

$$
\chi_{ij}=
\begin{cases}
1,& s_i=s_j,\\
0,& s_i\neq s_j.
\end{cases}
$$

Die Redundanz einer Kante ist der Anteil anderer eingehender Kanten von $j$, deren Quellknoten denselben Zustand wie $i$ tragen:

$$
R_e
=
\frac{1}{m_j-1}
\sum_{\substack{e'=(u\to j)\in I(j)\\ e'\neq e}}
\mathbf{1}[s_u=s_i].
$$

Zusätzlich werden genealogische Ähnlichkeiten der eingehenden Parent-Mengen ausgewertet. Daraus entstehen:

- ein Konzentrationsdruck $\Pi_j^{\text{conc}}$,
- ein Crowding-Term $\Gamma_e^{\text{crowd}}$,
- ein Inhibitionsterm $\Gamma_e^{\text{inh}}$.

Parallel wird die Lastsättigung über die relativen Gewichtsanteile einer Kante an eingehender und ausgehender Gesamtlast erfasst. Damit ergeben sich

$$
\Delta_e^{\text{coh}}
=
\eta
\frac{2\chi_{ij}-1}{1+\beta_{\text{load}}\phi_e},
\qquad
\Gamma_e^{\text{load}}
=
\gamma_{\text{load}}\phi_e^2.
$$

Über lokale Shadow-Nachbarschaften erhält die Kante ferner einen Outflow-Bonus

$$
\Delta_e^{\text{cross}},
$$

der genealogisch neue, topologisch nichttriviale und nicht-überlastete Verbindungen bevorzugt.

Alte Kanten können über einen altersabhängigen Plastizitätsterm zusätzlich geschwächt werden:

$$
\Gamma_e^{\text{plast}}.
$$

Das vollständige Baseline-Update lautet damit

$$
w_e(t+1)
=
w_e(t)
+\Delta_e^{\text{coh}}
+\Delta_e^{\text{cross}}
-\nu R_e
-\Gamma_e^{\text{inh}}
-\Gamma_e^{\text{crowd}}
-\Gamma_e^{\text{load}}
-\Gamma_e^{\text{plast}}
-\mu (w_e-w_0).
$$

Fällt die Kante unter einen effektiven pruning threshold

$$
w_{\min}^{\text{eff}}(j)=w_{\min}(1+\lambda_p D_j),
$$

wird sie deaktiviert.

---

## 3. Diagnostik-Framework K1-K7

### 3.1 K1: strukturelle Stabilisierung

K1 misst:

- Zahl aktiver Kanten,
- Mittelwert und Varianz der Out-Degree,
- Gewichtsstatistik,
- Entropie der Degree-Verteilung.

Damit lässt sich unterscheiden, ob ein Modell trivial kollabiert oder ein stabiles dünnes Netzwerk bildet.

### 3.2 K2: globale Diffusions- und Volumenmaße

Auf zufällig gewählten BFS-Regionen messen wir:

- Rückkehrwahrscheinlichkeiten $P(\tau)$,
- spektrale Diffusionsdimension $d_s$,
- Volumenwachstumsdimension $d_v$.

Die spektrale Dimension wird über lokale Fits von

$$
P(\tau)\sim \tau^{-d_s/2}
$$

geschätzt.

Das Volumenwachstum wird über

$$
V(r)\sim r^{d_v}
$$

approximiert.

### 3.3 K4: Konzentration, Effizienz, Pfadlänge

K4 misst:

- eingehende Herfindahl-Konzentration,
- Cluster-Dominanz,
- globale Effizienz,
- mittlere Pfadlänge.

Diese Größen sind wichtig, um Geometrieversagen von einfachem Hub- oder Monopolkollaps zu unterscheiden.

### 3.4 K5: Schalenstruktur und Frontdicke

K5 misst:

- Schalenentropie,
- Frontdicke,
- Peak-Shell.

Damit lässt sich erkennen, ob BFS-Bälle eher kugelartig oder patchig wachsen.

### 3.5 K7: fixe Anker

K7 ist der methodische Kern dieser Arbeit.

Eine feste Menge von Anchor-Seeds wird einmalig gewählt. Um jeden Anchor wird zu jedem Messzeitpunkt eine gleich große BFS-induzierte Shadow-Region erzeugt. In diesen Regionen messen wir:

- ankerlokales $d_s$,
- ankerlokales $d_v$,
- Isotropiedefekt,
- Kausalfront-Proxys,
- core/mid/front-Diffusionssplits.

Das trennt:

- Patch-Heterogenität,
- von echter zeitlicher Drift.

Ohne K7 wäre ein Rückgang der Geometrie nicht kausal sauber interpretierbar.

---

## 4. Versuchsdesign

Wir vergleichen vier Varianten derselben lokalen Mechanismenklasse.

### 4.1 Baseline

Die reine lokale Fluss- und Konkurrenzdynamik aus Abschnitt 2.4.

### 4.2 V7.1: Branch-Balancing

Eine zusätzliche lokale Strafregel, die Richtungsdominanz am Zielknoten reduzieren soll. Sie bestraft Verstärkung bereits stark repräsentierter lokaler Sektoren.

### 4.3 V8: Ball-Integrity

Eine belohnungsbasierte Regel, die nicht dominante Richtungen schwächt, sondern lokale Ball-Integrität stützen soll. Dazu gehören:

- Triangle-Support,
- 2-Hop-Coverage,
- Sektorverknüpfung,
- Mehrpfadigkeit.

### 4.4 V8a: gewichtskalibrierte Ball-Integrity

Da V8 in ein deutlich höheres Gewichtsregime driftete, wird in V8a zusätzlich ein weight-centering drag und ein excess-weight penalty eingeführt, um das Regime näher an die Baseline zurückzuführen und so einen faireren Mechanismenvergleich zu ermöglichen.

---

## 5. Ergebnisse

### 5.1 Baseline: strukturell stabil, geometrisch instabil

Die Baseline erzeugt ein stabiles dünnes Netzwerk. `mean_k_out` bleibt im späten Lauf bei ungefähr 3.9, die Gewichte bleiben beschränkt, und das Netzwerk kollabiert weder in ein leeres noch in ein vollständig dichtes Regime.

Geometrisch scheitert die Baseline jedoch klar. Das globale $d_s$ fällt im Verlauf in den Bereich 2.7 bis 3.0, während $d_v$ höher bleibt und sich nicht konsistent mit $d_s$ mitbewegt. Der ankerlokale Isotropiedefekt steigt systematisch und erreicht im Bereich zwischen etwa 11750 und 12250 erstmals den Ordnungsbereich 1.

Die wichtigste Aussage der Baseline lautet damit:

**Lokale Flussökonomie stabilisiert Netzwerkstruktur, aber keine Makrogeometrie.**

### 5.2 K7 zeigt: Das ist echte Zeitdrift, kein Sampling-Artefakt

Ohne fixe Anker könnte man argumentieren, dass globale Messwerte nur deshalb schlechter werden, weil spätere BFS-Patches zufällig ungünstiger sind. K7 widerlegt das.

Die gleichen Anchor-Regionen zeigen im Zeitverlauf ebenfalls einen Rückgang der Diffusionsdimension und einen Anstieg des Isotropiedefekts. Der Effekt ist also nicht bloß ein Mittelungsproblem über wechselnde Regionen, sondern echte zeitliche Degradation.

Das ist der methodische Kernbefund des gesamten Projekts.

### 5.3 K4 bleibt flach: kein einfacher Hub-Kollaps

Ein naheliegender Mechanismus für Geometrieversagen wäre lokale Monopolisierung. Genau hier ist K4 entscheidend.

Die eingehende Herfindahl-Konzentration und die Cluster-Dominanz bleiben in der Baseline vergleichsweise flach. Sie zeigen keinen scharfen Übergang, der mit dem Kollaps von $d_s$ oder dem Anstieg von `iso` korrespondiert.

Damit ist einfache lokale Monopolisierung als Primärmechanismus weitgehend ausgeschlossen. Das System wird geometrisch schlechter, ohne zuerst trivial hub-dominiert zu werden.

### 5.4 V7.1: Branch-Balancing verschlimmert das Problem

Die strafbasierte Richtungsbalance-Regel V7.1 ist ein klares Negativresultat.

Im Vergleich zur Baseline führt sie zu:

- starkem Grad-Kollaps,
- drastisch früherem Isotropieanstieg,
- deutlich niedrigerem $d_s$,
- längeren Pfaden,
- schlechterer Effizienz.

Mechanisch ist die Ursache klar: Dominante lokale Richtungen werden geschwächt, ohne dass lokale Ball-Integrität gesichert wird. Das zerstört tragende Mehrpfadstrukturen und erzeugt ein dünnes, fragiles Regime.

Die Lehre daraus ist wichtig:

**Lokale Dominanzstrafe ist kein Ersatz für Geometrieerhaltung.**

### 5.5 V8: Ball-Integrity ist die plausiblere lokale Richtung, aber noch nicht hinreichend

V8 ersetzt Strafe durch Belohnung. Statt dominante Sektoren zu dämpfen, belohnt der Zusatzterm Kanten, die lokale Ball-Struktur stützen.

Gegenüber V7.1 ist das ein klarer qualitativer Fortschritt:

- kein Grad-Kollaps,
- deutlich höhere Diffusionsdimension,
- spätere Anisotropie,
- bessere Effizienz,
- kürzere Pfade.

Allerdings driftet V8 in ein stark anderes Gewichtsregime. `mean_w` steigt auf etwa 1.5, während die Baseline bei ungefähr 0.6 liegt. Gleichzeitig verschwindet Pruning fast vollständig.

Das macht V8 kausal unsauber interpretierbar: Ein Teil des scheinbaren Vorteils kann ebenso gut aus schwächerem Pruning und insgesamt höheren Gewichten stammen wie aus dem Ball-Integrity-Mechanismus selbst.

### 5.6 V8a: Gewichtskalibrierung kontrolliert den Konfundierungseffekt

V8a ist der entscheidende Kontrolllauf.

Hier wird das Gewichtsregime durch zusätzliche Kalibrierung wieder näher an die Baseline herangeführt. `mean_w` liegt nun bei etwa 0.9 statt bei 1.5, die Out-Degree bleibt stabil bei ungefähr 3.95, und das Netzwerk bleibt vergleichbar dünn.

Das Ergebnis ist eindeutig:

- V8a ist weiterhin deutlich weniger destruktiv als V7.1,
- aber der große scheinbare Vorteil von V8 schrumpft erheblich.

Insbesondere:

- der späte Bereich von $d_s$ liegt wieder grob im selben Korridor wie die Baseline,
- der Isotropiedefekt überschreitet erneut um etwa 12k–14k den Bereich 1,
- globale K2-Maße bleiben qualitativ ähnlich wie in der Baseline.

Damit ist die zentrale Kausalfrage beantwortet:

**Der V8-Effekt war nicht bloß ein Gewichts-Artefakt, aber zu einem erheblichen Teil regimebedingt.**

### 5.7 Gesamtablation

Die vollständige Ablation ergibt ein sauberes Bild:

- **Baseline:** Geometrie degradiert
- **V7.1:** lokale Richtungsstrafe verschlimmert aktiv
- **V8:** Ball-Integrity wirkt zunächst viel besser, aber in anderem Regime
- **V8a:** nach Kalibrierung bleibt Ball-Integrity die plausiblere Richtung, ändert aber die asymptotische Geometrieklasse nicht

Das ist einer der stärksten Befunde dieser Arbeit. Nicht alle lokalen Erweiterungen sind gleichwertig. Belohnungsbasierter Ball-Erhalt ist klar weniger falsch als strafbasiertes Branch-Balancing. Aber keine der getesteten Varianten stabilisiert eine konsistente Makrogeometrie.

---

## 6. Interpretation

### 6.1 Was das Modell erzeugt

Die getestete Mechanismenklasse organisiert Fluss und Last, nicht Geometrie.

Ihr natürlicher Output ist:

- ein stabiles dünnes Netzwerk,
- mit anisotropen diffusionsgeometrischen Patches,
- teilweise hohem Volumenwachstum,
- aber keiner konsistenten Raumstruktur.

Die treffendste Beschreibung lautet daher:

**ein selbststabilisiertes anisotropes diffusionsgeometrisches Patch-Medium**

und nicht emergenter Raum.

### 6.2 Was die Ablation zeigt

Die Ablationskette erlaubt einen präzisen Mechanismensatz:

1. reine lokale Flussökonomie reicht nicht,
2. lokale Dominanzstrafe ist aktiv schädlich,
3. lokaler Ball-Erhalt ist weniger destruktiv,
4. aber weiterhin nicht hinreichend.

Das bedeutet: Der fehlende Mechanismus liegt tiefer als bloße Richtungsbalance oder bloße Mehrpfadigkeit auf Kantenebene. Wahrscheinlich fehlt eine Form von nichtlokaler geometrischer Information, coarse-grained consistency oder höherordentlicher Struktur.

### 6.3 Diffusion gegen Volumen

Ein wiederkehrender theoretisch interessanter Punkt ist die Entkopplung von $d_s$ und $d_v$. Gerade in V8 und V8a bleibt $d_v$ häufig höher als $d_s$. Das spricht gegen eine glatte euklidische oder Riemannsche Geometrie und eher für ein poröses, schwammartiges, diffusionsgestörtes Medium.

Das ist kein positives Raumresultat, aber ein positiver struktureller Befund darüber, was diese Dynamiken tatsächlich erzeugen.

---

## 7. Einordnung in die Literatur

Die Arbeit steht nicht im Widerspruch zur breiteren emergent-geometry-Literatur. Sie grenzt eine spezielle Mechanismenklasse ein.

Causal-Set-Ansätze gehen ebenfalls von diskreter kausaler Ordnung aus, enthalten aber stärkere strukturelle Annahmen und oft explizite Diskussionen nichtlokaler Effekte. 1

Quantum Graphity untersucht emergente Lokalität auf dynamischen Graphen, allerdings in einem energiebasierten Setting. Wichtig ist, dass dort ebenfalls Probleme nicht-geometrischer bevorzugter Zustände identifiziert wurden. 2

Network Geometry with Flavor erzeugt emergente Geometrie auf simplicialen Komplexen. Der entscheidende Unterschied ist, dass dort höhere kombinatorische Ordnung eingebaut ist und nicht nur gewichtete gerichtete Kanten vorliegen. 3

Neuere Arbeiten zu spektraler und krümmungsbasierter Graphgeometrie verwenden explizit globale oder halbglobale geometrische Zielgrößen. Genau solche Strukturen fehlen in unserem Modell absichtlich. 4

Die spezifische Leistung dieser Arbeit liegt also nicht in einem neuen positiven Mechanismus emergenter Geometrie, sondern in der sauberen negativen Eingrenzung:

**Lokale kantenbezogene Fluss- und Integritätsregeln sind kein Ersatz für geometrische Selektion.**

---

## 8. Einschränkungen

Diese Arbeit hat klare Grenzen.

### 8.1 Heuristische Regelklasse

Das Modell ist nicht aus einem fundamentalen Wirkungsprinzip abgeleitet. Es ist ein heuristisches Testbett.

### 8.2 Endliche Größe

Alle Diagnostiken sind auf endlichen Graphen definiert. Aussagen über wahre Kontinuumsgrenzen bleiben daher hypothetisch.

### 8.3 Begrenzte Ensemble-Breite

Die hier präsentierten Läufe zeigen starke qualitative Signale, aber für Journal-Niveau sind mehrere Seeds und Fehlerbalken zwingend.

### 8.4 Kommensurabilität von V8

Der unkorrigierte V8-Lauf war nicht vollständig mit der Baseline kommensurabel, weil er in ein stark anderes Gewichtsregime driftete. Genau deshalb ist V8a methodisch notwendig.

### 8.5 Kein Beweis für alle lokalen Mechanismen

Die Ergebnisse zeigen nicht, dass jede lokale Ergänzung scheitert. Sie zeigen nur, dass diese getestete Klasse lokaler kantenbezogener Erweiterungen nicht hinreichend ist.

---

## 9. Schlussfolgerung

Wir haben untersucht, ob makroskopische Geometrie aus rein lokalen, kausalen, kantenbezogenen Regeln auf einem wachsenden Graphen emergieren kann.

Die Antwort lautet für die getestete Mechanismenklasse: **nein**.

Das Basismodell stabilisiert ein dünnes gewichtetes Netzwerk, aber keine Geometrie. K7 zeigt, dass die Degradation echte Zeitdrift ist. K4 schließt einfache lokale Monopolisierung als Primärmechanismus weitgehend aus. Branch-Balancing verschlechtert das Regime aktiv. Ball-Integrity ist die plausiblere lokale Richtung, bleibt nach Gewichtskalibrierung aber ebenfalls unzureichend.

Damit ist die zentrale Konklusion präzise:

> Lokale, kantenbezogene Fluss-, Balance- und Ball-Integrity-Regeln stabilisieren keine makroskopische Geometrie. Sie erzeugen höchstens ein selbststabilisiertes anisotropes diffusionsgeometrisches Patch-Medium.

Die Suche nach emergenter Geometrie muss daher über diese Mechanismenklasse hinausgehen. Wahrscheinliche Kandidaten sind:

- höherordentliche kombinatorische Strukturen,
- coarse-grained consistency constraints,
- nichtlokale geometrische Information,
- explizite spektrale oder krümmungsbezogene Selektionsmechanismen.

---

## Danksagung

Diese Arbeit verdankt ihren methodischen Kern der konsequenten Falsifikationslogik: Nicht das schöne Modell ist entscheidend, sondern die saubere Trennung dessen, was eine Regelklasse leisten kann, von dem, was sie nicht leisten kann.

---

## Daten- und Codeverfügbarkeit

Die hier beschriebenen Modelle sind vollständig algorithmisch definiert. Für eine spätere Einreichung sollten vollständiger Code, Reproduktionsparameter, Seed-Listen und Run-Logs offengelegt werden.

---

## Abbildungsvorschläge

**Abbildung 1:** Baseline: globales $d_s$, $d_v$ und K7-Isotropiedefekt über die Zeit.  
**Abbildung 2:** K7-Fixanker-Diagnostik: Drift derselben Patches statt wechselnder Samples.  
**Abbildung 3:** Ablation Baseline vs V7.1 vs V8 vs V8a für `mean_k_out`, K7-$d_s$, K7-`iso`, Effizienz und Pfadlänge.  
**Abbildung 4:** Schematische Gegenüberstellung: anisotropes Patch-Medium vs. hypothetischer isotroper Makroraum.  
**Abbildung 5:** K4-Flachheit als Ausschluss einfacher Monopolisierung.

---

## Kernaussage in einem Satz

**Die getestete Klasse lokaler Regeln stabilisiert Transportstruktur, aber keinen Raum.**
