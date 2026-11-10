"""Paso 2 del diagnóstico de capas: ¿qué distingue a la melodía principal de las otras capas de guitarra?

Uso:
    python scripts/diagnostico_capas.py outputs/*_limpieza > diagnostico_capas.txt
    python scripts/diagnostico_capas.py outputs/*_limpieza --sin-estereo      # sin leer el audio

El paso 1 mostró que la melodía se repite a la vuelta del looper igual que el riff, así que REPET a esa vuelta la
manda al fondo. Este script mide, sobre la partitura alineada, tres pistas que podrían separarla de otra forma:

1. Edad de la capa: cuántas vueltas seguidas lleva sonando la misma nota en el mismo punto del ciclo (vuelta local:
   el ciclo más corto que contiene la nota). Si la melodía suele ser la capa más nueva, se puede aislar restando el
   estado del looper antes de que entrara.
2. Registro: qué parte de la melodía es la nota más aguda que suena en ese momento.
3. Estéreo: en la pista de guitarra, dónde suena cada nota (-1 izquierda, +1 derecha) y cuánta energía tiene en los
   lados (L-R) frente al centro (L+R). Se mide en la fundamental y los armónicos 2 y 3 de cada nota, y se dejan fuera
   las notas que coinciden en clase de altura con una nota del otro grupo que suena a la vez.

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

MARGEN = 0.05
SR, N_FFT, HOP = 22050, 4096, 512
MAX_EDAD = 20
SKIP_DIRS = {".venv", ".git", "outputs", "node_modules", "__pycache__"}


def local_period(cycles, t):
    cover = [c["period_s"] for group in cycles.values() for c in group if c["start_s"] <= t < c["end_s"]]
    return min(cover) if cover else None


def arrays(notes):
    return (np.array([n["t"] for n in notes]), np.array([n["te"] for n in notes]), np.array([n["p"] for n in notes]))


def sounding(arr, t, p):
    ts, te, ps = arr
    return bool(np.any((np.abs(ps - p) < 0.26) & (ts < t + MARGEN) & (te > t - MARGEN)))


def age(n, arr, cycles, inside):
    """Vueltas seguidas hacia atrás en que la misma altura suena en el mismo punto."""
    m = (n["t"] + n["te"]) / 2
    P = local_period(cycles, m)
    if P is None or not inside(m - P):
        return None
    k = 0
    while k < MAX_EDAD and inside(m - (k + 1) * P) and sounding(arr, m - (k + 1) * P, n["p"]):
        k += 1
    return k


def is_top(n, arr):
    ts, te, ps = arr
    m = (n["t"] + n["te"]) / 2
    on = (ts <= m) & (te > m)
    return bool(ps[on].max() <= n["p"] + 0.26) if on.any() else True


def no_collision(ns, other):
    """Deja fuera notas que comparten clase de altura con el otro grupo simultáneo."""
    ts, te, ps = arrays(other)
    out = []
    for n in ns:
        ov = (ts < n["te"]) & (te > n["t"])
        d = np.abs((ps[ov] - n["p"] + 6) % 12 - 6)
        if not np.any(d < 0.26):
            out.append(n)
    return out


def find_guitar_stem(run):
    r = json.loads((run / "resumen.json").read_text(encoding="utf-8"))
    name, audio = (r.get("pistas") or {}).get("guitarra"), r.get("audio")
    if not name:
        return None
    cands = [Path(audio).parent / name] if audio else []
    for d in ROOT.iterdir():
        if d.is_dir() and d.name not in SKIP_DIRS:
            cands += list(d.rglob(name))
    return next((c for c in cands if c.exists()), None)


def load_stereo(path):
    import librosa
    y, _ = librosa.load(str(path), sr=SR, mono=False)
    if y.ndim == 1:
        y = np.vstack([y, y])
    mono = bool(np.allclose(y[0], y[1], atol=1e-5))
    L = librosa.stft(y[0], n_fft=N_FFT, hop_length=HOP)
    R = librosa.stft(y[1], n_fft=N_FFT, hop_length=HOP)
    return L, R, mono


def stereo(n, L, R, shift):
    """(posición, lados/centro) de una nota, o None si no hay energía medible."""
    a, b = n["t"] + shift + 0.03, n["te"] + shift - 0.01
    f0 = max(int(a * SR / HOP), 0)
    f1 = min(max(int(b * SR / HOP) + 1, f0 + 1), L.shape[1])
    if f0 >= L.shape[1]:
        return None
    bins = []
    for h in (1, 2, 3):
        k = int(round(h * 440.0 * 2 ** ((n["p"] - 69) / 12) * N_FFT / SR))
        if 1 <= k < L.shape[0] - 1:
            bins += [k - 1, k, k + 1]
    if not bins:
        return None
    l, r = L[bins, f0:f1], R[bins, f0:f1]
    el, er = float(np.sum(np.abs(l) ** 2)), float(np.sum(np.abs(r) ** 2))
    em, es = float(np.sum(np.abs(l + r) ** 2)), float(np.sum(np.abs(l - r) ** 2))
    if el + er <= 0:
        return None
    return (er - el) / (er + el), es / max(em, 1e-12)


def med(v):
    v = [x for x in v if x is not None]
    return (float(np.median(v)), len(v)) if v else (float("nan"), 0)


def frac(v, test):
    v = [x for x in v if x is not None]
    return 100.0 * sum(1 for x in v if test(x)) / len(v) if v else float("nan")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas de corrida con line_diagnostics.json")
    ap.add_argument("--sin-estereo", action="store_true", help="no lee el audio (solo edad y registro)")
    args = ap.parse_args(argv)
    for run in args.corridas:
        song = M.song_key(run.name)
        diag = run / "line_diagnostics.json"
        if song is None or not diag.exists():
            print(f"\n{run.name}: sin partitura de evaluación o sin line_diagnostics.json")
            continue
        J = json.loads(diag.read_text(encoding="utf-8"))
        cycles = J.get("cycles_n") or {}
        al = M.Alignment(song)
        gu = M.mapped(al, al.ref["guitars"])
        lead = M.lead_line(al, song)
        key = lambda n: (round(n["t"], 4), n["p"], n["part"])
        lead_keys = {key(n) for n in lead}
        others = [n for n in gu if key(n) not in lead_keys]
        spans = [(float(al.t(t0)), float(al.t(t1))) for t0, t1, nm, kn in al.ref["sections"] if kn]
        inside = lambda t: any(a <= t < b for a, b in spans)
        arr = arrays(gu)
        names = [nm for t0, t1, nm, kn in al.ref["sections"]]

        age_l = [age(n, arr, cycles, inside) for n in lead]
        age_o = [age(n, arr, cycles, inside) for n in others]
        top_l = [is_top(n, arr) for n in lead]

        st_l = st_o = None
        stem_txt = "no se leyó (--sin-estereo)"
        if not args.sin_estereo:
            path = find_guitar_stem(run)
            if path is None:
                stem_txt = "no encontré la pista de guitarra"
            else:
                L, R, mono = load_stereo(path)
                shift = M.calib(M.top_line(gu), M._notes(J["raw_high"]))
                stem_txt = f"{path.name} ({'mono: izquierda y derecha son iguales' if mono else 'estéreo'})"
                cl, co = no_collision(lead, others), no_collision(others, lead)
                st_l = {key(n): stereo(n, L, R, shift) for n in cl}
                st_o = {key(n): stereo(n, L, R, shift) for n in co}
                del L, R

        print(f"\n{run.name}")
        print("   1) edad de la capa: vueltas seguidas que la misma nota lleva sonando en ese punto (vuelta local)")
        print(f"      {'':24s} {'mediana':>8s} {'nueva (0-1)':>12s} {'veterana (8+)':>14s} {'notas':>6s}")
        for name, v in (("melodía principal", age_l), ("otras capas", age_o)):
            m, n = med(v)
            print(f"      {name:24s} {m:8.1f} {frac(v, lambda x: x <= 1):11.1f}% {frac(v, lambda x: x >= 8):13.1f}% {n:6d}")
        print(f"   2) registro: la melodía principal es la nota más aguda que suena en el "
              f"{100.0 * sum(top_l) / max(len(top_l), 1):.1f} % de sus {len(top_l)} notas")
        print(f"   3) estéreo, pista {stem_txt}")
        if st_l is not None:
            print(f"      {'':24s} {'posición':>9s} {'lados/centro':>13s} {'notas':>6s}   (posición: -1 izquierda, +1 derecha)")
            for name, d in (("melodía principal", st_l), ("otras capas", st_o)):
                v = [x for x in d.values() if x is not None]
                (p, n), (s, _) = med([x[0] for x in v]), med([x[1] for x in v])
                print(f"      {name:24s} {p:9.2f} {s:13.2f} {n:6d}")

        print(f"   por sección: {'':26s} {'edad mel/otras':>15s} {'+aguda':>7s} {'posición mel/otras':>19s} {'lados/centro mel/otras':>23s}")
        seen = []
        for nm in names:
            if nm in seen:
                continue
            seen.append(nm)
            il = [i for i, n in enumerate(lead) if names[n["sec"]] == nm]
            io = [i for i, n in enumerate(others) if names[n["sec"]] == nm]
            if not il:
                continue
            (al_, _), (ao_, _) = med([age_l[i] for i in il]), med([age_o[i] for i in io])
            tp = 100.0 * sum(top_l[i] for i in il) / len(il)
            line = f"      {nm[:38]:38s} {al_:6.1f} / {ao_:5.1f} {tp:6.0f}%"
            if st_l is not None:
                vl = [st_l.get(key(lead[i])) for i in il]
                vo = [st_o.get(key(others[i])) for i in io]
                vl, vo = [x for x in vl if x], [x for x in vo if x]
                (pl, _), (po, _) = med([x[0] for x in vl]), med([x[0] for x in vo])
                (sl, _), (so, _) = med([x[1] for x in vl]), med([x[1] for x in vo])
                line += f" {pl:9.2f} / {po:6.2f} {sl:12.2f} / {so:7.2f}"
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
