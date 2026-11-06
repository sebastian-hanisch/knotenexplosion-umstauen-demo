"""Inhalt der App: Kennzahlen der Presets, Tabelle der Varianten, Baum der Mini-Bucht, Verdikte, Permalink (AppTest, DEMO-PLAYBOOK §5)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import kex_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))


def _run(at=None):
    if at is None:                                              # nicht `at or ...`: ein ungelaufener AppTest ist falsy
        at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _metrics(at):
    return {m.label: m.value for m in at.metric}


def _preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return " ".join(md.value for md in at.markdown)


def test_default_bay_shows_the_variants_and_the_verdict():
    at = _run()
    m = _metrics(at)
    assert m["Volle Aufzählung (Knoten)"] == "229" and m["Branch and Bound, engste Passung (Knoten)"] == "29" and m["Optimum"] == "5" and m["Bucht"] == "3 × 3"
    text = _texts(at)
    assert "| Volle Aufzählung | 229 | 114 | 5 |" in text and "| Branch and Bound, engste Passung zuerst | 29 | 1 | 5 |" in text
    assert any("das 7,9-Fache weniger (Optimum 5, Untergrenze 4)" in s.value for s in at.success)


def test_mini_preset_shows_nine_nodes_and_five_leaves():
    at = _preset(_run(), "Die Mini-Bucht")
    assert _metrics(at)["Volle Aufzählung (Knoten)"] == "9" and "| Volle Aufzählung | 9 | 5 | 2 |" in _texts(at)


def test_explosion_preset_gives_up_the_full_enumeration_and_says_so():
    at = _preset(_run(), "Explosion (4 Stapel, 3 Lagen)")
    m = _metrics(at)
    assert m["Volle Aufzählung (Knoten)"] == "mehr als 500 000" and m["Branch and Bound, engste Passung (Knoten)"] == "1 819" and m["Optimum"] == "8"
    assert "| Volle Aufzählung | mehr als 500 000 | 333 327+ | nicht bewiesen |" in _texts(at)
    assert any("Die volle Aufzählung gibt bei 500 000 Knoten auf" in w.value and "mit 1 819 Knoten" in w.value for w in at.warning)


def test_order_preset_shows_the_large_order_effect():
    at = _preset(_run(), "Reihenfolge zählt (4 Stapel, 3 Lagen)")
    text = _texts(at)
    assert "| Branch and Bound, schlechteste zuerst | 1 724 |" in text and "| Branch and Bound, engste Passung zuerst | 116 |" in text


def test_the_mini_tree_is_written_out_for_every_setting():
    at = _run()
    code = "\n".join(c.value for c in at.code)
    assert code.count("Knoten ") == 9 and code.count("Blatt (leer)") == 5 and code.startswith("Knoten 1: (1, 4) | (5, 2) | (6, 3) nach 0 Hüben")
    assert any("9 Knoten, 5 Blätter, Optimum 2" in s.value for s in at.success)


def test_the_table_and_the_verdicts_name_the_numbers_of_the_default_cell():
    at = _run()
    text = _texts(at)
    assert "| 3 × 3 (100) | 230 / 1 403 / 13 427 | 48 / 92 / 427 | 33 / 68 / 419 | 65 / 146 / 845 | 1,25 | 2,11 (4,9) |" in text
    assert "| 4 × 3 (40) | 3 611,5 / 108 841 / 612 886, 10 über Limit |" in text
    bodies = " ".join(e.value for kind in (at.success, at.info, at.warning) for e in kind)
    assert "Die Schranke aus der besten Lösung spart im Median das 6,5-Fache der Knoten" in bodies and "100 Buchten" in bodies
    assert "3 × 3, volle Aufzählung: Verhältnisse aufeinanderfolgender Mediane 4,6, 5,4, 4,2, 2,4, 2,2." in bodies
    assert "Bei 4 × 3 liegt ab 6 Blockern die Hälfte oder mehr der Läufe" in bodies
    assert "Von 100 Buchten gibt die volle Aufzählung in 0 bei 1 000 000 Knoten auf" in bodies
    assert "Bei 3 Stapeln und 3 Lagen braucht die volle Aufzählung bei Platz 1 im Median 71,5 Knoten, bei Platz 4 235" in bodies


def test_a_setting_without_a_stored_cell_says_so():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params.update({"stacks": "3", "layers": "2", "extra": "1", "seed": "5"})
    _run(at)
    at.sidebar.slider(key="layers_slider").set_value(4).run()
    at.sidebar.slider(key="stacks_slider").set_value(4).run()
    assert not at.exception
    assert any("keine vorberechnete Zelle" in i.value for i in at.info)        # 4 x 4 gibt es nicht in der Tabelle


def test_permalink_is_clamped_to_the_slider_bounds():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["stacks"] = "99"
    at.query_params["layers"] = "-4"
    at.query_params["extra"] = "17"
    _run(at)
    assert at.sidebar.slider(key="stacks_slider").value == C.STACKS_MAX
    assert at.sidebar.slider(key="layers_slider").value == C.LAYERS_MIN
    assert at.sidebar.slider(key="extra_slider").value == C.EXTRA_MAX
