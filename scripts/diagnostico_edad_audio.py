"""Paso 4b de la separación por capas: ¿la edad medida en el audio distingue la melodía?

Uso:
    python scripts/diagnostico_edad_audio.py outputs/*_limpieza > diagnostico_edad_audio.txt

Usa los cinco picos de saliencia por cuadro que guarda cada corrida (`line_candidates.npz`) y la voz aguda del
cuaderno (`line_diagnostics.json`), y los compara cuadro a cuadro con la melodía principal de la partitura alineada.
Solo mide: usa la partitura para evaluar, nunca para decidir nada dentro del cuaderno.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from tabroll.evaluation import melodia as M  # noqa: E402

RELS = (0.3, 0.5, 0.7)
MARGINS = (2, 4)
STEP = 0.25
MAX_TURNS = 20


def local_period_frames(cycles, T, fps):
    per = np.zeros(T)
    for c in (c for group in cycles.values() for c in group):
        a, b = max(int(c["start_s"] * fps), 0), min(int(c["end_s"] * fps), T)
        if a < b:
            p = c["period_s"] * fps
            seg = per[a:b]
            per[a:b] = np.where((seg == 0) | (p < seg), p, seg)
    return per


def peak_ages(pitch, present, per):
    from scipy.ndimage import maximum_filter1d
    T, k = pitch.shape
    if not present.any():
        return np.zeros((T, k), np.int16)
    lo = float(np.min(pitch[present]))
    idx = np.where(present, np.round((pitch - lo) / STEP), 0).astype(int)
    C = int(idx.max()) + 1
    grid = np.zeros((C, T), np.uint8)
    rows, cols = np.nonzero(present)
    grid[idx[rows, cols], rows] = 1
    near = maximum_filter1d(maximum_filter1d(grid, 3, axis=0), 3, axis=1).astype(bool)
    age = np.zeros((T, k), np.int16)
    run = present & (per > 0)[:, None]
    frames = np.arange(T)
    for turn in range(1, MAX_TURNS + 1):
        back = np.round(frames - turn * per).astype(int)
        ok = (per > 0) & (back >= 0)
        b = np.clip(back, 0, T - 1)
        run &= near[idx, b[:, None]] & ok[:, None]
        if not run.any():
            break
        age += run
    return age


def lead_frames(lead, ft, shift):
    out = np.full(len(ft), np.nan)
    for n in lead:
        a, b = np.searchsorted(ft, n["t"] + shift), np.searchsorted(ft, n["te"] + shift)
        out[a:b] = n["p"]
    return out


def pct(mask, where):
    n = int(where.sum())
    return (100.0 * float((mask & where).sum()) / n if n else float("nan")), n


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas con line_diagnostics.json y line_candidates.npz")
    args = ap.parse_args(argv)
    for run in args.corridas:
        song = M.song_key(run.name)
        if song is None or not (run / "line_diagnostics.json").exists():
            print(f"\n{run.name}: sin partitura de evaluación o sin line_diagnostics.json")
            continue
        if not (run / "line_candidates.npz").exists():
            print(f"\n{run.name}: no tiene line_candidates.npz")
            continue
        J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
        Z = np.load(run / "line_candidates.npz")
        ft = np.asarray(J["frame_times_s"], float)
        mel = np.array([np.nan if v is None else float(v) for v in J["melody_n"]], float)
        pitch, val = Z["pitch_n"].astype(float), Z["val_n"].astype(float)
        T = min(len(ft), len(mel), len(pitch))
        ft, mel, pitch, val = ft[:T], mel[:T], pitch[:T], val[:T]
        fps = 1.0 / (ft[1] - ft[0])

        al = M.Alignment(song)
        gu = M.mapped(al, al.ref["guitars"])
        lead = M.lead_line(al, song)
        shift = M.calib(M.top_line(gu), M._notes(J["raw_high"]))
        ref = lead_frames(lead, ft, shift)
        voiced = np.isfinite(ref)
        per = local_period_frames(J.get("cycles_n") or {}, T, fps)
        floor = np.percentile(val.max(axis=1), 55)
        rows = np.arange(T)
        same = lambda a: np.abs(a - ref) < 0.26

        print(f"\n{run.name}")
        print(f"   cuadros con melodía en la partitura: {int(voiced.sum())}; cuadros dentro de un ciclo: {100.0 * (per > 0).mean():.0f} %")
        for rel in RELS:
            present = (val > 0) & (val >= rel * val.max(axis=1, keepdims=True)) & (val >= floor)
            age = peak_ages(pitch, present, per)
            npres = present.sum(axis=1)
            has = npres > 0
            strongest = np.argmax(np.where(present, val, -1.0), axis=1)
            highest = np.argmax(np.where(present, pitch, -np.inf), axis=1)
            youngest = np.argmin(np.where(present, age * 1000.0 - val / (val.max() + 1e-9), np.inf), axis=1)
            p_strong = np.where(has, pitch[rows, strongest], np.nan)
            p_high = np.where(has, pitch[rows, highest], np.nan)
            p_young = np.where(has, pitch[rows, youngest], np.nan)
            a_young = np.where(has, age[rows, youngest], 10 ** 6)

            match_lead = present & (np.abs(pitch - ref[:, None]) < 0.26)
            lead_in = match_lead.any(axis=1)
            a_lead = np.where(match_lead, age, 10 ** 6).min(axis=1)
            match_mel = present & (np.abs(pitch - mel[:, None]) < 0.26)
            a_mel = np.where(match_mel, age, 10 ** 6).min(axis=1)

            choose = voiced & lead_in & (npres >= 2)
            print(f"   rel = {rel}: picos que suenan por cuadro, mediana {np.median(npres[voiced]):.0f}")
            (v1, n1), (v2, _), (v3, _) = pct(a_lead <= a_young, choose), pct(same(p_strong), choose), pct(same(p_high), choose)
            print(f"      cuando la melodía está entre los picos que suenan y hay más de uno ({n1} cuadros): "
                  f"es la más nueva {v1:.1f} %, la más fuerte {v2:.1f} %, la más aguda {v3:.1f} %")
            rules = [("techo (la melodía está entre los picos)", lead_in), ("cuaderno (melody_n)", same(mel)),
                     ("más fuerte", same(p_strong)), ("más aguda", same(p_high)), ("más nueva", same(p_young))]
            for D in MARGINS:
                switch = (a_mel < 10 ** 6) & (a_young <= a_mel - D)
                rules.append((f"cuaderno salvo más nueva por {D}", same(np.where(switch, p_young, mel))))
            multi = voiced & (npres >= 2)
            print(f"      {'regla':42s} {'acierta':>9s} {'acierta cuando hay que elegir':>30s}")
            for label, ok in rules:
                (va, _), (vb, nb) = pct(ok, voiced), pct(ok, multi)
                print(f"      {label:42s} {va:8.1f}% {vb:21.1f}% ({nb:5d})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
