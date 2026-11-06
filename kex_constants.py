"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

STACKS_MIN, STACKS_MAX, DEFAULT_STACKS = 3, 5, 3          # Zahl der Stapel
LAYERS_MIN, LAYERS_MAX, DEFAULT_LAYERS = 2, 4, 3          # Anfangsfüllung je Stapel (Lagen)
EXTRA_MIN, EXTRA_MAX, DEFAULT_EXTRA = 1, 4, 2             # Platz: Höchsthöhe = Lagen + Zuschlag (Standard 2 wie in Stück 1 bis 3)
SEED_MAX = 999999

LIVE_CAP = 500_000                                        # Knotenlimit der Live-Läufe (rund zwei Sekunden je Lauf); darüber: „gibt auf“
BAND_CAP = 1_000_000                                      # Knotenlimit der vorberechneten Kurven
SAMPLE_SEEDS = tuple(range(100))                          # feste Buchten: nie eine einzelne Bucht als Befund

# Zellen der vorberechneten Tabelle: (Stapel, Lagen, Zahl der festen Buchten); große Zellen mit weniger Buchten, weil die Läufe lange dauern
TABLE_CELLS = ((3, 2, 100), (4, 2, 100), (3, 3, 100), (5, 2, 60), (4, 3, 40), (3, 4, 40), (5, 3, 20))
GROWTH_CELLS = ((3, 3), (4, 3))                           # Zellen der Wachstumskurve (aus den Buchten der Tabelle)
SPACE_CELLS = ((3, 3, 60), (4, 2, 60))                    # Zellen der Platzkurve: (Stapel, Lagen, Zahl der Buchten)

BOUND_STRONG, BOUND_WEAK = 10.0, 2.0                      # Verdikt „die Schranke wirkt“: Verhältnis der Mediane volle Aufzählung / Branch and Bound
SPACE_STEP = 1.5                                          # Platzkurve: so viel mehr (Verhältnis) zählt als deutlich

VARIANTS = (("none", "index"), ("best", "index"), ("best", "tight"), ("best", "anti"))
VARIANT_KEYS = {v: f"{v[0]}/{v[1]}" for v in VARIANTS}
VARIANT_NAMES = {
    ("none", "index"): "Volle Aufzählung",
    ("best", "index"): "Branch and Bound, Stapelnummern",
    ("best", "tight"): "Branch and Bound, engste Passung zuerst",
    ("best", "anti"): "Branch and Bound, schlechteste zuerst",
}
VARIANT_SHORT = {("none", "index"): "volle Aufzählung", ("best", "index"): "B&B Stapelnummern", ("best", "tight"): "B&B engste Passung", ("best", "anti"): "B&B schlechteste"}

COLOR_CELL = "#7a8fa6"
COLOR_BLOCK = "#b5545a"        # blockierend (liegt über einem früher abzurufenden)
COLOR_TARGET = "#2F6B65"       # nächster Abruf
COLOR_CAPPED = "#b5545a"       # Lauf am Knotenlimit abgebrochen
COLOR_VARIANT = {("none", "index"): "#7a8fa6", ("best", "index"): "#4c78a8", ("best", "tight"): "#2F6B65", ("best", "anti"): "#d9822b"}
COLOR_LINES = ("#7a8fa6", "#2F6B65", "#d9822b", "#4c78a8")

# Sonderbuchten (in der Vormessung gefunden, Eigenschaften in tests/test_presets.py festgehalten)
MINI_SEED = 223        # 3 x 2: (5, 2), (1, 4), (6, 3) = der einzelne Blocker aus Stück 2 bis auf Vertauschen der Stapel: volle Aufzählung 9 Knoten, 5 Blätter
EVERYDAY_SEED = 12     # 3 x 3, Platz 2: volle Aufzählung 229 Knoten, engste Passung 29
EXPLOSION_SEED = 3     # 4 x 3, Platz 2: volle Aufzählung am Limit (über 500 000 Knoten), Branch and Bound mit engster Passung 1 819
ORDER_SEED = 31        # 4 x 3, Platz 2: schlechteste zuerst braucht das 14,9-Fache der engsten Passung (1 724 gegen 116 Knoten)
MINI_BAY = ((1, 4), (5, 2), (6, 3))                       # die Mini-Bucht des ausgeschriebenen Baums (Stück 2: einzelner Blocker), Höchsthöhe 4
MINI_HEIGHT = 4

PRESETS = {
    "Alltag (3 Stapel, 3 Lagen)": {"stacks": 3, "layers": 3, "extra": DEFAULT_EXTRA, "seed": EVERYDAY_SEED},
    "Die Mini-Bucht": {"stacks": 3, "layers": 2, "extra": DEFAULT_EXTRA, "seed": MINI_SEED},
    "Explosion (4 Stapel, 3 Lagen)": {"stacks": 4, "layers": 3, "extra": DEFAULT_EXTRA, "seed": EXPLOSION_SEED},
    "Reihenfolge zählt (4 Stapel, 3 Lagen)": {"stacks": 4, "layers": 3, "extra": DEFAULT_EXTRA, "seed": ORDER_SEED},
}
PRESET_HELP = {
    "Alltag (3 Stapel, 3 Lagen)": "9 Container: die volle Aufzählung braucht rund 230 Knoten, Branch and Bound mit engster Passung 29.",
    "Die Mini-Bucht": "6 Container, ein einziger Blocker: volle Aufzählung 9 Knoten und 5 Blätter, das Optimum ist 2.",
    "Explosion (4 Stapel, 3 Lagen)": "12 Container: die volle Aufzählung gibt bei 500 000 Knoten auf, Branch and Bound mit engster Passung beweist das Optimum mit rund 1 800.",
    "Reihenfolge zählt (4 Stapel, 3 Lagen)": "12 Container: die schlechteste Reihenfolge braucht hier fast das 15-Fache der engsten Passung.",
}
