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


def nombre(corrida: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", corrida)
    n = re.sub(r"(angine_de_poitrine_|primus_|_audio_off\w*|_official_audio|_repro|_\d{4}_\w+$)", "", n)
    return n.replace("_", " ").strip().capitalize()


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
        r["grupo"] = next((n for n, t in reglas if t.lower() in run.name.lower()), "Angine de Poitrine")
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
    fig, ejes = plt.subplots(2, 3, figsize=(15, 1.6 + 0.62 * len(filas)), facecolor=fondo)
    y = list(range(len(filas)))[::-1]
    for ax, (m, titulo) in zip(ejes.flat, MEDIDAS):
        vals = [r.get(m) for r in filas]
        ax.barh(y, [v or 0 for v in vals], color=[COLORES[grupos.index(r["grupo"]) % 4] for r in filas], height=0.62)
        tope = max([v for v in vals if v is not None] + [1])
        for yi, v, r in zip(y, vals, filas):
            txt = "sin cambios" if v is None and m == "novedad_progresion" else "—" if v is None else f"{v:g}"
            if m == "novedad_progresion" and v is not None:
                txt += f"  ({r.get('cambios_distintos', 0)})"
            ax.text((v or 0) + tope * 0.02, yi, txt, va="center", fontsize=9, color=tinta)
        if m == "novedad_progresion" and filas[0].get("novedad_progresion_pop"):
            p = filas[0]["novedad_progresion_pop"]
            ax.axvline(p, color=gris, lw=1)
            ax.text(p, len(filas) - 0.45, f"pop {p:g}", fontsize=8, color=gris, ha="center")
        ax.set_yticks(y, [r["cancion"] for r in filas] if ax in ejes[:, 0] else [""] * len(filas), fontsize=9.5)
        ax.set_xlim(0, tope * 1.25)
        ax.set_ylim(-0.6, len(filas) - 0.1)
        ax.set_title(titulo, loc="left", fontsize=10.5, color=tinta)
        ax.set_facecolor(fondo)
        ax.tick_params(colors=gris, length=0, labelsize=8.5)
        ax.grid(axis="x", color=rejilla, lw=0.8)
        ax.set_axisbelow(True)
        for s in ax.spines.values():
            s.set_visible(False)
    fig.suptitle("Comparación de métricas estructurales entre canciones", x=0.012, ha="left", fontsize=14, color=tinta)
    fig.text(0.012, 0.955, "Barras: valores crudos de la canción; unidades según cada panel. Colores = grupos de comparación.", fontsize=8.5, color=gris)
    for k, g in enumerate(grupos):
        fig.text(0.012 + 0.16 * k, 0.975, "■ " + g, color=COLORES[k % 4], fontsize=11, fontweight="bold", va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(a.salida + ".png", dpi=200, facecolor=fondo)
    print(f"{a.salida}.png y .csv · {len(filas)} canciones · grupos: {', '.join(grupos)}")


if __name__ == "__main__":
    main()
