"""Randfälle, an denen Kernroutinen erfahrungsgemäß brechen (DEMO-PLAYBOOK §12)."""

import kex_algorithm as K
import kex_evaluation as ev


def test_two_stacks_one_hub():
    for prune in K.PRUNES:
        for order in K.ORDERS:
            r = K.search(((1, 2), ()), 3, prune, order)
            assert (r.optimum, r.nodes, r.leaves) == (1, 2, 1)         # Wurzel, ein Hub auf den leeren Stapel, Blatt


def test_single_container_and_empty_bay():
    assert K.search(((1,), ()), 2, "none", "index").nodes == 1
    assert K.search(((), ()), 2, "best", "tight").optimum == 0


def test_exactly_two_containers_in_each_order():
    assert K.search(((2,), (1,)), 2, "none", "index").optimum == 0
    assert K.search(((2, 1),), 2, "none", "index").optimum == 0
    assert K.search(((1, 2), ()), 2, "none", "index").optimum == 1


def test_only_one_free_slot_leaves_exactly_one_child_per_hub():
    r = K.search(((1, 5), (2, 3), (4, 6)), 3, "none", "index")          # Höchsthöhe 3: jeder Blocker findet höchstens einen freien Platz
    assert r.optimum is not None and r.leaves >= 1


def test_capped_result_never_claims_an_optimum_and_the_bay_analysis_says_so(counter):
    bay, h = counter
    r = K.search(bay, h, "none", "index", cap=10)
    assert r.optimum is None and r.capped and r.leaves <= 10
    capped = K.SearchResult(None, 10, 2, True, None)
    a = ev.Analysis(bay, h, 3, {v: capped for v in ev.C.VARIANTS})
    assert a.optimum is None


def test_num_and_factor_text():
    assert ev.num(5) == "5" and ev.num(1234) == "1 234" and ev.num(1_000_000) == "1 000 000"
    assert ev.factor_text(1.0) == "1,0" and ev.factor_text(9.94) == "9,9" and ev.factor_text(10.0) == "10" and ev.factor_text(47.4) == "47"


def test_cell_stats_with_all_runs_over_the_limit_has_no_medians():
    rows = [{"seed": 0, "lb": 5, "none/index": None, "best/index": None, "best/tight": None, "best/anti": None}]
    st = ev.cell_stats(rows)
    assert st["variants"]["none/index"] == {"ok": 0, "over": 1, "median": None, "mean": None, "max": None}
    assert st["bound"]["median"] is None and st["anti_tight"]["median"] is None and st["index_tight"]["n"] == 0
