#!/usr/bin/env python3
"""Convierte una partitura Guitar Pro 8 en JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tabroll.reference.guitarpro import parse_gp as parse_score_json


def parse_gp(path: str | Path) -> dict:
    """Compatibilidad para consumidores que importaban el script anterior."""
    return parse_score_json(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="archivo Guitar Pro .gp")
    parser.add_argument("-o", "--output", type=Path, help="archivo JSON de salida; por defecto, stdout")
    parser.add_argument("--pretty", action="store_true", help="formatea el JSON con indentación")
    args = parser.parse_args(argv)
    text = json.dumps(parse_score_json(args.file), ensure_ascii=False, indent=2 if args.pretty else None) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
