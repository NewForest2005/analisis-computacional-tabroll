"""Corre todo el proyecto sobre las cinco canciones de la banda y junta el tabroll y las demás gráficas en una carpeta.

    python scripts/todo.py                 # usa la corrida más reciente de cada canción que ya esté en outputs/
    python scripts/todo.py --correr        # primero vuelve a correr el cuaderno en las cinco (tarda: varios minutos cada una)
    python scripts/todo.py --otras primus  # además compara con las corridas cuyo nombre contenga «primus»

Pasos, por canción: (1) cuaderno completo con run_song.py, solo con --correr o si la canción no tiene corrida;
(2) tarjeta resumen; (3) tira de ciclos. Al final: (4) comparación de tarjetas y pruebas de estilo de la banda (y de --otras);
(5) copia a outputs/graficas_<fecha>/<canción>/ el mapa de armonía, el círculo armónico, los ciclos, la tarjeta y la tira,
y escribe un índice (indice.md) y las líneas de las tarjetas (tarjetas.jsonl). No copia el tabroll.

Si un paso falla en una canción, sigue con las demás y lo dice al final. No cambia el cuaderno ni las referencias.
Utzp entra como una canción más: desde que sus salidas se usan aquí, deja de servir como prueba a ciegas.
"""
from __future__ import annotations

import argparse
import datetime
import json
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CANCIONES = [("Sarniezz", "sarniezz"), ("Mata Zyklek", "mata_zyklek"), ("Fabienk", "fabienk"), ("Yor Zarad", "yor_zarad"), ("Utzp", "utzp")]
PATRONES = ["circulo_armonico*.png", "mapa_ciclos*.png", "ciclo_*.png", "tarjeta*.png", "tira_de_ciclos.png",
            "radar_de_estilos.png", "radar_ritmico.png"]


def mas_reciente(salidas: Path, clave: str) -> Path | None:
    """La corrida más reciente de una canción que terminó bien (tiene armonia.json)."""
    runs = [d for d in salidas.iterdir() if d.is_dir() and clave in d.name.lower() and (d / "armonia.json").exists()]
    return max(runs, key=lambda d: d.name) if runs else None


def correr(args: list[str]) -> tuple[bool, str]:
    r = subprocess.run([sys.executable, *args], cwd=RAIZ, capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--correr", action="store_true", help="vuelve a correr el cuaderno en las cinco canciones")
    ap.add_argument("--otras", action="append", default=[], metavar="TEXTO", help="grupo extra para comparar (p. ej. primus)")
    ap.add_argument("--salidas", default=str(RAIZ / "outputs"))
    a = ap.parse_args()
    salidas = Path(a.salidas)
    destino = salidas / f"graficas_{datetime.datetime.now():%Y-%m-%d_%H%M}"
    destino.mkdir(parents=True, exist_ok=True)
    fallos, usadas, lineas = [], {}, []

    for titulo, clave in CANCIONES:
        run = None if a.correr else mas_reciente(salidas, clave)
        if run is None:
            print(f"[{titulo}] corriendo el cuaderno…", flush=True)
            ok, txt = correr(["scripts/run_song.py", titulo, "--salidas", str(salidas)])
            if not ok:
                fallos.append((titulo, "cuaderno", txt[-600:]))
            run = mas_reciente(salidas, clave)
        if run is None:
            fallos.append((titulo, "sin corrida", "no hay ninguna corrida con armonia.json"))
            continue
        usadas[titulo] = run
        print(f"[{titulo}] {run.name}", flush=True)
        ok, txt = correr(["scripts/tarjeta_cancion.py", str(run), "--titulo", titulo])
        if ok:
            lineas.append(txt.splitlines()[-1])
        else:
            fallos.append((titulo, "tarjeta", txt[-600:]))
        ok, txt = correr(["scripts/tira_de_ciclos.py", str(run), "--titulo", titulo])
        if not ok:
            fallos.append((titulo, "tira de ciclos", txt[-600:]))

    # comparación de tarjetas: la banda sola y, si se pide, con otros grupos
    runs = [str(r) for r in usadas.values()]
    grupos = []
    for texto in a.otras:
        extra = sorted({d.name: d for d in salidas.iterdir() if d.is_dir() and texto.lower() in d.name.lower() and (d / "armonia.json").exists()}.values())
        por_cancion = {}
        for d in extra:                                                 # la corrida más reciente de cada canción del grupo
            por_cancion[d.name.split("_", 2)[-1]] = d
        for d in por_cancion.values():
            ok, txt = correr(["scripts/tarjeta_cancion.py", str(d)])
            if ok:
                lineas.append(txt.splitlines()[-1])
                runs.append(str(d))
            else:
                fallos.append((d.name, "tarjeta", txt[-600:]))
        grupos += ["--grupo", f"{texto.capitalize()}={texto}"]
    if runs:
        ok, txt = correr(["scripts/comparar_tarjetas.py", *runs, *grupos, "--salida", str(destino / "comparacion_tarjetas")])
        if not ok:
            fallos.append(("todas", "comparación de tarjetas", txt[-600:]))

    # pruebas de estilo: cada canción frente a rock, práctica común, jazz, pentatónica, tonos enteros, dodecafonismo, etc.
    if runs:
        ok, txt = correr(["scripts/pruebas_de_estilo.py", *runs, "--salida", str(destino / "pruebas_de_estilo")])
        if not ok:
            fallos.append(("todas", "pruebas de estilo", txt[-600:]))

    # radares por canción: estilo (armonía y melodía) y estructura rítmica
    if runs:
        ok, txt = correr(["scripts/radar_de_estilos.py", *runs])
        if not ok:
            fallos.append(("todas", "radar de estilos", txt[-600:]))
        ok, txt = correr(["scripts/radar_ritmico.py", *runs, "--salida", str(destino / "radar_ritmico_comparado.png")])
        if not ok:
            fallos.append(("todas", "radar rítmico", txt[-600:]))

    # copiar las gráficas
    indice = [f"# Gráficas del {datetime.datetime.now():%Y-%m-%d %H:%M}", ""]
    for titulo, run in usadas.items():
        d = destino / titulo.replace(" ", "_")
        d.mkdir(exist_ok=True)
        n = 0
        for patron in PATRONES:
            for f in sorted(run.rglob(patron)):
                shutil.copy2(f, d / f.name)
                n += 1
        for nombre in ("resumen.md", "tarjeta.json", "tira_de_ciclos.json", "evaluacion_melodia.json", "evaluacion_melodia_por_seccion.csv",
                       "armonia.json", "armonia_por_compas.csv", "evaluacion_armonia.json", "evaluacion_armonia_por_compas.csv",
                       "evaluacion_armonia_referencias.json", "evaluacion_armonia_referencias_por_compas.csv",
                       "radar_de_estilos.json", "radar_ritmico.json"):
            if (run / nombre).exists():
                shutil.copy2(run / nombre, d / nombre)
        indice.append(f"- **{titulo}**: {n} imágenes, de `{run.name}`")
    (destino / "tarjetas.jsonl").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    if fallos:
        indice += ["", "## Pasos que fallaron", ""] + [f"- {t} · {paso}: `{msg.splitlines()[-1] if msg else ''}`" for t, paso, msg in fallos]
    (destino / "indice.md").write_text("\n".join(indice) + "\n", encoding="utf-8")

    print(f"\nListo: {destino}")
    print(f"Canciones: {', '.join(usadas) or 'ninguna'} | tarjetas: {len(lineas)} | fallos: {len(fallos)}")
    for t, paso, msg in fallos:
        print(f"  FALLÓ {t} · {paso}\n    " + msg.replace("\n", "\n    "))


if __name__ == "__main__":
    main()
