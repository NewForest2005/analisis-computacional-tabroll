"""Evaluación de la armonía por compás contra las partituras corregidas (solo mide; el cuaderno no usa este módulo).

Para cada compás del cuaderno se analiza la partitura con la misma función (`chord24`), en el mismo tramo de audio:
el bajo con los bajos de la partitura y la voz aguda con todas las guitarras de la partitura. Así se compara lo que
sale de las notas detectadas con lo que saldría de las notas verdaderas. Solo cuentan los compases que caen enteros en
tramos medibles (la misma alineación que la evaluación de la melodía). Las medidas se ponderan por la duración.

- fundamental: misma fundamental en 24-EDO.
- fundamental_y_calidad: además, la misma calidad (5, m, n, M, ...). Es exigente: el cuaderno solo transcribe dos voces
  y la partitura tiene todas.
- bajo: la nota que más suena en el bajo.
- confiables: los compases con confianza ≥ 0.5. Si la confianza sirve, ahí la fundamental acierta mucho más que en el
  resto.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from tabroll.cells.chord24 import chord24
from tabroll.cells.notetable import NoteTable
from tabroll.evaluation import melodia as M


def evaluate(song: str, bars: list[dict], raw_high, min_conf: float = 0.5) -> dict:
    al = M.Alignment(song)
    gu, ba = M.mapped(al, al.ref["guitars"]), M.mapped(al, al.ref["basses"])
    sh = M.calib(M.top_line(gu), M._notes(raw_high))                  # mismo desfase que la evaluación de la melodía
    G = NoteTable([(n["t"] + sh, n["te"] + sh, n["p"]) for n in gu])
    B = NoteTable([(n["t"] + sh, n["te"] + sh, n["p"]) for n in ba])
    spans = [(float(al.t(t0)) + sh, float(al.t(t1)) + sh) for t0, t1, nm, kn in al.ref["sections"] if kn]
    rows = []
    for b in bars:
        t0, t1 = b["inicio_s"], b["fin_s"]
        if b.get("fundamental_pc24") is None or not any(a <= t0 + 0.05 and t1 - 0.05 <= e for a, e in spans):
            continue
        ref = chord24(B.profile(t0, t1), G.profile(t0, t1))
        if ref is None:
            continue
        rows.append(dict(compas=b["compas"], inicio_s=t0, fin_s=t1, detectada=b["fundamental"], calidad=b["calidad"],
                         confianza=b["confianza"], ref_fundamental_pc24=ref["fundamental"], ref_calidad=ref["calidad"],
                         ok_fundamental=b["fundamental_pc24"] == ref["fundamental"], ok_calidad=b["calidad"] == ref["calidad"],
                         ok_bajo=b.get("bajo_pc24") == ref["bajo"]))
    r = dict(cancion=song, compases_medidos=len(rows))
    if not rows:
        return r
    w = np.array([x["fin_s"] - x["inicio_s"] for x in rows])
    ok_f = np.array([x["ok_fundamental"] for x in rows], float)
    ok_fc = np.array([x["ok_fundamental"] and x["ok_calidad"] for x in rows], float)
    ok_b = np.array([x["ok_bajo"] for x in rows], float)
    conf = np.array([x["confianza"] for x in rows]) >= min_conf
    pct = lambda v, m=None: round(100 * float(np.average(v[m], weights=w[m])), 1) if m is None or m.any() else None
    r.update(fundamental=pct(ok_f), fundamental_y_calidad=pct(ok_fc), bajo=pct(ok_b),
             tiempo_confiable=round(100 * float(w[conf].sum() / w.sum()), 1),
             fundamental_confiables=pct(ok_f, conf), fundamental_resto=pct(ok_f, ~conf), compases=rows)
    return r


def evaluate_run(run_dir: Path, song: str | None = None, write: bool = True) -> dict | None:
    """Evalúa una corrida con armonia.json y line_diagnostics.json; guarda evaluacion_armonia.json y su .csv."""
    run_dir = Path(run_dir)
    song = song or M.song_key(run_dir.name)
    if song is None or not (run_dir / "armonia.json").exists() or not (run_dir / "line_diagnostics.json").exists():
        return None
    bars = json.loads((run_dir / "armonia.json").read_text(encoding="utf-8"))["compases"]
    raw_high = json.loads((run_dir / "line_diagnostics.json").read_text(encoding="utf-8"))["raw_high"]
    r = evaluate(song, bars, raw_high)
    if write:
        detail = r.pop("compases", [])
        (run_dir / "evaluacion_armonia.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        if detail:
            with open(run_dir / "evaluacion_armonia_por_compas.csv", "w", newline="", encoding="utf-8") as fh:
                wr = csv.DictWriter(fh, fieldnames=list(detail[0]))
                wr.writeheader()
                wr.writerows(detail)
    return r
