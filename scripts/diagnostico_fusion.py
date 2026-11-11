"""Camino 2, paso 2: cómo juntar las notas de Basic Pitch con la voz aguda del cuaderno.

Uso (entorno normal, después de basic_pitch_notas.py):
    python scripts/diagnostico_fusion.py outputs/limpieza/*_limpieza > diagnostico_fusion.txt

Basic Pitch indica dónde hay una nota; la altura sale de la saliencia del cuaderno, llevada a 24-EDO. Se comparan
huecos, re-ataques, reemplazos y la combinación de todas esas reglas. Solo mide; no modifica el cuaderno.
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
from basic_pitch_notas import bp_path  # noqa: E402
from diagnostico_capas import find_guitar_stem  # noqa: E402
from tabroll.evaluation import melodia as M  # noqa: E402

LOW = 47.0
GROUP = 0.05
MIN_GAP = 0.08


def refine_pitch(a, b, q, S, cand, off, fps):
    k0, k1 = int(a * fps), max(int(b * fps), int(a * fps) + 1)
    win = np.abs(cand - q) <= 0.75
    fallback = round((q - off) * 2) / 2
    if not win.any() or k0 >= S.shape[1]:
        return fallback
    prof = np.nanmean(S[win, k0:k1], axis=1)
    if not np.isfinite(prof).any() or np.nanmax(prof) <= 0:
        return fallback
    return round((cand[win][int(np.nanargmax(prof))] - off) * 2) / 2


def onset_groups(bp, S, cand, off, fps):
    bp = sorted(n for n in bp if n[2] >= LOW - 0.5 and n[1] - n[0] > 0.04)
    out, group = [], []
    for n in bp + [(np.inf, np.inf, 0.0, 0.0)]:
        if group and n[0] - group[0][0] >= GROUP:
            a, b, q, amp = max(group, key=lambda x: x[3])
            p = refine_pitch(a, b, q, S, cand, off, fps)
            if p >= LOW:
                out.append((a, b, p, amp))
            group = []
        group.append(n)
    return out


def fuse(nb, groups, huecos=None, reataques=False, reemplazo=None):
    nb = sorted(nb)
    starts, ends, ps = np.array([n[0] for n in nb]), np.array([n[1] for n in nb]), np.array([n[2] for n in nb])
    add, cuts, repl = [], {}, {}
    for a, b, p, amp in groups:
        cover = np.flatnonzero((starts - 0.03 <= a) & (a < ends))
        if cover.size == 0:
            if huecos is not None and amp >= huecos:
                nxt = starts[starts > a]
                add.append((a, min(b, float(nxt[0])) if nxt.size else b, p))
            continue
        j = int(cover[-1])
        if abs(ps[j] - p) < 0.26:
            if reataques and a - starts[j] >= MIN_GAP and ends[j] - a >= MIN_GAP:
                cuts.setdefault(j, []).append(a)
        elif reemplazo is not None and amp >= reemplazo and j not in repl:
            repl[j] = (a, p)
    out = []
    for j, (s, e, p0) in enumerate(nb):
        if j in repl:
            a, p = repl[j]
            if a - s >= 0.05:
                out.append((s, a, p0))
            out.append((a, e, p))
            continue
        prev = s
        for c in sorted(cuts.get(j, [])):
            out.append((prev, c, p0)); prev = c
        out.append((prev, e, p0))
    return sorted(out + add)


def scores(lead, top, det, al):
    det = sorted(det)
    if not det:
        return 0.0, 0.0, 0.0, 0
    sh = M.calib(top, det)
    det = M.in_known([(a - sh, b - sh, p) for a, b, p in det], al)
    h = M.match(lead, det, M.exact)
    return M.f_measure(h, len(lead), len(det)), 100.0 * len(h) / max(len(lead), 1), 100.0 * len(h) / max(len(det), 1), len(det)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas de corrida con line_diagnostics.json")
    args = ap.parse_args(argv)
    for run in args.corridas:
        song = M.song_key(run.name)
        if song is None or not (run / "line_diagnostics.json").exists():
            print(f"\n{run.name}: sin partitura de evaluación o sin line_diagnostics.json")
            continue
        stem = find_guitar_stem(run)
        if stem is None or not bp_path(stem).exists():
            print(f"\n{run.name}: falta <canción>_basic_pitch.json (corre antes basic_pitch_notas.py)")
            continue
        J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
        bp = [tuple(float(v) for v in n) for n in json.loads(bp_path(stem).read_text(encoding="utf-8"))["notas"]]
        S, cand = np.array(J["selector_salience"], dtype=float), np.array(J["cand_ishigh"], dtype=float)
        off, ft = float(J.get("off") or 0.0), np.asarray(J["frame_times_s"], float)
        fps, nb = 1.0 / (ft[1] - ft[0]), sorted(M._notes(J["raw_high"]))
        groups = onset_groups(bp, S, cand, off, fps)
        al = M.Alignment(song)
        gu, lead = M.mapped(al, al.ref["guitars"]), M.lead_line(al, song)
        top, sh = M.top_line(gu), M.calib(M.top_line(gu), nb)
        nb_s = [(a - sh, b - sh, p) for a, b, p in nb]
        bp_s = sorted((a - sh, b - sh, p) for a, b, p, amp in groups)
        hit_nb, hit_bp = {k for k, _ in M.match(lead, nb_s, M.exact)}, {k for k, _ in M.match(lead, bp_s, M.exact)}
        only = sorted(hit_bp - hit_nb)
        s0, e0, p0 = np.array([n[0] for n in nb_s]), np.array([n[1] for n in nb_s]), np.array([n[2] for n in nb_s])
        kinds = {"hueco": 0, "misma altura sin ataque": 0, "otra altura": 0}
        for k in only:
            t, p = lead[k]["t"], lead[k]["p"]
            cover = np.flatnonzero((s0 - 0.03 <= t) & (t < e0))
            if cover.size == 0: kinds["hueco"] += 1
            elif abs(p0[cover[-1]] - p) < 0.26: kinds["misma altura sin ataque"] += 1
            else: kinds["otra altura"] += 1
        n = max(len(lead), 1)
        print(f"\n{run.name}")
        print(f"   Basic Pitch: {len(bp)} notas; {len(groups)} ataques en la voz aguda")
        print(f"   recupera de la melodía: cuaderno {100.0 * len(hit_nb) / n:.1f} %, Basic Pitch {100.0 * len(hit_bp) / n:.1f} %, juntos {100.0 * len(hit_nb | hit_bp) / n:.1f} %")
        print(f"   notas solo de Basic Pitch ({len(only)}): " + ", ".join(f"{k} {100.0 * v / max(len(only), 1):.0f} %" for k, v in kinds.items()))
        rules = [("cuaderno", {}), ("+ huecos (fuerza ≥ 0.3)", dict(huecos=0.3)), ("+ huecos (fuerza ≥ 0.5)", dict(huecos=0.5)),
                 ("+ re-ataques", dict(reataques=True)), ("+ huecos 0.3 y re-ataques", dict(huecos=0.3, reataques=True)),
                 ("+ reemplazo (fuerza ≥ 0.5)", dict(reemplazo=0.5)), ("+ todo", dict(huecos=0.3, reataques=True, reemplazo=0.5))]
        print(f"   {'regla':48s} {'principal':>9s} {'recupera':>9s} {'precisión':>10s} {'notas':>6s}")
        for label, kw in rules:
            F, R, P, k = scores(lead, top, fuse(nb, groups, **kw), al)
            print(f"   {label:48s} {F:9.1f} {R:8.1f}% {P:9.1f}% {k:6d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
