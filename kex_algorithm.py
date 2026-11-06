"""Kern: Tiefensuche über alle Hubfolgen beim Umstauen (restricted), mit Knotenzählung.

Eine Bucht besteht aus Stapeln (Tupel von unten nach oben). Die Abrufnummer 1 kommt zuerst dran; nur der oberste Container eines Stapels ist erreichbar.
Liegt die nächste Nummer nicht oben, wird der oberste Container ihres Stapels (ein Blocker) auf einen anderen Stapel mit Platz gesetzt, jeder Hub kostet 1;
die nächste Nummer wird kostenlos entnommen, sobald sie oben liegt (restricted: nur Container über dem gesuchten werden bewegt).

Suchbaum: Ein **Knoten** ist eine Bucht nach den kostenlosen Abrufen (mit den bisherigen Hüben), seine **Kinder** entstehen, indem der Blocker auf jeden anderen
Stapel mit Platz gesetzt wird. Ein **Blatt** ist eine leere Bucht; ein Weg von der Wurzel zu einem Blatt ist eine Hubfolge, seine Länge die Hubzahl.
Kein Zustandsmerken, kein Symmetriebruch, keine Untergrenze: gleiche Zustände zählen mehrfach.

  search          Tiefensuche mit Knoten- und Blattzählung: prune "none" (volle Aufzählung) oder "best" (Branch and Bound: Abbruch, sobald die bisherigen
                  Hübe plus 1 nicht mehr unter der besten bisher gefundenen Lösung liegen); order "index" (Stapelnummern), "tight" (engste Passung zuerst),
                  "anti" (schlechteste zuerst). Knotenlimit: Überschreitung gibt capped=True und kein Optimum.
  tree_lines      der ausgeschriebene Baum der vollen Aufzählung für kleine Buchten
  autopop, blocker_count, target_stack   Abruf und Untergrenze (aus Stück 2 kopiert)
"""

from dataclasses import dataclass

INF = 10 ** 9
PRUNES = ("none", "best")
ORDERS = ("index", "tight", "anti")
VARIANTS = (("none", "index"), ("best", "index"), ("best", "tight"), ("best", "anti"))


def autopop(stacks):
    """Ruft ab, was oben liegt und gerade dran ist. Gibt (neue Stapel, abgerufene Nummern in Reihenfolge) zurück."""
    st = [list(s) for s in stacks]
    popped = []
    while True:
        present = [c for s in st for c in s]
        if not present:
            return tuple(tuple(s) for s in st), popped
        t = min(present)
        for s in st:
            if s and s[-1] == t:
                s.pop()
                popped.append(t)
                break
        else:
            return tuple(tuple(s) for s in st), popped


def stack_blockers(stack):
    """Container in einem Stapel (unten nach oben), die über einem früher abzurufenden liegen."""
    total, lowest = 0, INF
    for c in stack:
        if c > lowest:
            total += 1
        else:
            lowest = c
    return total


def blocker_count(stacks):
    """Zahl der blockierenden Container (Untergrenze der Hubzahl, Stück 2)."""
    return sum(stack_blockers(s) for s in stacks)


def target_stack(stacks):
    """(nächste Abrufnummer, Index ihres Stapels). Die Bucht darf nicht leer sein."""
    t = min(c for s in stacks for c in s)
    for i, s in enumerate(stacks):
        if t in s:
            return t, i


def _fit_key(stacks, j, c):
    """Sortierschlüssel der engsten Passung für den Zielstapel j: Stapel, auf denen c nichts blockiert, zuerst (kleinster frühester Abruf zuerst, leerer Stapel zuletzt
    unter ihnen), danach die übrigen nach größtem frühesten Abruf."""
    m = min(stacks[j]) if stacks[j] else INF
    return (0, m) if m > c else (1, -m)


def child_targets(stacks, src, height, c, order):
    """Zielstapel für den Blocker c (Stapel `src`, Bucht ohne c) in der Reihenfolge `order`; nur Stapel mit Platz, gleiche Stapel werden NICHT zusammengefasst."""
    if order not in ORDERS:
        raise ValueError(f"unbekannte Reihenfolge {order!r}")
    dests = [j for j in range(len(stacks)) if j != src and len(stacks[j]) < height]
    if order == "index":
        return dests
    dests.sort(key=lambda j: (_fit_key(stacks, j, c), j))
    return dests[::-1] if order == "anti" else dests


@dataclass(frozen=True)
class SearchResult:
    optimum: int | None     # None, wenn das Knotenlimit erreicht wurde
    nodes: int              # Zahl der besuchten Knoten (bei capped: das Limit)
    leaves: int             # Zahl der besuchten Blätter
    capped: bool
    first_leaf: int | None  # Hubzahl des ersten besuchten Blatts (der erste Tauchgang)


class _CapReached(Exception):
    pass


def search(stacks, height, prune="best", order="tight", cap=1_000_000) -> SearchResult:
    """Tiefensuche über alle Hubfolgen mit Knotenzählung (siehe Moduldoc)."""
    if prune not in PRUNES:
        raise ValueError(f"unbekannte Schranke {prune!r}")
    if order not in ORDERS:
        raise ValueError(f"unbekannte Reihenfolge {order!r}")
    best = [INF]
    nodes = [0]
    leaves = [0]
    first = [None]

    def rec(state, g):
        nodes[0] += 1
        if nodes[0] > cap:
            raise _CapReached
        st, _ = autopop(state)
        if not any(st):
            leaves[0] += 1
            if first[0] is None:
                first[0] = g
            if g < best[0]:
                best[0] = g
            return
        if prune == "best" and g + 1 >= best[0]:      # jeder weitere Hub kostet mindestens 1: es kann nicht mehr besser werden
            return
        _, i = target_stack(st)
        lst = [list(s) for s in st]
        c = lst[i].pop()
        base = tuple(tuple(s) for s in lst)
        for j in child_targets(base, i, height, c, order):
            nxt = [list(s) for s in lst]
            nxt[j].append(c)
            rec(tuple(tuple(s) for s in nxt), g + 1)

    try:
        rec(tuple(tuple(s) for s in stacks), 0)
    except _CapReached:
        return SearchResult(None, cap, leaves[0], True, first[0])
    return SearchResult(best[0], nodes[0], leaves[0], False, first[0])


def tree_lines(stacks, height, max_nodes=200):
    """Der Baum der vollen Aufzählung als Textzeilen (Einrückung = Tiefe), Kinder in Stapelnummern-Reihenfolge. Wirft ValueError, wenn der Baum mehr als
    `max_nodes` Knoten hat (nur für kleine Buchten gedacht)."""
    lines = []
    count = [0]

    def rec(state, g, depth):
        count[0] += 1
        if count[0] > max_nodes:
            raise ValueError("Baum zu groß zum Ausschreiben")
        st, popped = autopop(state)
        leaf = not any(st)
        pop_txt = f", abgerufen {', '.join(str(p) for p in popped)}" if popped else ""
        lines.append(f"{'    ' * depth}Knoten {count[0]}: {_fmt(st)} nach {g} {'Hub' if g == 1 else 'Hüben'}{pop_txt}" + (" – Blatt (leer)" if leaf else ""))
        if leaf:
            return
        _, i = target_stack(st)
        lst = [list(s) for s in st]
        c = lst[i].pop()
        base = tuple(tuple(s) for s in lst)
        for j in child_targets(base, i, height, c, "index"):
            lines.append(f"{'    ' * depth}→ Container {c} von Stapel {i + 1} auf Stapel {j + 1}")
            nxt = [list(s) for s in lst]
            nxt[j].append(c)
            rec(tuple(tuple(s) for s in nxt), g + 1, depth + 1)

    rec(tuple(tuple(s) for s in stacks), 0, 0)
    return lines


def _fmt(stacks):
    return " | ".join("(" + ", ".join(str(c) for c in s) + ")" if s else "()" for s in stacks)
