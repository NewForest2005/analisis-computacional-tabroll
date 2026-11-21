"""Separa guitarra y bajo con BS-RoFormer SW (audio-separator) y deja las pistas listas para run_song.py.

Corre en un entorno aparte, `.venv-rof` (ver docs/separacion_roformer.md): audio-separator necesita
torch >= 2.3 y numpy >= 2, que no conviven con el entorno principal del proyecto.

Uso:
    .venv-rof/bin/python scripts/separar_roformer.py --entorno               # versiones, dispositivo y ffmpeg
    .venv-rof/bin/python scripts/separar_roformer.py Sarniezz --fragmento 20 # prueba rápida con 20 s
    .venv-rof/bin/python scripts/separar_roformer.py Sarniezz --fragmento 20 --comprobar-determinismo
    .venv-rof/bin/python scripts/separar_roformer.py Sarniezz Fabienk        # canciones completas

Escribe en pistas_roformer/ (fuera de la carpeta de audios, para que el flujo de Demucs nunca las tome sin querer):
    <Canción>_guitar.flac, <Canción>_bass.flac  pistas a 44.1 kHz estéreo
    <Canción>.json                              manifiesto: versiones, SHA-256 del modelo y de las pistas, parámetros, tiempo

Después: .venv/bin/python scripts/run_song.py Sarniezz --separador roformer
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIO_FOLDER = ROOT / "Angine de Poitrine Audios"
OUT_DIR = ROOT / "pistas_roformer"
MODEL_DIR = Path.home() / "models" / "audio-separator"
AUDIO_EXT = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aiff", ".aif"}

MODEL_FILE = "BS-Roformer-SW.ckpt"
# Checkpoint BS-Rofo-SW-Fixed publicado en Hugging Face (enerjazzer/BS-ROFO-SW-Fixed). Si audio-separator
# descarga otra copia, el manifiesto lo dice; no se detiene, porque el nombre del archivo puede cambiar.
EXPECTED_CKPT_SHA256 = "24e7d35ee9c64415673d3fd33e06a67cac2c103c5df6267ba1576459c775916e"
SAMPLE_RATE = 44100
KINDS = {"guitar": "Guitar", "bass": "Bass"}


# ---------------------------------------------------------------- utilidades sin dependencias pesadas

def name_key(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", str(text).casefold()) if not unicodedata.combining(ch))


def is_stem(path: Path) -> bool:
    return bool(re.search(r"(^|_)(guitar|bass|other|drums|vocals|piano)( \(\d+\))?$", path.stem.lower()))


def find_song(selector: str, folder: Path = AUDIO_FOLDER) -> Path:
    """Una ruta, o una parte del nombre de una canción de la carpeta de audios (sin contar sus pistas)."""
    candidate = Path(selector).expanduser()
    if candidate.is_file():
        return candidate.resolve()
    if not folder.is_dir():
        raise SystemExit(f"No existe la carpeta de audios: {folder}")
    songs = [p for p in folder.rglob("*")
             if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in AUDIO_EXT and not is_stem(p)]
    key = name_key(selector)
    hits = [p for p in songs if key in name_key(p.relative_to(folder))]
    if len(hits) > 1:
        hits = [p for p in hits if re.search(r"off?ici(al|el)", name_key(p.stem))] or hits
    if len(hits) != 1:
        found = "\n".join(f"  - {p.name}" for p in sorted(hits)) or "  (ninguna)"
        raise SystemExit(f"«{selector}» no identifica una sola canción:\n{found}")
    return hits[0]


def sha256(path: Path | None) -> str | None:
    if not path or not Path(path).is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def output_paths(song: Path, out_dir: Path = OUT_DIR, fragment: float | None = None) -> dict[str, Path]:
    """Rutas finales. Los fragmentos de prueba van aparte para no confundirse con las pistas completas."""
    base = out_dir / "fragmentos" if fragment else out_dir
    suffix = f"_{int(fragment)}s" if fragment else ""
    return {kind: base / f"{song.stem}{suffix}_{kind}.flac" for kind in KINDS}


def pick_outputs(files: list[str | Path], out_dir: Path) -> dict[str, Path]:
    """Encuentra la guitarra y el bajo entre los archivos que devuelve audio-separator."""
    found: dict[str, Path] = {}
    for f in files:
        p = Path(f)
        p = p if p.is_absolute() else out_dir / p
        low = p.stem.lower()
        for kind, label in KINDS.items():
            if f"({label.lower()})" in low or low.endswith(f"_{kind}") or low == kind:
                found.setdefault(kind, p)
    return found


def yaml_info(model_dir: Path) -> dict:
    """SHA-256 y parámetros de inferencia del YAML del modelo, si audio-separator lo dejó junto al checkpoint."""
    yml = model_dir / MODEL_FILE.replace(".ckpt", ".yaml")
    info: dict = {"archivo": yml.name if yml.is_file() else None, "sha256": sha256(yml)}
    if yml.is_file():
        text = yml.read_text(encoding="utf-8", errors="replace")
        for key in ("dim_t", "num_overlap", "chunk_size", "sample_rate", "normalize"):   # batch_size del YAML es el de entrenamiento
            m = re.search(rf"^\s*{key}\s*:\s*(.+?)\s*$", text, re.M)
            if m:
                info[key] = m.group(1).split("#")[0].strip()
        m = re.search(r"instruments\s*:\s*(\[[^\]]*\])", text)
        if m:
            info["instruments"] = m.group(1)
    return info


def to_wav(src: Path, dest: Path, fragment: float | None) -> None:
    """La entrada se convierte aquí a 44.1 kHz estéreo, para que el remuestreo no dependa de la herramienta."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src)]
    if fragment:
        cmd += ["-t", str(fragment)]
    cmd += ["-ac", "2", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_f32le", str(dest)]
    subprocess.run(cmd, check=True)


# ---------------------------------------------------------------- separación (necesita .venv-rof)

def environment(threads: int) -> dict:
    import importlib.metadata as md

    import torch

    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True, warn_only=True)
    torch.set_num_threads(threads)
    # La misma regla que audio-separator: MPS solo en procesadores ARM. En un Mac Intel con GPU AMD, torch ofrece MPS,
    # pero audio-separator separa en CPU (y es lo que queremos: fp32 en CPU es lo reproducible).
    mps = torch.backends.mps.is_available() and platform.machine() == "arm64"
    device = "cuda" if torch.cuda.is_available() else ("mps" if mps else "cpu")
    versions = {}
    for pkg in ("audio-separator", "torch", "numpy", "onnxruntime", "librosa", "soundfile"):
        try:
            versions[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            versions[pkg] = None
    ffmpeg = shutil.which("ffmpeg")
    ffmpeg_version = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True).stdout.split("\n")[0] if ffmpeg else None
    return {"python": platform.python_version(), "maquina": platform.machine(), "sistema": platform.platform(),
            "versiones": versions, "dispositivo": device, "hilos": threads, "ffmpeg": ffmpeg_version}


def make_separator(out_dir: Path, args):
    from audio_separator.separator import Separator

    kwargs = dict(output_dir=str(out_dir), output_format="FLAC", model_file_dir=str(args.modelos),
                  mdxc_params={"segment_size": args.segment_size, "override_model_segment_size": False,
                               "batch_size": args.batch_size, "overlap": args.overlap, "pitch_shift": 0})
    try:
        sep = Separator(sample_rate=SAMPLE_RATE, **kwargs)
    except TypeError:                                                   # versiones sin el parámetro: usan 44100 por defecto
        sep = Separator(**kwargs)
    sep.load_model(model_filename=MODEL_FILE)
    return sep


def used_device(sep) -> str | None:
    device = getattr(getattr(sep, "model_instance", None), "torch_device", None) or getattr(sep, "torch_device", None)
    return str(device) if device is not None else None


def separate_once(wav: Path, work: Path, args) -> dict[str, Path]:
    """Separa una vez; deja en args los segundos de carga del modelo y de separación (sin contar la descarga)."""
    work.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    sep = make_separator(work, args)
    args.carga_s = round(time.time() - t0, 1)
    args.dispositivo_usado = used_device(sep)
    t0 = time.time()
    files = sep.separate(str(wav), {label: f"{wav.stem}_{kind}" for kind, label in KINDS.items()})
    args.separacion_s = round(time.time() - t0, 1)
    got = pick_outputs(files, work)
    missing = [k for k in KINDS if k not in got or not got[k].is_file()]
    if missing:
        raise SystemExit(f"audio-separator no devolvió {', '.join(missing)}. Archivos recibidos: {files}")
    return got


def max_abs_diff(a: Path, b: Path) -> float:
    import numpy as np
    import soundfile as sf

    x, _ = sf.read(a, dtype="float32")
    y, _ = sf.read(b, dtype="float32")
    n = min(len(x), len(y))
    return float(np.max(np.abs(x[:n] - y[:n]))) if n else 0.0


def process(song: Path, args, env: dict) -> dict:
    out = output_paths(song, args.salida, args.fragmento)
    if all(p.is_file() for p in out.values()) and not args.rehacer and not args.comprobar_determinismo:
        print(f"Ya existen las pistas de {song.name}; uso --rehacer para separar de nuevo.")
        return json.loads((out["guitar"].parent / f"{out['guitar'].stem[:-len('_guitar')]}.json").read_text(encoding="utf-8"))

    args.modelos.mkdir(parents=True, exist_ok=True)
    out["guitar"].parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="roformer_") as tmp:
        tmp = Path(tmp)
        wav = tmp / f"{song.stem}.wav"
        to_wav(song, wav, args.fragmento)
        print(f"Separando {song.name}" + (f" (primeros {args.fragmento:g} s)" if args.fragmento else "")
              + f" con {MODEL_FILE} en {env['dispositivo']} ({env['hilos']} hilos)…", flush=True)
        got = separate_once(wav, tmp / "a", args)
        seconds, load_s = args.separacion_s, args.carga_s
        determinism = None
        if args.comprobar_determinismo:
            print("Segunda separación para comprobar el determinismo…", flush=True)
            again = separate_once(wav, tmp / "b", args)
            determinism = {kind: {"sha256_igual": sha256(got[kind]) == sha256(again[kind]),
                                  "max_diferencia": max_abs_diff(got[kind], again[kind])} for kind in KINDS}
            determinism["segunda_separacion_s"] = args.separacion_s
        for kind, src in got.items():
            shutil.move(str(src), out[kind])
        duration = None
        try:
            import soundfile as sf
            duration = round(sf.info(str(wav)).duration, 2)
        except Exception:
            pass

    ckpt = args.modelos / MODEL_FILE
    ckpt_sha = sha256(ckpt)
    manifest = {
        "cancion": song.stem, "audio": str(song), "sha256_mezcla": sha256(song),
        "fragmento_s": args.fragmento, "duracion_s": duration, "tiempo_s": seconds, "carga_modelo_s": load_s,
        "veces_tiempo_real": round(seconds / duration, 2) if duration else None,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "modelo": {"archivo": MODEL_FILE, "sha256": ckpt_sha, "sha256_esperado": EXPECTED_CKPT_SHA256,
                   "coincide_con_bs_rofo_sw_fixed": ckpt_sha == EXPECTED_CKPT_SHA256, "yaml": yaml_info(args.modelos)},
        "parametros": {"overlap": args.overlap, "segment_size": args.segment_size, "batch_size": args.batch_size,
                       "sample_rate": SAMPLE_RATE, "formato": "FLAC", "precision": "fp32", "pitch_shift": 0,
                       "entrada": "ffmpeg a 44.1 kHz estéreo pcm_f32le"},
        "entorno": {**env, "dispositivo_usado": getattr(args, "dispositivo_usado", None)},
        "pistas": {kind: {"archivo": p.name, "sha256": sha256(p)} for kind, p in out.items()},
        "determinismo": determinism,
    }
    stem = out["guitar"].stem[:-len("_guitar")]
    (out["guitar"].parent / f"{stem}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  listo en {seconds} s" + (f" ({manifest['veces_tiempo_real']}× tiempo real)" if duration else ""))
    for kind, p in out.items():
        print(f"  {kind:6s} {p.relative_to(ROOT) if p.is_relative_to(ROOT) else p}")
    if not manifest["modelo"]["coincide_con_bs_rofo_sw_fixed"]:
        print(f"  Aviso: el SHA-256 del checkpoint ({(ckpt_sha or 'no encontrado')[:12]}…) no es el de BS-Rofo-SW-Fixed "
              f"({EXPECTED_CKPT_SHA256[:12]}…). Queda registrado en el manifiesto.")
    if determinism:
        for kind, d in ((k, determinism[k]) for k in KINDS):
            print(f"  determinismo {kind:6s}: SHA-256 igual={d['sha256_igual']}, diferencia máxima={d['max_diferencia']:.2e}")
    return manifest


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("canciones", nargs="*", help="rutas o partes del nombre dentro de «Angine de Poitrine Audios/»")
    ap.add_argument("--entorno", action="store_true", help="muestra versiones, dispositivo y ffmpeg, y termina")
    ap.add_argument("--fragmento", type=float, metavar="S", help="separa solo los primeros S segundos (prueba rápida)")
    ap.add_argument("--comprobar-determinismo", action="store_true", help="separa dos veces y compara las pistas")
    ap.add_argument("--rehacer", action="store_true", help="separa aunque ya existan las pistas")
    ap.add_argument("--overlap", type=int, default=2, help="ventanas solapadas de RoFormer (por defecto 2)")
    ap.add_argument("--segment-size", type=int, default=256, help="segment_size de MDXC (por defecto 256)")
    ap.add_argument("--batch-size", type=int, default=1, help="batch_size de MDXC (por defecto 1)")
    ap.add_argument("--hilos", type=int, default=8, help="hilos de torch, fijos para que el resultado no varíe (por defecto 8)")
    ap.add_argument("--modelos", type=Path, default=MODEL_DIR, help=f"carpeta del checkpoint (por defecto {MODEL_DIR})")
    ap.add_argument("--salida", type=Path, default=OUT_DIR, help="carpeta de las pistas (por defecto pistas_roformer/)")
    args = ap.parse_args(argv)

    try:
        env = environment(args.hilos)
    except ModuleNotFoundError as e:
        raise SystemExit(f"Falta {e.name}: este script corre en .venv-rof (ver docs/separacion_roformer.md).")
    if args.entorno or not args.canciones:
        print(json.dumps(env, ensure_ascii=False, indent=1))
        if not args.canciones:
            return 0
    if not env["ffmpeg"]:
        raise SystemExit("Falta ffmpeg en el entorno (conda install -c conda-forge ffmpeg).")
    for selector in args.canciones:
        process(find_song(selector), args, env)
    return 0


if __name__ == "__main__":
    sys.exit(main())
