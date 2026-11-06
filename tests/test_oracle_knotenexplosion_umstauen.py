"""Orakel-Test knotenexplosion-umstauen-demo (ORACLE-PLAYBOOK, DEMO-PLAYBOOK §12): Optimum und Knotenzahlen gegen ANDERE Rechenwege.

Orakel 1: Breitensuche über alle Buchtzustände (restricted) liefert das Optimum; jede Variante der Tiefensuche muss es treffen.
Orakel 2: Knoten und Blätter der vollen Aufzählung per **memoisierter Zählung** (nodes(Zustand) = 1 + Summe über die Kinder, Zustände werden gemerkt), dazu die Blattzahl
          per Zählung nach Weglänge. Die Tiefensuche zählt dagegen Aufruf für Aufruf ohne Zustandsmerken.
Orakel 3: Knoten von Branch and Bound mit einer zweiten, **iterativen** Fassung mit eigenem Stapel (gleiche Besuchsreihenfolge, gleiche Regel).
Vorher an den Handzahlen geprüft: Mini-Bucht 9 Knoten und 5 Blätter, Gegenbeispiel 153 und 77."""

from collections import Counter
from itertools import permutations

import kex_algorithm as K
from kex_scenario import canonical, make_bay, max_height

INF = 10 ** 9


def _pop(st):
    st = [list(s) for s in st]
    while True:
        items = [c for s in st for c in s]
        if not items:
            return tuple(tuple(s) for s in st)
        t = min(items)
        hit = [s for s in st if s and s[-1] == t]
        if not hit:
            return tuple(tuple(s) for s in st)
        hit[0].pop()


def own_children(state, height):
    """Kinder eines Knotens (Bucht nach den Abrufen), alle Zielstapel in Stapelreihenfolge, als Liste von Buchten nach dem Hub (noch vor den Abrufen)."""
    items = [c for s in state for c in s]
    t = min(items)
    src = next(i for i, s in enumerate(state) if t in s)
    c = state[src][-1]
    out = []
    for dst in range(len(state)):
        if dst == src or len(state[dst]) >= height:
            continue
        nxt = [list(s) for s in state]
        nxt[src].pop()
        nxt[dst].append(c)
        out.append(tuple(tuple(s) for s in nxt))
    return out


def bfs_optimum(bay, height):
    start = _pop(bay)
    if not any(start):
        return 0
    frontier, seen, depth = {start}, {start}, 0
    while frontier:
        depth += 1
        nxt = set()
        for state in frontier:
            for child in own_children(state, height):
                new = _pop(child)
                if not any(new):
                    return depth
                if new not in seen:
                    seen.add(new)
                    nxt.add(new)
        frontier = nxt
    raise AssertionError("keine Lösung")


def memo_count(bay, height):
    """(Knoten, Blätter) der vollen Aufzählung per memoisierter Zählung über die Zustände."""
    memo = {}

    def rec(state):
        if state in memo:
            return memo[state]
        if not any(state):
            memo[state] = (1, 1)
            return memo[state]
        nodes, leaves = 1, 0
        for child in own_children(state, height):
            n, l = rec(_pop(child))
            nodes += n
            leaves += l
        memo[state] = (nodes, leaves)
        return memo[state]

    return rec(_pop(bay))


def leaf_lengths(bay, height):
    """Zahl der Hubfolgen je Länge (Zählung nach Weglänge, ohne Zustandsmerken)."""
    out = Counter()

    def rec(state, g):
        if not any(state):
            out[g] += 1
            return
        for child in own_children(state, height):
            rec(_pop(child), g + 1)

    rec(_pop(bay), 0)
    return out


def iterative_branch_and_bound(bay, height, order):
    """Branch and Bound mit eigenem Stapel statt Rekursion; Kinder in der Reihenfolge `order` (aus den Regeln der Beschreibung, nicht aus dem Kern)."""
    def ordered(state):
        t = min(c for s in state for c in s)
        src = next(i for i, s in enumerate(state) if t in s)
        c = state[src][-1]
        base = [list(s) for s in state]
        base[src].pop()
        dests = [j for j in range(len(state)) if j != src and len(state[j]) < height]
        if order == "index":
            return src, c, dests

        def key(j):
            m = min(base[j]) if base[j] else INF
            return (0, m) if m > c else (1, -m)
        dests.sort(key=lambda j: (key(j), j))
        return src, c, (dests[::-1] if order == "anti" else dests)

    best, nodes, first = INF, 0, None
    stack = [(_pop(bay), 0, None, None)]                               # (Knoten, Hübe, noch nicht abgearbeitete Kinder, Kontext)
    while stack:
        state, g, kids, ctx = stack.pop()
        if kids is None:                                                # Knoten wird zum ersten Mal besucht
            nodes += 1
            if not any(state):
                first = g if first is None else first
                best = min(best, g)
                continue
            if g + 1 >= best:
                continue
            src, c, dests = ordered(state)
            kids, ctx = list(dests), (src, c)
        if not kids:
            continue
        j = kids.pop(0)
        stack.append((state, g, kids, ctx))
        src, c = ctx
        nxt = [list(s) for s in state]
        nxt[src].pop()
        nxt[j].append(c)
        stack.append((_pop(tuple(tuple(s) for s in nxt)), g + 1, None, None))
    return best, nodes, first


def all_bays_3x2():
    seen = {}
    for perm in permutations(range(1, 7)):
        bay = tuple(tuple(perm[i * 2:(i + 1) * 2]) for i in range(3))
        seen.setdefault(canonical(bay), bay)
    return list(seen.values())


def test_oracle_on_the_hand_numbers(mini, counter):
    assert memo_count(*mini) == (9, 5) and bfs_optimum(*mini) == 2
    assert memo_count(*counter) == (153, 77) and bfs_optimum(*counter) == 4
    assert leaf_lengths(*mini) == Counter({2: 3, 3: 2})                # drei Folgen mit 2 und zwei mit 3 Hüben (von Hand: Blätter 3, 8, 9 und 5, 6)


def test_every_variant_finds_the_optimum_of_the_breadth_first_search():
    for stacks, layers, seeds in ((3, 2, 100), (4, 2, 60), (3, 3, 40)):
        h = max_height(layers, 2)
        for sd in range(seeds):
            bay = make_bay(stacks, layers, sd)
            opt = bfs_optimum(bay, h)
            for prune in K.PRUNES:
                for order in K.ORDERS:
                    r = K.search(bay, h, prune, order)
                    assert (r.optimum, r.capped) == (opt, False), (stacks, layers, sd, prune, order)


def test_full_enumeration_matches_the_memoised_count_on_all_3x2_and_many_4x2_bays():
    h = max_height(2, 2)
    for bay in all_bays_3x2():
        r = K.search(bay, h, "none", "index")
        assert (r.nodes, r.leaves) == memo_count(bay, h), bay
    for sd in range(100):
        bay = make_bay(4, 2, sd)
        r = K.search(bay, max_height(2, 2), "none", "tight")
        assert (r.nodes, r.leaves) == memo_count(bay, max_height(2, 2)), sd


def test_leaves_equal_the_number_of_sequences_by_length_and_the_shortest_is_the_optimum():
    h = max_height(2, 2)
    for bay in all_bays_3x2():
        lengths = leaf_lengths(bay, h)
        r = K.search(bay, h, "none", "index")
        assert sum(lengths.values()) == r.leaves and min(lengths) == r.optimum, bay


def test_branch_and_bound_matches_an_iterative_second_implementation():
    for stacks, layers, seeds in ((3, 2, 120), (4, 2, 60), (3, 3, 40)):
        h = max_height(layers, 2)
        bays = all_bays_3x2() if (stacks, layers) == (3, 2) else [make_bay(stacks, layers, sd) for sd in range(seeds)]
        for bay in bays:
            for order in K.ORDERS:
                r = K.search(bay, h, "best", order)
                assert (r.optimum, r.nodes, r.first_leaf) == iterative_branch_and_bound(bay, h, order), (stacks, layers, bay, order)
