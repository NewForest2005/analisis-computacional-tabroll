"""Tira de ciclos de una corrida: una fila por patrón de ciclo, con sus acordes como círculos de color, al estilo de los
análisis de álbum de Hooktheory y adaptada a 24-EDO.

Uso:
    python scripts/comparacion/tira_de_ciclos.py outputs/<corrida> [--titulo "Fabienk"] [--voz grave|aguda]

Lee armonia.json (resumen → patrones). Escribe tira_de_ciclos.png y tira_de_ciclos.json en la carpeta de la corrida.
- Color = grado de la fundamental respecto del centro medido: 1 rojo, 2 naranja, 3 amarillo, 4 verde, 5 azul, 6 morado,
  7 rosa. Un grado cromático (♭ o ♯) va con los dos colores vecinos, mitad y mitad. Un cuarto de tono lleva un aro
  negro y «+» en el cifrado.
- A la derecha de cada fila: cuántas vueltas da el patrón y cuánto dura la vuelta.
- Si la canción no tiene ciclos (no usa looper), no hay tira: el script lo dice y no escribe la imagen.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

COLORES = {1: "#F90002", 2: "#FBB014", 3: "#EFE602", 4: "#3CD301", 5: "#4824FF", 6: "#B720E5", 7: "#F81CCB"}
ROMANOS = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7}


def grado(cifrado: str):
    """(grado 1-7, alteración -1/0/+1, cuarto de tono) de un cifrado como «♭VIIsus2» o «♭II+5»."""
    m = re.match(r"([♭♯]*)([ivIV]+)(\+?)", cifrado)
    if not m or m.group(2).upper() not in ROMANOS:
        return None
    alt = sum(-1 if c == "♭" else 1 for c in m.group(1))
    return ROMANOS[m.group(2).upper()], max(-1, min(1, alt)), bool(m.group(3))


def filas(run: Path, voz: str | None = None) -> list[dict]:
    H = json.loads((run / "armonia.json").read_text(encoding="utf-8"))
    pat = (H.get("resumen") or {}).get("patrones") or {}
    orden = [f"Voz {voz}"] if voz else ["Voz grave", "Voz aguda"]
    out = []
    for v in orden:
        for letra, x in (pat.get(v) or {}).items():
            acordes = (x.get("acorde_usual") or "").split()
            if acordes:
                out.append(dict(voz=v, patron=letra, acordes=acordes, vueltas=x.get("vueltas"), periodo_s=x.get("periodo_s"),
                                inicio_s=min(s[0] for s in x["segmentos"]) if x.get("segmentos") else 0.0))
        if out and not voz:                                             # por defecto, la voz grave; la aguda solo si la grave no tiene ciclos
            break
    return sorted(out, key=lambda f: f["inicio_s"])


def dibujar(fs: list[dict], salida: Path, titulo: str, centro: str | None, modo: str | None) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle, Wedge

    tinta, gris, fondo = "#0b0b0b", "#52514e", "#fcfcfb"
    n = max(len(f["acordes"]) for f in fs)
    ancho, alto = max(7.0, 2.6 + 1.05 * n + 2.4), 1.3 + 1.35 * len(fs)
    fig = plt.figure(figsize=(ancho, alto), facecolor=fondo)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, ancho)
    ax.set_ylim(0, alto)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(0.4, alto - 0.5, f"{titulo}: ciclos armónicos repetidos", fontsize=15, fontweight="bold", color=tinta, va="center")
    ax.text(0.4, alto - 0.9, f"Centro {centro or '—'} · modo {modo or '—'} · color = grado de la fundamental · × = vueltas · s = duración de vuelta", fontsize=9.5, color=gris, va="center")
    for k, f in enumerate(fs):
        y = alto - 1.9 - 1.35 * k
        ax.text(0.4, y, f"{f['patron']}", fontsize=13, fontweight="bold", color=tinta, va="center")
        ax.text(0.85, y, f["voz"].replace("Voz ", ""), fontsize=8.5, color=gris, va="center")
        for i, c in enumerate(f["acordes"]):
            x = 2.2 + 1.05 * i
            g = grado(c)
            if g is None:
                ax.add_patch(Circle((x, y + 0.12), 0.36, fc="#d9d8d2", ec="none"))
            else:
                num, alt, cuarto = g
                if alt == 0:
                    ax.add_patch(Circle((x, y + 0.12), 0.36, fc=COLORES[num], ec="none"))
                else:
                    otro = (num - 2) % 7 + 1 if alt < 0 else num % 7 + 1
                    ax.add_patch(Wedge((x, y + 0.12), 0.36, 90, 270, fc=COLORES[otro if alt < 0 else num], ec="none"))
                    ax.add_patch(Wedge((x, y + 0.12), 0.36, 270, 90, fc=COLORES[num if alt < 0 else otro], ec="none"))
                if cuarto:
                    ax.add_patch(Circle((x, y + 0.12), 0.36, fc="none", ec=tinta, lw=2.2))
            ax.text(x, y - 0.46, c, fontsize=9.5, color=tinta, ha="center", va="center", family="serif")
        ax.text(2.2 + 1.05 * n + 0.1, y + 0.12, f"×{f['vueltas']}" if f["vueltas"] else "", fontsize=12, fontweight="bold", color=tinta, va="center")
        ax.text(2.2 + 1.05 * n + 0.1, y - 0.25, f"{f['periodo_s']:.2f} s por vuelta" if f["periodo_s"] else "", fontsize=8.5, color=gris, va="center")
    fig.savefig(salida, dpi=200, facecolor=fondo)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--titulo")
    ap.add_argument("--voz", choices=("grave", "aguda"), help="por defecto la grave; la aguda si la grave no tiene ciclos")
    a = ap.parse_args()
    for run in a.corridas:
        fs = filas(run, a.voz)
        if not fs:
            print(f"{run.name}: sin ciclos, no hay tira")
            continue
        res = json.loads((run / "armonia.json").read_text(encoding="utf-8")).get("resumen") or {}
        titulo = a.titulo or re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", run.name).replace("_", " ")[:40]
        (run / "tira_de_ciclos.json").write_text(json.dumps(fs, ensure_ascii=False, indent=2), encoding="utf-8")
        dibujar(fs, run / "tira_de_ciclos.png", titulo, res.get("centro"), (res.get("modo") or {}).get("nombre"))
        print(run.name + ": " + " | ".join(f"{f['patron']} ×{f['vueltas']}: {' '.join(f['acordes'])}" for f in fs))


if __name__ == "__main__":
    main()
