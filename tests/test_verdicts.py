"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier."""

import kex_algorithm as K
import kex_constants as C
import kex_evaluation as ev


def _res(nodes, opt=2, capped=False, leaves=1):
    return K.SearchResult(None if capped else opt, nodes, leaves, capped, None if capped else opt)


def _analysis(none, tight, opt=2, lower=1, others=None, none_capped=False, tight_capped=False):
    results = {("none", "index"): _res(none, opt, none_capped), ("best", "index"): _res(tight * 2, opt, tight_capped),
               ("best", "tight"): _res(tight, opt, tight_capped), ("best", "anti"): _res(tight * 3, opt, tight_capped)}
    return ev.Analysis(((1,),), 4, lower, results)


def test_bay_verdict_success_names_nodes_factor_optimum_and_lower_bound():
    kind, text = ev.verdict_bay(_analysis(229, 29, opt=5, lower=4))
    assert kind == "success"
    assert "Die volle Aufzählung braucht 229 Knoten, Branch and Bound mit der engsten Passung zuerst 29: das 7,9-Fache weniger (Optimum 5, Untergrenze 4)." in text


def test_bay_verdict_thresholds_at_factor_two():
    assert ev.verdict_bay(_analysis(10, 5))[0] == "success"            # genau das Doppelte zählt
    kind, text = ev.verdict_bay(_analysis(9, 5))
    assert kind == "info" and "so klein, dass die Schranke kaum etwas spart: 9 Knoten gegen 5" in text


def test_bay_verdict_when_the_full_enumeration_gives_up():
    kind, text = ev.verdict_bay(_analysis(500_000, 1819, opt=7, lower=6, none_capped=True))
    assert kind == "warning"
    assert "Die volle Aufzählung gibt bei 500 000 Knoten auf; Branch and Bound mit der engsten Passung zuerst beweist das Optimum 7 mit 1 819 Knoten (Untergrenze 6)." in text


def test_bay_verdict_when_everything_gives_up():
    a = _analysis(500_000, 500_000, none_capped=True, tight_capped=True)
    kind, text = ev.verdict_bay(a)
    assert kind == "warning" and "Alle vier Varianten geben bei 500 000 Knoten auf" in text and "Untergrenze 1" in text and a.optimum is None


def test_bay_verdict_when_only_another_branch_and_bound_finishes():
    results = {("none", "index"): _res(500_000, capped=True), ("best", "index"): _res(900, 6), ("best", "tight"): _res(500_000, capped=True),
               ("best", "anti"): _res(500_000, capped=True)}
    kind, text = ev.verdict_bay(ev.Analysis(((1,),), 4, 5, results))
    assert kind == "warning" and "ein Branch and Bound beweist das Optimum 6 mit 900 Knoten" in text


def test_result_rows_and_analysis_optimum():
    a = _analysis(9, 5, opt=2)
    rows = ev.result_rows(a)
    assert [r["name"] for r in rows] == [C.VARIANT_NAMES[v] for v in C.VARIANTS] and rows[0]["nodes_text"] == "9" and rows[0]["optimum"] == "2"
    capped = ev.result_rows(_analysis(500_000, 5, none_capped=True))
    assert capped[0]["nodes_text"] == "mehr als 500 000" and capped[0]["optimum"] == "nicht bewiesen" and capped[0]["capped"]


def _stats(bound=12.0, index=1.5, anti=3.0, anti_max=15.0, n=40, over_none=0, over_tight=0):
    var = lambda over: {"ok": n - over, "over": over, "median": 100.0, "mean": 200.0, "max": 900}
    return {"n": n, "variants": {"none/index": var(over_none), "best/index": var(0), "best/tight": var(over_tight), "best/anti": var(0)},
            "index_tight": {"n": n, "median": index}, "anti_tight": {"n": n, "median": anti, "max": anti_max}, "bound": {"n": n - over_none, "median": bound}}


def test_bound_verdict_three_states_and_numbers():
    kind, text = ev.verdict_bound(_stats(bound=12.0))
    assert kind == "success"
    assert "spart im Median das 12-Fache der Knoten" in text and "40 Buchten" in text and "das 1,5-Fache (Stapelnummern gegen engste Passung)" in text
    assert "das 3,0-Fache (schlechteste gegen engste Passung, Maximum 15)" in text and "Die Schranke wirkt hier stark" in text
    assert ev.verdict_bound(_stats(bound=10.0))[0] == "success" and ev.verdict_bound(_stats(bound=9.9))[0] == "info"
    assert ev.verdict_bound(_stats(bound=2.0))[0] == "info"
    kind, text = ev.verdict_bound(_stats(bound=1.9))
    assert kind == "warning" and "kaum" in text
    assert ev.verdict_bound({**_stats(), "bound": {"n": 0, "median": None}})[0] == "warning"


def test_over_limit_verdict_three_states():
    assert ev.verdict_over_limit(_stats())[0] == "info"
    kind, text = ev.verdict_over_limit(_stats(over_none=10, over_tight=1))
    assert kind == "warning" and "Von 40 Buchten gibt die volle Aufzählung in 10 bei 1 000 000 Knoten auf; Branch and Bound mit engster Passung in 1." in text and "in einem Teil" in text
    kind, text = ev.verdict_over_limit(_stats(over_none=20))
    assert kind == "warning" and "in der Mehrzahl" in text                  # genau die Hälfte zählt zur Mehrzahl


def _table(none_medians, none_over=None, tight_medians=None):
    table = {}
    for i, m in enumerate(none_medians, 1):
        over = (none_over or {}).get(i, 0)
        table[str(i)] = {"n": 10, "none": {"ok": 10 - over, "over": over, "median": m, "mean": m, "max": m}, "tight": {"ok": 10, "over": 0, "median": (tight_medians or none_medians)[i - 1], "mean": 1, "max": 1}}
    return table


def test_growth_factors_and_text_by_hand():
    t = _table([5, 25, 100, 400])
    assert ev.growth_factors(t, "none") == [5.0, 4.0, 4.0]
    assert ev.growth_text(t, "none", "3 × 3, volle Aufzählung") == "3 × 3, volle Aufzählung: Verhältnisse aufeinanderfolgender Mediane 5,0, 4,0, 4,0."
    censored = _table([5, 25, 100, 400], none_over={3: 5})
    assert ev.growth_factors(censored, "none") == [5.0]                    # Stufen mit Läufen über Limit zählen nicht
    assert "keine vollständigen Stufen" in ev.growth_text(_table([5], none_over=None), "none", "x")


def test_half_over_from_is_inclusive_at_half():
    t = _table([5, 25, 100, 400], none_over={3: 5, 4: 9})
    assert ev.half_over_from(t, "none") == 3                                # 5 von 10 zählt
    assert ev.half_over_from(_table([5, 25], none_over={2: 4}), "none") is None
    assert ev.half_over_from(_table([5, 25]), "none") is None               # ohne Läufe über Limit nie


def test_blocker_table_by_hand():
    rows = [{"lb": 1, "none/index": 5, "best/tight": 3}, {"lb": 1, "none/index": 9, "best/tight": 3}, {"lb": 2, "none/index": None, "best/tight": 7}]
    t = ev.blocker_table(rows)
    assert t["1"]["n"] == 2 and t["1"]["none"]["median"] == 7 and t["1"]["none"]["over"] == 0
    assert t["2"]["none"]["median"] is None and t["2"]["none"]["over"] == 1 and t["2"]["tight"]["median"] == 7


def test_num_f_by_hand():
    assert ev.num_f(5.0) == "5" and ev.num_f(71.5) == "71,5" and ev.num_f(525188.5) == "525 188,5" and ev.num_f(1234.0) == "1 234"


def test_space_verdict_and_points():
    pts = [{"extra": 1, "none": 71.5, "tight": 17.0, "n": 60}, {"extra": 4, "none": 235.0, "tight": 33.0, "n": 60}]
    kind, text = ev.verdict_space(pts, 3, 3)
    assert kind == "info" and "Bei 3 Stapeln und 3 Lagen braucht die volle Aufzählung bei Platz 1 im Median 71,5 Knoten, bei Platz 4 235; Branch and Bound mit engster Passung 17 bzw. 33." in text
    assert "vergrößert den Baum" in text
    assert "Der Median ändert sich hier wenig." in ev.verdict_space([{"extra": 1, "none": 40.0, "tight": 7.0, "n": 60}, {"extra": 4, "none": 40.0, "tight": 7.0, "n": 60}], 4, 2)[1]   # ohne Mittel
    grows = ev.verdict_space([{"extra": 1, "none": 40.0, "mean": 270.65, "tight": 7.0, "n": 60}, {"extra": 4, "none": 40.0, "mean": 819.45, "tight": 7.0, "n": 60}], 4, 2)[1]
    assert "Der Median ändert sich hier wenig, das Mittel der vollen Aufzählung wächst von 271 auf 819." in grows
    flat = ev.verdict_space([{"extra": 1, "none": 40.0, "mean": 100.0, "tight": 7.0, "n": 60}, {"extra": 4, "none": 40.0, "mean": 120.0, "tight": 7.0, "n": 60}], 4, 2)[1]
    assert "Median und Mittel der vollen Aufzählung ändern sich hier wenig." in flat
    assert "wächst von 271 auf 819" in ev.verdict_space(ev.space_points(ev.load_bands(), 4, 2), 4, 2)[1]
    assert "vergrößert" in ev.verdict_space([{"extra": 1, "none": 100.0, "tight": 7.0, "n": 60}, {"extra": 4, "none": 150.0, "tight": 7.0, "n": 60}], 4, 2)[1]   # genau das 1,5-Fache zählt
