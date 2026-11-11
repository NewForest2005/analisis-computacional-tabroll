"""Camino estéreo, paso 1: ¿la melodía se ve mejor en algún canal de la pista de guitarra?

Uso:
    python scripts/diagnostico_canales.py outputs/limpieza/*_limpieza > diagnostico_canales.txt

Calcula la saliencia de la voz aguda con la misma función del cuaderno en versiones mono, izquierda, derecha y lados
de la pista de guitarra, y mide techo y pico más fuerte contra la partitura alineada. Solo mide; no modifica el cuaderno.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy.ndimage import uniform_filter1d

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))
sys.path.insert(0, str(HERE))
import tabroll.cells.pitch_salience as _ps  # noqa: E402
import tabroll.cells.stft_mag as _sm  # noqa: E402
from diagnostico_capas import find_guitar_stem  # noqa: E402
from diagnostico_edad_audio import lead_frames  # noqa: E402
from tabroll.evaluation import melodia as M  # noqa: E402

_sm.np = _ps.np = np
_ps.uniform_filter1d = uniform_filter1d
SR, NFFT, HOP = 22050, 4096, 512
SPLIT, REL = 47.0, 0.3
SHORT = {"cuaderno (saliencia actual)": "cuaderno", "pista mono": "mono", "izquierda": "izq", "derecha": "der",
         "lados": "lados", "izquierda + derecha": "izq+der"}


def top_peaks(S, cand, k=5):
    up = np.vstack([np.zeros_like(S[:1]), S[:-1]])
    dn = np.vstack([S[1:], np.zeros_like(S[-1:])])
    values = np.where((S >= up) & (S >= dn), S, 0.0)
    idx = np.argsort(-values, axis=0)[:k]
    return cand[idx].T.astype(float), np.take_along_axis(values, idx, axis=0).T.astype(float)


def channel_peaks(x):
    S, cand = _ps.pitch_salience(_sm.stft_mag(x, NFFT, HOP), SR, NFFT, gamma=0.0)
    hi = cand >= SPLIT
    return top_peaks(S[hi], cand[hi])


def load_channels(path):
    import librosa
    y, _ = librosa.load(str(path), sr=SR, mono=False)
    if y.ndim == 1:
        return {"mono": y}, True
    L, R = y[0], y[1]
    mono = bool(np.allclose(L, R, atol=1e-5))
    ch = {"mono": (L + R) / 2}
    if not mono:
        ch.update(izquierda=L, derecha=R, lados=(L - R) / 2)
    return ch, mono


def present_of(val):
    top = val.max(axis=1, keepdims=True)
    return (val > 0) & (val >= REL * top) & (val >= np.percentile(val.max(axis=1), 55))


def measures(pitch, val, ref):
    pres = present_of(val)
    techo = np.any(pres & (np.abs(pitch - ref[:, None]) < 0.26), axis=1)
    s = np.argmax(np.where(pres, val, -1.0), axis=1)
    fuerte = pres.any(axis=1) & (np.abs(pitch[np.arange(len(pitch)), s] - ref) < 0.26)
    return techo, fuerte, pres


def frame_sections(al, ft, shift):
    sec = np.full(len(ft), -1)
    for k, (t0, t1, nm, kn) in enumerate(al.ref["sections"]):
        if kn:
            a = np.searchsorted(ft, float(al.t(t0)) + shift)
            b = np.searchsorted(ft, float(al.t(t1)) + shift)
            sec[a:b] = k
    return sec


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas con line_diagnostics.json y line_candidates.npz")
    args = ap.parse_args(argv)
    for run in args.corridas:
        song = M.song_key(run.name)
        if song is None or not (run / "line_diagnostics.json").exists() or not (run / "line_candidates.npz").exists():
            print(f"\n{run.name}: sin partitura de evaluación, line_diagnostics.json o line_candidates.npz")
            continue
        path = find_guitar_stem(run)
        if path is None:
            print(f"\n{run.name}: no encontré la pista de guitarra")
            continue
        J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
        Z = np.load(run / "line_candidates.npz")
        chans, mono = load_channels(path)
        reps = {"cuaderno (saliencia actual)": (Z["pitch_n"].astype(float), Z["val_n"].astype(float))}
        for name, x in chans.items():
            reps["pista mono" if name == "mono" else name] = channel_peaks(x)
        T = min(len(J["melody_n"]), *(p.shape[0] for p, v in reps.values()))
        reps = {k: (p[:T], v[:T]) for k, (p, v) in reps.items()}
        ft = np.arange(T) * HOP / SR
        mel = np.array([np.nan if v is None else float(v) for v in J["melody_n"][:T]], float)
        al = M.Alignment(song)
        gu = M.mapped(al, al.ref["guitars"])
        lead = M.lead_line(al, song)
        shift = M.calib(M.top_line(gu), M._notes(J["raw_high"]))
        ref = lead_frames(lead, ft, shift)
        voiced = np.isfinite(ref)
        sec = frame_sections(al, ft, shift)
        res = {k: measures(p, v, ref) for k, (p, v) in reps.items()}
        if not mono:
            (tl, _, pl), (tr, _, pr) = res["izquierda"], res["derecha"]
            (pL, vL), (pR, vR) = reps["izquierda"], reps["derecha"]
            nL = vL / max(np.percentile(vL.max(axis=1), 90), 1e-9)
            nR = vR / max(np.percentile(vR.max(axis=1), 90), 1e-9)
            P = np.hstack([pL, pR])
            V = np.hstack([np.where(pl, nL, -1.0), np.where(pr, nR, -1.0)])
            s = np.argmax(V, axis=1)
            fu = (V.max(axis=1) > 0) & (np.abs(P[np.arange(T), s] - ref) < 0.26)
            res["izquierda + derecha"] = (tl | tr, fu, None)
        n = max(int(voiced.sum()), 1)
        side = 0.0 if mono else float(np.sum(chans["lados"] ** 2) / max(np.sum(chans["mono"] ** 2), 1e-12))
        print(f"\n{run.name}")
        print(f"   pista {path.name}: " + ("mono" if mono else f"estéreo, energía lados/centro {side:.2f}"))
        acc = 100.0 * float(np.sum(voiced & (np.abs(mel - ref) < 0.26))) / n
        print(f"   cuadros con melodía en la partitura: {int(voiced.sum())}; la voz aguda del cuaderno acierta en {acc:.1f} %")
        print(f"   {'versión de la saliencia':30s} {'techo':>8s} {'más fuerte':>11s}")
        for k, (t, f, _) in res.items():
            print(f"   {k:30s} {100.0 * np.sum(t & voiced) / n:7.1f}% {100.0 * np.sum(f & voiced) / n:10.1f}%")
        names = [nm for t0, t1, nm, kn in al.ref["sections"]]
        groups = {}
        for k in np.unique(sec[sec >= 0]):
            groups.setdefault(names[k], []).append(int(k))
        best = 0
        for ks in groups.values():
            m = voiced & np.isin(sec, ks)
            best += max(int(np.sum(t & m)) for t, f, _ in res.values())
        print(f"   techo usando en cada sección la mejor versión (tope, usa la partitura): {100.0 * best / n:.1f} %")
        cols = list(res)
        print(f"   por sección, techo: {'':16s}" + " ".join(f"{SHORT[c]:>7s}" for c in cols) + f" {'cuadros':>8s}")
        for nm, ks in groups.items():
            m = voiced & np.isin(sec, ks)
            nm_ = int(m.sum())
            if nm_:
                print(f"      {nm[:30]:30s} " + " ".join(f"{100.0 * np.sum(res[c][0] & m) / nm_:6.0f}%" for c in cols) + f" {nm_:8d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
