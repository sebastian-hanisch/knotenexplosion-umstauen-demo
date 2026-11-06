"""Kern gegen Handrechnung und Eigenschaften (DEMO-PLAYBOOK §1b und §12)."""

import pytest

import kex_algorithm as K
from kex_scenario import make_bay, max_height


def test_autopop_and_blockers_by_hand(mini):
    bay, _ = mini
    assert K.autopop(bay) == (bay, [])                                 # die 1 liegt unter der 4
    assert K.autopop(((2, 1), (3,))) == (((), ()), [1, 2, 3])
    assert K.blocker_count(bay) == 1 and K.stack_blockers((1, 2, 3)) == 2 and K.stack_blockers((3, 2, 1)) == 0
    assert K.target_stack(bay) == (1, 0) and K.target_stack(((5, 3), (2, 1))) == (1, 1)


def test_mini_bay_by_hand_in_every_variant(mini):
    bay, h = mini
    expected = {("none", "index"): (9, 5), ("none", "tight"): (9, 5), ("none", "anti"): (9, 5),
                ("best", "index"): (5, 1), ("best", "tight"): (5, 2), ("best", "anti"): (7, 3)}
    for (prune, order), (nodes, leaves) in expected.items():
        r = K.search(bay, h, prune, order)
        assert (r.optimum, r.nodes, r.leaves, r.capped) == (2, nodes, leaves, False), (prune, order)


def test_counterexample_by_hand_in_every_variant(counter):
    bay, h = counter
    expected = {("none", "index"): (153, 77), ("none", "tight"): (153, 77), ("none", "anti"): (153, 77),
                ("best", "index"): (47, 7), ("best", "tight"): (27, 3), ("best", "anti"): (53, 8)}
    for (prune, order), (nodes, leaves) in expected.items():
        r = K.search(bay, h, prune, order)
        assert (r.optimum, r.nodes, r.leaves) == (4, nodes, leaves), (prune, order)
    assert K.search(bay, h, "best", "tight").first_leaf == 5            # der erste Tauchgang ist die engste Passung aus Stück 1 (5 Hübe)


def test_first_dive_of_tight_first_equals_the_tight_fit_rule():
    for sd in range(40):
        bay, h = make_bay(3, 3, sd), max_height(3, 2)
        st, hubs = K.autopop(bay)[0], 0
        cur = st
        while any(cur):                                                # Regel aus Stück 1 nachgebaut: engste Passung für jeden Blocker
            _, i = K.target_stack(cur)
            lst = [list(s) for s in cur]
            c = lst[i].pop()
            base = tuple(tuple(s) for s in lst)
            j = K.child_targets(base, i, h, c, "tight")[0]
            lst[j].append(c)
            hubs += 1
            cur, _ = K.autopop(tuple(tuple(s) for s in lst))
        assert K.search(bay, h, "best", "tight").first_leaf == hubs, sd


def test_child_targets_orders_by_hand():
    stacks = ((7,), (5, 8), (9,), ())                                  # Blocker 3 kommt von Stapel 1 (Index 0), die übergebene Bucht ist die ohne ihn
    assert K.child_targets(stacks, 0, 6, 3, "index") == [1, 2, 3]
    assert K.child_targets(stacks, 0, 6, 3, "tight") == [1, 2, 3]      # kleinster früher Abruf über 3 ist 5 (Stapel 2), dann 9 (Stapel 3), dann der leere
    assert K.child_targets(stacks, 0, 6, 3, "anti") == [3, 2, 1]
    assert K.child_targets(((7,), (2, 8), (1,), (4,)), 0, 6, 9, "tight") == [3, 1, 2]   # alle blockieren: größter frühester Abruf zuerst: 4, 2, 1
    assert K.child_targets(((1, 2), (3, 4), (5,)), 0, 2, 9, "index") == [2]             # Höchsthöhe 2: nur Stapel 3 hat Platz


def test_nodes_never_increase_with_branch_and_bound_and_leaves_do_not_depend_on_the_order():
    for sd in range(40):
        bay, h = make_bay(3, 3, sd), max_height(3, 2)
        none = {o: K.search(bay, h, "none", o) for o in K.ORDERS}
        assert len({r.nodes for r in none.values()}) == 1 and len({r.leaves for r in none.values()}) == 1, sd
        for o in K.ORDERS:
            best = K.search(bay, h, "best", o)
            assert best.nodes <= none[o].nodes and best.optimum == none[o].optimum, (sd, o)


def test_sorted_bay_has_exactly_one_node_and_one_leaf():
    for prune in K.PRUNES:
        r = K.search(((5, 3), (2, 1), (6, 4)), 4, prune, "tight")
        assert (r.optimum, r.nodes, r.leaves) == (0, 1, 1)


def test_cap_stops_the_search_and_reports_no_optimum(counter):
    bay, h = counter
    r = K.search(bay, h, "none", "index", cap=100)
    assert r.capped and r.optimum is None and r.nodes == 100
    ok = K.search(bay, h, "none", "index", cap=153)
    assert not ok.capped and ok.nodes == 153 and ok.optimum == 4
    assert K.search(bay, h, "none", "index", cap=152).capped            # genau ein Knoten zu wenig


def test_unknown_options_are_rejected(mini):
    with pytest.raises(ValueError):
        K.search(*mini, "x", "tight")
    with pytest.raises(ValueError):
        K.search(*mini, "best", "x")
    with pytest.raises(ValueError):
        K.child_targets(((1,), ()), 0, 3, 2, "x")


def test_tree_lines_of_the_mini_bay(mini):
    lines = K.tree_lines(*mini)
    assert lines[0] == "Knoten 1: (1, 4) | (5, 2) | (6, 3) nach 0 Hüben"
    assert lines[1] == "→ Container 4 von Stapel 1 auf Stapel 2"
    assert lines[2] == "    Knoten 2: () | (5, 2, 4) | (6, 3) nach 1 Hub, abgerufen 1"
    assert lines[4] == "        Knoten 3: () | () | () nach 2 Hüben, abgerufen 2, 3, 4, 5, 6 – Blatt (leer)"
    assert sum(1 for l in lines if l.lstrip().startswith("Knoten ")) == 9 and sum(1 for l in lines if l.endswith("Blatt (leer)")) == 5
    assert sum(1 for l in lines if l.lstrip().startswith("→")) == 8     # jeder Knoten außer der Wurzel hängt an genau einem Hub


def test_tree_lines_refuses_big_trees(counter):
    with pytest.raises(ValueError):
        K.tree_lines(*counter, max_nodes=100)                          # der Baum hat 153 Knoten
    assert len(K.tree_lines(*counter, max_nodes=153)) > 153
