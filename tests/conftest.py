"""Gemeinsame Fixtures: die Mini-Buchten, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def mini():
    """Die Mini-Bucht (einzelner Blocker aus Stück 2): 3 Stapel mit je 2 Containern, Höchsthöhe 4, von unten nach oben (1, 4), (5, 2), (6, 3).

    Handrechnung des Baums der vollen Aufzählung: Die 4 muss weg (Knoten 1). Auf Stapel 2 (über 5 und 2): Knoten 2, die 4 muss wieder weg; auf Stapel 1: Blatt (2 Hübe);
    auf Stapel 3 (über 6 und 3) Knoten 4, wieder weg, auf Stapel 1 und 2: zwei Blätter (3 Hübe). Auf Stapel 3 (nach der 1): Knoten 7, wieder weg, auf Stapel 1 und
    Stapel 2: zwei Blätter (2 Hübe). Zusammen 9 Knoten und 5 Blätter, Optimum 2."""
    return ((1, 4), (5, 2), (6, 3)), 4


@pytest.fixture
def counter():
    """Das Gegenbeispiel aus Stück 1: (3, 6), (2, 4), (1, 5), Höchsthöhe 4. Volle Aufzählung 153 Knoten und 77 Blätter, Optimum 4."""
    return ((3, 6), (2, 4), (1, 5)), 4
