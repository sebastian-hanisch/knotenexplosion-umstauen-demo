"""Alle Hubfolgen durchgehen: die Knotenexplosion - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 4 der Reihe „Umstauen: Untergrenze und Suche“. Die einfachste exakte Suche geht alle Hubfolgen durch (Tiefensuche) und behält die beste. Die Demo zählt die Knoten
des Suchbaums für vier Varianten (volle Aufzählung, Branch and Bound mit drei Reihenfolgen der Kinder) an einer Bucht (live, mit Knotenlimit) und zeigt vorberechnet,
wie die Knotenzahl mit den blockierenden Containern wächst und was Schranke und Reihenfolge bringen.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import kex_algorithm as K
import kex_constants as C
from kex_evaluation import (
    Settings,
    analyse,
    cell_key,
    growth_text,
    half_over_from,
    load_bands,
    num,
    num_f,
    result_rows,
    space_points,
    verdict_bay,
    verdict_bound,
    verdict_over_limit,
    verdict_space,
)
from kex_layout import dunkles_design, kopf_css
from kex_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from kex_visualization import build_bay, build_growth, build_nodes, build_over_limit, build_ratios, build_space

st.set_page_config(page_title="Knotenexplosion – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _bands():
    return load_bands()


@st.cache_data(show_spinner=False)
def _mini():
    res = K.search(C.MINI_BAY, C.MINI_HEIGHT, "none", "index")
    return K.tree_lines(C.MINI_BAY, C.MINI_HEIGHT), res


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in kex_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("💥 Alle Hubfolgen durchgehen: die Knotenexplosion")
st.markdown(
    """
Die einfachste **exakte** Suche nach der kleinsten Hubzahl probiert **alle Hubfolgen** durch (Tiefensuche) und behält die beste. Sie ist korrekt, aber der **Suchbaum** wächst mit jedem blockierenden Container um ein Vielfaches. Die Demo **zählt die Knoten**: für die volle Aufzählung und für **Branch and Bound**, das einen Teilbaum abschneidet, sobald er nicht mehr besser werden kann, mit drei Reihenfolgen der Kinder.

Weiter unten: die Abschnitte **🔬 Experiment** (der Baum der Mini-Bucht von Hand, vier Varianten an einer Bucht, Wachstum mit den Blockern, Schranke gegen Reihenfolge, Platz, Läufe über dem Limit), **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**. Dies ist das vierte Stück der Reihe „Umstauen: Untergrenze und Suche“; die Schranke aus der **Untergrenze** (Stück 2), die diese Explosion dämpft, kommt im nächsten.
"""
)

with st.expander("So funktioniert die Tiefensuche", expanded=True):
    st.markdown(
        """
1. **Ein Knoten** ist eine Bucht nach den kostenlosen Abrufen, mit den bisherigen Hüben. Liegt die nächste Nummer nicht oben, muss der oberste Container ihres Stapels (der Blocker) auf einen anderen Stapel mit Platz.
2. **Die Kinder** eines Knotens entstehen, indem der Blocker auf jeden anderen Stapel mit Platz gesetzt wird. Ein **Blatt** ist eine leere Bucht; der Weg dorthin ist eine Hubfolge, seine Länge die Hubzahl.
3. **Volle Aufzählung:** alle Wege durchgehen, die kürzeste behalten. **Branch and Bound:** Ist die beste bisher gefundene Lösung schon so kurz, dass ein weiterer Hub sie nicht mehr unterbieten kann, wird der Teilbaum abgeschnitten.
4. **Reihenfolge der Kinder:** *Stapelnummern*, *engste Passung zuerst* (Regel aus Stück 1) oder *schlechteste zuerst*. Sie bestimmt, wie früh eine gute Lösung gefunden wird und damit, wie viel abgeschnitten werden kann.
5. **Nicht dabei:** keine Untergrenze, kein Zustandsmerken, kein Symmetriebruch. Gleiche Zustände zählen mehrfach; das ist der Grund für die Explosion und der Ansatzpunkt der nächsten Stücke.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Bucht**")
    stacks = st.slider("Stapel", *bounds("stacks_slider"), key="stacks_slider", help="Wie viele Stapel die Bucht hat.")
    layers = st.slider("Lagen je Stapel", *bounds("layers_slider"), key="layers_slider", help="So viele Container stehen anfangs auf jedem Stapel.")
    extra = st.slider("Platz (Lagen über der Anfangshöhe)", *bounds("extra_slider"), key="extra_slider",
                      help="Höchsthöhe = Lagen + Platz. Standard 2. Mehr Platz vergrößert den Suchbaum, in den Messungen bis etwa Platz 3 (gemessen bis Platz 4).")
    seed = st.number_input("Bucht-Nummer (Seed)", *bounds("seed_input"), key="seed_input", step=1, help="Die Nummer bestimmt, wie die Abrufnummern auf die Plätze verteilt sind.")
    st.button("🎲 Neue Bucht würfeln", width="stretch", on_click=randomize_seed)

sync_query_params({"stacks_slider": int(stacks), "layers_slider": int(layers), "extra_slider": int(extra), "seed_input": int(seed)})

settings = Settings(int(stacks), int(layers), int(extra), int(seed))
with st.spinner(f"Zähle die Knoten der vier Varianten (höchstens {num(C.LIVE_CAP)} je Variante) …"):
    a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
rows = result_rows(a)
m1, m2, m3, m4 = st.columns(4)
m1.metric("Volle Aufzählung (Knoten)", rows[0]["nodes_text"], help=f"Alle Hubfolgen; Läufe über {num(C.LIVE_CAP)} Knoten werden abgebrochen.")
m2.metric("Branch and Bound, engste Passung (Knoten)", rows[2]["nodes_text"], help="Beste bisherige Lösung als Schranke, engste Passung zuerst.")
m3.metric("Optimum", "nicht bewiesen" if a.optimum is None else a.optimum, delta=f"Untergrenze {a.lower}", delta_color="off", help="Alle Varianten, die fertig werden, liefern dasselbe Optimum.")
m4.metric("Bucht", f"{settings.stacks} × {settings.layers}", delta=f"{settings.stacks * settings.layers} Container, Platz {settings.extra}", delta_color="off")
st.plotly_chart(build_bay(a.bay, a.height, target=min(c for s in a.bay for c in s)), width="stretch", key="chart_bay")
st.caption("Rot: blockierende Container (liegen über einem früher abzurufenden), grün: der nächste Abruf, grau-blau: alle übrigen.")
table = ["| Variante | Knoten | Blätter | Optimum |", "|---|---|---|---|"]
for r in rows:
    table.append(f"| {r['name']} | {r['nodes_text']} | {num(r['leaves'])}{'+' if r['capped'] else ''} | {r['optimum']} |")
st.markdown("\n".join(table))
st.caption(f"Knoten: besuchte Aufrufe der Suche; „mehr als“ heißt: am Limit von {num(C.LIVE_CAP)} abgebrochen (dann sind auch die Blätter nur die bis dahin besuchten).")
st.plotly_chart(build_nodes(rows), width="stretch", key="chart_nodes")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie viele Knoten braucht das exakte Durchsuchen, und was spart die Schranke?")
kind, text = verdict_bay(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: der Baum der Mini-Bucht ---------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Der Suchbaum der Mini-Bucht von Hand")
lines, mini = _mini()
st.caption("3 Stapel mit je 2 Containern, Höchsthöhe 4, von unten nach oben (1, 4), (5, 2), (6, 3): nur die 4 blockiert (Untergrenze 1). Hier der vollständige Baum der "
           "vollen Aufzählung, Kinder in der Reihenfolge der Stapelnummern; ein Pfeil ist ein Hub.")
st.plotly_chart(build_bay(C.MINI_BAY, C.MINI_HEIGHT, target=1), width="stretch", key="chart_mini")
st.code("\n".join(lines), language=None)
st.success(f"{mini.nodes} Knoten, {mini.leaves} Blätter, Optimum {mini.optimum}: Die 4 landet auf Stapel 2 über der 2 oder auf Stapel 3 über der 3 und blockiert dort wieder, "
           "darum genügt ein Hub nicht, auch wenn nur ein Container blockiert.")

st.markdown("---")

# --- Experiment: Tabelle der Zellen --------------------------------------------------------------------------------------------------------------

bands = _bands()
tab = bands["tabelle"]
st.subheader("🔬 Experiment: Wie viel bringen Schranke und Reihenfolge?")
st.caption(f"Je Zelle feste Buchten (Platz 2), Knotenlimit {num(C.BAND_CAP)} je Lauf; vorberechnet (`generate_precomputed.py`). Median / Mittel / Maximum der fertigen Läufe; "
           "„über Limit“ = abgebrochene Läufe, die im Median fehlen (der Median ist dann nur eine Untergrenze).")


def _cell(st_, key):
    v = st_["variants"][key]
    if v["median"] is None:
        return f"alle {v['over']} über Limit"
    over = f", {v['over']} über Limit" if v["over"] else ""
    return f"{num_f(v['median'])} / {num(round(v['mean']))} / {num(v['max'])}{over}"


header = "| Zelle (Buchten) | volle Aufzählung | B&B, Stapelnummern | B&B, engste Passung | B&B, schlechteste | Stapelnummern / engste (Median) | schlechteste / engste (Median, Maximum) |"
lines_t = [header, "|---|---|---|---|---|---|---|"]
for s_, l_, n_ in C.TABLE_CELLS:
    c = tab[cell_key(s_, l_)]
    it, at = c["index_tight"]["median"], c["anti_tight"]
    lines_t.append(f"| {s_} × {l_} ({c['n']}) | {_cell(c, 'none/index')} | {_cell(c, 'best/index')} | {_cell(c, 'best/tight')} | {_cell(c, 'best/anti')} | "
                   f"{it:.2f} | {at['median']:.2f} ({at['max']:.1f}) |".replace(".", ","))
st.markdown("\n".join(lines_t))
cells = {f"{s_} × {l_}": tab[cell_key(s_, l_)] for s_, l_, _ in C.TABLE_CELLS if tab[cell_key(s_, l_)]["bound"]["median"] is not None}
st.plotly_chart(build_ratios(cells), width="stretch", key="chart_ratios")
here = tab.get(cell_key(settings.stacks, settings.layers))
if here is None:
    st.info(f"Für {settings.stacks} Stapel × {settings.layers} Lagen gibt es keine vorberechnete Zelle; die Tabelle zeigt die Zellen, die gerechnet wurden.")
else:
    st.markdown(f"**Zelle {settings.stacks} × {settings.layers} (Ihre Einstellung):**")
    kind, text = verdict_bound(here)
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Wachstum mit den Blockern -------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie wächst die Knotenzahl mit den Blockern?")
growth = bands["wachstum"]
st.caption("Median der Knoten je Zahl der blockierenden Container, aus den Buchten der Tabelle (die Stufen bestehen aus verschiedenen Buchten, keine Messung an einer Bucht); Rauten:ein Teil der Läufe lag über dem Limit, der Median ist dann nur eine Untergrenze.")
st.plotly_chart(build_growth({f"{k.replace(',', ' × ')}": v for k, v in growth.items()}), width="stretch", key="chart_growth")
g33 = growth["3,3"]
half = half_over_from(growth["4,3"], "none")
st.info(growth_text(g33, "none", "3 × 3, volle Aufzählung") + " " + growth_text(g33, "tight", "3 × 3, Branch and Bound mit engster Passung")
        + (f" Bei 4 × 3 liegt ab {half} Blockern die Hälfte oder mehr der Läufe der vollen Aufzählung über dem Limit, dort lässt sich kein Wachstumsverhältnis angeben." if half else ""))

st.markdown("---")

# --- Experiment: Platz ------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wie wirkt der Platz?")
space = {f"{s_} × {l_}": space_points(bands, s_, l_) for s_, l_, _ in C.SPACE_CELLS}
st.caption(f"Je Punkt {C.SPACE_CELLS[0][2]} feste Buchten, Platz 1 bis 4, vorberechnet.")
st.plotly_chart(build_space(space), width="stretch", key="chart_space")
for s_, l_, _ in C.SPACE_CELLS:
    kind, text = verdict_space(space[f"{s_} × {l_}"], s_, l_)
    getattr(st, kind)(text)

st.markdown("---")

# --- Experiment: Läufe über dem Limit -------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment: Wo gibt die volle Aufzählung auf?")
st.caption(f"Anteil der Läufe über {num(C.BAND_CAP)} Knoten je Zelle (dieselben Buchten wie in der Tabelle). Das Limit zählt Knoten, nicht Sekunden.")
st.plotly_chart(build_over_limit({f"{s_} × {l_}": tab[cell_key(s_, l_)] for s_, l_, _ in C.TABLE_CELLS}), width="stretch", key="chart_over")
if here is not None:
    kind, text = verdict_over_limit(here)
    getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Ohne Untergrenze, Zustandsmerken und Symmetriebruch** | Das ist die Absicht: so zeigt die Explosion sich am deutlichsten. Mit ihnen schrumpft der Baum weiter (in einer Vorab-Messung im Median um etwa das 2- bis 10-Fache gegenüber Branch and Bound mit engster Passung); hier nicht gemessen. | die nächsten Stücke der Reihe |
| **Knotenlimit statt Zeitlimit** | Läufe über dem Limit fehlen in den Medianen, die Mediane sind dann Untergrenzen der wahren Mediane; Knoten pro Sekunde und Laufzeiten sind nicht gemessen. | – |
| **Große Zellen mit wenigen Buchten** | 5 × 2 mit 60, 4 × 3 und 3 × 4 mit 40, 5 × 3 mit 20 Buchten: die Mediane dort sind grob. | – |
| **Nur restricted, nur volle Buchten, Platz 2 in der Tabelle** | Mit anderer Hubmenge (Stück 3) oder anderer Füllung ändern sich die Knotenzahlen. | – |
| **Wachstum je Blocker nur für 3 × 3 belegt** | Bei 4 × 3 sind die Mediane ab 5 Blockern zensiert; die Stufen bestehen aus verschiedenen Buchten (bei 3 × 3 und 6 Blockern aus 4); ein Gesetz folgt daraus nicht. | – |
| **Zahlen aus Zufallsbuchten** | Größenordnungen aus festen Buchten, keine Messung an einem echten Terminal oder Lager. | – |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben:** eine Bucht aus $s$ Stapeln der Höchsthöhe $H$, die Container tragen die Abrufnummern $1, \dots, N$ (kleiner = früher). Ein Hub setzt den obersten Container eines Stapels auf einen anderen Stapel mit Platz; im *restricted* Modell werden nur Container über der nächsten abzurufenden Nummer bewegt, die nächste Nummer wird entnommen, sobald sie oben liegt.

**Suchbaum.** Die Wurzel ist die Ausgangsbucht (nach den kostenlosen Abrufen). Liegt die nächste Nummer $t$ nicht oben, sei $c$ der oberste Container ihres Stapels; die Kinder sind die Buchten, die entstehen, wenn $c$ auf einen anderen Stapel mit Platz gesetzt wird (und danach alles Fällige entnommen wird). Blätter sind leere Buchten. Ein Weg von der Wurzel zu einem Blatt mit $k$ Kanten ist eine Hubfolge mit $k$ Hüben; das Optimum ist die kleinste solche Länge. Die Zahl der **Knoten** ist die Zahl der besuchten Aufrufe der Suche; gleiche Buchten, die auf verschiedenen Wegen entstehen, zählen mehrfach.

**Volle Aufzählung.** Besuche alle Knoten, merke die kürzeste Weglänge. Die Zahl der Knoten ist $1 + \sum_{\text{Kinder}} (\text{Knoten des Kindes})$; sie ist von der Reihenfolge der Kinder unabhängig (nur die Reihenfolge des Besuchs ändert sich).

**Branch and Bound.** Sei $b$ die Länge der besten bisher gefundenen Lösung ($\infty$ zu Beginn). Erreicht ein Knoten mit $g$ bisherigen Hüben, der kein Blatt ist, $g + 1 \ge b$, wird sein Teilbaum übergangen: Jeder weitere Hub kostet mindestens 1, also gibt es darunter keine Lösung mit weniger als $b$ Hüben. Das Ergebnis ist dasselbe Optimum wie bei der vollen Aufzählung.

**Reihenfolge der Kinder.** *Stapelnummern*, *engste Passung zuerst* (unter den Stapeln, auf denen $c$ nichts blockiert, der mit dem kleinsten frühesten Abruf; leerer Stapel zuletzt unter ihnen; danach die übrigen nach größtem frühesten Abruf) oder *schlechteste zuerst* (Umkehrung). Der erste Tauchgang mit engster Passung zuerst entspricht der Regel aus Stück 1.

**Literatur.** Das Problem heißt in der Literatur Block Relocation Problem (auch Container Relocation Problem). Branch and Bound und IDA\* für das Problem nennt der Fachkanon dieser Reihe (Treffer aus Zusammenfassungen, im Volltext nicht gelesen); eine Klassifikation verwandter Stapelprobleme geben Lehnfeld und Knust, European Journal of Operational Research 239(2), 2014, S. 297–312 (Fundstelle geprüft, Volltext nicht gelesen). Die Zählung der Knoten und die vier Varianten sind hier selbst gebaut.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
