"""Camino 2, paso 1: ¿Basic Pitch ve la melodía mejor que el cuaderno?

Corre en un entorno aparte con Python 3.10 y basic-pitch:
    .venv-bp/bin/python scripts/diagnostico_basic_pitch.py outputs/limpieza/*_limpieza > diagnostico_basic_pitch.txt

Basic Pitch transcribe notas polifónicas con una red ya entrenada. Este script lo corre sobre la pista de guitarra de
cada canción con partitura y mide, contra la partitura alineada, el techo de notas, alturas refinadas, líneas simples
y el techo juntando el cuaderno con Basic Pitch. Solo mide: usa la partitura para evaluar, nunca para decidir nada
dentro del cuaderno.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))
from diagnostico_capas import find_guitar_stem  # noqa: E402
from tabroll.evaluation import melodia as M  # noqa: E402

CONFIGS = {
    "por defecto": dict(onset_threshold=0.5, frame_threshold=0.3, minimum_note_length=127.70),
    "notas cortas": dict(onset_threshold=0.4, frame_threshold=0.3, minimum_note_length=58.0),
}
loose_pc = M.pclass


def refine(notes, contour, duration):
    """Afina cada nota con el contorno de Basic Pitch y la lleva al cuarto de tono más cercano."""
    if contour is None or contour.ndim != 2:
        return notes, None
    if contour.shape[0] in (264, 360) and contour.shape[1] not in (264, 360):
        contour = contour.T
    fps = contour.shape[0] / max(duration, 1e-9)
    bps = contour.shape[1] / 88.0
    out = []
    for a, b, p in notes:
        f0 = int(a * fps)
        f1 = max(int(b * fps), f0 + 1)
        c0 = int(round((p - 21) * bps))
        lo, hi = max(c0 - int(round(bps)), 0), min(c0 + int(round(bps)) + 1, contour.shape[1])
        seg = contour[f0:f1, lo:hi]
        if seg.size == 0 or float(seg.sum()) <= 0:
            out.append((a, b, p))
            continue
        k = lo + int(np.argmax(seg.sum(axis=0)))
        out.append((a, b, round((21 + k / bps) * 2) / 2))
    return out, fps


def as_dicts(notes, amp=None):
    return [dict(t=a, te=b, p=p, amp=(amp[i] if amp is not None else 1.0)) for i, (a, b, p) in enumerate(notes)]


def strongest_line(ns):
    ts = np.array([n["t"] for n in ns]); te = np.array([n["te"] for n in ns]); am = np.array([n["amp"] for n in ns])
    out = []
    for n in ns:
        on = (ts <= n["t"] + 0.02) & (te > n["t"] + 0.02)
        if not on.any() or am[on].max() <= n["amp"] + 1e-9:
            out.append(n)
    return out


def tuples(ns):
    return sorted((n["t"], n["te"], n["p"]) for n in ns)


def principal(lead, top, det, al):
    det = sorted(det)
    if not det:
        return 0.0
    sh = M.calib(top, det)
    det = M.in_known([(a - sh, b - sh, p) for a, b, p in det], al)
    return M.f_measure(M.match(lead, det, M.exact), len(lead), len(det))


def recall(ref, det, top, ok):
    det = sorted(det)
    if not det:
        return 0.0, set()
    sh = M.calib(top, det)
    det = [(a - sh, b - sh, p) for a, b, p in det]
    hit = M.match(ref, det, ok)
    return 100.0 * len(hit) / max(len(ref), 1), {k for k, _ in hit}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas de corrida con line_diagnostics.json")
    args = ap.parse_args(argv)
    import librosa
    from basic_pitch import ICASSP_2022_MODEL_PATH
    from basic_pitch.inference import Model, predict
    model = Model(ICASSP_2022_MODEL_PATH)

    for run in args.corridas:
        song = M.song_key(run.name)
        if song is None or not (run / "line_diagnostics.json").exists():
            print(f"\n{run.name}: sin partitura de evaluación o sin line_diagnostics.json")
            continue
        path = find_guitar_stem(run)
        if path is None:
            print(f"\n{run.name}: no encontré la pista de guitarra")
            continue
        J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
        al = M.Alignment(song)
        gu = M.mapped(al, al.ref["guitars"])
        top, lead = M.top_line(gu), M.lead_line(al, song)
        nb = M._notes(J["raw_high"])
        duration = float(librosa.get_duration(path=str(path)))

        print(f"\n{run.name}")
        print(f"   pista {path.name}; {len(lead)} notas de la melodía principal, {len(gu)} notas de guitarra")
        r_nb, hits_nb = recall(lead, nb, top, M.exact)
        r_nb_pc, _ = recall(lead, nb, top, loose_pc)
        print(f"   cuaderno (voz aguda): recupera {r_nb:.1f} % de la melodía ({r_nb_pc:.1f} % sin octava); "
              f"principal {principal(lead, top, nb, al):.1f}")

        for cname, kw in CONFIGS.items():
            model_output, midi_data, events = predict(str(path), model, **kw)
            notes = sorted((float(e[0]), float(e[1]), float(e[2])) for e in events)
            amps = {(float(e[0]), float(e[1]), float(e[2])): float(e[3]) for e in events}
            refined, fps = refine(notes, np.asarray(model_output.get("contour")), duration)
            print(f"   Basic Pitch, {cname} ({len(notes)} notas; contorno a {fps:.1f} cuadros por segundo):")
            for label, ns in (("semitonos", notes), ("refinadas a 1/4 de tono", refined)):
                r, hits_bp = recall(lead, ns, top, M.exact)
                r_pc, _ = recall(lead, ns, top, loose_pc)
                r_all, _ = recall(gu, ns, top, M.exact)
                both = 100.0 * len(hits_nb | hits_bp) / max(len(lead), 1)
                d = as_dicts(ns, [amps.get(n, 1.0) for n in notes])
                print(f"      {label}: recupera {r:.1f} % de la melodía ({r_pc:.1f} % sin octava) y {r_all:.1f} % de "
                      f"todas las guitarras; junto con el cuaderno, {both:.1f} %")
                print(f"         línea más aguda: principal {principal(lead, top, tuples(M.top_line(d)), al):.1f}   "
                      f"línea más fuerte: principal {principal(lead, top, tuples(strongest_line(d)), al):.1f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
