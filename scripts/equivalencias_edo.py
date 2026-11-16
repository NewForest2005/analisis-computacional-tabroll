"""¿Cómo serían las progresiones conocidas «al estilo Angine de Poitrine», y qué pasa en 19, 31 o 53 notas por octava?

Uso:
    python scripts/equivalencias_edo.py outputs/*angine_de_poitrine* outputs/*fabienk_official_audio_repro [--edo 12 19 22 24 31 53 72] \
        --salida outputs/equivalencias_edo

1. Campos de quintas de cada sistema n-EDO: la quinta mide q = round(n·log2(3/2)) pasos y el ciclo de quintas se parte en
   mcd(q, n) campos. 24-EDO: q = 14, dos campos (Hába). 19, 22, 31, 53: uno. 36: tres. 72: seis.
2. Cómo encaja lo que toca la banda: el reparto del tiempo de la melodía en los 24 grados (respecto del centro, todo el
   disco) se proyecta en cada n-EDO (paso más cercano). Error medio ponderado por uso, en cents, y error de los grados en
   cuarto de tono por separado. Un sistema de un solo campo que conserve los cuartos de tono con poco error sería el
   equivalente «sin dos campos» del lenguaje de la banda.
3. Intervalos de referencia (justos y neutros) en cada sistema, para leer los errores.
4. Progresiones conocidas en grados y en pasos de cada sistema, y su versión «Vol. II»: la banda casi no pone acordes en
   cuarto de tono (los cuartos van en la melodía, sobre fundamentales regulares; ver campos_haba.py). La traducción es
   entonces: mismas fundamentales, y la escala de la melodía cambia los grados 2, 3, 6 y 7 por los grados en cuarto de
   tono que más usa el disco en ese lugar (medido, no elegido). Es una regla, no una composición.

Escribe <salida>.md, <salida>.json y <salida>.png (error por grado usado y sistema).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figuras_album import grado24, nombre, orden_banda, reparto, unicas  # noqa: E402

INTERVALOS = [("quinta justa 3/2", 3 / 2), ("tercera mayor 5/4", 5 / 4), ("tercera menor 6/5", 6 / 5), ("séptima armónica 7/4", 7 / 4),
              ("tercera neutra 11/9", 11 / 9), ("segunda neutra 12/11", 12 / 11), ("sexta neutra 13/8", 13 / 8), ("cuarta undecimal 11/8", 11 / 8)]
PROGRESIONES = [("I–V–vi–IV (pop)", ["I", "V", "vi", "IV"]), ("ii–V–I (jazz)", ["ii", "V", "I"]), ("I–IV–V (blues, rock)", ["I", "IV", "V"]),
                ("I–♭VII–IV (rock modal)", ["I", "♭VII", "IV"]), ("i–♭VII–♭VI–V (andaluza)", ["i", "♭VII", "♭VI", "V"]),
                ("I–♭III–♭VII (lo que mide el cuaderno en Fabienk y Sarniezz)", ["I", "♭III", "♭VII"])]
ROM = {"I": 0, "II": 2, "III": 4, "IV": 5, "V": 7, "VI": 9, "VII": 11}


def cents(n: int, pasos: int) -> float:
    return 1200 * pasos / n


def paso(n: int, c: float) -> int:
    return round(c * n / 1200)


def raiz(r: str) -> tuple[int, bool]:
    alt = -1 if r.startswith("♭") else 1 if r.startswith("♯") else 0
    base = r.lstrip("♭♯")
    return (ROM[base.upper()] + alt) % 12, base.islower()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--edo", nargs="+", type=int, default=[12, 19, 22, 24, 31, 36, 53, 72])
    ap.add_argument("--salida", default="outputs/equivalencias_edo")
    a = ap.parse_args()

    runs = sorted(unicas(a.corridas), key=lambda r: orden_banda(nombre(r.name)))
    uso = np.zeros(24)
    for r in runs:
        alt, _ = reparto(r)
        if alt.sum():
            uso += alt / alt.sum()
    uso /= uso.sum()
    print("Disco:", ", ".join(nombre(r.name) for r in runs))

    md = ["# Equivalencias en otros sistemas de afinación", "", f"Canciones: {', '.join(nombre(r.name) for r in runs)}.", "",
          "## 1 y 2. Campos de quintas y cómo encaja lo que toca la banda", "",
          "| Sistema | Paso (c) | Quinta (pasos, error c) | Campos de quintas | Error medio de los grados usados (c) | Error en los grados ¼ (c) | Grados ¼ que se funden con un vecino regular |",
          "|---|---|---|---|---|---|---|"]
    tabla, err_grado = [], {}
    for n in a.edo:
        q = round(n * math.log2(1.5))
        campos = math.gcd(q, n)
        e = np.array([abs(cents(n, paso(n, 50 * d)) - 50 * d) for d in range(24)])
        destino = [paso(n, 50 * d) % n for d in range(24)]
        fundidos = [grado24(d) for d in range(1, 24, 2) if uso[d] > 0.005 and destino[d] in (destino[d - 1], destino[(d + 1) % 24])]
        em = float((e * uso).sum())
        eq = float((e[1::2] * uso[1::2]).sum() / uso[1::2].sum()) if uso[1::2].sum() else float("nan")
        err_grado[n] = e
        tabla.append(dict(edo=n, paso_c=round(1200 / n, 1), quinta_pasos=q, quinta_error=round(cents(n, q) - 1200 * math.log2(1.5), 1),
                          campos=campos, error_medio=round(em, 1), error_cuartos=round(eq, 1), cuartos_fundidos=fundidos))
        md.append(f"| {n}-EDO | {1200 / n:.1f} | {q} ({cents(n, q) - 1200 * math.log2(1.5):+.1f}) | {campos} | {em:.1f} | {eq:.1f} | "
                  f"{', '.join(fundidos) or 'ninguno'} |")
        print(f"{n:3d}-EDO: quinta {q} pasos, {campos} campo(s), error medio {em:.1f} c, en ¼ {eq:.1f} c, ¼ fundidos: {fundidos or 'ninguno'}")

    md += ["", "Grados del disco más usados (todo el disco, % del tiempo de la melodía): " +
           ", ".join(f"{grado24(d)} {100 * uso[d]:.1f}" for d in np.argsort(uso)[::-1][:12]), "",
           "## 3. Intervalos de referencia", "", "| Intervalo | Cents | " + " | ".join(f"{n}-EDO" for n in a.edo) + " |",
           "|---|---|" + "---|" * len(a.edo)]
    for nom, r in INTERVALOS:
        c = 1200 * math.log2(r)
        md.append(f"| {nom} | {c:.0f} | " + " | ".join(f"{paso(n, c)} ({cents(n, paso(n, c)) - c:+.0f})" for n in a.edo) + " |")

    # versión Vol. II: para cada grado diatónico 2, 3, 6, 7, la variante más usada del disco (regular o ¼) en su vecindad
    vecinos = {"2": [2, 3, 4, 5], "3": [6, 7, 8, 9], "6": [16, 17, 18, 19], "7": [20, 21, 22, 23]}
    escala = {g: max(ds, key=lambda d: uso[d]) for g, ds in vecinos.items()}
    escala_txt = "1 · " + " · ".join(f"{grado24(escala[g])}" for g in ("2", "3")) + " · 4 · 5 · " + " · ".join(grado24(escala[g]) for g in ("6", "7"))
    md += ["", "## 4. Progresiones conocidas y su versión «Vol. II»", "",
           f"Escala de la melodía del disco (la variante más usada de cada grado móvil, medida): **{escala_txt}**.",
           "Las fundamentales quedan en el campo regular (así lo hace la banda); la melodía usa esa escala, con sus grados en ¼ en el otro campo.", "",
           "| Progresión | Fundamentales (pasos en " + ", ".join(f"{n}" for n in a.edo) + "-EDO) | Grados de la melodía en ¼ sobre cada acorde |", "|---|---|---|"]
    top_q = [int(d) for d in np.argsort(uso[1::2])[::-1][:3] * 2 + 1]
    md.insert(len(md) - 3, f"Grados en ¼ más usados del disco (los que se ponen sobre cada acorde): {', '.join(grado24(d) for d in top_q)}. "
              "Sobre cada acorde se dan como intervalo desde su fundamental.")
    ejemplos = []
    for nom, prog in PROGRESIONES:
        pasos_txt = []
        for n in a.edo:
            pasos_txt.append("·".join(str(paso(n, 100 * raiz(r)[0])) for r in prog))
        sobre = []
        for r in prog:
            p, _ = raiz(r)
            q24 = top_q
            rel = sorted({grado24((d - 2 * p) % 24) for d in q24})
            sobre.append(f"{r}: {', '.join(rel)}")
        ejemplos.append(dict(progresion=nom, grados=prog, pasos={n: t for n, t in zip(a.edo, pasos_txt)}, cuartos_sobre_cada_acorde=sobre))
        md.append(f"| {nom} | {' / '.join(f'{n}: {t}' for n, t in zip(a.edo, pasos_txt))} | {'; '.join(sobre)} |")
    md += ["", "Lectura: en 24-EDO los grados en ¼ de la escala del disco quedan en el otro campo de quintas que las fundamentales, y la "
           "melodía cruza de campo. En un sistema de un solo campo (19, 31, 53) esa separación desaparece: los mismos sonidos quedan a "
           "distancia de quintas de la fundamental. Ver la tabla 1 para saber cuánto se desafinan y cuáles se funden con un grado regular."]

    Path(a.salida + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    Path(a.salida + ".json").write_text(json.dumps(dict(sistemas=tabla, escala_disco=escala_txt, uso={grado24(d): round(100 * uso[d], 2) for d in range(24)},
                                                       progresiones=ejemplos), ensure_ascii=False, indent=1), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    usados = [d for d in range(24) if uso[d] > 0.005]
    M = np.array([[err_grado[n][d] for d in usados] for n in a.edo])
    fig, ax = plt.subplots(figsize=(1.2 + 0.62 * len(usados), 1.4 + 0.45 * len(a.edo)), facecolor="#fcfcfb")
    cmap = LinearSegmentedColormap.from_list("e", ["#f1f0ea", "#9ec5f4", "#3987e5", "#184f95", "#0d366b"])
    ax.imshow(M, cmap=cmap, vmin=0, vmax=25, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:.0f}", ha="center", va="center", fontsize=8, color="#ffffff" if M[i, j] > 12 else "#0b0b0b")
    ax.set_xticks(range(len(usados)), [f"{grado24(d)}\n{100 * uso[d]:.0f} %" for d in usados], fontsize=8)
    ax.set_yticks(range(len(a.edo)), [f"{n}-EDO ({t['campos']} campo{'s' if t['campos'] > 1 else ''})" for n, t in zip(a.edo, tabla)], fontsize=8.5)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title("Error (cents) de cada grado que usa el disco al pasarlo a otro sistema (debajo: % del tiempo de la melodía)",
                 loc="left", fontsize=10, color="#0b0b0b")
    fig.tight_layout()
    fig.savefig(a.salida + ".png", dpi=200, facecolor="#fcfcfb")
    print(f"→ {a.salida}.md/.json/.png")


if __name__ == "__main__":
    main()
