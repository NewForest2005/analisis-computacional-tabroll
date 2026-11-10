"""Distancias entre círculos armónicos y pruebas de validación del círculo (no interviene en el cuaderno).

Distancias por capa, de 0 (iguales) a 1:
- Perfiles (bajo, voz aguda, fundamentales, fundamentales por ciclo): transporte sobre el círculo de 24 posiciones.
  Dos posiciones vecinas se parecen más que dos opuestas, y 1 significa toda la masa en el punto opuesto.
- Transiciones, movimientos y calidades: Jensen-Shannon. Si alguno de los dos círculos tiene menos de 5 cambios de
  fundamental, transiciones y movimientos no se comparan: una canción casi estática no tiene movimientos que medir, y
  eso ya lo dice el ritmo armónico.
- Ritmo armónico: diferencia de cambios por compás.
La distancia combinada es la media de las capas disponibles, con el mismo peso por ahora. Los pesos definitivos se
fijarán con el corpus de estilos, no a mano.

Pruebas de validación de la estrategia:
1. Audio frente a partitura, en los mismos compases. Debe quedar muy por debajo de la distancia entre canciones.
2. Primera mitad frente a segunda mitad de la misma canción.
3. Distancia a la canción más cercana.
"""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np

from tabroll.cells.chord24 import chord24
from tabroll.cells.harmony_circle import harmony_circle
from tabroll.cells.notetable import NoteTable
from tabroll.evaluation import melodia as M
from tabroll.evaluation.armonia import PC24, ear_tonic

MIN_CAMBIOS = 5


def circular_emd(p, q):
    p, q = np.asarray(p, float), np.asarray(q, float)
    if p.sum() <= 0 or q.sum() <= 0:
        return None
    d = np.cumsum(p / p.sum() - q / q.sum())
    return float(np.abs(d - np.median(d)).sum() / 12)


def js(p, q):
    if isinstance(p, dict):
        keys = sorted(set(p) | set(q))
        p, q = [p.get(k, 0.0) for k in keys], [q.get(k, 0.0) for k in keys]
    a, b = np.asarray(p, float).ravel(), np.asarray(q, float).ravel()
    if a.sum() <= 0 or b.sum() <= 0:
        return None
    a, b = a / a.sum(), b / b.sum()
    m = (a + b) / 2
    kl = lambda x, y: float(np.sum(x[x > 0] * np.log2(x[x > 0] / y[x > 0])))
    return 0.5 * kl(a, m) + 0.5 * kl(b, m)


LAYERS = {"perfil_bajo": circular_emd, "perfil_aguda": circular_emd, "fundamentales": circular_emd,
          "fundamentales_por_ciclo": circular_emd, "transiciones": js, "movimientos": js, "calidades": js}


def circle_distance(c1: dict, c2: dict) -> dict:
    d = {k: f(c1[k], c2[k]) for k, f in LAYERS.items()}
    if min(c1["cambios"], c2["cambios"]) < MIN_CAMBIOS:
        d["transiciones"] = d["movimientos"] = None
    d["ritmo_armonico"] = abs(c1["cambios_por_compas"] - c2["cambios_por_compas"])
    vals = [v for v in d.values() if v is not None]
    d["combinada"] = float(np.mean(vals)) if vals else None
    return {k: (round(v, 3) if v is not None else None) for k, v in d.items()}


def score_circles(song: str, bars: list[dict], raw_high, center_pc24: int) -> tuple[dict, dict] | None:
    """Círculo del audio y de la partitura en los mismos compases medibles. En la partitura, la fundamental sale de los
    bajos y todas las guitarras (como en la evaluación de la armonía) y la voz aguda de la melodía principal."""
    if song not in M.CANCIONES:
        return None
    al = M.Alignment(song)
    gu, ba = M.mapped(al, al.ref["guitars"]), M.mapped(al, al.ref["basses"])
    sh = M.calib(M.top_line(gu), M._notes(raw_high))
    shift = lambda ns: [(n["t"] + sh, n["te"] + sh, n["p"]) for n in ns]
    G, B, L = NoteTable(shift(gu)), NoteTable(shift(ba)), NoteTable(shift(M.lead_line(al, song)))
    spans = [(float(al.t(t0)) + sh, float(al.t(t1)) + sh) for t0, t1, nm, kn in al.ref["sections"] if kn]
    det, ref = [], []
    for b in bars:
        t0, t1 = b["inicio_s"], b["fin_s"]
        if b.get("fundamental_pc24") is None or not any(a <= t0 + 0.05 and t1 - 0.05 <= e for a, e in spans):
            continue
        ch = chord24(B.profile(t0, t1), G.profile(t0, t1))
        if ch is None:
            continue
        det.append(b)
        ref.append(dict(compas=b["compas"], inicio_s=t0, fin_s=t1, fundamental_pc24=ch["fundamental"], calidad=ch["calidad"],
                        confianza=1.0, ciclo_bajo=b.get("ciclo_bajo"), perfil_bajo=B.profile(t0, t1).tolist(),
                        perfil_aguda=L.profile(t0, t1).tolist()))
    return (harmony_circle(det, center_pc24), harmony_circle(ref, center_pc24)) if det else None


def compare_runs(run_dirs: list[Path]) -> dict:
    """Círculos de varias corridas, distancias entre ellas y las pruebas de validación."""
    circles, halves, vs_score = {}, {}, {}
    for d in map(Path, run_dirs):
        if not (d / "armonia.json").exists():
            continue
        H = json.loads((d / "armonia.json").read_text(encoding="utf-8"))
        bars, res = H["compases"], H.get("resumen") or {}
        name = d.name
        center = PC24.index(res["centro"]) if res.get("centro") in PC24 else int(H.get("tonica_pc24") or 0)
        circles[name] = harmony_circle(bars, center)
        h = len(bars) // 2
        halves[name] = circle_distance(harmony_circle(bars[:h], center), harmony_circle(bars[h:], center))
        song = M.song_key(name)
        if song and (d / "line_diagnostics.json").exists():
            J = json.loads((d / "line_diagnostics.json").read_text(encoding="utf-8"))
            pair = score_circles(song, bars, J["raw_high"], center)
            if pair:
                vs_score[name] = circle_distance(*pair)
        circles[name].update(centro=PC24[center], tonica_de_oido=ear_tonic(name))
    between = {f"{a} | {b}": circle_distance(circles[a], circles[b]) for a, b in itertools.combinations(circles, 2)}
    nearest = {n: min((v["combinada"] for k, v in between.items() if n in k.split(" | ") and v["combinada"] is not None),
                      default=None) for n in circles}
    return dict(circulos=circles, entre_canciones=between, mitades=halves, audio_vs_partitura=vs_score, cancion_mas_cercana=nearest)

