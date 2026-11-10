"""Paso 3 del diagnóstico de capas: ¿elegir la capa más nueva mejora la elección de la melodía?

Uso:
    python scripts/diagnostico_seleccion.py outputs/*_limpieza > diagnostico_seleccion.txt

El paso 2 mostró que la melodía principal suele ser la capa más nueva del looper y que, donde no es la nota más aguda,
suele ser justamente la más nueva. Este script mide reglas de elección y REPET causal sobre la partitura alineada.

Solo mide: usa la partitura para evaluar, nunca para decidir nada dentro del cuaderno.
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
from diagnostico_capas import MAX_EDAD, arrays, local_period, sounding  # noqa: E402
from tabroll.evaluation import melodia as M  # noqa: E402

MARGINS = (1, 2, 4)
KS = (4, 6, 8, 12)


def age_at(p, m, arr, cycles, inside):
    """Vueltas seguidas hacia atrás en que la altura p suena en el instante m."""
    P = local_period(cycles, m)
    if P is None or not inside(m - P):
        return None
    k = 0
    while k < MAX_EDAD and inside(m - (k + 1) * P) and sounding(arr, m - (k + 1) * P, p):
        k += 1
    return k


def causal_fg(p, m, arr, cycles, inside, K):
    """True si la altura queda en primer plano con la mediana de las K vueltas anteriores."""
    P = local_period(cycles, m)
    if P is None:
        return None
    votes = [sounding(arr, m - k * P, p) for k in range(1, K + 1) if inside(m - k * P)]
    if not votes:
        return None
    return sum(votes) <= len(votes) / 2


def choose(cands, rule, margin=0):
    """cands: [(altura, edad)]. Devuelve la altura elegida por la regla."""
    top = max(cands, key=lambda c: c[0])
    if rule == "aguda" or any(a is None for _, a in cands):
        return top[0]
    new = min(cands, key=lambda c: (c[1], -c[0]))
    if rule == "nueva":
        return new[0]
    return new[0] if top[1] - new[1] >= margin else top[0]


def pct(values):
    v = [x for x in values if x is not None]
    return (100.0 * sum(v) / len(v), len(v)) if v else (float("nan"), 0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas de corrida con line_diagnostics.json")
    args = ap.parse_args(argv)
    rules = [("más aguda", "aguda", 0), ("más nueva", "nueva", 0)] + [(f"más nueva por {d}", "margen", d) for d in MARGINS]
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
        ts, te, ps = arr
        names = [nm for t0, t1, nm, kn in al.ref["sections"]]

        hits = {label: [] for label, _, _ in rules}
        sec_of = []
        for n in lead:
            m = (n["t"] + n["te"]) / 2
            on = (ts <= m) & (te > m)
            pitches = sorted({round(float(p) * 2) / 2 for p in ps[on]})
            sec_of.append(names[n["sec"]])
            if len(pitches) < 2:
                for label, _, _ in rules:
                    hits[label].append(None)
                continue
            cands = [(p, age_at(p, m, arr, cycles, inside)) for p in pitches]
            for label, rule, d in rules:
                hits[label].append(abs(choose(cands, rule, d) - n["p"]) < 0.26)

        n_all = len(lead)
        n_multi = sum(1 for x in hits["más aguda"] if x is not None)
        print(f"\n{run.name}")
        print("   1) elegir entre las notas que suenan a la vez, en el centro de cada nota de la melodía principal")
        print(f"      notas de la melodía: {n_all}; con más de una nota sonando: {n_multi} ({100.0 * n_multi / max(n_all, 1):.1f} %)")
        print(f"      {'regla':22s} {'acierta cuando hay que elegir':>30s} {'acierta en total':>17s}")
        for label, _, _ in rules:
            v, n = pct(hits[label])
            total = 100.0 * (sum(1 for x in hits[label] if x) + (n_all - n)) / max(n_all, 1)
            print(f"      {label:22s} {v:29.1f}% {total:16.1f}%")

        print("   2) REPET causal: fondo = mediana de las K vueltas anteriores; % de notas en primer plano")
        print(f"      {'K':>4s} {'melodía':>16s} {'otras capas':>16s}")
        for K in KS:
            fl = [causal_fg(n["p"], (n["t"] + n["te"]) / 2, arr, cycles, inside, K) for n in lead]
            fo = [causal_fg(n["p"], (n["t"] + n["te"]) / 2, arr, cycles, inside, K) for n in others]
            (vl, nl), (vo, no) = pct(fl), pct(fo)
            print(f"      {K:4d} {vl:8.1f} % ({nl:4d}) {vo:8.1f} % ({no:4d})")

        print(f"   por sección, acierta cuando hay que elegir: {'más aguda':>10s} {'más nueva':>10s} {'nueva por 2':>12s} {'notas':>6s}")
        seen = []
        for nm in sec_of:
            if nm in seen:
                continue
            seen.append(nm)
            idx = [i for i, s in enumerate(sec_of) if s == nm]
            row = [pct([hits[label][i] for i in idx]) for label in ("más aguda", "más nueva", "más nueva por 2")]
            if row[0][1]:
                print(f"      {nm[:42]:42s} {row[0][0]:9.0f}% {row[1][0]:9.0f}% {row[2][0]:11.0f}% {row[0][1]:6d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
