"""Notas de Basic Pitch para las pistas de guitarra de las corridas de limpieza.

Uso:
    .venv-bp/bin/python scripts/basic_pitch_notas.py outputs/limpieza/*_limpieza
    .venv-bp/bin/python scripts/basic_pitch_notas.py outputs/limpieza/*_limpieza --rehacer

Guarda <canción>_basic_pitch.json junto a la pista de guitarra usando el ajuste de notas cortas.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))
from diagnostico_capas import find_guitar_stem  # noqa: E402

CONFIG = dict(onset_threshold=0.4, frame_threshold=0.3, minimum_note_length=58.0)


def bp_path(stem: Path) -> Path:
    base = stem.stem[: -len("_guitar")] if stem.stem.endswith("_guitar") else stem.stem
    return stem.with_name(base + "_basic_pitch.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas de corrida")
    ap.add_argument("--rehacer", action="store_true", help="vuelve a calcular aunque el archivo exista")
    args = ap.parse_args(argv)
    from basic_pitch import ICASSP_2022_MODEL_PATH
    from basic_pitch.inference import Model, predict
    model = None
    for run in args.corridas:
        if not (run / "resumen.json").exists():
            print(f"{run.name}: sin resumen.json")
            continue
        stem = find_guitar_stem(run)
        if stem is None:
            print(f"{run.name}: no encontré la pista de guitarra")
            continue
        out = bp_path(stem)
        if out.exists() and not args.rehacer:
            print(f"{out.name}: ya existe")
            continue
        if model is None:
            model = Model(ICASSP_2022_MODEL_PATH)
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            _, _, events = predict(str(stem), model, **CONFIG)
        notes = sorted([round(float(e[0]), 4), round(float(e[1]), 4), float(e[2]), round(float(e[3]), 4)] for e in events)
        data = dict(formato="tabroll-basic-pitch-v1", pista=stem.name, ajuste=CONFIG, notas=notes)
        out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print(f"{out.name}: {len(notes)} notas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
