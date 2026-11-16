"""Compara canción por canción a la banda con un repertorio y con controles.

Uso:
    python scripts/comparar_repertorio.py <corridas de la banda> --repertorio outputs/*king_gizzard* \
        --control <corridas de Primus> --salida outputs/comparar_kg

Calcula distancias de Jensen-Shannon para armonía, cuartos de tono y metro,
además de una distancia conjunta («todo a la vez»).
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
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
    armonia = js(x["fundamentales"], y["fundamentales"])
    if x["cambios_v"] is not None and y["cambios_v"] is not None:
        armonia = (armonia + js(x["cambios_v"], y["cambios_v"])) / 2
    d = dict(armonia=armonia, cuartos=js(cuartos(x), cuartos(y)), metro=js(x["metro"], y["metro"]))
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

    corto = lambda r: nombre(r.name).replace("King gizzard ", "").capitalize()
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
    print("\nMás parecida de cada grupo (distancia; 0 = igual):")
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
    Path(a.salida + ".json").write_text(json.dumps(dict(filas=filas, escala=escala,
        grados={corto(r): dict(top=R[r]["top"], concentracion=round(R[r]["conc"], 1)) for r in R}),
        ensure_ascii=False, indent=1), encoding="utf-8")
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
    for ax, k, titulo in ((ejes[0], "cuartos", "Qué grados en ¼ de tono se usan"), (ejes[1], "todo", "Todo a la vez (armonía, ¼ de tono y metro)")):
        M = np.array([[next(f[k] for f in filas if f["cancion"] == corto(b) and f["comparada"] == corto(c)) for c in cols] for b in a.banda])
        ax.imshow(M, cmap=cmap, vmin=0, vmax=0.8, aspect="auto")
        for i in range(M.shape[0]):
            j0 = int(np.argmin(M[i, :len(a.repertorio)]))
            for j in range(M.shape[1]):
                ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=9.5,
                        color="#ffffff" if M[i, j] < 0.3 else tinta, fontweight="bold" if j == j0 else "normal")
        ax.axvline(len(a.repertorio) - 0.5, color=fondo, lw=5)
        ax.set_xticks(range(len(cols)), etiquetas, fontsize=8.3, color=tinta)
        ax.set_yticks(range(len(a.banda)), filas_b if ax is ejes[0] else [""] * len(a.banda), fontsize=9.5, color=tinta)
        ax.xaxis.tick_top(); ax.tick_params(length=0)
        for s in ax.spines.values(): s.set_visible(False)
        ax.set_title(titulo, loc="left", fontsize=11, color=tinta, pad=52)
    fig.tight_layout()
    fig.savefig(a.salida + ".png", dpi=200, facecolor=fondo)
    plt.close(fig)


if __name__ == "__main__":
    main()
