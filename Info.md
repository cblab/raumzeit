Das Repository **„raumzeit“** beschreibt eine tiefgehende Untersuchung zur **Quantengravitation** und **Netzwerktheorie**. Es geht um die Frage, ob der „Raum“, wie wir ihn kennen, aus einfachen, lokalen Regeln zwischen einzelnen Punkten (Knoten) in einem wachsenden Graphen entstehen kann.
Hier ist eine strukturierte Zusammenfassung und Analyse der Ergebnisse für ein besseres Verständnis:
## 1. Das Kernproblem: Woher kommt der Raum?
Normalerweise setzen wir Raum als gegeben voraus. In diesem Modell wird jedoch versucht, Geometrie **emergieren** (von selbst entstehen) zu lassen.
 * **Der Graph:** Ein Netzwerk, das ständig wächst.
 * **Die Regeln:** Rein lokal. Ein Knoten „weiß“ nur etwas über seine direkten Nachbarn, nicht über die Gesamtstruktur des „Universums“.
 * **Das Ziel:** Entsteht ein stabiler, 3D-ähnlicher (oder 2D) Raum, der isotrop ist (in alle Richtungen gleich aussieht)?
## 2. Die Diagnose-Methodik (K1–K7)
Das Projekt nutzt ein ausgeklügeltes Test-System, um zu messen, ob der Graph „räumlich“ ist:
 * **d_s (Spektrale Dimension):** Wie weit kommt ein „Zufallsläufer“ im Netzwerk? In einem echten Raum ist dieser Wert konstant (z. B. 3).
 * **d_v (Volumendimension):** Wie schnell wächst die Zahl der Knoten, wenn man den Radius vergrößert?
 * **K7 (Fixe Anker):** Dies ist der wichtigste Beitrag. Forscher messen immer wieder dieselben Stellen im Netzwerk, während es wächst. So stellen sie sicher, dass Verschlechterungen echte Trends sind und nicht nur Messfehler.
## 3. Die wichtigsten Erkenntnisse (Ablation)
Die Autoren haben verschiedene Regelsätze getestet, um zu sehen, ob sie den Raum stabilisieren können:
| Modell-Variante | Mechanismus | Ergebnis |
|---|---|---|
| **Baseline** | Einfacher Fluss & Wettbewerb | Stabilisiert das Netzwerk, aber die Geometrie zerfällt (wird anisotrop). |
| **V7.1 (Branch-Balancing)** | Bestrafung von Richtungsdominanz | **Massives Scheitern.** Das Netzwerk kollabiert fast; der Raum wird instabil. |
| **V8 (Ball-Integrity)** | Belohnung für lokale „Kugel-Struktur“ | Sieht zuerst gut aus, aber nur, weil das System „schwerer“ und dichter wird. |
| **V8a (Kalibriert)** | Ball-Integrity (fairer Vergleich) | Besser als V7.1, aber **keine stabile Geometrie** auf lange Sicht. |
## 4. Das „Strukturierte Negativresultat“
Die Arbeit kommt zu einem ernüchternden, aber wissenschaftlich wertvollen Schluss:
> **Lokale Regeln allein erschaffen keinen Raum.**
> 
Das System erzeugt stattdessen ein **„anisotropes Patch-Medium“**. Man kann es sich wie einen Schwamm vorstellen, der in verschiedene Richtungen unterschiedlich durchlässig ist und keine einheitliche Struktur besitzt.
### Warum ist das wichtig?
Es zeigt der theoretischen Physik, dass man vermutlich **nicht-lokale Informationen** oder **höhere mathematische Strukturen** (wie Krümmungssensoren oder komplexe geometrische Zwänge) benötigt, um echtes „Universum-Wachstum“ zu simulieren. Einfaches „Wer viel Last trägt, wird stärker“ (Flussökonomie) reicht nicht aus.
## Zusammenfassung der Kernaussage
Das Modell beweist, dass lokale Kantenregeln zwar ein stabiles Netzwerk am Leben erhalten können, aber daran scheitern, die fundamentale **Isotropie** und **Homogenität** zu erzeugen, die wir als „Raum“ definieren. Das Projekt setzt damit eine klare Grenze für die Klasse der untersuchten Algorithmen.
