# Alle Hubfolgen durchgehen: die Knotenexplosion – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-knotenexplosion-umstauen-demo.streamlit.app/)** -->

Viertes Stück der Konzepte-Reihe **„Umstauen: Untergrenze und Suche“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. [Stück 1](https://sebastianhanisch-umstauen-regeln-demo.streamlit.app/) vergleicht Regeln mit dem bewiesenen Optimum, [Stück 2](https://sebastianhanisch-untergrenze-umstauen-demo.streamlit.app/) erklärt die Untergrenze, [Stück 3](https://sebastianhanisch-umlagern-freiheit-demo.streamlit.app/) hebt die Annahme „nur über dem Ziel bewegen“ auf. Dieses Stück zeigt, wie das Optimum **berechnet** wird, auf dem einfachsten Weg: **alle Hubfolgen durchgehen** (Tiefensuche) und die kürzeste behalten. Es **zählt die Knoten des Suchbaums** und zeigt, wie schnell sie explodieren und was Branch and Bound und die Reihenfolge der Kinder dagegen ausrichten.

## Warum dieses Problem

Eine exakte Suche ist leicht hinzuschreiben und schwer zu bändigen. Erst die Knotenzahl macht sichtbar, warum: Mit jedem blockierenden Container wächst der Baum um ein Vielfaches. Die Messung vergleicht zwei Gegenmittel, die oft verwechselt werden: die **Schranke aus der besten bisherigen Lösung** (wirkt zusammen mit einer guten Reihenfolge stark) und die **Reihenfolge der Kinder** (Stapelnummern gegen engste Passung wirkt im Median schwach, eine schlechte Reihenfolge kostet im Median bis zum 5,11-Fachen). Der Vergleich beider ist nicht sauber getrennt: Die Schranke wird nur zusammen mit der engsten Passung gemessen.

## Modell

Eine Bucht aus *s* Stapeln mit Höchsthöhe *H* = Lagen + Platz (Platz 1 bis 4, Standard 2), anfangs jeder Stapel gleich hoch gefüllt, Abrufnummern 1 bis *N* zufällig verteilt (Familie wie in Stück 1 bis 3). Ein Hub setzt den obersten Container eines Stapels auf einen anderen Stapel mit Platz; **restricted**: nur der Blocker über der nächsten abzurufenden Nummer wird bewegt, die nächste Nummer wird entnommen, sobald sie oben liegt.

**Suchbaum:** Ein **Knoten** ist eine Bucht nach den kostenlosen Abrufen (mit den bisherigen Hüben). Die **Kinder** entstehen, indem der Blocker auf jeden anderen Stapel mit Platz gesetzt wird. Ein **Blatt** ist eine leere Bucht; ein Weg von der Wurzel zu einem Blatt ist eine Hubfolge, seine Länge die Hubzahl. Es gibt **keine** Untergrenze, **kein** Zustandsmerken und **keinen** Symmetriebruch: gleiche Zustände zählen mehrfach. Formal im Expander „📐 Mathematische Formulierung“.

## Methodik

- **Volle Aufzählung** (`none`): alle Wege, kürzesten behalten. **Branch and Bound** (`best`): Sobald die bisherigen Hübe plus 1 nicht mehr unter der besten bisher gefundenen Lösung liegen, wird der Teilbaum übergangen (jeder weitere Hub kostet mindestens 1).
- **Reihenfolge der Kinder:** *index* (Stapelnummern), *tight* (engste Passung aus Stück 1 zuerst), *anti* (schlechteste zuerst, Umkehrung von tight). Die Zahl der Knoten der vollen Aufzählung hängt nicht von ihr ab, die von Branch and Bound schon.
- **Knotenlimit:** Läufe über 500 000 Knoten (live) beziehungsweise 1 000 000 (vorberechnet) werden abgebrochen und als „über Limit“ gezählt; sie liefern kein Optimum und fehlen in den Medianen (diese sind dann nur Untergrenzen der wahren Mediane). Gezählt werden Knoten, keine Sekunden.
- **Abschnitte der App:** Ergebnis (vier Varianten an einer Bucht, live); der ausgeschriebene Suchbaum der Mini-Bucht von Hand; Tabelle über sieben Zellen mit Schranke und Reihenfolge; Wachstum mit den Blockern; Platz; Läufe über dem Limit. Die Tabellen und Kurven sind vorberechnet (`kex_bands.json`, erzeugt von `generate_precomputed.py`, rund zehn bis fünfzehn Minuten).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an den festen Buchten 0 bis (Zahl der Buchten − 1) je Zelle bei Platz 2 (Python-Zufallsfolge, `random.shuffle`), nachgerechnet in `tests/test_claims.py`, `tests/test_presets.py` und `tests/test_oracle_knotenexplosion_umstauen.py`. Zahlen: Median / Mittel / Maximum der fertigen Läufe, „über Limit“ = Läufe über 1 000 000 Knoten.

| Zelle (Buchten) | volle Aufzählung | B&B, Stapelnummern | B&B, engste Passung | B&B, schlechteste | Stapelnummern / engste (Median) | schlechteste / engste (Median, Maximum) | volle Aufzählung / engste (Median, Buchten) |
|---|---|---|---|---|---|---|---|
| 3 × 2 (100) | 9 / 20 / 161 | 5 / 8 / 47 | 5 / 6 / 27 | 7 / 10 / 53 | 1,00 | 1,56 (3,4) | 1,8 (100) |
| 4 × 2 (100) | 67 / 713 / 20 867 | 13 / 28 / 261 | 7 / 16 / 117 | 23,5 / 52 / 513 | 1,43 | 2,50 (6,6) | 5,7 (100) |
| 3 × 3 (100) | 230 / 1 403 / 13 427 | 48 / 92 / 427 | 33 / 68 / 419 | 65 / 146 / 845 | 1,25 | 2,11 (4,9) | 6,5 (100) |
| 5 × 2 (60) | 1 721 / 25 019 / 654 257, 1 über Limit | 37 / 125 / 1 420 | 25 / 80 / 1 268 | 107 / 340 / 4 210 | 1,43 | 3,56 (12,6) | 53,9 (59) |
| 3 × 4 (40) | 18 163,5 / 82 533 / 696 375 | 491 / 893 / 3 801 | 384 / 625 / 3 665 | 1 027,5 / 1 463 / 5 637 | 1,28 | 2,17 (9,1) | 40,3 (40) |
| 4 × 3 (40) | 3 611,5 / 108 841 / 612 886, **10 über Limit** | 320 / 2 331 / 41 082 | 120 / 1 221 / 15 455 | 708,5 / 3 751 / 47 161 | 1,62 | 3,48 (14,9) | 76,4 (30) |
| 5 × 3 (20) | 12 693 / 212 067 / 800 161, **15 über Limit** | 3 933 / 52 338 / 451 905 | 1 361 / 32 211 / 253 266 | 13 998 / 96 179 / 669 879, 1 über Limit | 1,41 | 5,11 (16,9) | 202,4 (5) |

Das Verhältnis der letzten Spalte ist der Median über die Buchten, in denen **beide** Läufe fertig wurden; bei 4 × 3 und 5 × 3 fehlen die Buchten, in denen die volle Aufzählung am Limit abbrach, es ist dort also eher zu klein.

| Frage | Befund |
|---|---|
| **Wie wächst die Knotenzahl mit den Blockern?** (3 × 3, 100 Buchten) | Median der Knoten bei 1 / 2 / 3 / 4 / 5 / 6 blockierenden Containern (7 / 12 / 30 / 27 / 20 / 4 Buchten): volle Aufzählung 5 / 23 / 125 / 527 / 1 285 / 2 883, Branch and Bound mit engster Passung 3 / 7 / 17 / 57 / 134 / 128,5. Verhältnisse aufeinanderfolgender Mediane: 4,6 / 5,4 / 4,2 / 2,4 / 2,2 bei der vollen Aufzählung und 2,3 / 2,4 / 3,4 / 2,4 / 1,0 bei Branch and Bound; am stärksten bei den ersten Übergängen (bis 4 Blocker), danach flacher. Die Stufen bestehen aus verschiedenen Buchten (kein Wachstum an einer Bucht); die Stufen mit 1, 5 und 6 Blockern beruhen auf 7, 20 und 4 Buchten, das letzte Verhältnis (1,0) auf 4. |
| **Was geschieht bei 4 × 3?** (40 Buchten) | Die vollen Aufzählungen sind ab 5 Blockern zum Teil über dem Limit: 2 von 6 bei 5, 4 von 8 bei 6, 4 von 4 bei 7 Blockern. Ein Wachstumsverhältnis lässt sich dort nicht angeben (Mediane der Stufen mit 1 bis 11 Buchten, zensiert). Branch and Bound mit engster Passung bleibt in allen 40 Buchten unter dem Limit (Median 654,5 bei 5, 1 337,5 bei 6, 1 912 bei 7 Blockern). |
| **Was bringt die Schranke aus der besten Lösung?** | Das 5,7- bis 202-Fache der Knoten (Median über die Buchten, in denen beide fertig wurden): 5,7 / 6,5 bei 4 × 2 und 3 × 3, 40,3 bei 3 × 4, 53,9 bei 5 × 2, 76,4 bei 4 × 3, 202,4 bei 5 × 3 (nur 5 Buchten); nur bei der kleinsten Zelle (3 × 2, 6 Container) ist es 1,8. Verglichen wird die volle Aufzählung mit Branch and Bound mit engster Passung, also Schranke und gute Reihenfolge zusammen; gegen „schlechteste zuerst“ ist der Gewinn kleiner (4 × 3: Median 3 611,5 gegen 708,5 Knoten). |
| **Was bringt die Reihenfolge der Kinder?** | Im Median wenig: Stapelnummern gegen engste Passung das 1,00- bis 1,62-Fache, schlechteste gegen engste das 1,56- bis 5,11-Fache. Das ist **keine** Größenordnung; nur einzelne Buchten erreichen das 16,9-Fache (5 × 3), 14,9-Fache (4 × 3), 12,6-Fache (5 × 2). |
| **Wo gibt die volle Aufzählung auf?** | Über 1 000 000 Knoten: 0 von 100 bei 3 × 2, 4 × 2 und 3 × 3, 1 von 60 bei 5 × 2, 0 von 40 bei 3 × 4, **10 von 40 bei 4 × 3**, **15 von 20 bei 5 × 3**. Branch and Bound mit engster Passung bleibt in allen Zellen darunter, die Variante „schlechteste zuerst“ gibt bei 5 × 3 in 1 von 20 auf. |
| **Wie wirkt der Platz?** (60 Buchten, Platz 1 / 2 / 3 / 4) | 3 × 3: Median der vollen Aufzählung 71,5 / 217 / 235 / 235, mit engster Passung 17 / 33 / 33 / 33 (Mittel der vollen Aufzählung 207 / 1 093 / 1 889 / 2 003). 4 × 2: Median 40 in allen vier, mit engster Passung 7 (Mittel der vollen Aufzählung 271 / 740 / 819 / 819). Ein Hub mehr Platz erweitert den Baum bis etwa Platz 3 (bei 4 × 2 im Mittel, nicht im Median); ab Platz 3 ändern sich die Mediane nicht mehr (die Mittel bei 3 × 3 noch leicht). |
| **Die Mini-Bucht** | 3 Stapel × 2 Lagen, von unten nach oben (1, 4), (5, 2), (6, 3), Höchsthöhe 4: nur die 4 blockiert (Untergrenze 1). Volle Aufzählung **9 Knoten, 5 Blätter**, Optimum 2: Die 4 landet auf Stapel 2 über der 2 oder auf Stapel 3 über der 3 und blockiert dort wieder. Branch and Bound: Stapelnummern 5 Knoten (1 Blatt), engste Passung 5 (2 Blätter), schlechteste zuerst 7 (3 Blätter). |
| **Das Gegenbeispiel aus Stück 1** | (3, 6), (2, 4), (1, 5): volle Aufzählung **153 Knoten, 77 Blätter**, Optimum 4; Branch and Bound Stapelnummern 47, engste Passung 27, schlechteste zuerst 53. Der erste Tauchgang mit engster Passung hat 5 Hübe: die Regel aus Stück 1. |

**Presets** (Eigenschaften in `tests/test_presets.py`): „Alltag“ (3 × 3, Bucht 12: volle Aufzählung 229 Knoten, Branch and Bound mit engster Passung 29, Optimum 5, Untergrenze 4), „Die Mini-Bucht“ (3 × 2, Bucht 223: 9 Knoten, 5 Blätter, Optimum 2), „Explosion“ (4 × 3, Bucht 3: volle Aufzählung über 500 000 Knoten, engste Passung 1 819, Optimum 8, Untergrenze 6), „Reihenfolge zählt“ (4 × 3, Bucht 31: schlechteste zuerst 1 724 gegen 116 Knoten der engsten Passung).

## Ehrliche Grenzen

- **Ohne Untergrenze, Zustandsmerken und Symmetriebruch.** Das ist die Absicht. Mit ihnen schrumpft der Baum weiter (in einer Vorab-Messung im Median um etwa das 2- bis 10-Fache gegenüber Branch and Bound mit engster Passung); das zeigen die folgenden Stücke, hier ist es nicht gemessen.
- **Knotenlimit statt Zeitlimit.** Knoten pro Sekunde und alle Laufzeiten sind nicht gemessen. Läufe über dem Limit fehlen in den Medianen; sie sind dann nur Untergrenzen der wahren Mediane.
- **Große Zellen mit wenigen Buchten:** 5 × 2 mit 60, 4 × 3 und 3 × 4 mit 40, 5 × 3 mit 20 Buchten. Der Median der Schrankenwirkung bei 5 × 3 beruht auf 5 Buchten.
- **Wachstum je Blocker nur für 3 × 3 belegt;** bei 4 × 3 ist es zensiert. Die Mediane der Stufen stammen aus verschiedenen Buchten, keine Messung an einer Bucht; Stufen mit wenigen Buchten (6 Blocker: 4) sind grob. Aus den Messreihen folgt kein Gesetz.
- **Nur restricted, nur volle Buchten mit gleich hohen Stapeln, Platz 2 in der Tabelle.** Mit anderer Hubmenge (Stück 3) oder anderer Füllung ändern sich die Knotenzahlen.
- **Die Reihenfolge-Aussage gilt für den Median.** Einzelne Buchten reagieren bis zum 16,9-Fachen; eine Garantie für die Reihenfolge gibt es nicht.
- **Zahlen aus Zufallsbuchten:** feste Buchten aus der Zufallsfolge von Python (`random.shuffle`), keine Messung an einem echten Terminal oder Lager; die CI prüft die Zahlen unter Linux.
- **Die Literatur zu Branch and Bound und IDA\* beim Relocation-Problem wurde nicht gelesen;** die Varianten sind hier selbst gebaut.

## Verifikation

- **Kern:** Knoten und Blätter jeder Variante gegen Handzählung an zwei Mini-Buchten (9 und 153 Knoten); der erste Tauchgang mit engster Passung zuerst hat die Hubzahl der Regel aus Stück 1; Knoten von Branch and Bound nie über denen der vollen Aufzählung; Blätter der vollen Aufzählung unabhängig von der Reihenfolge; sortierte Bucht hat genau einen Knoten; das Knotenlimit stoppt genau beim Überschreiten und liefert kein Optimum.
- **Orakel:** das Optimum jeder der sechs Varianten gegen eine **Breitensuche** über alle Zustände (3 × 2 und 4 × 2, 3 × 3); Knoten und Blätter der vollen Aufzählung gegen eine **memoisierte Zählung** über die Zustände auf allen 120 Buchten 3 × 2 und 100 Buchten 4 × 2; die Blattzahl gegen die **Zählung nach Weglänge**; die Knoten von Branch and Bound gegen eine **zweite, iterative Fassung** mit eigenem Stapel für alle drei Reihenfolgen.
- **Zahlen im README:** jede Zahl der Befunde in `tests/test_claims.py` (Tabelle, Wachstum, Platz, Läufe über Limit); kleine Zellen und die 3-×-3-Wachstumstabelle gegen eine frische Rechnung (`tests/test_presets.py`).
- **Verdikte:** reine Funktionen, jede Schwelle (Faktor 2 und 10, Hälfte der Läufe über Limit, das 1,5-Fache beim Platz) und jede genannte Zahl an von Hand gesetzten Werten (`tests/test_verdicts.py`).
- **Presets und Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an Minimum und Maximum), Inhalt (Kennzahlen je Preset, ausgeschriebener Baum, Tabellenzeilen, Permalink), Layout (Schnellstart oben, fester Kopf, aktives Preset hervorgehoben, jede Reglerwirkung), Footer, Laufzeit-Importe.
- **Abbildungen:** Farben je Rolle des Containers, feste Achsen, logarithmische Achsen, Rauten für zensierte Punkte.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Aufbau nach DEMO-PLAYBOOK §2) |
| `generate_precomputed.py` | erzeugt `kex_bands.json` (Tabelle, Wachstum, Platz) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `kex_algorithm.py` | Kern: Tiefensuche mit Knotenzählung (volle Aufzählung, Branch and Bound, drei Reihenfolgen), Baumtext |
| `kex_bands.json` | vorberechnete Kennzahlen der festen Buchten je Zelle |
| `kex_constants.py` | Regler-Grenzen, Knotenlimits, Zellen, Farben, Sonderbuchten, Presets |
| `kex_evaluation.py` | Analyse einer Bucht, Stichproben, Wachstum, Verdikte (reine Funktionen) |
| `kex_layout.py` | Fester Kopf (Stylesheet), Tabellen scrollen im eigenen Rahmen |
| `kex_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `kex_scenario.py` | Buchten (volle Buchten, Zufallsbuchten) |
| `kex_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handrechnung, Orakel, Randfälle, Behauptungen, Verdikte, Presets, Abbildungen, AppTest, Layout, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Untergrenze als Schranke, Zustandsmerken, Symmetriebruch:** die folgenden Stücke der Reihe.
- **Eine Zeitmessung:** nur Knotenzahlen, weil die Rechenzeit je Gerät schwankt.
- **Eine Gesetzmäßigkeit für das Wachstum:** nur Messwerte.
- **Mehr als 100 Buchten je Zelle und größere Zellen:** zu langsam.
- **PDF-Export:** nicht vorgesehen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

98 Tests, rund 145 Sekunden (auf dem Entwicklungsrechner gemessen).

Gebaut mit Streamlit und Plotly.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
