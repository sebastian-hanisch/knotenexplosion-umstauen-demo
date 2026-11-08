"""Kennzahlen, Verdikt-Logik, vorberechnete Kurven. Reine Funktionen: die App ruft st.<Art>(Text), die Tests prüfen jede Zahl und jede Schwelle."""

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

import kex_algorithm as K
import kex_constants as C
from kex_scenario import make_bay, max_height

BANDS_FILE = Path(__file__).resolve().parent / "kex_bands.json"


@dataclass(frozen=True)
class Settings:
    stacks: int = C.DEFAULT_STACKS
    layers: int = C.DEFAULT_LAYERS
    extra: int = C.DEFAULT_EXTRA
    seed: int = C.EVERYDAY_SEED


@dataclass(frozen=True)
class Analysis:
    bay: tuple
    height: int
    lower: int          # Untergrenze: blockierende Container (Stück 2)
    results: dict       # (Schranke, Reihenfolge) -> SearchResult

    def res(self, variant) -> K.SearchResult:
        return self.results[variant]

    @property
    def optimum(self):
        """Das Optimum, sobald eine Variante es bewiesen hat (alle Varianten, die fertig werden, liefern dasselbe); sonst None."""
        found = {r.optimum for r in self.results.values() if not r.capped}
        assert len(found) <= 1, found
        return found.pop() if found else None


def analyse(settings: Settings, cap: int = C.LIVE_CAP) -> Analysis:
    bay = make_bay(settings.stacks, settings.layers, settings.seed)
    height = max_height(settings.layers, settings.extra)
    return Analysis(bay, height, K.blocker_count(bay), {v: K.search(bay, height, v[0], v[1], cap) for v in C.VARIANTS})


def num(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner."""
    return f"{n:,}".replace(",", " ")


def num_f(x: float) -> str:
    """Zahl mit Leerzeichen als Tausendertrenner; hat sie einen Nachkommaanteil (Median einer geraden Zahl von Läufen), mit einer Nachkommastelle und Komma."""
    if float(x).is_integer():
        return num(int(x))
    whole, frac = f"{x:.1f}".split(".")
    return f"{num(int(whole))},{frac}"


def nodes_text(r: K.SearchResult) -> str:
    return f"mehr als {num(r.nodes)}" if r.capped else num(r.nodes)


def factor_text(x: float) -> str:
    """Verhältnis mit einer Nachkommastelle unter 10, sonst ganzzahlig gerundet."""
    return f"{x:.1f}".replace(".", ",") if x < 10 else f"{x:.0f}"


# ---------------------------------------------------------------- Verdikt einer Bucht

def verdict_bay(a: Analysis, cap: int = C.LIVE_CAP) -> tuple[str, str]:
    """Verdikt der Kernfrage: wie viel spart die Schranke aus der besten bisherigen Lösung gegenüber der vollen Aufzählung?"""
    none, tight = a.res(("none", "index")), a.res(("best", "tight"))
    opt = a.optimum
    if opt is None:
        return "warning", f"Alle vier Varianten geben bei {num(cap)} Knoten auf: In dieser Bucht ist das Optimum so nicht zu beweisen (Untergrenze {a.lower})."
    if none.capped:
        who = "Branch and Bound mit der engsten Passung zuerst" if not tight.capped else "ein Branch and Bound"
        n = tight.nodes if not tight.capped else min(r.nodes for r in a.results.values() if not r.capped)
        return "warning", (f"Die volle Aufzählung gibt bei {num(cap)} Knoten auf; {who} beweist das Optimum {opt} mit {num(n)} Knoten "
                           f"(Untergrenze {a.lower}).")
    factor = none.nodes / tight.nodes
    if factor >= C.BOUND_WEAK:
        return "success", (f"Die volle Aufzählung braucht {num(none.nodes)} Knoten, Branch and Bound mit der engsten Passung zuerst {num(tight.nodes)}: "
                           f"das {factor_text(factor)}-Fache weniger (Optimum {opt}, Untergrenze {a.lower}).")
    return "info", (f"Die Bucht ist so klein, dass die Schranke kaum etwas spart: {num(none.nodes)} Knoten gegen {num(tight.nodes)} "
                    f"(Optimum {opt}, Untergrenze {a.lower}).")


def result_rows(a: Analysis) -> list[dict]:
    """Eine Zeile je Variante: Name, Knoten (Text), Blätter, Optimum (oder „nicht bewiesen“)."""
    rows = []
    for v in C.VARIANTS:
        r = a.res(v)
        rows.append({"variant": v, "name": C.VARIANT_NAMES[v], "nodes": r.nodes, "capped": r.capped, "nodes_text": nodes_text(r),
                     "leaves": r.leaves, "optimum": "nicht bewiesen" if r.capped else str(r.optimum)})
    return rows


# ---------------------------------------------------------------- Stichproben (vorberechnet)

def cell_rows(stacks: int, layers: int, extra: int, seeds, cap: int = C.BAND_CAP) -> list[dict]:
    """Eine Zeile je feste Bucht: Untergrenze und Knoten je Variante (None = über Limit); langsam bei großen Zellen, nur offline und in Tests."""
    height = max_height(layers, extra)
    rows = []
    for sd in seeds:
        bay = make_bay(stacks, layers, sd)
        row = {"seed": sd, "lb": K.blocker_count(bay)}
        for v in C.VARIANTS:
            r = K.search(bay, height, v[0], v[1], cap)
            row[C.VARIANT_KEYS[v]] = None if r.capped else r.nodes
        rows.append(row)
    return rows


def _stat(xs):
    ok = [x for x in xs if x is not None]
    if not ok:
        return {"ok": 0, "over": len(xs), "median": None, "mean": None, "max": None}
    return {"ok": len(ok), "over": len(xs) - len(ok), "median": median(ok), "mean": mean(ok), "max": max(ok)}


def _ratios(rows, top, bottom):
    return [r[top] / r[bottom] for r in rows if r[top] is not None and r[bottom] is not None]


def cell_stats(rows: list[dict]) -> dict:
    """Kennzahlen einer Stichprobe: Knoten je Variante (Median, Mittel, Maximum der fertigen Läufe, Zahl der Läufe über Limit) und die Verhältnisse
    index/tight, anti/tight (Median, Maximum) und volle Aufzählung/engste Passung (Median) über die Buchten, in denen beide fertig wurden."""
    k = C.VARIANT_KEYS
    out = {"n": len(rows), "variants": {k[v]: _stat([r[k[v]] for r in rows]) for v in C.VARIANTS}}
    idx = _ratios(rows, k[("best", "index")], k[("best", "tight")])
    anti = _ratios(rows, k[("best", "anti")], k[("best", "tight")])
    bound = _ratios(rows, k[("none", "index")], k[("best", "tight")])
    out["index_tight"] = {"n": len(idx), "median": median(idx) if idx else None}
    out["anti_tight"] = {"n": len(anti), "median": median(anti) if anti else None, "max": max(anti) if anti else None}
    out["bound"] = {"n": len(bound), "median": median(bound) if bound else None}
    return out


def blocker_table(rows: list[dict]) -> dict:
    """Median der Knoten je Zahl der blockierenden Container für die volle Aufzählung und Branch and Bound mit engster Passung: {Untergrenze: {n, none, tight}};
    Läufe über Limit fehlen im Median (der Median ist dann eine Untergrenze des wahren Medians)."""
    k = C.VARIANT_KEYS
    table = {}
    for lb in sorted({r["lb"] for r in rows}):
        sub = [r for r in rows if r["lb"] == lb]
        table[str(lb)] = {"n": len(sub), "none": _stat([r[k[("none", "index")]] for r in sub]), "tight": _stat([r[k[("best", "tight")]] for r in sub])}
    return table


def growth_factors(table: dict, key: str) -> list[float]:
    """Verhältnisse aufeinanderfolgender Mediane (Zahl der Blocker um 1 größer); nur dort, wo beide Mediane aus ganzen Stichproben stammen
    (keine Läufe über Limit) und aufeinanderfolgende Untergrenzen vorliegen."""
    out = []
    keys = sorted(int(x) for x in table)
    for a, b in zip(keys, keys[1:]):
        sa, sb = table[str(a)][key], table[str(b)][key]
        if b == a + 1 and sa["median"] is not None and sb["median"] is not None and sa["over"] == 0 and sb["over"] == 0 and sa["median"] > 0:
            out.append(sb["median"] / sa["median"])
    return out


def load_bands() -> dict:
    """Vorberechnete Kennzahlen, erzeugt von generate_precomputed.py: {"tabelle": {"s,l": Stichprobe}, "wachstum": {"s,l": Tabelle}, "platz": {"s,l,e": Stichprobe}}."""
    return json.loads(BANDS_FILE.read_text(encoding="utf-8"))


def cell_key(stacks: int, layers: int) -> str:
    return f"{stacks},{layers}"


def space_key(stacks: int, layers: int, extra: int) -> str:
    return f"{stacks},{layers},{extra}"


def verdict_bound(stats: dict) -> tuple[str, str]:
    """Verdikt „was bringt die Schranke aus der besten Lösung, was die Reihenfolge?“ in drei Zuständen nach dem Median der Verhältnisse volle Aufzählung / Branch and Bound."""
    b, i, a = stats["bound"], stats["index_tight"], stats["anti_tight"]
    if b["median"] is None:
        return "warning", "In dieser Zelle wurde keine volle Aufzählung fertig: Der Vergleich ist so nicht möglich."
    text = (f"Die Schranke aus der besten Lösung spart im Median das {factor_text(b['median'])}-Fache der Knoten (volle Aufzählung gegen Branch and Bound mit engster Passung, also Schranke und gute Reihenfolge zusammen; "
            f"{b['n']} Buchten). Die Reihenfolge der Kinder bringt im Median das {factor_text(i['median'])}-Fache (Stapelnummern gegen engste Passung) bzw. "
            f"das {factor_text(a['median'])}-Fache (schlechteste gegen engste Passung, Maximum {factor_text(a['max'])}).")
    if b["median"] >= C.BOUND_STRONG:
        return "success", text + " Die Schranke wirkt hier stark, die Reihenfolge deutlich schwächer."
    if b["median"] >= C.BOUND_WEAK:
        return "info", text + " Die Schranke wirkt hier mäßig."
    return "warning", text + " Die Schranke wirkt hier kaum: Die Bucht ist zu klein."


def verdict_over_limit(stats: dict) -> tuple[str, str]:
    """Verdikt „wo gibt die volle Aufzählung auf?“: Zahl der Läufe über dem Limit je Variante in der Zelle."""
    n = stats["n"]
    over = {v: stats["variants"][C.VARIANT_KEYS[v]]["over"] for v in C.VARIANTS}
    o = over[("none", "index")]
    text = f"Von {n} Buchten gibt die volle Aufzählung in {o} bei {num(C.BAND_CAP)} Knoten auf; Branch and Bound mit engster Passung in {over[('best', 'tight')]}."
    if o == 0:
        return "info", text + " Hier kommt die volle Aufzählung noch durch."
    if o * 2 >= n:
        return "warning", text + " Die volle Aufzählung scheitert hier in der Mehrzahl der Buchten."
    return "warning", text + " Die volle Aufzählung scheitert hier in einem Teil der Buchten."


def half_over_from(table: dict, key: str):
    """Kleinste Zahl blockierender Container, ab der in der Stufe mindestens die Hälfte der Läufe über dem Limit lag (sonst None)."""
    for lb in sorted(int(x) for x in table):
        st = table[str(lb)][key]
        if st["over"] * 2 >= table[str(lb)]["n"] and st["over"] > 0:
            return lb
    return None


def growth_text(table: dict, key: str, label: str) -> str:
    """Satz zum Wachstum je Blocker aus den Verhältnissen aufeinanderfolgender Mediane (ohne zensierte Stufen)."""
    g = growth_factors(table, key)
    if not g:
        return f"{label}: keine vollständigen Stufen für ein Wachstumsverhältnis."
    return f"{label}: Verhältnisse aufeinanderfolgender Mediane " + ", ".join(factor_text(x) for x in g) + "."


def space_points(bands: dict, stacks: int, layers: int) -> list[dict]:
    """Knoten über den Platz (Median volle Aufzählung und Branch and Bound mit engster Passung)."""
    pts = []
    for extra in range(C.EXTRA_MIN, C.EXTRA_MAX + 1):
        st = bands["platz"][space_key(stacks, layers, extra)]
        pts.append({"extra": extra, "none": st["variants"]["none/index"]["median"], "mean": st["variants"]["none/index"]["mean"], "tight": st["variants"]["best/tight"]["median"], "n": st["n"]})
    return pts


def verdict_space(points: list[dict], stacks: int, layers: int) -> tuple[str, str]:
    """Verdikt der Platzkurve: Median der Knoten der vollen Aufzählung bei dem knappsten und dem größten Platz."""
    first, last = points[0], points[-1]
    text = (f"Bei {stacks} Stapeln und {layers} Lagen braucht die volle Aufzählung bei Platz {first['extra']} im Median {num_f(first['none'])} Knoten, bei Platz {last['extra']} "
            f"{num_f(last['none'])}; Branch and Bound mit engster Passung {num_f(first['tight'])} bzw. {num_f(last['tight'])}.")
    if first["none"] > 0 and last["none"] / first["none"] >= C.SPACE_STEP:
        return "info", text + " Mehr Platz vergrößert den Baum."
    m1, m2 = first.get("mean"), last.get("mean")
    if m1 and m2 and m2 / m1 >= C.SPACE_STEP:
        return "info", text + f" Der Median ändert sich hier wenig, das Mittel der vollen Aufzählung wächst von {num(round(m1))} auf {num(round(m2))}."
    if m1 and m2:
        return "info", text + " Median und Mittel der vollen Aufzählung ändern sich hier wenig."
    return "info", text + " Der Median ändert sich hier wenig."
