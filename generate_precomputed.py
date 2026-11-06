"""Erzeugt kex_bands.json: Knotenzahlen der festen Buchten (Seeds ab 0) für drei Auswertungen.

    python generate_precomputed.py

"tabelle": je Zelle (Stapel, Lagen) Kennzahlen der vier Varianten (kex_constants.TABLE_CELLS; große Zellen mit weniger Buchten).
"wachstum": Median der Knoten je Zahl der blockierenden Container (aus denselben Buchten wie die Tabelle) für 3 x 3 und 4 x 3.
"platz": Platz 1 bis 4 für 3 x 3 und 4 x 2 (60 Buchten).

Rechenzeit rund zehn bis fünfzehn Minuten (Knotenlimit 1 000 000 je Lauf; 4 x 3 und 5 x 3 sind die teuren Zellen). Dieselben Funktionen wie die Tests
(`kex_evaluation.cell_rows`, `cell_stats`, `blocker_table`); die Datei speichert nur Kennzahlen, keine Zeilen. tests/test_presets.py rechnet kleine Zellen neu
und vergleicht."""

import json
import sys

import kex_constants as C
import kex_evaluation as ev

sys.stdout.reconfigure(encoding="utf-8")


def main():
    bands = {"tabelle": {}, "wachstum": {}, "platz": {}}
    for stacks, layers, n in C.TABLE_CELLS:
        rows = ev.cell_rows(stacks, layers, C.DEFAULT_EXTRA, range(n))
        bands["tabelle"][ev.cell_key(stacks, layers)] = ev.cell_stats(rows)
        if (stacks, layers) in C.GROWTH_CELLS:
            bands["wachstum"][ev.cell_key(stacks, layers)] = ev.blocker_table(rows)
        print(f"{stacks} Stapel x {layers} Lagen ({n} Buchten): fertig", flush=True)
    for stacks, layers, n in C.SPACE_CELLS:
        for extra in range(C.EXTRA_MIN, C.EXTRA_MAX + 1):
            bands["platz"][ev.space_key(stacks, layers, extra)] = ev.cell_stats(ev.cell_rows(stacks, layers, extra, range(n)))
            print(f"Platz {stacks} x {layers}, Platz {extra}: fertig", flush=True)
    ev.BANDS_FILE.write_text(json.dumps(bands, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("geschrieben:", ev.BANDS_FILE.name)


if __name__ == "__main__":
    main()
