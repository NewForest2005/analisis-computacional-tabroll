#!/usr/bin/env python3
"""Corre las gráficas comparativas no-tabroll sobre las corridas existentes.

Selecciona la corrida más reciente por canción, regenera las gráficas por canción y
produce las comparaciones de la banda con Primus, King Gizzard, Zappa, King Crimson
y Gentle Giant, además de todos los corpus disponibles en references/corpus.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
OUT = OUTPUTS / f"graficas_completas_{datetime.now():%Y-%m-%d_%H%M}"
ZAPPA_KEYS = ("g_spot_tornado", "inca_roads", "peaches_en_regalia", "the_black_page", "zomby_woof")


def song_name(run: Path) -> str:
    try:
        return str(json.loads((run / "resumen.json").read_text(encoding="utf-8")).get("cancion") or run.name)
    except (OSError, json.JSONDecodeError):
        return run.name


def latest(keys: tuple[str, ...], exclude: tuple[str, ...] = ()) -> list[Path]:
    found: dict[str, Path] = {}
    for run in OUTPUTS.iterdir():
        if not run.is_dir() or not (run / "armonia.json").exists() or not (run / "line_diagnostics.json").exists():
            continue
        low = run.name.lower()
        if not any(k in low for k in keys) or any(k in low for k in exclude):
            continue
        found[song_name(run).lower()] = max(found.get(song_name(run).lower(), run), run, key=lambda p: p.name)
    return sorted(found.values(), key=lambda p: p.name)


def call(args: list[str], failures: list[str]) -> None:
    command = [sys.executable, *args]
    print("→", " ".join(args))
    result = subprocess.run(command, cwd=ROOT)
    if result.returncode:
        failures.append(" ".join(args))


def main() -> int:
    failures: list[str] = []
    # Matplotlib hereda esta ruta en cada subproceso; evita la caché no escribible de macOS.
    cache = OUTPUTS / ".matplotlib"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))

    banda = latest(("sarniezz", "mata_zyklek", "fabienk_official", "yor_zarad", "utzp", "angor"),
                   exclude=("king_gizzard", "primus", "king_crimson", "gentle_giant"))
    primus = latest(("primus",))
    king_gizzard = latest(("king_gizzard",))
    king_crimson = latest(("king_crimson",))
    gentle_giant = latest(("gentle_giant",))
    zappa = latest(ZAPPA_KEYS)

    if not banda:
        raise SystemExit("No se encontraron corridas de Angine de Poitrine.")
    OUT.mkdir(parents=True, exist_ok=True)

    grupos = {
        "banda": banda,
        "primus": primus,
        "king_gizzard": king_gizzard,
        "zappa": zappa,
        "king_crimson": king_crimson,
        "gentle_giant": gentle_giant,
    }
    for nombre, runs in grupos.items():
        print(f"{nombre}: {len(runs)} canciones")

    todos = banda + primus + king_gizzard + zappa + king_crimson + gentle_giant
    externos = king_gizzard + zappa + king_crimson + gentle_giant

    def paths(runs: list[Path]) -> list[str]:
        return [str(r) for r in runs]

    for run in todos:
        call(["scripts/tarjeta_cancion.py", str(run)], failures)
        call(["scripts/tira_de_ciclos.py", str(run)], failures)

    # Ambos radares aceptan varias corridas; se cargan los corpus una sola vez.
    call(["scripts/radar_de_estilos.py", *paths(todos)], failures)
    call(["scripts/radar_ritmico.py", *paths(todos), "--salida", str(OUT / "radar_ritmico_comparado.png")], failures)

    call(["scripts/pruebas_de_estilo.py", *paths(todos), "--salida", str(OUT / "pruebas_de_estilo")], failures)
    call(["scripts/verosimilitud_estilos.py", *paths(todos), "--salida", str(OUT / "verosimilitud")], failures)
    call(["scripts/microtonal.py", *paths(todos), "--salida", str(OUT / "microtonal")], failures)
    call(["scripts/ciclos_metricos.py", *paths(todos), "--salida", str(OUT / "ciclos_metricos")], failures)

    call(["scripts/campos_haba.py", *paths(banda), "--control", *paths(primus),
          "--comparar", *paths(externos), "--salida", str(OUT / "campos_haba")], failures)
    call(["scripts/verosimilitud_por_bloques.py", *paths(banda), "--control", *paths(primus),
          "--comparar", *paths(externos), "--salida", str(OUT / "bloques")], failures)
    call(["scripts/comparar_tarjetas.py", *paths(todos), "--salida", str(OUT / "comparacion_tarjetas")], failures)

    for nombre, repertorio in (("king_gizzard", king_gizzard), ("zappa", zappa),
                               ("king_crimson", king_crimson), ("gentle_giant", gentle_giant)):
        if repertorio:
            call(["scripts/comparar_repertorio.py", *paths(banda), "--repertorio", *paths(repertorio),
                  "--control", *paths(primus), "--nombre", nombre.replace("_", " ").title(),
                  "--salida", str(OUT / f"comparar_{nombre}")], failures)

    call(["scripts/equivalencias_edo.py", *paths(banda), "--salida", str(OUT / "equivalencias_edo")], failures)

    bloques = OUT / "bloques.json"
    campos = OUT / "campos_haba"
    fases = OUT / "ciclos_metricos_fases.csv"
    if bloques.exists():
        call(["scripts/figuras_album.py", *paths(banda), "--control", *paths(primus),
              "--comparar", *paths(king_gizzard), "--bloques", str(bloques), "--campos", str(campos),
              "--fases", str(fases), "--salida", str(OUT / "figuras_album")], failures)

    print(f"\nSalida completa: {OUT}")
    if failures:
        print(f"Fallos: {len(failures)}")
        for failure in failures:
            print("  ", failure)
        return 1
    print("Todas las gráficas no-tabroll terminaron correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

