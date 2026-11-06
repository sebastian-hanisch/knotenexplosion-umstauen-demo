"""JEDE Zahl aus dem README wird hier nachgerechnet (DEMO-PLAYBOOK §4): über die vorberechneten Kurven (kex_bands.json, gegen eine frische Rechnung geprüft in
test_presets.py für die kleinen Zellen) und die Auswertungsfunktionen der App, über die festen Buchten je Zelle, nie über eine einzelne Bucht."""

import pytest

import kex_constants as C
import kex_evaluation as ev

BANDS = ev.load_bands()

# Zelle -> (Buchten, {Variante: (Median, Mittel, Maximum, Läufe über Limit)}, Stapelnummern/engste (Median), schlechteste/engste (Median, Maximum), volle Aufzählung/engste (Median, Buchten))
TABELLE = {
    (3, 2): (100, {"none/index": (9, 20, 161, 0), "best/index": (5, 8, 47, 0), "best/tight": (5, 6, 27, 0), "best/anti": (7, 10, 53, 0)}, 1.00, 1.56, 3.4, 1.8, 100),
    (4, 2): (100, {"none/index": (67, 713, 20867, 0), "best/index": (13, 28, 261, 0), "best/tight": (7, 16, 117, 0), "best/anti": (23.5, 52, 513, 0)}, 1.43, 2.50, 6.6, 5.7, 100),
    (3, 3): (100, {"none/index": (230, 1403, 13427, 0), "best/index": (48, 92, 427, 0), "best/tight": (33, 68, 419, 0), "best/anti": (65, 146, 845, 0)}, 1.25, 2.11, 4.9, 6.5, 100),
    (5, 2): (60, {"none/index": (1721, 25019, 654257, 1), "best/index": (37, 125, 1420, 0), "best/tight": (25, 80, 1268, 0), "best/anti": (107, 340, 4210, 0)}, 1.43, 3.56, 12.6, 53.9, 59),
    (3, 4): (40, {"none/index": (18163.5, 82533, 696375, 0), "best/index": (491, 893, 3801, 0), "best/tight": (384, 625, 3665, 0), "best/anti": (1027.5, 1463, 5637, 0)}, 1.28, 2.17, 9.1, 40.3, 40),
    (4, 3): (40, {"none/index": (3611.5, 108841, 612886, 10), "best/index": (320, 2331, 41082, 0), "best/tight": (120, 1221, 15455, 0), "best/anti": (708.5, 3751, 47161, 0)}, 1.62, 3.48, 14.9, 76.4, 30),
    (5, 3): (20, {"none/index": (12693, 212067, 800161, 15), "best/index": (3933, 52338, 451905, 0), "best/tight": (1361, 32211, 253266, 0), "best/anti": (13998, 96179, 669879, 1)}, 1.41, 5.11, 16.9, 202.4, 5),
}


@pytest.mark.parametrize("cell", list(TABELLE))
def test_readme_table_cell(cell):
    n, variants, idx, anti, anti_max, bound, bound_n = TABELLE[cell]
    st = BANDS["tabelle"][ev.cell_key(*cell)]
    assert st["n"] == n
    for key, (med, mean, mx, over) in variants.items():
        v = st["variants"][key]
        assert (v["median"], round(v["mean"]), v["max"], v["over"]) == (med, mean, mx, over), key
    assert round(st["index_tight"]["median"], 2) == idx and round(st["anti_tight"]["median"], 2) == anti and round(st["anti_tight"]["max"], 1) == anti_max
    assert round(st["bound"]["median"], 1) == bound and st["bound"]["n"] == bound_n


def test_the_table_cells_are_the_documented_ones():
    assert [(s, l, n) for s, l, n in C.TABLE_CELLS] == [(s, l, TABELLE[(s, l)][0]) for s, l, _ in C.TABLE_CELLS]
    assert {(s, l) for s, l, _ in C.TABLE_CELLS} == set(TABELLE)


def test_the_bound_helps_far_more_than_the_order_in_every_cell_but_the_smallest():
    for cell, (n, variants, idx, anti, anti_max, bound, bound_n) in TABELLE.items():
        if cell == (3, 2):
            continue                                                       # 6 Container: der Baum ist so klein, dass die Schranke kaum etwas spart
        assert bound > anti and anti > idx >= 1.0, cell
    assert TABELLE[(3, 2)][5] < C.BOUND_WEAK


def test_the_order_effect_stays_small_in_the_median_but_not_in_the_extremes():
    meds = [v[3] for v in TABELLE.values()]
    assert max(v[2] for v in TABELLE.values()) < 1.7 and max(meds) < 5.2 and min(meds) > 1.5
    assert max(v[4] for v in TABELLE.values()) == 16.9


def test_runs_over_the_limit_per_cell():
    over = {cell: BANDS["tabelle"][ev.cell_key(*cell)]["variants"]["none/index"]["over"] for cell in TABELLE}
    assert over == {(3, 2): 0, (4, 2): 0, (3, 3): 0, (5, 2): 1, (3, 4): 0, (4, 3): 10, (5, 3): 15}
    assert all(BANDS["tabelle"][ev.cell_key(*c)]["variants"]["best/tight"]["over"] == 0 for c in TABELLE)
    assert BANDS["tabelle"][ev.cell_key(5, 3)]["variants"]["best/anti"]["over"] == 1


def test_readme_growth_table_3x3():
    t = BANDS["wachstum"]["3,3"]
    assert {lb: (r["n"], r["none"]["median"], r["tight"]["median"]) for lb, r in t.items()} == {
        "1": (7, 5, 3), "2": (12, 23, 7), "3": (30, 125, 17), "4": (27, 527, 57), "5": (20, 1285, 134), "6": (4, 2883, 128.5)}
    assert [round(x, 1) for x in ev.growth_factors(t, "none")] == [4.6, 5.4, 4.2, 2.4, 2.2]
    assert [round(x, 1) for x in ev.growth_factors(t, "tight")] == [2.3, 2.4, 3.4, 2.4, 1.0]
    assert ev.half_over_from(t, "none") is None


def test_readme_growth_table_4x3_is_censored_from_five_blockers():
    t = BANDS["wachstum"]["4,3"]
    assert {lb: (r["n"], r["none"]["median"], r["none"]["over"]) for lb, r in t.items()} == {
        "1": (1, 829, 0), "2": (4, 329.5, 0), "3": (6, 2626, 0), "4": (11, 3016, 0), "5": (6, 53753, 2), "6": (8, 525188.5, 4), "7": (4, None, 4)}
    assert [round(r["tight"]["median"], 1) for r in t.values()] == [16.0, 16.0, 43.0, 43.0, 654.5, 1337.5, 1912.0]
    assert ev.half_over_from(t, "none") == 6 and all(r["tight"]["over"] == 0 for r in t.values())


def test_readme_space_table():
    expected = {(3, 3): ([71.5, 217, 235, 235], [17, 33, 33, 33]), (4, 2): ([40, 40, 40, 40], [7, 7, 7, 7])}
    for (s, l), (none, tight) in expected.items():
        pts = ev.space_points(BANDS, s, l)
        assert [p["none"] for p in pts] == none and [p["tight"] for p in pts] == tight and all(p["n"] == 60 for p in pts)
    assert [round(BANDS["platz"][ev.space_key(4, 2, e)]["variants"]["none/index"]["mean"]) for e in (1, 2, 3, 4)] == [271, 740, 819, 819]
    assert [round(BANDS["platz"][ev.space_key(3, 3, e)]["variants"]["none/index"]["mean"]) for e in (1, 2, 3, 4)] == [207, 1093, 1889, 2003]


def test_the_medians_do_not_change_beyond_space_three():
    for s, l, _ in C.SPACE_CELLS:
        a, b = BANDS["platz"][ev.space_key(s, l, 3)], BANDS["platz"][ev.space_key(s, l, 4)]
        for key in ("none/index", "best/tight", "best/index"):
            assert a["variants"][key]["median"] == b["variants"][key]["median"], (s, l, key)
    # die Mittel der vollen Aufzählung ändern sich bei 3 x 3 noch leicht (ein weiterer freier Platz erlaubt wenige zusätzliche Wege), bei 4 x 2 nicht
    assert BANDS["platz"][ev.space_key(4, 2, 3)]["variants"]["none/index"] == BANDS["platz"][ev.space_key(4, 2, 4)]["variants"]["none/index"]
    assert BANDS["platz"][ev.space_key(3, 3, 3)]["variants"]["none/index"]["mean"] != BANDS["platz"][ev.space_key(3, 3, 4)]["variants"]["none/index"]["mean"]
