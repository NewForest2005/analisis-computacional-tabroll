"""Radar de estilos de una canción, en dos gráficas dentro de una imagen: la estructura armónica y la estructura melódica.
Cada punta es un estilo o un rasgo, y la distancia al centro es el parecido (0-100).

Uso:
    python scripts/radar_de_estilos.py outputs/<corrida> [--titulo "Sarniezz"]

Usa las medidas de scripts/pruebas_de_estilo.py. Escribe radar_de_estilos.png y radar_de_estilos.json en la carpeta de la
corrida. Es una primera gráfica de referencia: cada punta usa una fórmula sencilla y distinta, así que las puntas no están
en la misma escala. Más adelante se cambia por una matriz de verosimilitud contra corpus.

ARMONÍA (fundamentales de los compases confiables):
- Rock, Práctica común, Pop: 100 × (1 − distancia de Jensen-Shannon entre las fundamentales de la canción y las del estilo).
- Pentatónica: % del tiempo en fundamentales de la pentatónica sobre el centro.
- Minimalismo (ciclos): % del tiempo dentro de ciclos repetidos de la voz grave.
- Microtonal (24-EDO): el doble del % del tiempo con la fundamental en cuarto de tono (50 % → 100).
- Jazz: cuota de cuarta ascendente entre los cambios, reescalada entre el rock (24,8 % → 0) y los estándares de jazz
  (55,8 % → 100); vale la mitad si a la tónica no se llega desde el quinto grado. Con menos de 8 cambios, 0.

MELODÍA (la voz aguda):
- Modal: % del tiempo en notas del modo de la canción (con sus grados en cuarto de tono, si los tiene).
- Pentatónica: % del tiempo en notas de la pentatónica sobre el centro.
- Minimalismo (ciclos): % del tiempo dentro de ciclos repetidos de la voz aguda.
- Microtonal (24-EDO): % del tiempo en cuartos de tono, reescalado entre el piso de ruido medido en música sin cuartos de
  tono (11 % → 0) y las 24 clases por igual (50 % → 100).
- Pasos de ¼ de tono (cromatismo) y de ¾ de tono (segunda neutra, la firma del maqam): % de los pasos entre notas seguidas.
- Dodecafonismo: entropía de las 12 clases, reescalada entre una escala de 7 notas usada por igual (2,81 bits → 0) y las 12
  por igual (3,58 bits → 100).
- Tonos enteros: % dentro de una escala de tonos enteros, reescalado (50 % es el azar → 0).
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pruebas_de_estilo as PE  # noqa: E402


def recorta(x: float) -> float:
    return round(max(0.0, min(100.0, x)), 1)


def parecidos(r: dict) -> tuple[dict, dict]:
    """(armonía, melodía): el parecido de 0 a 100 de cada punta."""
    armonia = {"Rock (corpus)": recorta(100 * (1 - r["distancia_rock"])),
               "Clásica (KP)": recorta(100 * (1 - r["distancia_practica_comun"])),
               "Jazz (iRealB)": recorta(100 * (1 - r["distancia_jazz"])) if r.get("distancia_jazz") is not None else 0.0,
               "Pentatónica": recorta(max(r["pentatonica_menor"], r["pentatonica_mayor"])),
               "Minimalismo\n(ciclos)": recorta(r["tiempo_en_ciclos"]),
               "Microtonal\n(24-EDO)": recorta(2 * r["fundamentales_cuarto_de_tono"]),
               "Jazz por movimiento": recorta(100 * (r["cuarta_ascendente"] - 24.8) / (PE.JAZZ_CUARTA_ASCENDENTE - 24.8) * (0.5 + 0.5 * min(1.0, r["antes_de_la_tonica"].get("V", 0.0) / 30)))
               if r["cambios"] >= 8 else 0.0}
    if "distancia_pop" in r:
        armonia["Pop (corpus)"] = recorta(100 * (1 - r["distancia_pop"]))
    if "distancia_pop" in r:
        armonia["Pop"] = recorta(100 * (1 - r["distancia_pop"]))
    melodia = {"Modal\n(el modo de la canción)": recorta(r["melodia_en_el_modo"]),
               "Pentatónica": recorta(r["melodia_pentatonica"]),
               "Minimalismo\n(ciclos)": recorta(r["melodia_en_ciclos"]),
               "Microtonal\n(24-EDO)": recorta(100 * (r["cuartos_de_tono_melodia"] - 11) / (50 - 11)),
               "Pasos de ¼ de tono\n(cromatismo)": recorta(r["paso_de_cuarto_de_tono"]),
               "Pasos de ¾ de tono\n(maqam)": recorta(r["paso_de_tres_cuartos"]),
               "Dodecafonismo": recorta(100 * (r["entropia_melodia_bits"] - math.log2(7)) / (math.log2(12) - math.log2(7))),
               "Tonos enteros": recorta(100 * (r["tonos_enteros"] - 50) / 50)}
    return armonia, melodia


def panel(ax, p: dict, titulo: str, color: str) -> None:
    import numpy as np

    tinta, gris, rejilla, fondo = "#0b0b0b", "#52514e", "#d9d8d2", "#fcfcfb"
    nombres, vals = list(p), list(p.values())
    ang = np.linspace(0, 2 * np.pi, len(vals), endpoint=False)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_facecolor(fondo)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100], ["25", "50", "75", "100"], fontsize=7.5, color=gris)
    ax.set_rlabel_position(180 / len(vals))
    ax.set_xticks(ang, [""] * len(vals))
    ax.grid(color=rejilla, lw=0.9)
    ax.spines["polar"].set_color(rejilla)
    cierre = np.append(ang, ang[0])
    ax.fill(cierre, vals + vals[:1], color=color, alpha=0.22)
    ax.plot(cierre, vals + vals[:1], color=color, lw=2)
    ax.scatter(ang, vals, s=42, color=color, zorder=3, edgecolors=fondo, linewidths=1.5)
    for a, n, v in zip(ang, nombres, vals):
        ha = "center" if abs(math.sin(a)) < 0.2 else "left" if math.sin(a) > 0 else "right"
        va = "bottom" if math.cos(a) > 0.5 else "top" if math.cos(a) < -0.5 else "center"
        ax.text(a, 108, n, ha=ha, va=va, fontsize=10, color=tinta, fontweight="bold", linespacing=1.1)
        ax.text(a, v + 10 if v < 80 else v - 13, f"{v:g}", ha="center", va="center", fontsize=9.5, color=color, fontweight="bold",
                bbox=dict(fc=fondo, ec="none", pad=1.2))
    ax.set_title(titulo, fontsize=13, fontweight="bold", color=tinta, pad=58)


def dibujar(armonia: dict, melodia: dict, salida: Path, titulo: str, sub: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tinta, gris, fondo = "#0b0b0b", "#52514e", "#fcfcfb"
    fig = plt.figure(figsize=(17, 9.2), facecolor=fondo)
    panel(fig.add_axes([0.11, 0.14, 0.31, 0.57], polar=True), armonia, "Estructura armónica", "#2a78d6")
    panel(fig.add_axes([0.60, 0.14, 0.31, 0.57], polar=True), melodia, "Estructura melódica", "#eb6834")
    fig.text(0.04, 0.95, titulo, fontsize=18, fontweight="bold", color=tinta)
    fig.text(0.04, 0.915, sub, fontsize=10.5, color=gris)
    fig.text(0.04, 0.025, "Parecido con cada estilo o rasgo, de 0 a 100. Primera referencia: cada punta usa una fórmula sencilla propia (ver el script), así que las puntas no "
             "están en la misma escala.\nArmonía: fundamentales de los compases confiables frente a cifras publicadas de rock (de Clercq y Temperley 2011), práctica común "
             "(Temperley 2009) y jazz (Broze y Shanahan 2013). Melodía: la voz aguda del cuaderno.", fontsize=8, color=gris)
    fig.savefig(salida, dpi=200, facecolor=fondo)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--titulo")
    a = ap.parse_args()
    for run in a.corridas:
        r = PE.medir(run)
        armonia, melodia = parecidos(r)
        limpio = lambda d: {k.replace("\n", " "): v for k, v in d.items()}
        p = dict(armonia=limpio(armonia), melodia=limpio(melodia))
        titulo = a.titulo or PE.nombre(run.name)
        sub = f"Angine de Poitrine · centro {r['centro']} · modo {r['modo']} · ¿a qué estilos se parece?" if "primus" not in run.name.lower() \
            else f"centro {r['centro']} · modo {r['modo']} · ¿a qué estilos se parece?"
        (run / "radar_de_estilos.json").write_text(json.dumps(p, ensure_ascii=False, indent=1), encoding="utf-8")
        dibujar(armonia, melodia, run / "radar_de_estilos.png", titulo, sub)
        print(run.name + ": " + json.dumps(p, ensure_ascii=False))


if __name__ == "__main__":
    main()
