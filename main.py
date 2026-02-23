from pyscript import web, when, workers
from pyscript.ffi import create_proxy
from js import Bokeh, JSON, window, document, MathJax
from math import sqrt
import json
from bokeh.embed import json_item
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, LinearAxis, Range1d
from bokeh.themes import Theme

LIGHT_THEME = {
    "attrs": {
        "Plot": {
            "background_fill_color": "#ffffff",
            "border_fill_color": "#f0f2f6"
        },

        "Axis": {
            "major_tick_line_alpha": 0,
            "major_tick_line_color": "#5B5B5B",

            "minor_tick_line_alpha": 0,
            "minor_tick_line_color": "#5B5B5B",

            "axis_line_alpha": 0,
            "axis_line_color": "#5B5B5B",

            "major_label_text_color": "#5B5B5B",
            "major_label_text_font": "Helvetica",
            "major_label_text_font_size": "1.025em",

            "axis_label_standoff": 10,
            "axis_label_text_color": "#5B5B5B",
            "axis_label_text_font": "Helvetica",
            "axis_label_text_font_size": "1.25em",
            "axis_label_text_font_style": "normal",
        },

        "Legend": {
            "spacing": 8,
            "glyph_width": 15,

            "label_standoff": 8,
            "label_text_color": "#5B5B5B",
            "label_text_font": "Helvetica",
            "label_text_font_size": "1.025em",

            "border_line_alpha": 0,
            "background_fill_alpha": 0.25,
        },

        "BaseColorBar": {
            "title_text_color": "#5B5B5B",
            "title_text_font": "Helvetica",
            "title_text_font_size": "1.025em",
            "title_text_font_style": "normal",

            "major_label_text_color": "#5B5B5B",
            "major_label_text_font": "Helvetica",
            "major_label_text_font_size": "1.025em",

            "major_tick_line_alpha": 0,
            "bar_line_alpha": 0,
        },

        "Title": {
            "text_color": "#5B5B5B",
            "text_font": "Helvetica",
            "text_font_size": "1.15em",
        },
    },
}

DARK_THEME = {
    "attrs": {
        "Plot": {
            "background_fill_color": "#0e1117",
            "border_fill_color": "#262730",
            "outline_line_color": "#E0E0E0",
            "outline_line_alpha": 0.25,
        },

        "Grid": {
            "grid_line_color": "#E0E0E0",
            "grid_line_alpha": 0.25,
        },

        "Axis": {
            "major_tick_line_alpha": 0,
            "major_tick_line_color": "#E0E0E0",

            "minor_tick_line_alpha": 0,
            "minor_tick_line_color": "#E0E0E0",

            "axis_line_alpha": 0,
            "axis_line_color": "#E0E0E0",

            "major_label_text_color": "#E0E0E0",
            "major_label_text_font": "Helvetica",
            "major_label_text_font_size": "1.025em",

            "axis_label_standoff": 10,
            "axis_label_text_color": "#E0E0E0",
            "axis_label_text_font": "Helvetica",
            "axis_label_text_font_size": "1.25em",
            "axis_label_text_font_style": "normal",
        },

        "Legend": {
            "spacing": 8,
            "glyph_width": 15,

            "label_standoff": 8,
            "label_text_color": "#E0E0E0",
            "label_text_font": "Helvetica",
            "label_text_font_size": "1.025em",

            "border_line_alpha": 0,
            "background_fill_alpha": 0.25,
            "background_fill_color": "#20262B",
        },

        "BaseColorBar": {
            "title_text_color": "#E0E0E0",
            "title_text_font": "Helvetica",
            "title_text_font_size": "1.025em",
            "title_text_font_style": "normal",

            "major_label_text_color": "#E0E0E0",
            "major_label_text_font": "Helvetica",
            "major_label_text_font_size": "1.025em",

            "background_fill_color": "#262730",
            "major_tick_line_alpha": 0,
            "bar_line_alpha": 0,
        },

        "Title": {
            "text_color": "#E0E0E0",
            "text_font": "Helvetica",
            "text_font_size": "1.15em",
        },
    },
}

dark_theme = False
simulation_anzahl = 0


@when("click", "#start")
async def simulation_starten_click(event):
    await simulation_starten()


async def simulation_starten(sim_wort=""):
    global simulation_anzahl
    global dark_theme

    form = web.page["form"]
    openers = web.page["openers"].value if sim_wort == "" else sim_wort
    custom_openers = web.page["custom-openers"]
    strategie = web.page["strategy"].value
    strategie_text = web.page["strategy"].options[web.page["strategy"].selectedIndex].text
    hilfsmittel = (web.page["secret"].checked, web.page["history"].checked)
    seed = web.page["seed"].value

    hat_custom_woerter = openers == "custom" and sim_wort == ""
    custom_openers.required = hat_custom_woerter
    if not form.checkValidity():
        form.reportValidity()
        return

    eroeffnungswoerter = []
    if not hat_custom_woerter:
        eroeffnungswoerter = openers.split("-")
    else:
        eroeffnungswoerter = "".join(custom_openers.value.split()).split(",")

    if openers == "keine":
        eroeffnungswoerter = []

    mc = await workers["monte_carlo"]
    n = int(web.page["num-simulations"].value)

    daten = await mc.wort_analysieren(eroeffnungswoerter, strategie, hilfsmittel, n, seed if seed != "" else None)

    durchschnitt_verlauf = []
    summe = 0
    for i in range(n):
        summe += daten[i]
        durchschnitt_verlauf.append(summe / (i+1))
    s_quadrat = 0
    arithmetisches_mittel = summe / n
    for i in daten:
        s_quadrat += (1/n) * ((i - arithmetisches_mittel) ** 2)
    s = sqrt(s_quadrat)
    nummierte_liste = list(range(n))
    sortierte_daten = list(daten)
    sortierte_daten.sort()
    median_wert = median(sortierte_daten)

    color = "navy" if not dark_theme else "#26aae1"
    theme = Theme(json=(DARK_THEME if dark_theme else LIGHT_THEME))

    p = figure(width=400, height=400,
               tools="pan,wheel_zoom,reset,save", active_scroll="wheel_zoom", sizing_mode="scale_both")
    p.axis.axis_label_text_font_size = "10pt"
    p.axis.major_label_text_font_size = "9pt"
    p.toolbar.logo = None
    p.line(nummierte_liste, durchschnitt_verlauf,
           line_width=2, line_color=color)
    p.xaxis.axis_label = r"Anzahl gespielter Spiele ($$n$$)"
    p.yaxis.axis_label = r"Durchschn. Anzahl Versuche ($$\bar{x}_n$$)"

    versuche = []
    anzahl = []
    for i in range(1, 8):
        versuche.append(str(i) if i != 7 else "Nicht erraten")
        anzahl.append(daten.count(i))
    rel_anzahl = [i / len(daten) for i in anzahl]
    src = ColumnDataSource(
        data={"x": versuche, "absolute": anzahl, "relative": rel_anzahl})
    b = figure(x_range=versuche, width=400, height=400,
               tools="hover,save", tooltips=[
                   ("Versuche", "@x"),
                   ("Absolute Häufigkeit", "@absolute"),
                   ("Relative Häufigkeit", "@relative{0.00%}")
               ], sizing_mode="scale_both", y_range=(0, 1.05 * max(anzahl)))
    b.vbar(x="x", top="absolute", width=0.9, color=color, source=src)
    b.xgrid.grid_line_color = None
    b.toolbar.logo = None
    b.axis.axis_label_text_font_size = "10pt"
    b.yaxis.major_label_text_font_size = "9pt"
    b.xaxis.major_label_text_font_size = "8pt"
    b.xaxis.axis_label = r"Anzahl Versuche ($$x$$)"
    b.yaxis.axis_label = r"Absolute H\"aufigkeit ($$H_n(x)$$)"

    b.add_layout(LinearAxis(y_range_name="relative", axis_label_text_font_size="10pt",
                 axis_label=r"Relative H\"aufigkeit ($$h_n(x)$$)"), "right")
    b.extra_y_ranges = {"relative": Range1d(
        start=0, end=1.05 * max(rel_anzahl))}

    platzhalter = document.getElementById("ergebnis-platzhalter")
    if platzhalter:
        platzhalter.remove()

    hinweis = document.getElementById("lag-hinweis")
    if hinweis:
        hinweis.remove()

    sim_div = web.div(id="sim" + str(simulation_anzahl))
    sim_div.classes.add("ergebnis-container")
    sim_div.innerHTML = f"""
    <h2>Simulation Nr. ${simulation_anzahl + 1}$</h2>
    <h3>Parameter</h3>
    <p>Simulationen: $n={n}$</p>
    <p>Eröffnungswörter: <span class="grau">{", ".join(eroeffnungswoerter) if len(eroeffnungswoerter) != 0 else "Keine"}</span></p>
    <p>Strategie: <span class="grau">{strategie_text}</span></p>
    <p>Geheime Liste: <span class="grau">{"ja" if hilfsmittel[0] else "nein"}</span><p/>
    <p>Historie: <span class="grau">{"ja" if hilfsmittel[1] else "nein"}</span><p/>
    <p>Seed: <span class="grau">{seed if seed != "" else "Kein Seed wurde benutzt"}</span><p/>
    <h3>Ergebnisse</h3>
    <p>Arithmetisches Mittel: <span class="grau">${arithmetisches_mittel}$</span> | Median: <span class="grau">${median_wert}$</span></p>
    <p>Empirische Varianz: <span class="grau">$s^2={s_quadrat}$</span></p>
    <p>Empirische Standardabweichung: <span class="grau">$s={s}$</span></p>
    <div id="sim{simulation_anzahl}-plot" class="bokeh-plot"></div>
    <div id="sim{simulation_anzahl}-bar" class="bokeh-bar"></div>
    """
    web.page["ergebnisse-container"].append(sim_div)
    MathJax.typeset()  # LaTeX rendern

    p_json = json.dumps(
        json_item(p, "sim" + str(simulation_anzahl) + "-plot", theme=theme))
    js_object = JSON.parse(p_json)
    Bokeh.embed.embed_item(js_object)

    b_json = json.dumps(
        json_item(b, "sim" + str(simulation_anzahl) + "-bar", theme=theme))
    js_object = JSON.parse(b_json)
    Bokeh.embed.embed_item(js_object)

    simulation_anzahl += 1
    print(median_wert, arithmetisches_mittel, s,
          str(rel_anzahl).replace(" ", "")[1:][:-1])


@when("click", "#start-all")
async def alle_simulationen_starten(event):
    woerter = ["keine", "tarse", "salet", "caret", "sater", "torse", "audio", "adieu",
               "parse-clint", "crane-split", "crine-spalt", "slant-price", "larnt-spice", "hates-round-climb"]
    for wort in woerter:
        await simulation_starten(sim_wort=wort)


def schema_wechseln(dark: bool):
    global dark_theme
    dark_theme = dark


def median(daten):
    daten.sort()
    mitte = len(daten) // 2
    return (daten[mitte] + daten[~mitte]) / 2.0


function = create_proxy(schema_wechseln)
window.schemaWechselnPy = function
