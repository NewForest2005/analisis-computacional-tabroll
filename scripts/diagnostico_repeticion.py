"""Paso 1 de la separación por capas del looper: ¿la melodía principal se repite a la vuelta del looper?

Uso:
    python scripts/diagnostico_repeticion.py outputs/*_limpieza --secciones

REPET (Rafii y Pardo, 2013) separa lo que se repite con un periodo (el fondo) de lo que no se repite (el primer
plano): en cada instante toma la mediana del espectrograma en el mismo punto de las vueltas vecinas. Una nota queda en
el fondo si su altura suena en la mayoría de esas vueltas. Este script lo mide sobre la partitura alineada, sin tocar
el audio ni el cuaderno: qué parte de la melodía principal y qué parte de las otras capas de guitarra quedarían en
primer plano. Si la melodía queda en primer plano mucho más que las otras capas, vale la pena separar; si no, REPET a
esa vuelta no las distingue.

Dos formas de elegir la vuelta:
- global: la vuelta del looper que calcula el cuaderno (`loop_period`, el periodo de los ciclos que más tiempo cubren).
- local: el ciclo más corto que contiene la nota (la unidad que más se repite en ese tramo).
Y dos tamaños de mediana: 3 vueltas (la nota y una a cada lado) o 5 (dos a cada lado).

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

MARGEN = 0.05          # s: cuánto puede correrse una nota entre vueltas en la partitura alineada


def loop_period(cycles: dict) -> float | None:
    """La vuelta del looper como en la celda `loop_period`: el periodo de los ciclos que más tiempo cubren."""
    by = {}
    for c in (c for group in cycles.values() for c in group):
        by.setdefault(round(c["period_s"], 1), []).append(c)
    if not by:
        return None
    best = max(by.values(), key=lambda cs: sum(c["end_s"] - c["start_s"] for c in cs))
    return float(np.median([c["period_s"] for c in best]))


def local_period(cycles: dict, t: float, default: float) -> float:
    """El ciclo más corto que contiene el instante t; si ninguno lo contiene, la vuelta global."""
    cover = [c["period_s"] for group in cycles.values() for c in group if c["start_s"] <= t < c["end_s"]]
    return min(cover) if cover else default


def foreground(notes, everything, spans, turns, period_of):
    """Para cada nota: True si queda en primer plano, False si queda en el fondo, None si no se puede comparar."""
    ts = np.array([n["t"] for n in everything])
    te = np.array([n["te"] for n in everything])
    ps = np.array([n["p"] for n in everything])
    inside = lambda t: any(a <= t < b for a, b in spans)
    r = (turns - 1) // 2
    out = []
    for n in notes:
        m = (n["t"] + n["te"]) / 2
        period = period_of(m)
        votes = []
        for k in [k for k in range(-r, r + 1) if k != 0]:
            t = m + k * period
            if inside(t):
                votes.append(bool(np.any((np.abs(ps - n["p"]) < 0.26) & (ts < t + MARGEN) & (te > t - MARGEN))))
        if not votes:
            out.append(None)
            continue
        present, total = 1 + sum(votes), 1 + len(votes)
        out.append(present <= total / 2)
    return out


def pct(values):
    v = [x for x in values if x is not None]
    return (100.0 * sum(v) / len(v), len(v)) if v else (float("nan"), 0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path, help="carpetas de corrida con line_diagnostics.json")
    ap.add_argument("--secciones", action="store_true", help="detalle por sección (vuelta local, 5 vueltas)")
    args = ap.parse_args(argv)
    for run in args.corridas:
        song = M.song_key(run.name)
        diag = run / "line_diagnostics.json"
        if song is None or not diag.exists():
            print(f"\n{run.name}: sin partitura de evaluación o sin line_diagnostics.json")
            continue
        J = json.loads(diag.read_text(encoding="utf-8"))
        cycles = J.get("cycles_n") or {}
        P = loop_period(cycles)
        if P is None:
            print(f"\n{run.name}: el cuaderno no encontró ciclos")
            continue
        al = M.Alignment(song)
        gu = M.mapped(al, al.ref["guitars"])
        lead = M.lead_line(al, song)
        key = lambda n: (round(n["t"], 4), n["p"], n["part"])
        lead_keys = {key(n) for n in lead}
        others = [n for n in gu if key(n) not in lead_keys]
        spans = [(float(al.t(t0)), float(al.t(t1))) for t0, t1, nm, kn in al.ref["sections"] if kn]

        print(f"\n{run.name}")
        print(f"   vuelta del looper (global): {P:.3f} s")
        for voice, group in cycles.items():
            desc = ", ".join(f"{c['period_s']:.2f} s en {c['start_s']:.0f}-{c['end_s']:.0f} s" for c in group)
            print(f"   ciclos de la {voice.lower()}: {desc or 'ninguno'}")
        print("   % de notas en primer plano (entre paréntesis, notas que se pudieron medir):")
        print(f"   {'':26s} {'global, 3':>14s} {'global, 5':>14s} {'local, 3':>14s} {'local, 5':>14s}")
        res = {}
        for name, ns in (("melodía principal", lead), ("otras capas de guitarra", others)):
            row = []
            for label, period_of in (("global", lambda t: P), ("local", lambda t: local_period(cycles, t, P))):
                for turns in (3, 5):
                    f = foreground(ns, gu, spans, turns, period_of)
                    res[(name, label, turns)] = f
                    v, n = pct(f)
                    row.append(f"{v:5.1f} % ({n:4d})")
            print(f"   {name:26s} " + " ".join(f"{x:>14s}" for x in row))

        if args.secciones:
            names = [nm for t0, t1, nm, kn in al.ref["sections"]]
            f_lead = res[("melodía principal", "local", 5)]
            f_oth = res[("otras capas de guitarra", "local", 5)]
            print(f"   por sección (vuelta local, 5 vueltas): {'':4s} {'melodía':>15s} {'otras capas':>15s}")
            seen = []
            for nm in names:
                if nm in seen:
                    continue
                seen.append(nm)
                a = [f for n, f in zip(lead, f_lead) if names[n["sec"]] == nm]
                b = [f for n, f in zip(others, f_oth) if names[n["sec"]] == nm]
                (va, na), (vb, nb) = pct(a), pct(b)
                if na or nb:
                    print(f"      {nm[:38]:38s} {va:6.1f} % ({na:4d}) {vb:6.1f} % ({nb:4d})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
