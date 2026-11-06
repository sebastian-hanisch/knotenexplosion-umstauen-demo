"""Abbildungen: Farben je Rolle des Containers, feste Achsen, logarithmische Achsen, Zahlen der Kurven."""

import kex_algorithm as K
import kex_constants as C
import kex_evaluation as ev
import kex_visualization as V


def _cell_colors(fig):
    out = {}
    for tr in fig.data:
        for txt, color in zip(tr.text, tr.marker.color):
            if txt:
                out[int(txt)] = color
    return out


def test_bay_colours_by_role(mini):
    bay, h = mini
    cols = _cell_colors(V.build_bay(bay, h, target=1))
    assert cols[1] == C.COLOR_TARGET and cols[4] == C.COLOR_BLOCK and cols[5] == cols[2] == cols[6] == cols[3] == C.COLOR_CELL
    assert sorted(_cell_colors(V.build_bay(bay, h))) == [1, 2, 3, 4, 5, 6] and len(V.build_bay(bay, h).data) == h


def test_blocker_cells_agree_with_the_kernel():
    from kex_scenario import make_bay
    assert V.blocker_cells(((1, 4), (5, 2), (6, 3))) == {(0, 1)}
    for sd in range(20):
        bay = make_bay(4, 3, sd)
        assert len(V.blocker_cells(bay)) == K.blocker_count(bay)


def _a():
    return ev.analyse(ev.Settings(3, 2, 2, C.MINI_SEED))


def test_axes_are_locked_in_every_figure():
    a = _a()
    bands = ev.load_bands()
    tab = {k: v for k, v in bands["tabelle"].items() if v["bound"]["median"] is not None}
    figs = [V.build_bay(a.bay, a.height), V.build_nodes(ev.result_rows(a)), V.build_growth({k: v for k, v in bands["wachstum"].items()}), V.build_ratios(tab),
            V.build_space({"3 × 3": ev.space_points(bands, 3, 3)}), V.build_over_limit(bands["tabelle"])]
    for fig in figs:
        assert fig.layout.xaxis.fixedrange is True and fig.layout.yaxis.fixedrange is True


def test_nodes_figure_marks_capped_runs_and_uses_a_log_axis():
    rows = [{"variant": ("none", "index"), "nodes": 500_000, "capped": True, "nodes_text": "mehr als 500 000"},
            {"variant": ("best", "tight"), "nodes": 1819, "capped": False, "nodes_text": "1 819"}]
    fig = V.build_nodes(rows)
    assert fig.layout.yaxis.type == "log" and list(fig.data[0].y) == [500_000, 1819] and list(fig.data[0].text) == ["mehr als 500 000", "1 819"]
    assert list(fig.data[0].marker.color) == [C.COLOR_CAPPED, C.COLOR_VARIANT[("best", "tight")]]


def test_growth_figure_uses_diamonds_for_censored_points():
    table = {"1": {"n": 5, "none": {"ok": 5, "over": 0, "median": 5, "mean": 5, "max": 5}, "tight": {"ok": 5, "over": 0, "median": 3, "mean": 3, "max": 3}},
             "2": {"n": 5, "none": {"ok": 2, "over": 3, "median": 80, "mean": 80, "max": 90}, "tight": {"ok": 5, "over": 0, "median": 9, "mean": 9, "max": 9}}}
    fig = V.build_growth({"4 × 3": table})
    assert [t.name for t in fig.data] == ["4 × 3, volle Aufzählung", "4 × 3, Branch and Bound, engste Passung"] and fig.layout.yaxis.type == "log"
    assert list(fig.data[0].marker.symbol) == ["circle", "diamond"] and list(fig.data[1].marker.symbol) == ["circle", "circle"]


def test_ratio_and_over_limit_figures_have_three_and_two_series():
    bands = ev.load_bands()
    tab = {k: v for k, v in bands["tabelle"].items() if v["bound"]["median"] is not None}
    assert len(V.build_ratios(tab).data) == 3 and V.build_ratios(tab).layout.yaxis.type == "log"
    fig = V.build_over_limit(bands["tabelle"])
    assert len(fig.data) == 2 and list(fig.layout.yaxis.range) == [0, 100]
