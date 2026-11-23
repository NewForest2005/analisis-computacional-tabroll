#!/usr/bin/env python3
"""Corre las gráficas comparativas no-tabroll sobre las corridas existentes.

Selecciona la corrida más reciente por canción, regenera las gráficas por canción y
produce las comparaciones de la banda con Primus, King Gizzard, Zappa, King Crimson
y Gentle Giant, además de todos los corpus disponibles en references/corpus.

Con --clave solo corre lo necesario para las seis gráficas de la presentación (tres diapositivas de dos) y las
copia numeradas en <salida>/diapositivas/.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
OUT = OUTPUTS / f"graficas_completas_{datetime.now():%Y-%m-%d_%H%M}"
# Diapositiva 1: armonía fuera de todos los corpus · 2: cuartos de tono como grados fijos · 3: síntesis, un híbrido.
# Diapositiva 1: armonía fuera de todos los corpus · 2: cuartos de tono como grados fijos · 3: síntesis, un híbrido.
# La lista (origen, nombre en diapositivas/) se arma en main(), cuando ya se conoce la carpeta de salida.
CLAVE: list[tuple[Path, str]] = []
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


def main(argv: list[str] | None = None) -> int:
    global OUT
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clave", action="store_true", help="solo las seis gráficas de la presentación")
    args = ap.parse_args(argv)
    if args.clave:
        OUT = OUTPUTS / f"graficas_clave_{datetime.now():%Y-%m-%d_%H%M}"
    global CLAVE
    fuente = OUT / "fuente_diapositivas"
    CLAVE = [
        (fuente / "verosimilitud_banda_matriz.png", "1a_armonia_matriz_verosimilitud.png"),
        (fuente / "verosimilitud_banda_primus_mapa.png", "1b_armonia_mapa_fundamentales.png"),
        (fuente / "microtonal_banda_uso.png", "2a_melodia_uso_cuartos_de_tono.png"),
        (fuente / "figuras_album_c_circulo_haba.png", "2b_melodia_circulo_24edo.png"),
        (fuente / "ciclos_banda.png", "3a_sintesis_ciclos_metricos.png"),
        (fuente / "figuras_album_a_clasificacion.png", "3b_sintesis_clasificacion_album.png"),
        (fuente / "figuras_album_a_clasificacion_mapa.png", "3b_sintesis_clasificacion_mapa.png"),
        (fuente / "figuras_album_a_clasificacion_barras.png", "3c_sintesis_corpus_por_bloque.png"),
        # Apoyo: matriz con solo rock y pop (diapositiva 19), una mini-gráfica por fórmula (14) y el acierto (18).
        (fuente / "verosimilitud_banda_rock_pop_matriz.png", "1a_armonia_matriz_rock_pop.png"),
        (fuente / "presentacion_formula_js.png", "formula_js.png"),
        (fuente / "presentacion_formula_percentil.png", "formula_percentil.png"),
        (fuente / "presentacion_formula_repeticion.png", "formula_repeticion.png"),
        (fuente / "presentacion_formula_campos.png", "formula_campos.png"),
        (fuente / "presentacion_acierto.png", "acierto_herramienta.png"),
    ]
    failures: list[str] = []
    # Matplotlib hereda esta ruta en cada subproceso; evita la caché no escribible de macOS.
    cache = OUTPUTS / ".matplotlib"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(cache))

    # Las corridas con pistas de BS-RoFormer (docs/separacion_roformer.md) no entran: Demucs es el separador por defecto.
    banda = latest(("sarniezz", "mata_zyklek", "fabienk_official", "yor_zarad", "utzp", "angor"),
                   exclude=("king_gizzard", "primus", "king_crimson", "gentle_giant", "_roformer"))
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

    if args.clave:
        return clave(banda, primus, king_gizzard, todos, externos, paths, failures)

    for run in todos:
        call(["scripts/comparacion/tarjeta_cancion.py", str(run)], failures)
        call(["scripts/comparacion/tira_de_ciclos.py", str(run)], failures)

    # Ambos radares aceptan varias corridas; se cargan los corpus una sola vez.
    call(["scripts/comparacion/radar_de_estilos.py", *paths(todos)], failures)
    call(["scripts/comparacion/radar_ritmico.py", *paths(todos), "--salida", str(OUT / "radar_ritmico_comparado.png")], failures)

    call(["scripts/comparacion/pruebas_de_estilo.py", *paths(todos), "--salida", str(OUT / "pruebas_de_estilo")], failures)
    call(["scripts/comparacion/verosimilitud_estilos.py", *paths(todos), "--salida", str(OUT / "verosimilitud")], failures)
    call(["scripts/comparacion/microtonal.py", *paths(todos), "--salida", str(OUT / "microtonal")], failures)
    call(["scripts/comparacion/ciclos_metricos.py", *paths(todos), "--salida", str(OUT / "ciclos_metricos")], failures)

    call(["scripts/comparacion/campos_haba.py", *paths(banda), "--control", *paths(primus),
          "--comparar", *paths(externos), "--salida", str(OUT / "campos_haba")], failures)
    call(["scripts/comparacion/verosimilitud_por_bloques.py", *paths(banda), "--control", *paths(primus),
          "--comparar", *paths(externos), "--salida", str(OUT / "bloques")], failures)
    call(["scripts/comparacion/comparar_tarjetas.py", *paths(todos), "--salida", str(OUT / "comparacion_tarjetas")], failures)

    for nombre, repertorio in (("king_gizzard", king_gizzard), ("zappa", zappa),
                               ("king_crimson", king_crimson), ("gentle_giant", gentle_giant)):
        if repertorio:
            call(["scripts/comparacion/comparar_repertorio.py", *paths(banda), "--repertorio", *paths(repertorio),
                  "--control", *paths(primus), "--nombre", nombre.replace("_", " ").title(),
                  "--salida", str(OUT / f"comparar_{nombre}")], failures)

    call(["scripts/comparacion/equivalencias_edo.py", *paths(banda), "--salida", str(OUT / "equivalencias_edo")], failures)

    bloques = OUT / "bloques.json"
    campos = OUT / "campos_haba"
    fases = OUT / "ciclos_metricos_fases.csv"
    if bloques.exists():
        call(["scripts/comparacion/figuras_album.py", *paths(banda), "--control", *paths(primus),
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


def clave(banda, primus, king_gizzard, todos, externos, paths, failures: list[str]) -> int:
    """Solo los scripts de las gráficas de la presentación; las copia en diapositivas/ (las seis principales, numeradas)."""
    call(["scripts/comparacion/verosimilitud_estilos.py", *paths(todos), "--salida", str(OUT / "verosimilitud")], failures)
    call(["scripts/comparacion/microtonal.py", *paths(todos), "--salida", str(OUT / "microtonal")], failures)
    call(["scripts/comparacion/ciclos_metricos.py", *paths(todos), "--salida", str(OUT / "ciclos_metricos")], failures)
    call(["scripts/comparacion/verosimilitud_por_bloques.py", *paths(banda), "--control", *paths(primus),
          "--comparar", *paths(externos), "--salida", str(OUT / "bloques")], failures)
    call(["scripts/comparacion/figuras_album.py", *paths(banda), "--control", *paths(primus),
          "--comparar", *paths(king_gizzard), "--bloques", str(OUT / "bloques.json"), "--salida", str(OUT / "figuras_album")],
         failures)
    # Versiones para diapositiva (no tocan las salidas normales de arriba): solo las 6 canciones de la banda en la
    # matriz, los cuartos de tono y los ciclos; en el mapa, la banda frente a Primus con estrellas grandes. Sin
    # subtítulos ni notas al pie: esos textos van como leyenda debajo de cada imagen en la presentación.
    fuente = OUT / "fuente_diapositivas"
    fuente.mkdir(exist_ok=True)
    call(["scripts/comparacion/verosimilitud_estilos.py", *paths(banda), "--diapositiva",
          "--salida", str(fuente / "verosimilitud_banda")], failures)
    call(["scripts/comparacion/verosimilitud_estilos.py", *paths(banda + primus), "--diapositiva",
          "--salida", str(fuente / "verosimilitud_banda_primus")], failures)
    call(["scripts/comparacion/microtonal.py", *paths(banda), "--diapositiva", "--salida", str(fuente / "microtonal_banda")], failures)
    call(["scripts/comparacion/ciclos_metricos.py", *paths(banda), "--diapositiva", "--salida", str(fuente / "ciclos_banda")], failures)
    call(["scripts/comparacion/verosimilitud_estilos.py", *paths(banda), "--estilos", "rock,pop", "--diapositiva",
          "--salida", str(fuente / "verosimilitud_banda_rock_pop")], failures)
    # Clasificación y círculo de 24-EDO sin subtítulos ni notas, con los círculos de cada canción más grandes.
    call(["scripts/comparacion/figuras_album.py", *paths(banda), "--bloques", str(OUT / "bloques.json"), "--diapositiva",
          "--salida", str(fuente / "figuras_album")], failures)
    # El acierto se mide en las corridas congeladas «_repro», las mismas de docs/evaluacion_melodia.md y docs/armonia.md.
    repro = sorted(r for r in OUTPUTS.iterdir() if r.name.endswith("_repro") and (r / "evaluacion_melodia.json").exists())
    # Las fórmulas de la diapositiva 14 se ilustran con Primus para no adelantar los resultados de la banda.
    call(["scripts/comparacion/figuras_presentacion.py", *paths(banda + primus), "--evaluaciones", *map(str, repro),
          "--salida", str(fuente / "presentacion")], failures)
    destino = OUT / "diapositivas"
    destino.mkdir(exist_ok=True)
    faltan = []
    for origen, nombre in CLAVE:
        if origen.exists():
            shutil.copy2(origen, destino / nombre)
        else:
            faltan.append(str(origen))
    print(f"\nDiapositivas: {destino}")
    for _, nombre in CLAVE:
        print("  ", nombre)
    if failures or faltan:
        for item in failures + [f"falta {f}" for f in faltan]:
            print("  fallo:", item)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

