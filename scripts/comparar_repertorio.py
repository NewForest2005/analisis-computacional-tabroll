"""Compara canción por canción a la banda con un repertorio (King Gizzard) y con el control (Primus).

Uso:
    python scripts/comparar_repertorio.py <corridas de la banda> --repertorio outputs/*king_gizzard* \
        --control <corridas de Primus> [--nombre "King Gizzard"] --salida outputs/comparar_kg

Tres distancias de Jensen-Shannon entre dos canciones (0 = iguales, 1 = nada en común):
- armonía: media de fundamentales (12) y cambios de fundamental (144), como en verosimilitud_por_bloques.py;
- cuartos de tono: SOLO el reparto del tiempo entre los 12 grados en cuarto de tono (cuáles se usan), sin los semitonos;
- metro: reparto por familia de compás.
«Todo a la vez» = la mayor de las tres: dos canciones están cerca en todo solo si lo están en cada bloque.
Para leer la escala se dan las mismas distancias entre los temas del repertorio y entre los de la banda.
No es un test con percentiles: el repertorio tiene pocas piezas. Es una comparación directa.

Escribe <salida>.csv, <salida>.json y <salida>.png (distancias de cuartos de tono y de todo a la vez).
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verosimilitud_por_bloques import concentracion, js_pares, nombre, rasgos_cancion  # noqa: E402

GRADOS = ["1", "♭2", "2", "♭3", "3", "4", "♯4", "5", "♭6", "6", "♭7", "7"]


def js(a: np.ndarray, b: np.ndarray) -> float:
    return float(js_pares(a[None], b[None])[0, 0])


def cuartos(r: dict) -> np.ndarray:
    o = r["alt24"][1::2]
    return o / o.sum() if o.sum() else o


def distancias(x: dict, y: dict) -> dict:
    a = js(x["fundamentales"], y["fundamentales"])
    if x["cambios_v"] is not None and y["cambios_v"] is not None:
        a = (a + js(x["cambios_v"], y["cambios_v"])) / 2
    d = dict(armonia=a, cuartos=js(cuartos(x), cuartos(y)), metro=js(x["metro"], y["metro"]))
    d["todo"] = max(d.values())
    return d


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("banda", nargs="+", type=Path)
    ap.add_argument("--repertorio", nargs="+", type=Path, required=True)
    ap.add_argument("--control", nargs="*", type=Path, default=[])
    ap.add_argument("--nombre", default="King Gizzard")
    ap.add_argument("--salida", default="outputs/comparar_repertorio")
    a = ap.parse_args()

    # sin el nombre del grupo delante (King Gizzard, King Crimson, Gentle Giant…)
    corto = lambda r: re.sub(r"^(king gizzard( and the lizard wizard)?|king crimson|gentle giant|primus) ", "", nombre(r.name).lower()).capitalize()
    def unicas(lista: list[Path]) -> list[Path]:
        """Sin corridas repetidas (globs que se solapan) ni dos corridas de la misma canción (se queda la última)."""
        por_nombre = {}
        for r in sorted(lista, key=lambda r: r.name):
            por_nombre[corto(r)] = r
        return list(por_nombre.values())

    a.banda, a.repertorio, a.control = unicas(a.banda), unicas(a.repertorio), unicas(a.control)
    R = {r: rasgos_cancion(r) for r in a.banda + a.repertorio + a.control}
    for r, x in R.items():
        x["top"] = [GRADOS[i] + "+" for i in np.argsort(cuartos(x))[::-1][:2]]
        x["conc"] = concentracion(x["alt24"])[1]

    filas = []
    for b in a.banda:
        for grupo, lista in (("repertorio", a.repertorio), ("control", a.control)):
            for o in lista:
                d = distancias(R[b], R[o])
                filas.append(dict(cancion=corto(b), grupo=grupo, comparada=corto(o), **{k: round(v, 3) for k, v in d.items()}))
    escala = {g: sorted(round(distancias(R[x], R[y])["todo"], 3) for x, y in itertools.combinations(l, 2))
              for g, l in (("entre_repertorio", a.repertorio), ("entre_banda", a.banda))}

    print("Grados en ¼ de tono más usados (concentración en los dos primeros):")
    for r in a.banda + a.repertorio + a.control:
        print(f"  {corto(r):26s} {' y '.join(R[r]['top']):10s} {R[r]['conc']:.0f} %")
    print(f"\nMás parecida de cada grupo (distancia; 0 = igual):")
    resumen = []
    for b in a.banda:
        linea = {"cancion": corto(b)}
        partes = []
        for grupo in ("repertorio", "control"):
            fs = [f for f in filas if f["cancion"] == corto(b) and f["grupo"] == grupo]
            if not fs:
                continue
            for k in ("cuartos", "todo"):
                m = min(fs, key=lambda f: f[k])
                linea[f"{k}_{grupo}"] = (m["comparada"], m[k])
            partes.append(f"{a.nombre if grupo == 'repertorio' else 'control'}: ¼ {linea['cuartos_' + grupo][0]} {linea['cuartos_' + grupo][1]:.2f}, "
                          f"todo {linea['todo_' + grupo][0]} {linea['todo_' + grupo][1]:.2f}")
        resumen.append(linea)
        print(f"  {corto(b):12s} " + " | ".join(partes))
    print(f"\nEscala de «todo a la vez»: entre temas de {a.nombre} {escala['entre_repertorio']}; entre temas de la banda {escala['entre_banda']}")

    with open(a.salida + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    Path(a.salida + ".json").write_text(json.dumps(dict(filas=filas, escala=escala, grados={corto(r): dict(top=R[r]["top"], concentracion=round(R[r]["conc"], 1))
                                                                                          for r in R}), ensure_ascii=False, indent=1), encoding="utf-8")
    dibujar(a, R, filas, escala, corto)


def dibujar(a, R, filas, escala, corto) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    tinta, gris, fondo = "#0b0b0b", "#52514e", "#fcfcfb"
    cmap = LinearSegmentedColormap.from_list("cerca", ["#0d3c78", "#2a78d6", "#a9c8ef", "#f1f0ea"])
    cols = a.repertorio + a.control
    etiquetas = [f"{corto(c)}\n({' '.join(R[c]['top'])})" for c in cols]
    filas_b = [f"{corto(b)}  ({' '.join(R[b]['top'])})" for b in a.banda]
    fig, ejes = plt.subplots(1, 2, figsize=(4 + 2.1 * len(cols), 1.8 + 0.62 * len(a.banda)), facecolor=fondo)
    for ax, k, titulo in ((ejes[0], "cuartos", "Distancia microtonal: grados en ¼ de tono"), (ejes[1], "todo", "Distancia conjunta: armonía, ¼ de tono y metro")):
        M = np.array([[next(f[k] for f in filas if f["cancion"] == corto(b) and f["comparada"] == corto(c)) for c in cols] for b in a.banda])
        ax.imshow(M, cmap=cmap, vmin=0, vmax=0.8, aspect="auto")
        for i in range(M.shape[0]):
            j0 = int(np.argmin(M[i, :len(a.repertorio)]))
            for j in range(M.shape[1]):
                ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=9.5, color="#ffffff" if M[i, j] < 0.3 else tinta,
                        fontweight="bold" if j == j0 else "normal")
        ax.axvline(len(a.repertorio) - 0.5, color=fondo, lw=5)
        ax.set_xticks(range(len(cols)), etiquetas, fontsize=8.3, color=tinta)
        ax.set_yticks(range(len(a.banda)), filas_b if ax is ejes[0] else [""] * len(a.banda), fontsize=9.5, color=tinta)
        ax.xaxis.tick_top()
        ax.tick_params(length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(titulo, loc="left", fontsize=11, color=tinta, pad=52)
        ax.text(len(a.repertorio) / 2 - 0.5, M.shape[0] - 0.3 + 0.75, a.nombre, ha="center", fontsize=9, color=gris)
        if a.control:
            ax.text(len(a.repertorio) + len(a.control) / 2 - 0.5, M.shape[0] - 0.3 + 0.75, "Primus (control)", ha="center", fontsize=9, color=gris)
    fig.suptitle(f"Comparación de {a.nombre} con su repertorio y el control Primus", x=0.01, ha="left", fontsize=13, color=tinta)
    fig.text(0.01, 0.01, f"Distancia de Jensen-Shannon (0 = iguales; más oscuro = más parecido); en negrita, el tema de {a.nombre} más cercano. "
             f"Entre paréntesis, los dos grados en ¼ de tono más usados.\n«Todo a la vez» = la mayor de las tres distancias. Escala: entre temas de {a.nombre} "
             f"{min(escala['entre_repertorio']):.2f}–{max(escala['entre_repertorio']):.2f}; entre temas de la banda {min(escala['entre_banda']):.2f}–{max(escala['entre_banda']):.2f}.",
             fontsize=7.5, color=gris)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(a.salida + ".png", dpi=200, facecolor=fondo)
    plt.close(fig)


if __name__ == "__main__":
    main()
