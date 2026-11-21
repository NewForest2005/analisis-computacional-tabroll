"""Compara las tarjetas (tarjeta.json) de varias corridas: un panel por medida y una barra por canción, con un color
por grupo (por ejemplo, la banda y una influencia).

Uso:
    python scripts/comparacion/comparar_tarjetas.py outputs/<corrida> [...] --grupo "Primus=primus" --salida outputs/comparacion_primus

Cada corrida debe tener tarjeta.json (lo escribe scripts/comparacion/tarjeta_cancion.py). Con --grupo NOMBRE=TEXTO, las corridas
cuyo nombre contiene TEXTO van a ese grupo; las demás, a «Angine de Poitrine». Escribe <salida>.png y <salida>.csv.
Las medidas son valores crudos del cuaderno (ver tarjeta_cancion.py). En la novedad, la línea gris es el pop consigo
mismo y el número entre paréntesis dice cuántos cambios distintos hay: con menos de 5, el valor es poco fiable.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estilo_figuras  # noqa: E402

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


def dibujar(filas: list[dict], grupos: list[str]):
    """Seis paneles en una fila (una medida cada uno) con las canciones compartidas en el eje vertical."""
    import matplotlib.pyplot as plt
    from estilo_figuras import FONDO, GRIS, REJILLA, TINTA, partir

    ancho_panel = 3.1
    fig, cuerpo = estilo_figuras.figura(
        2.4 + ancho_panel * len(MEDIDAS), 0.2 * len(filas) + 1.4,
        "Comparación de métricas estructurales entre canciones",
        subtitulo="Complejidad, tensión, novedad, microtonalidad y confiabilidad de la medición en la banda y sus "
                  "repertorios de referencia. Los valores son medidas directas del análisis; no son percentiles.",
        nota="Paréntesis en novedad: número de cambios de fundamental distintos observados. "
             "Menos de 5 cambios = estimación poco estable.")
    ejes = cuerpo.subplots(1, len(MEDIDAS), sharey=True)
    y = list(range(len(filas)))[::-1]
    colores = [PALETA.get(r["grupo"], COLORES[grupos.index(r["grupo"]) % 4]) for r in filas]
    for ax, (m, titulo) in zip(ejes, MEDIDAS):
        vals = [r.get(m) for r in filas]
        ax.barh(y, [v or 0 for v in vals], color=colores, height=0.68)
        tope = max([v for v in vals if v is not None] + [1])
        for yi, v, r in zip(y, vals, filas):
            txt = "sin cambios" if v is None and m == "novedad_progresion" else "—" if v is None else f"{v:g}"
            if m == "novedad_progresion" and v is not None:
                txt += f" ({r.get('cambios_distintos', 0)})"
            ax.text((v or 0) + tope * 0.03, yi, txt, va="center", fontsize=7, color=TINTA)
        ax.set_xlim(0, tope * 1.45)
        ax.set_xticks([t for t in ax.get_xticks() if 0 <= t <= tope * 1.1])
        ax.set_ylim(-0.6, len(filas) - 0.4)
        ax.set_title(partir(titulo, ancho_panel - 0.2, 10), fontsize=10, fontweight="bold", color=TINTA)
        ax.set_xlabel(partir(EJES[m], ancho_panel - 0.2, 8.5), fontsize=8.5, color=GRIS)
        ax.set_facecolor(FONDO)
        ax.tick_params(colors=GRIS, length=0, labelsize=7.5)
        ax.grid(axis="x", color=REJILLA, lw=0.8)
        ax.set_axisbelow(True)
        for s in ax.spines.values():
            s.set_visible(False)
    ejes[0].set_yticks(y, [r["cancion"] for r in filas], fontsize=8)
    handles = [plt.Line2D([0], [0], color=PALETA.get(g, COLORES[i % 4]), lw=8, label=g) for i, g in enumerate(grupos)]
    cuerpo.legend(handles=handles, loc="outside upper center", ncol=len(grupos), frameon=False, fontsize=9.5)
    return fig


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

    estilo_figuras.preparar()
    estilo_figuras.guardar(dibujar(filas, grupos), a.salida + ".png")
    print(f"{a.salida}.png y .csv · {len(filas)} canciones · grupos: {', '.join(grupos)}")


if __name__ == "__main__":
    main()
