"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Eigenschaften der Sonderbuchten und der vorberechneten Kurven."""

import pytest

import kex_algorithm as K
import kex_constants as C
import kex_evaluation as ev
import kex_presets as P
from kex_scenario import canonical, make_bay, max_height


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_slider_bounds():
    for preset in C.PRESETS.values():
        assert C.STACKS_MIN <= preset["stacks"] <= C.STACKS_MAX and C.LAYERS_MIN <= preset["layers"] <= C.LAYERS_MAX
        assert C.EXTRA_MIN <= preset["extra"] <= C.EXTRA_MAX and 0 <= preset["seed"] <= C.SEED_MAX


def test_default_preset_equals_the_default_settings():
    p = C.PRESETS[next(iter(C.PRESETS))]
    assert ev.Settings(p["stacks"], p["layers"], p["extra"], p["seed"]) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def _analysis(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(p["stacks"], p["layers"], p["extra"], p["seed"]))


def _nodes(a):
    return {v: a.res(v).nodes for v in C.VARIANTS}


def test_everyday_preset():
    a = _analysis("Alltag (3 Stapel, 3 Lagen)")
    n = _nodes(a)
    assert (a.lower, a.optimum) == (4, 5) and n[("none", "index")] == 229 and n[("best", "tight")] == 29 and not any(r.capped for r in a.results.values())


def test_mini_preset_is_the_stage_two_bay_with_nine_nodes():
    p = C.PRESETS["Die Mini-Bucht"]
    assert canonical(make_bay(p["stacks"], p["layers"], p["seed"])) == canonical(C.MINI_BAY)
    a = _analysis("Die Mini-Bucht")
    assert (a.lower, a.optimum) == (1, 2) and a.res(("none", "index")).nodes == 9 and a.res(("none", "index")).leaves == 5


def test_explosion_preset_breaks_the_full_enumeration_but_not_the_branch_and_bound():
    a = _analysis("Explosion (4 Stapel, 3 Lagen)")
    assert a.res(("none", "index")).capped and a.res(("none", "index")).nodes == C.LIVE_CAP
    assert not a.res(("best", "tight")).capped and a.res(("best", "tight")).nodes == 1819 and a.optimum == 8 and a.lower == 6


def test_order_preset_has_a_large_ratio_between_worst_and_best_order():
    a = _analysis("Reihenfolge zählt (4 Stapel, 3 Lagen)")
    anti, tight = a.res(("best", "anti")).nodes, a.res(("best", "tight")).nodes
    assert (anti, tight) == (1724, 116) and anti / tight > 14 and not a.res(("none", "index")).capped


@pytest.mark.parametrize("cell", [(3, 2, 100), (4, 2, 100)])
def test_stored_table_cells_equal_a_fresh_computation(cell):
    stacks, layers, n = cell
    stored = ev.load_bands()["tabelle"][ev.cell_key(stacks, layers)]
    assert stored == ev.cell_stats(ev.cell_rows(stacks, layers, C.DEFAULT_EXTRA, range(n)))


def test_stored_3x3_table_and_growth_equal_a_fresh_computation():
    rows = ev.cell_rows(3, 3, C.DEFAULT_EXTRA, range(100))
    bands = ev.load_bands()
    assert bands["tabelle"][ev.cell_key(3, 3)] == ev.cell_stats(rows)
    assert bands["wachstum"][ev.cell_key(3, 3)] == ev.blocker_table(rows)


def test_stored_space_cell_equals_a_fresh_computation():
    assert ev.load_bands()["platz"][ev.space_key(4, 2, 1)] == ev.cell_stats(ev.cell_rows(4, 2, 1, range(60)))


def test_every_band_cell_exists():
    bands = ev.load_bands()
    assert set(bands["tabelle"]) == {ev.cell_key(s, l) for s, l, _ in C.TABLE_CELLS}
    assert set(bands["wachstum"]) == {ev.cell_key(s, l) for s, l in C.GROWTH_CELLS}
    assert set(bands["platz"]) == {ev.space_key(s, l, e) for s, l, _ in C.SPACE_CELLS for e in range(C.EXTRA_MIN, C.EXTRA_MAX + 1)}
    assert all(bands["tabelle"][ev.cell_key(s, l)]["n"] == n for s, l, n in C.TABLE_CELLS)


def test_cell_rows_use_the_fixed_seeds_and_cap():
    rows = ev.cell_rows(3, 2, 2, range(10))
    assert [r["seed"] for r in rows] == list(range(10))
    for r in rows:
        bay = make_bay(3, 2, r["seed"])
        assert r["lb"] == K.blocker_count(bay) and r["none/index"] == K.search(bay, max_height(2, 2), "none", "index").nodes
    small = ev.cell_rows(4, 3, 2, [3], cap=1000)                          # Bucht 3 bei 4 x 3 gibt die volle Aufzählung weit unter einer Million Knoten nicht her
    assert small[0]["none/index"] is None


def test_the_curves_follow_their_orders():
    bands = ev.load_bands()
    assert [p["extra"] for p in ev.space_points(bands, 3, 3)] == [1, 2, 3, 4]
