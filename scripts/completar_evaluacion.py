"""Vuelve a medir corridas ya hechas contra las partituras corregidas y actualiza su resumen, sin correr el cuaderno.

Uso:
    python scripts/completar_evaluacion.py outputs/*_armonia_paso3

Sirve cuando la evaluación falló dentro de run_song.py o cuando cambia la evaluación. Reescribe evaluacion_*.json y
sus .csv, y actualiza evaluacion_melodia y evaluacion_armonia en resumen.json y resumen.md. Las canciones sin
partitura de evaluación quedan igual.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_song import evaluate_against_score, write_markdown  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas de corrida con resumen.json")
    args = ap.parse_args(argv)
    print(f"{'corrida':58s} {'melodía':>8s} {'fundamental':>12s} {'confiables':>11s} {'avisos':>7s}")
    for run in args.corridas:
        res = run / "resumen.json"
        if not res.exists():
            print(f"{run.name[:58]:58s} (sin resumen.json)")
            continue
        info = json.loads(res.read_text(encoding="utf-8"))
        found, avisos = evaluate_against_score(run, info.get("cancion") or run.name, (run / "armonia.json").exists())
        info["avisos"] = [a for a in info.get("avisos", []) if not a.startswith("No se pudo evaluar")] + avisos
        info.update(found)
        res.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        write_markdown(run / "resumen.md", info)
        em, ea = found.get("evaluacion_melodia") or {}, found.get("evaluacion_armonia") or {}
        print(f"{run.name[:58]:58s} {em.get('principal', '-'):>8} {ea.get('fundamental', '-'):>12} "
              f"{ea.get('fundamental_confiables', '-'):>11} {len(avisos):>7d}")
        for a in avisos:
            print(f"    {a}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

