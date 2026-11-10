"""Ruido de muestreo de las capas de transiciones y movimientos según el número de cambios de fundamental.

Uso:
    python scripts/ruido_cambios.py outputs/*_armonia_paso3

De cada canción con al menos 40 cambios se sacan dos muestras de n cambios de sus propios cambios (con reemplazo) y se
mide su distancia en cada capa. Las dos muestras vienen de la misma canción, así que todo lo que no sea 0 es ruido de
tener pocos cambios. Es la tabla que justifica el peso de esas capas en `change_weight`
(src/tabroll/evaluation/circulo.py).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tabroll.cells.harmony_circle import harmony_circle  # noqa: E402
from tabroll.evaluation.circulo import js, run_circle  # noqa: E402


def changes(bars: list[dict]) -> list[tuple[int, int]]:
    """Cambios de fundamental entre compases confiables seguidos, como los cuenta harmony_circle."""
    ok = {b["compas"]: b for b in bars if b.get("fundamental_pc24") is not None and b.get("confianza", 0) >= 0.5}
    return [(ok[k - 1]["fundamental_pc24"], b["fundamental_pc24"]) for k, b in ok.items()
            if k - 1 in ok and ok[k - 1]["fundamental_pc24"] != b["fundamental_pc24"]]


def circle_of(sample: list[tuple[int, int]], center: int) -> dict:
    """Círculo de una muestra de cambios: cada cambio es un par de compases, separado del siguiente por un hueco."""
    bar = lambda k, pc: dict(compas=k, inicio_s=float(k), fin_s=k + 1.0, fundamental_pc24=pc, calidad="5", confianza=1.0,
                             perfil_bajo=[0.0] * 24, perfil_aguda=[0.0] * 24)
    return harmony_circle([b for i, (a, z) in enumerate(sample) for b in (bar(3 * i, a), bar(3 * i + 1, z))], center)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas de corrida con armonia.json")
    ap.add_argument("--pares", type=int, default=400, help="pares de muestras por canción y por n")
    args = ap.parse_args(argv)
    rng = np.random.default_rng(0)
    songs = {}
    for d in args.corridas:
        rc = run_circle(d)
        if rc:
            ch = changes(rc[2]["compases"])
            if len(ch) >= 40:
                songs[d.name] = (ch, rc[1])
    if not songs:
        print("Ninguna corrida tiene 40 cambios o más.")
        return 1
    print("Canciones usadas: " + ", ".join(f"{n} ({len(v[0])} cambios)" for n, v in songs.items()))
    print(f"\n{'cambios':>8s} {'transiciones':>13s} {'movimientos':>12s}")
    for n in (3, 5, 6, 10, 15, 20, 30, 40):
        t, m = [], []
        for ch, center in songs.values():
            for _ in range(args.pares):
                a, b = (circle_of([ch[i] for i in rng.integers(len(ch), size=n)], center) for _ in range(2))
                t.append(js(a["transiciones"], b["transiciones"]))
                m.append(js(a["movimientos"], b["movimientos"]))
        print(f"{n:8d} {np.mean(t):13.3f} {np.mean(m):12.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
