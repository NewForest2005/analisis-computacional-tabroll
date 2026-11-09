"""Mide la voz aguda y la voz grave de una o varias corridas contra las partituras corregidas.

Uso:
    python scripts/evaluar_melodia.py outputs/2026-11-09_*            # una o varias carpetas de corrida
    python scripts/evaluar_melodia.py outputs/<carpeta> --cancion sarniezz

Escribe evaluacion_melodia.json y evaluacion_melodia_por_seccion.csv dentro de cada carpeta.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tabroll.evaluation.melodia import CANCIONES, evaluate_run  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas de corrida con line_diagnostics.json")
    ap.add_argument("--cancion", choices=sorted(CANCIONES), help="fuerza la canción (si el nombre de la carpeta no la dice)")
    ap.add_argument("--secciones", action="store_true", help="muestra también el detalle por sección")
    args = ap.parse_args(argv)
    print(f"{'corrida':58s} {'principal':>9s} {'sin 8va':>8s} {'+aguda':>7s} {'bajo':>6s} {'medible':>8s}")
    found = 0
    for run in args.corridas:
        r = evaluate_run(run, args.cancion)
        if r is None:
            print(f"{run.name[:58]:58s} (sin partitura de evaluación o sin line_diagnostics.json)")
            continue
        found += 1
        print(f"{run.name[:58]:58s} {r['principal']:9.1f} {r['principal_sin_octava']:8.1f} {r['mas_aguda']:7.1f} "
              f"{r['bajo']:6.1f} {r['tiempo_medible']:7.0f}%")
        if args.secciones:
            for s in r["secciones"]:
                if s["notas"]:
                    print(f"    {s['seccion'][:56]:56s} n={s['notas']:4d}  principal {s['principal']}  más aguda {s['mas_aguda']}")
    return 0 if found else 1


if __name__ == "__main__":
    raise SystemExit(main())
