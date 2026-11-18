"""Compara las tarjetas (tarjeta.json) de varias corridas: un panel por medida y una barra por canción, con un color
por grupo (por ejemplo, la banda y una influencia).

Uso:
    python scripts/comparar_tarjetas.py outputs/<corrida> [...] --grupo "Primus=primus" --salida outputs/comparacion_primus

Cada corrida debe tener tarjeta.json (lo escribe scripts/tarjeta_cancion.py). Con --grupo NOMBRE=TEXTO, las corridas
cuyo nombre contiene TEXTO van a ese grupo; las demás, a «Angine de Poitrine». Escribe <salida>.png y <salida>.csv.
Las medidas son valores crudos del cuaderno (ver tarjeta_cancion.py). En la novedad, la línea gris es el pop consigo
mismo y el número entre paréntesis dice cuántos cambios distintos hay: con menos de 5, el valor es poco fiable.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

MEDIDAS = [("complejidad_acordes", "Complejidad de acordes (0-100)"), ("complejidad_melodica", "Complejidad melódica (0-100)"),
           ("tension_acorde_melodia", "Tensión acorde-melodía (0-100)"), ("novedad_progresion", "Novedad de la progresión (bits)"),
           ("cuartos_de_tono_melodia", "Cuartos de tono en la melodía (% del tiempo)"), ("tiempo_confiable", "Compases confiables (% del tiempo)")]
COLORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
PALETA = {"Angine de Poitrine": "#2a78d6", "Primus": "#eb6834", "King Gizzard": "#1baf7a",
          "Frank Zappa": "#eda100", "King Crimson": "#8b5fbf", "Gentle Giant": "#d1495b"}
EJES = {
    "complejidad_acordes": "Porcentaje de complejidad (%)",
    "complejidad_melodica": "Porcentaje fuera del modo (%)",
    "tension_acorde_melodia": "Porcentaje fuera del acorde (%)",
    "novedad_progresion": "Sorpresa de los cambios (bits)",
    "cuartos_de_tono_melodia": "Tiempo en cuartos de tono (%)",
    "tiempo_confiable": "Compases confiables (%)",
}


def nombre(corrida: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", corrida)
    n = re.sub(r"(angine_de_poitrine_|primus_|_audio_off\w*|_official_audio|_repro|_\d{4}_\w+$)", "", n)
    n = re.sub(r"_cache$", "", n)
    return n.replace("_", " ").strip().capitalize()


def grupo_corrida(corrida: str) -> str:
    low = corrida.lower()
    if "primus" in low:
        return "Primus"
    if "king_gizzard" in low:
        return "King Gizzard"
    if "king_crimson" in low:
        return "King Crimson"
    if "gentle_giant" in low:
        return "Gentle Giant"
    if any(k in low for k in ("g_spot_tornado", "inca_roads", "peaches_en_regalia", "the_black_page", "zomby_woof")):
        return "Frank Zappa"
    return "Angine de Poitrine"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--grupo", action="append", default=[], metavar="NOMBRE=TEXTO")
    ap.add_argument("--salida", default="outputs/comparacion_tarjetas")
    a = ap.parse_args()
    reglas = [g.split("=", 1) for g in a.grupo]
    filas = []
    for run in a.corridas:
        f = run / "tarjeta.json"
        if not f.exists():
            print(f"sin tarjeta.json: {run.name}")
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        r["grupo"] = next((n for n, t in reglas if t.lower() in run.name.lower()), grupo_corrida(run.name))
        r["cancion"] = nombre(run.name)
        filas.append(r)
    grupos = list(dict.fromkeys(r["grupo"] for r in filas))
    filas.sort(key=lambda r: grupos.index(r["grupo"]))
    campos = ["grupo", "cancion", "centro", "modo", "tempo_bpm", "acorde_mas_usado", "cambios_distintos"] + [m for m, _ in MEDIDAS]
    with open(a.salida + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tinta, gris, rejilla, fondo = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
    fig, ejes = plt.subplots(2, 3, figsize=(16.5, 2.4 + 1.0 * len(filas)), facecolor=fondo)
    y = [1.15 * v for v in list(range(len(filas))[::-1])]
    for ax, (m, titulo) in zip(ejes.flat, MEDIDAS):
        vals = [r.get(m) for r in filas]
        ax.barh(y, [v or 0 for v in vals], color=[PALETA.get(r["grupo"], COLORES[grupos.index(r["grupo"]) % 4]) for r in filas], height=0.62)
        tope = max([v for v in vals if v is not None] + [1])
        for yi, v, r in zip(y, vals, filas):
            txt = "sin cambios" if v is None and m == "novedad_progresion" else "—" if v is None else f"{v:g}"
            if m == "novedad_progresion" and v is not None:
                txt += f"  ({r.get('cambios_distintos', 0)})"
            ax.text((v or 0) + tope * 0.02, yi, txt, va="center", fontsize=9, color=tinta)
        ax.set_yticks(y, [r["cancion"] for r in filas] if ax in ejes[:, 0] else [""] * len(filas), fontsize=9.5)
        ax.set_xlim(0, tope * 1.25)
        ax.set_ylim(-0.7, max(y, default=0) + 0.7)
        ax.set_title(titulo, loc="center", fontsize=11.5, fontweight="bold", color=tinta, pad=12)
        ax.set_xlabel(EJES[m], fontsize=9.5, color=gris, labelpad=13)
        ax.set_facecolor(fondo)
        ax.tick_params(colors=gris, length=0, labelsize=8.5)
        ax.grid(axis="x", color=rejilla, lw=0.8)
        ax.set_axisbelow(True)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle("Comparación de métricas estructurales entre canciones", x=0.5, y=0.98, ha="center",
                 fontsize=17, fontweight="bold", color=tinta)
    fig.text(0.03, 0.935, "Compara complejidad, tensión, novedad, microtonalidad y confiabilidad de la medición en la banda y sus repertorios de referencia. Los valores son medidas directas del análisis; no son percentiles.",
             fontsize=10.5, color=gris, ha="left", va="top")
    fig.text(0.03, 0.035, "Paréntesis en novedad: número de cambios de fundamental distintos observados. Menos de 5 cambios = estimación poco estable.",
             fontsize=10.5, color=gris, ha="left", va="bottom")
    handles = [plt.Line2D([0], [0], color=PALETA[g], lw=8, label=g) for g in grupos]
    fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.98, 0.905), ncol=2,
               frameon=False, fontsize=9.5, title="Banda / repertorio", title_fontsize=10)
    fig.subplots_adjust(left=0.20, right=0.98, top=0.84, bottom=0.12, wspace=0.38, hspace=0.45)
    fig.savefig(a.salida + ".png", dpi=200, facecolor=fondo)
    print(f"{a.salida}.png y .csv · {len(filas)} canciones · grupos: {', '.join(grupos)}")


if __name__ == "__main__":
    main()
