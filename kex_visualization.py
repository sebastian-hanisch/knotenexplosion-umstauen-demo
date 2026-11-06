"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go

import kex_algorithm as K
import kex_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=340):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def blocker_cells(stacks) -> set:
    """Container, die über einem früher abzurufenden im selben Stapel liegen (Position (Stapel, Lage))."""
    out = set()
    for i, s in enumerate(stacks):
        lowest = K.INF
        for j, c in enumerate(s):
            if c > lowest:
                out.add((i, j))
            else:
                lowest = c
    return out


def build_bay(stacks, height, target=None):
    """Die Bucht als Säulen: je Lage ein Balken mit der Abrufnummer. Rot: blockiert einen früher abzurufenden, grün: nächster Abruf
    (`target`, eine Abrufnummer oder None), grau-blau: übrige."""
    blockers = blocker_cells(stacks)
    fig = go.Figure()
    xs = list(range(len(stacks)))
    for j in range(height):
        ys, colors, texts = [], [], []
        for i, s in enumerate(stacks):
            if j < len(s):
                c = s[j]
                ys.append(1)
                texts.append(str(c))
                colors.append(C.COLOR_TARGET if c == target else C.COLOR_BLOCK if (i, j) in blockers else C.COLOR_CELL)
            else:
                ys.append(0)
                texts.append("")
                colors.append(C.COLOR_CELL)
        fig.add_trace(go.Bar(x=xs, y=ys, base=j, marker_color=colors, text=texts, textposition="inside", insidetextanchor="middle",
                             textfont=dict(color="#ffffff", size=16), width=0.78, showlegend=False,
                             hovertemplate="Abruf %{text}<extra></extra>", marker_line=dict(width=0)))
    fig.update_layout(barmode="overlay")
    fig.add_hline(y=height, line_dash="dot", line_color="rgba(128,128,128,0.7)", annotation_text="Höchsthöhe", annotation_position="top left")
    fig.update_xaxes(tickvals=xs, ticktext=[f"Stapel {i + 1}" for i in xs], showgrid=False)
    fig.update_yaxes(range=[0, height + 0.35], showticklabels=False, showgrid=False, zeroline=False)
    return _base(fig, height=48 * height + 90)


def build_nodes(rows):
    """Knoten je Variante als Balken (logarithmische Achse); Läufe am Knotenlimit sind rot und als „mehr als“ beschriftet. `rows`: Zeilen aus result_rows."""
    fig = go.Figure(go.Bar(
        x=[C.VARIANT_SHORT[r["variant"]] for r in rows], y=[r["nodes"] for r in rows],
        marker_color=[C.COLOR_CAPPED if r["capped"] else C.COLOR_VARIANT[r["variant"]] for r in rows],
        text=[r["nodes_text"] for r in rows], textposition="outside", cliponaxis=False,
        hovertemplate="%{x}: %{text} Knoten<extra></extra>"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Knoten (logarithmisch)", type="log")
    return _base(fig, height=320)


def build_growth(tables):
    """Median der Knoten je Zahl der Blocker (logarithmische Achse), eine Linie je Zelle und Variante. `tables`: {Zellname: blocker_table}.
    Punkte mit Läufen über Limit sind Untergrenzen des Medians und als Rauten gezeichnet."""
    fig = go.Figure()
    idx = 0
    for name, table in tables.items():
        for key, label in (("none", "volle Aufzählung"), ("tight", "Branch and Bound, engste Passung")):
            lbs = [int(x) for x in sorted(table, key=int) if table[x][key]["median"] is not None]
            ys = [table[str(x)][key]["median"] for x in lbs]
            symbols = ["diamond" if table[str(x)][key]["over"] else "circle" for x in lbs]
            fig.add_trace(go.Scatter(x=lbs, y=ys, mode="lines+markers", name=f"{name}, {label}", marker=dict(symbol=symbols, size=9),
                                     line=dict(color=C.COLOR_LINES[idx % len(C.COLOR_LINES)], width=3),
                                     hovertemplate="%{x} Blocker: Median %{y:,.0f} Knoten<extra>%{fullData.name}</extra>"))
            idx += 1
    fig.update_xaxes(title_text="blockierende Container", dtick=1)
    fig.update_yaxes(title_text="Median der Knoten (logarithmisch)", type="log")
    return _base(fig, height=380)


def build_ratios(cells):
    """Wirkung von Schranke und Reihenfolge je Zelle (logarithmisch): Median der Verhältnisse volle Aufzählung / engste Passung, schlechteste / engste, Stapelnummern /
    engste. `cells`: {Zellname: cell_stats}."""
    names = list(cells)
    fig = go.Figure()
    for label, key, color in (("volle Aufzählung / engste Passung", "bound", C.COLOR_LINES[0]), ("schlechteste / engste Passung", "anti_tight", C.COLOR_LINES[2]),
                              ("Stapelnummern / engste Passung", "index_tight", C.COLOR_LINES[3])):
        fig.add_trace(go.Bar(x=names, y=[cells[n][key]["median"] or 0 for n in names], name=label, marker_color=color,
                             hovertemplate="%{x}: %{y:.1f}-fach<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="Median des Verhältnisses (logarithmisch)", type="log")
    return _base(fig)


def build_space(curves):
    """Median der Knoten der vollen Aufzählung über den Platz, eine Linie je Zelle. `curves`: {Zellname: Punkte aus space_points}."""
    fig = go.Figure()
    for idx, (name, pts) in enumerate(curves.items()):
        fig.add_trace(go.Scatter(x=[p["extra"] for p in pts], y=[p["none"] for p in pts], mode="lines+markers", name=name,
                                 line=dict(color=C.COLOR_LINES[idx % len(C.COLOR_LINES)], width=3),
                                 hovertemplate="Platz %{x}: Median %{y:,.0f} Knoten<extra>%{fullData.name}</extra>"))
    fig.update_xaxes(title_text="Platz (Lagen über der Anfangshöhe)", tickvals=list(range(C.EXTRA_MIN, C.EXTRA_MAX + 1)))
    fig.update_yaxes(title_text="Median der Knoten, volle Aufzählung", rangemode="tozero")
    return _base(fig)


def build_over_limit(cells):
    """Anteil der Läufe über dem Knotenlimit je Zelle für die volle Aufzählung und Branch and Bound mit engster Passung (Prozent). `cells`: {Zellname: cell_stats}."""
    names = list(cells)
    fig = go.Figure()
    for label, key, color in (("volle Aufzählung", "none/index", C.COLOR_LINES[0]), ("Branch and Bound, engste Passung", "best/tight", C.COLOR_LINES[1])):
        fig.add_trace(go.Bar(x=names, y=[100.0 * cells[n]["variants"][key]["over"] / cells[n]["n"] for n in names], name=label, marker_color=color,
                             hovertemplate="%{x}: %{y:.0f} % über dem Limit<extra>%{fullData.name}</extra>"))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text=f"Läufe über {C.BAND_CAP:,} Knoten (%)".replace(",", " "), range=[0, 100])
    return _base(fig)
