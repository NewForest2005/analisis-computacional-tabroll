"""Compara los círculos armónicos de varias corridas y corre las pruebas de validación del círculo.

Uso:
    python scripts/comparar_circulos.py outputs/*_armonia_paso3
    python scripts/comparar_circulos.py outputs/*_armonia_paso3 --salida otra_comparacion.json
    python scripts/comparar_circulos.py outputs/*_armonia_paso3 --actualizar

Para cada corrida muestra la distancia entre sus dos mitades, la distancia a la canción más cercana y, si tiene
partitura, la distancia entre el círculo del audio y el de la partitura en los mismos compases. Después lista las
distancias entre canciones. Todas van de 0 (iguales) a 1.

Los círculos se rehacen siempre desde armonia.json con la celda actual del cuaderno. Con --actualizar, además se
reescriben circulo.json y circulo_armonico.png de cada corrida, sin volver a correr el cuaderno.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tabroll.evaluation.circulo import compare_runs, refresh_run  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas de corrida con armonia.json")
    ap.add_argument("--salida", type=Path, default=ROOT / "outputs" / "comparacion_circulos.json",
                    help="JSON con todo el detalle (por defecto en outputs/, que git ignora)")
    ap.add_argument("--actualizar", action="store_true", help="reescribe circulo.json y la figura de cada corrida")
    args = ap.parse_args(argv)
    if args.actualizar:
        for d in args.corridas:
            png = refresh_run(d)
            if png:
                print(f"Actualizado: {d.name}/circulo.json y {png.relative_to(d)}")
    r = compare_runs(args.corridas)
    if not r["circulos"]:
        print("Ninguna carpeta tiene armonia.json.")
        return 1
    short = lambda n: n[18:60] if len(n) > 18 and n[:4].isdigit() else n[:42]
    print(f"{'corrida':44s} {'centro':>6s} {'oído':>5s} {'mitades':>8s} {'+cercana':>9s} {'audio-partitura':>16s}")
    for n, c in r["circulos"].items():
        vs = r["audio_vs_partitura"].get(n, {}).get("combinada")
        near = r["cancion_mas_cercana"].get(n)
        print(f"{short(n):44s} {c['centro']:>6s} {c.get('tonica_de_oido') or '-':>5s} {r['mitades'][n]['combinada']:8.3f} "
              f"{near if near is not None else float('nan'):9.3f} {vs if vs is not None else '-':>16}")
    print("\nEntre canciones (de la más parecida a la menos):")
    for k, v in sorted(r["entre_canciones"].items(), key=lambda kv: kv[1]["combinada"]):
        a, b = k.split(" | ")
        print(f"    {short(a):42s} {short(b):42s} {v['combinada']:.3f}")
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nDetalle por capa en {args.salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

