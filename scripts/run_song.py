"""Corre el notebook completo sobre una canción y guarda todo en outputs/.

    python scripts/run_song.py Fabienk
    python scripts/run_song.py "Mata Zyklek" --preset mata_zyklek
    python scripts/run_song.py "ruta/Cancion.mp3" --sin-pistas --set GRID=0.5 --nombre prueba-grid
    python scripts/run_song.py --presets

Cada corrida crea outputs/<fecha>_<hora>_<canción>[_<nombre>]/ con:

    harmony_outputs/   las imágenes del notebook: tabroll, mapa de ciclos y ciclos
    salida.txt         todo lo que imprime el notebook, los avisos y el tiempo de cada celda
    resumen.md         tempo, tonalidad, compases, ciclos y capas, para leer o pegar en el chat
    resumen.json       lo mismo en formato estructurado, para comparar corridas

El notebook no se modifica: los cambios de --preset y --set se aplican a una copia en memoria.
Las pistas _guitar y _bass se buscan junto a la canción; si no hay, la celda 1b las crea con
Demucs y este script las deja junto a la canción para la próxima vez.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback
import unicodedata
import warnings
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
OUTPUTS = ROOT / "outputs"
AUDIO_EXT = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aiff", ".aif"}
AUDIO_FOLDER = "Angine de Poitrine Audios"
MARKER = ".corrida"


# ---------------------------------------------------------------- notebook

def load_code_cells(notebook: Path = NOTEBOOK) -> list[tuple[int, str]]:
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    return [(i, "".join(c["source"])) for i, c in enumerate(cells) if c["cell_type"] == "code"]


def without_magics(source: str) -> str:
    """Los comandos de Jupyter (!pip, %...) no son Python: se dejan como comentario."""
    return "\n".join("# " + line if line.lstrip().startswith(("!", "%")) else line for line in source.splitlines())


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()


def name_key(text: str) -> str:
    """Normaliza mayúsculas y tildes para seleccionar canciones por nombre."""
    return "".join(ch for ch in unicodedata.normalize("NFKD", str(text).casefold()) if not unicodedata.combining(ch))


def find_song(selector: str) -> Path:
    """Resuelve una ruta o una parte del nombre dentro de la carpeta de audios."""
    candidate = Path(selector).expanduser()
    if candidate.is_file():
        return candidate.resolve()

    folder = ROOT / AUDIO_FOLDER
    if not folder.is_dir():
        raise SystemExit(f"No existe la carpeta de audios: {folder}")
    is_stem = lambda p: re.search(r"(^|_)(guitar|bass|other|drums|vocals|piano)( \(\d+\))?$", p.stem.lower())
    found = [p for p in folder.rglob("*") if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in AUDIO_EXT and not is_stem(p)]
    key = name_key(selector)
    hits = [p for p in found if key in name_key(p.relative_to(folder))]
    if len(hits) > 1:
        exact = [p for p in hits if key in (name_key(p.name), name_key(p.stem))]
        hits = exact or hits
    if len(hits) > 1:
        official = [p for p in hits if re.search(r"off?ici(al|el)", name_key(p.stem))]
        hits = official or hits
    if len(hits) > 1:
        preferred = [p for p in hits if name_key(p.stem).startswith(key) and "official audio" in name_key(p.stem)]
        hits = preferred if len(preferred) == 1 else hits
    if len(hits) != 1:
        listed = "\n  ".join(str(p.relative_to(folder)) for p in (hits or sorted(found)))
        detail = "coincide con varios audios" if hits else "no coincide con ningún audio"
        raise SystemExit(f"'{selector}' {detail}. Opciones:\n  {listed}")
    return hits[0].resolve()


def find_presets(cells: list[tuple[int, str]]) -> dict[str, tuple[int, list[str]]]:
    """Presets de la celda de ajustes: un comentario '# Para <Canción> ...' seguido de líneas '# X = ...'."""
    presets = {}
    for k, (_, source) in enumerate(cells):
        lines = source.splitlines()
        for j, line in enumerate(lines):
            m = re.match(r"#\s*Para\s+([^(:]+)", line)
            if not m:
                continue
            body = []
            for nxt in lines[j + 1:]:
                if not re.match(r"#\s*[A-Za-z_][\w\s,]*=", nxt):
                    break
                body.append(re.sub(r"^#\s?", "", nxt))
            if body:
                presets[slug(m.group(1))] = (k, body)
    return presets


def assigns(line: str, name: str) -> bool:
    """¿La línea asigna `name` a nivel de celda? (también en asignaciones múltiples: A, B = ...)."""
    m = re.match(r"([A-Za-z_][\w\s,]*?)\s*=(?!=)", line)
    return bool(m) and name in [t.strip() for t in m.group(1).split(",")]


def apply_changes(cells: list[tuple[int, str]], preset: str | None, changes: dict[str, str]) -> list[tuple[int, str]]:
    cells = [(i, s) for i, s in cells]

    if preset:
        preset = slug(preset)
        presets = find_presets(cells)
        if preset not in presets:
            raise SystemExit(f"No hay un preset '{preset}'. Disponibles: {', '.join(sorted(presets)) or 'ninguno'}")
        k, body = presets[preset]
        i, source = cells[k]
        for line in body:
            source = source.replace("# " + line, line, 1) if "# " + line in source else source.replace("#" + line, line, 1)
        cells[k] = (i, source)

    for name, value in changes.items():
        try:
            compile(f"{name} = {value}", "--set", "exec")
        except SyntaxError as e:
            raise SystemExit(f"--set {name}={value}: no es Python válido ({e.msg})") from None

        for k, (i, source) in enumerate(cells):
            lines = source.splitlines()
            hits = [j for j, line in enumerate(lines) if assigns(line, name)]
            if hits:
                lines.insert(hits[-1] + 1, f"{name} = {value}                                    # --set de run_song.py")
                cells[k] = (i, "\n".join(lines))
                break
        else:
            raise SystemExit(f"--set {name}: el notebook no asigna esa variable en ninguna celda.")

    return cells


# ---------------------------------------------------------------- archivos

def find_stem(audio: Path, kind: str) -> Path | None:
    key = name_key(f"{audio.stem}_{kind}")
    hits = [p for p in audio.parent.rglob("*")
            if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in AUDIO_EXT and name_key(p.stem).startswith(key)]
    return max(hits, key=lambda p: (p.parent == audio.parent, p.stat().st_mtime)) if hits else None


def link_or_copy(src: Path, dest: Path) -> None:
    try:
        os.link(src, dest)                                                           # mismo disco: no ocupa espacio extra
    except OSError:
        shutil.copy2(src, dest)


def make_run_dir(base: Path, audio: Path, name: str | None) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run = base / "_".join(x for x in (stamp, slug(audio.stem)[:40], slug(name or "")) if x)
    for k in range(2, 100):                                                          # dos corridas en el mismo segundo
        if not run.exists():
            break
        run = run.with_name(f"{run.name.rsplit('__', 1)[0]}__{k}")
    run.mkdir(parents=True)
    (run / MARKER).write_text("Carpeta creada por scripts/run_song.py\n", encoding="utf-8")
    return run


def prune(base: Path, keep: int, current: Path) -> list[Path]:
    runs = sorted(p for p in base.iterdir() if p.is_dir() and (p / MARKER).is_file())
    old = [p for p in runs[:-keep] if p != current] if keep > 0 else []
    for p in old:
        shutil.rmtree(p)
    return old


def git_version() -> str:
    try:
        rev = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "notebooks"], capture_output=True, text=True).stdout.strip()
        return rev + (" (notebook con cambios sin commit)" if dirty else "")
    except Exception:
        return "desconocida"


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, text):
        for s in self.streams:
            s.write(text)
        return len(text)

    def flush(self):
        for s in self.streams:
            s.flush()


# ---------------------------------------------------------------- resumen

def mmss(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def plain(x):
    """Convierte tuplas y tipos de numpy a algo que JSON entienda."""
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if isinstance(x, Path):
        return str(x)
    if hasattr(x, "item") and not isinstance(x, (str, bytes)):
        try:
            return x.item()
        except (ValueError, AttributeError):
            pass
    return x


def summary(ns: dict) -> dict:
    get = ns.get
    out = {}

    if "y" in ns and "sr" in ns:
        out["duracion_s"] = round(len(ns["y"]) / ns["sr"], 1)
    if "tempo" in ns:
        out["tempo_bpm"] = round(float(ns["tempo"]), 1)
    if "scale" in ns and "mode" in ns:
        out["tonalidad"] = f"{ns['scale'].names[0]} {ns['mode']}"
        out["escala"] = list(ns["scale"].names)
    if "off" in ns:
        out["desafinacion_cents"] = round(float(ns["off"]) * 100)
    if get("key_alts") and "make_scale" in ns:
        out["tonalidad_dudosa"] = [f"{ns['make_scale'](t, m)[0].names[0]} {m}" for t, m in ns["key_alts"]]
    for key, var in (("notas", "notes"), ("acordes", "chords"), ("compases", "measures")):
        if var in ns:
            out[key] = len(ns[var])
    if "lens" in ns:
        lens = list(ns["lens"])
        out["compases_por_duracion"] = {str(L): lens.count(L) for L in sorted(set(lens))}

    if isinstance(get("cycles"), dict):
        bar_of, sub = get("bar_of"), get("sub", 1)
        out["ciclos"] = {
            voice: [{
                "letra": c.label, "inicio": mmss(c.start), "fin": mmss(c.end),
                "inicio_s": round(c.start, 2), "fin_s": round(c.end, 2), "periodo_s": round(c.period, 3),
                "compases": round(c.slots / sub / bar_of(c), 3) if bar_of and getattr(c, "slots", 0) else None,
                "vueltas": round((c.end - c.start) / c.period),
                "se_repite": round(float(c.score), 2), "dobla_al_bajo": bool(getattr(c, "doubled", 0) >= 0.8),
            } for c in group]
            for voice, group in ns["cycles"].items()
        }

    if get("layers"):
        events = ns["layers"][0]
        out["capas"] = {"loop_s": round(float(get("loop", 0)), 3),
                        "eventos": [{"tipo": k, "t": mmss(t), "t_s": round(float(t), 1)} for t, k in events]}

    out["ajustes_finales"] = {k: plain(ns[k]) for k in ("KEY_OVERRIDE", "TEMPO_OVERRIDE", "BAR_LENGTHS", "FORCE_BAR_BEATS",
                                                        "BEAT_DIV", "GRID", "MICRO_STEP", "HAS_DRUMS", "FINE_ROWS") if k in ns}
    return plain(out)


def write_markdown(path: Path, info: dict) -> None:
    r = info.get("resultado", {})
    L = [f"# {info['cancion']}", "",
         f"- Corrida: `{info['carpeta']}` ({info['fecha']}), notebook {info['version_notebook']}",
         f"- Estado: **{info['estado']}**" + (f" en la celda {info['celda_con_error']}" if info.get("celda_con_error") is not None else ""),
         f"- Pistas: guitarra `{info['pistas']['guitarra'] or 'ninguna'}`, bajo `{info['pistas']['bajo'] or 'ninguna'}`"
         + (" (creadas con Demucs)" if info["pistas"]["creadas_con_demucs"] else ""),
         f"- Preset: {info['preset'] or 'ninguno'} | cambios: {', '.join(f'{k}={v}' for k, v in info['cambios'].items()) or 'ninguno'}",
         f"- Tiempo: {info['tiempo_s']} s" + (f" | RAM máxima: {info['ram_max_mb']} MB" if info.get("ram_max_mb") else ""), ""]

    if r:
        L += ["## Resultado", ""]
        if "duracion_s" in r:
            L.append(f"- Duración: {r['duracion_s']} s | tempo: {r.get('tempo_bpm')} BPM")
        if "tonalidad" in r:
            L.append(f"- Tonalidad: {r['tonalidad']} ({' '.join(r['escala'])}) | desafinación: {r.get('desafinacion_cents', 0):+d} cents")
        if r.get("tonalidad_dudosa"):
            L.append(f"- Tonalidad dudosa: {', '.join(r['tonalidad_dudosa'])}")
        if "compases_por_duracion" in r:
            L.append("- Compases por duración: " + ", ".join(f"{k} pulsos ×{v}" for k, v in r["compases_por_duracion"].items()))
        if "notas" in r:
            L.append(f"- Notas: {r['notas']} | acordes: {r.get('acordes')} | compases: {r.get('compases')}")
        L.append(f"- Ajustes finales: " + ", ".join(f"{k}={v}" for k, v in r.get("ajustes_finales", {}).items()))

        for voice, group in r.get("ciclos", {}).items():
            L += ["", f"## Ciclos: {voice}", "", "| Ciclo | Tramo | Periodo | Compases | Vueltas | Se repite | Dobla al bajo |", "|---|---|---:|---:|---:|---:|---|"]
            L += [f"| {c['letra']} | {c['inicio']} – {c['fin']} | {c['periodo_s']:.3f} s | {c['compases'] if c['compases'] is not None else '–':g} | "
                  f"{c['vueltas']} | {c['se_repite']:.0%} | {'sí' if c['dobla_al_bajo'] else ''} |" for c in group]
            if not group:
                L.append("| – | sin ciclos | | | | | |")

        if "capas" in r:
            L += ["", f"## Capas de guitarra (loop de {r['capas']['loop_s']:.3f} s)", "",
                  "  ".join(f"{e['tipo']} {e['t']}" for e in r["capas"]["eventos"]) or "sin cambios"]

    if info.get("imagenes"):
        pages = [p for p in info["imagenes"] if re.search(r"_p\d+\.png$", p)]
        L += ["", "## Imágenes", ""] + [f"- `{p}`" for p in info["imagenes"] if p not in pages]
        if pages:
            L.append(f"- {len(pages)} páginas del tabroll: `{pages[0]}` … `{pages[-1]}`")
    if info.get("avisos"):
        L += ["", "## Avisos", ""] + [f"- {w}" for w in info["avisos"]]

    path.write_text("\n".join(L) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- corrida

def run(args) -> int:
    audio = find_song(args.audio)
    if audio.suffix.lower() not in AUDIO_EXT:
        raise SystemExit(f"No encuentro un audio válido en {audio} (extensiones: {', '.join(sorted(AUDIO_EXT))}).")

    changes = {}
    for item in args.set:
        name, _, value = item.partition("=")
        if not name.strip().isidentifier() or not value.strip():
            raise SystemExit(f"--set espera NOMBRE=VALOR, por ejemplo GRID=0.5 (recibí '{item}').")
        changes[name.strip()] = value.strip()
    if args.sin_pistas:
        changes.setdefault("SEPARATE", "False")

    run_dir = make_run_dir(Path(args.salidas).resolve(), audio, args.nombre)
    link_or_copy(audio, run_dir / audio.name)
    given = {"guitar": args.guitar, "bass": args.bass}
    used = {}
    for kind in ("guitar", "bass"):
        src = Path(given[kind]).expanduser().resolve() if given[kind] else (None if args.sin_pistas else find_stem(audio, kind))
        if src and not src.is_file():
            raise SystemExit(f"No encuentro la pista {src}.")
        if src:
            link_or_copy(src, run_dir / f"{audio.stem}_{kind}{src.suffix}")
        used[kind] = src

    # El notebook debe encontrar exactamente la copia de esta corrida, no elegir
    # otra canción por fecha dentro de la carpeta general de audios.
    changes.setdefault("SONG", repr(audio.stem))
    changes.setdefault("BASE_DIR", f"Path({str(run_dir)!r})")
    changes.setdefault("AUDIO_FOLDER", repr("."))
    cells = apply_changes(load_code_cells(), args.preset, changes)

    print(f"Corrida en {run_dir.relative_to(ROOT) if run_dir.is_relative_to(ROOT) else run_dir}")
    print(f"Pistas: guitarra {used['guitar'] or 'ninguna'} | bajo {used['bass'] or 'ninguna'}\n")

    try:
        import IPython.display                                                       # fuera de Jupyter, display() solo ensucia la salida
        IPython.display.display = lambda *a, **k: None
    except ImportError:
        pass

    ns = {"__name__": "__main__"}
    times, failed, error = {}, None, None
    log = open(run_dir / "salida.txt", "w", encoding="utf-8")
    start = time.time()
    previous = Path.cwd()

    with warnings.catch_warnings(record=True) as caught, contextlib.redirect_stdout(Tee(sys.stdout, log)):
        warnings.simplefilter("default")
        warnings.filterwarnings("ignore", category=ResourceWarning)                   # archivos que Python cierra solo: ruido
        os.chdir(run_dir)
        try:
            for i, source in cells:
                t = time.time()
                try:
                    exec(compile(without_magics(source), f"<celda {i}>", "exec"), ns)
                except Exception as e:
                    failed = i
                    error = "".join(traceback.format_exception(type(e), e, e.__traceback__.tb_next))   # sin el marco de este script
                    print(f"\nERROR en la celda {i} del notebook:\n{error}")
                    break
                except KeyboardInterrupt:
                    failed, error = i, "Corrida interrumpida con Ctrl+C."
                    print(f"\n{error}")
                    break
                finally:
                    times[i] = round(time.time() - t, 1)
        finally:
            os.chdir(previous)

    total = round(time.time() - start, 1)
    avisos = sorted({f"{w.category.__name__} ({Path(w.filename).name.strip('<>')}, línea {w.lineno}): {w.message}" for w in caught})
    log.write("\n\n# Tiempo por celda (s)\n" + "\n".join(f"celda {i}: {s}" for i, s in sorted(times.items(), key=lambda kv: -kv[1]) if s >= 0.5))
    if avisos:
        log.write("\n\n# Avisos\n" + "\n".join(avisos))
    log.close()

    created = {}
    for kind in ("guitar", "bass"):                                                  # pistas que hizo Demucs: se guardan junto a la canción
        if used[kind] is None:
            made = [p for p in run_dir.iterdir() if p.suffix.lower() in AUDIO_EXT and p.stem.startswith(f"{audio.stem}_{kind}")]
            if made:
                dest = audio.parent / made[0].name
                try:
                    if not dest.exists():
                        shutil.copy2(made[0], dest)
                except OSError as e:
                    print(f"No pude guardar {made[0].name} junto a la canción ({e}); queda en la carpeta de la corrida.")
                created[kind] = made[0].name

    ram = None
    try:
        import resource
        ram = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 if sys.platform != "darwin" else 1024 ** 2))
    except Exception:
        pass

    images = sorted(str(p.relative_to(run_dir)) for p in (run_dir / "harmony_outputs").glob("*.png")) if (run_dir / "harmony_outputs").is_dir() else []
    info = {
        "cancion": audio.stem, "audio": str(audio), "carpeta": run_dir.name, "fecha": datetime.now().isoformat(timespec="seconds"),
        "version_notebook": git_version(), "estado": "ok" if failed is None else ("interrumpida" if error and error.startswith("Corrida interrumpida") else "error"), "celda_con_error": failed,
        "error": error, "preset": args.preset, "cambios": changes,
        "pistas": {"guitarra": (used["guitar"].name if used["guitar"] else created.get("guitar")),
                   "bajo": (used["bass"].name if used["bass"] else created.get("bass")),
                   "creadas_con_demucs": bool(created)},
        "tiempo_s": total, "ram_max_mb": ram, "resultado": {}, "imagenes": images, "avisos": avisos,
    }
    try:
        info["resultado"] = summary(ns)
    except Exception as e:                                                           # el resumen nunca debe tumbar la corrida
        info["avisos"].append(f"No se pudo armar el resumen completo: {type(e).__name__}: {e}")
    (run_dir / "resumen.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(run_dir / "resumen.md", info)

    removed = prune(Path(args.salidas).resolve(), args.conservar, run_dir) if args.conservar else []
    print(f"\n{'Listo' if failed is None else 'Terminó con error'} en {total} s. Resultados en {run_dir}")
    if created:
        print("Pistas creadas con Demucs y guardadas junto a la canción: " + ", ".join(created.values()))
    if removed:
        print(f"Borradas {len(removed)} corridas viejas (--conservar {args.conservar}).")
    return 0 if failed is None else 1


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):                                          # en una consola de Windows, ♯ o ♭ no deben romper la corrida
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    p = argparse.ArgumentParser(description="Corre el notebook sobre una canción y guarda los resultados en outputs/.")
    p.add_argument("audio", nargs="?", help="ruta del audio o parte de su nombre dentro de Angine de Poitrine Audios/")
    p.add_argument("--guitar", help="pista de guitarra (si no se da, se busca <canción>_guitar.* junto a la canción)")
    p.add_argument("--bass", help="pista de bajo (si no se da, se busca <canción>_bass.* junto a la canción)")
    p.add_argument("--sin-pistas", action="store_true", help="analizar solo la mezcla: no usa pistas ni corre Demucs")
    p.add_argument("--preset", help="aplica un preset de la celda de ajustes (ver --presets)")
    p.add_argument("--set", action="append", default=[], metavar="NOMBRE=VALOR",
                   help="cambia una variable del notebook en esta corrida, por ejemplo --set GRID=0.5 o --set \"KEY_OVERRIDE=('E', 'dorian')\"")
    p.add_argument("--nombre", help="etiqueta corta para la carpeta de la corrida")
    p.add_argument("--salidas", default=str(OUTPUTS), help="carpeta base de las corridas (por defecto outputs/)")
    p.add_argument("--conservar", type=int, default=0, metavar="N", help="después de correr, deja solo las N corridas más recientes")
    p.add_argument("--presets", action="store_true", help="muestra los presets disponibles y termina")
    args = p.parse_args(argv)

    if args.presets:
        for name, (_, body) in sorted(find_presets(load_code_cells()).items()):
            print(f"{name}: {'; '.join(body)}")
        return 0
    if not args.audio:
        p.error("falta la ruta de la canción")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
