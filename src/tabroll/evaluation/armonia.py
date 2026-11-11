"""Evaluación de la armonía por compás contra las partituras corregidas (solo mide; el cuaderno no usa este módulo).

Para cada compás del cuaderno se analiza la partitura con la misma función (`chord24`), en el mismo tramo de audio:
el bajo con los bajos de la partitura y la voz aguda con todas las guitarras de la partitura. Así se compara lo que
sale de las notas detectadas con lo que saldría de las notas verdaderas. Solo cuentan los compases que caen enteros en
tramos medibles (la misma alineación que la evaluación de la melodía). Las medidas se ponderan por la duración.

- fundamental: misma fundamental en 24-EDO.
- fundamental_y_calidad: además, la misma calidad (5, m, n, M, ...). Es exigente: el cuaderno solo transcribe dos voces
  y la partitura tiene todas.
- bajo: la nota que más suena en el bajo. Si en la partitura dos notas de bajo suenan lo mismo en el compás, vale
  cualquiera de las dos (columna ref_bajo del .csv).
- confiables: los compases con confianza ≥ 0.5. Si la confianza sirve, ahí la fundamental acierta mucho más que en el
  resto.
- centro: la medida de centro en 24-EDO aplicada al bajo y a la melodía principal de la partitura, con los mismos ciclos,
  frente al centro que eligió el cuaderno.
- capas: los movimientos de la fundamental y las calidades en los compases medidos, del cuaderno frente a la partitura,
  con su distancia de Jensen-Shannon (0 = iguales, 1 = sin nada en común).
- funciones: la función de cada compás (`chord_roles`, con el centro del cuaderno) en el cuaderno y en la partitura.
  `funcion` es la parte del tiempo en que coinciden (también en los confiables), y `distancia_funciones` compara cómo se
  reparte el tiempo entre tónica, subdominante, dominante y neutra. `eje` y `distancia_ejes` hacen lo mismo con los ejes
  de Lendvai.
- progresiones: `chord_progressions` sobre todos los compases medidos, del cuaderno y de la partitura: qué parte de los
  cambios va por quintas, qué tan usuales son en la tabla de Piston, los vaivenes y las progresiones con nombre.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

from tabroll.cells.chord24 import chord24
from tabroll.cells.center24_by_layer import center24_by_layer
from tabroll.cells.chord_progressions import chord_progressions
from tabroll.cells.chord_roles import chord_roles
from tabroll.cells.harmony_layers import harmony_layers
from tabroll.cells.notetable import NoteTable
from tabroll.evaluation import melodia as M


PC24 = ['C', 'C+', 'C#', 'C#+', 'D', 'D+', 'D#', 'D#+', 'E', 'E+', 'F', 'F+',
        'F#', 'F#+', 'G', 'G+', 'G#', 'G#+', 'A', 'A+', 'A#', 'A#+', 'B', 'B+']


# Nota de reposo de cada canción, de oído (autor, 9-nov-2026). Sirve para comprobar el centro, también sin partitura.
TONICA_DE_OIDO = {"mata zyklek": "G", "sarniezz": "E", "fabienk": "E", "utzp": "E", "uztp": "E", "yor zarad": "G"}


def ear_tonic(name: str) -> str | None:
    """Tónica de oído para un nombre de audio o de carpeta, si la canción está en la lista."""
    low = name.lower().replace("_", " ")
    return next((t for k, t in TONICA_DE_OIDO.items() if k in low), None)


def _tied_max(profile) -> list[int]:
    """Clases que empatan en el máximo de un perfil, con redondeo estable entre máquinas."""
    p = np.round(np.asarray(profile, float), 6)
    return [int(k) for k in np.flatnonzero(p == p.max())] if p.max() > 0 else []


def _js(p: dict, q: dict) -> float | None:
    """Distancia de Jensen-Shannon (base 2) entre dos histogramas dados como diccionarios."""
    keys = sorted(set(p) | set(q))
    a, b = np.array([p.get(k, 0.0) for k in keys], float), np.array([q.get(k, 0.0) for k in keys], float)
    if a.sum() <= 0 or b.sum() <= 0:
        return None
    a, b = a / a.sum(), b / b.sum()
    m = (a + b) / 2
    kl = lambda x, y: float(np.sum(x[x > 0] * np.log2(x[x > 0] / y[x > 0])))
    return round(0.5 * kl(a, m) + 0.5 * kl(b, m), 3)


def _shares(rows: list[dict], key: str) -> dict:
    """Parte del tiempo (en %) de cada valor de `key`, de mayor a menor."""
    acc = {}
    for x in rows:
        if x.get(key) is not None:
            acc[x[key]] = acc.get(x[key], 0.0) + x["fin_s"] - x["inicio_s"]
    tot = sum(acc.values()) or 1.0
    return {k: round(100 * v / tot, 1) for k, v in sorted(acc.items(), key=lambda kv: -kv[1])}


def _progressions(rows: list[dict], menor: bool) -> dict:
    """Resumen de progresiones de todos los compases dados, en la forma corta que guarda la evaluación."""
    p = chord_progressions(rows, menor=menor)[1]["todos"]
    return dict(cambios=p["cambios"], por_quintas=p["por_quintas"], uso_piston=p["uso_piston"], ejes=p["ejes"],
                vaivenes=p["vaivenes"],
                con_nombre={k: v["veces"] for k, v in p["con_nombre"].items()}, frecuentes=p["frecuentes"][:5])


def evaluate(song: str, bars: list[dict], raw_high, min_conf: float = 0.5, cycles: dict | None = None,
             resumen: dict | None = None, tonic_pc24: int | None = None) -> dict:
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
        Pb = B.profile(t0, t1)
        ref = chord24(Pb, G.profile(t0, t1))
        if ref is None:
            continue
        bass = _tied_max(Pb)
        rows.append(dict(compas=b["compas"], inicio_s=t0, fin_s=t1, detectada=b["fundamental"], calidad=b["calidad"],
                         confianza=b["confianza"], ref_fundamental_pc24=ref["fundamental"], ref_calidad=ref["calidad"],
                         ref_bajo="/".join(PC24[k] for k in bass),
                         ok_fundamental=b["fundamental_pc24"] == ref["fundamental"], ok_calidad=b["calidad"] == ref["calidad"],
                         ok_bajo=b.get("bajo_pc24") in bass if bass else b.get("bajo_pc24") is None))
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
             fundamental_confiables=pct(ok_f, conf), fundamental_resto=pct(ok_f, ~conf))
    if cycles is not None:                                              # centro de la partitura con la misma medida
        lead = [(n["t"] + sh, n["te"] + sh, n["p"]) for n in M.lead_line(al, song)]
        low = [(n["t"] + sh, n["te"] + sh, n["p"]) for n in M.top_line(ba, low=True)]
        c = center24_by_layer(low, lead, cycles)
        r.update(centro_partitura=PC24[c["centro_pc24"]], centro_bajo_partitura=PC24[c["centro_bajo_pc24"]])
    if resumen:
        r.update(centro_cuaderno=resumen.get("centro"), centro_24edo_cuaderno=resumen.get("centro_24edo"),
                 tonica_12_cuaderno=resumen.get("tonica_cuaderno"))
    det = [dict(compas=x["compas"], inicio_s=x["inicio_s"], fin_s=x["fin_s"], fundamental_pc24=PC24.index(x["detectada"]),
                calidad=x["calidad"], confianza=1.0) for x in rows]
    ref = [dict(compas=x["compas"], inicio_s=x["inicio_s"], fin_s=x["fin_s"], fundamental_pc24=x["ref_fundamental_pc24"],
                calidad=x["ref_calidad"], confianza=1.0) for x in rows]
    ld, lr = harmony_layers(det, 0), harmony_layers(ref, 0)              # movimientos y calidades no dependen del centro
    r.update(movimientos_cuaderno=ld["movimientos"], movimientos_partitura=lr["movimientos"],
             distancia_movimientos=_js(ld["movimientos"], lr["movimientos"]),
             calidades_cuaderno=ld["calidades"], calidades_partitura=lr["calidades"],
             distancia_calidades=_js(ld["calidades"], lr["calidades"]),
             cambios_por_compas_cuaderno=ld["cambios_por_compas"], cambios_por_compas_partitura=lr["cambios_por_compas"])
    if tonic_pc24 is None and resumen and resumen.get("centro") in PC24:
        tonic_pc24 = PC24.index(resumen["centro"])
    if tonic_pc24 is not None:                                          # funciones y progresiones con el centro del cuaderno
        modo = ((resumen or {}).get("modo") or {}).get("nombre") or ""
        menor = "♭3" in [x.strip() for x in modo.split(",")]
        fd, fr = chord_roles(det, tonic_pc24), chord_roles(ref, tonic_pc24)
        for x, a, b in zip(rows, fd, fr):
            x.update(cifrado=a["cifrado"], funcion=a["funcion"], ref_cifrado=b["cifrado"], ref_funcion=b["funcion"],
                     ok_funcion=a["funcion"] == b["funcion"], eje=a["eje"], ref_eje=b["eje"], ok_eje=a["eje"] == b["eje"])
        ok_fn = np.array([x["ok_funcion"] for x in rows], float)
        ok_ej = np.array([x["ok_eje"] for x in rows], float)
        ej_d, ej_r = _shares(fd, "eje"), _shares(fr, "eje")
        prog_d, prog_r = _progressions(fd, menor), _progressions(fr, menor)
        fn_d, fn_r = _shares(fd, "funcion"), _shares(fr, "funcion")
        r.update(funcion=pct(ok_fn), funcion_confiables=pct(ok_fn, conf), funciones_cuaderno=fn_d, funciones_partitura=fn_r,
                 distancia_funciones=_js(fn_d, fn_r), por_quintas_cuaderno=prog_d["por_quintas"],
                 por_quintas_partitura=prog_r["por_quintas"], progresiones_cuaderno=prog_d, progresiones_partitura=prog_r,
                 eje=pct(ok_ej), eje_confiables=pct(ok_ej, conf), ejes_cuaderno=ej_d, ejes_partitura=ej_r,
                 distancia_ejes=_js(ej_d, ej_r))
    r["compases"] = rows
    return r


def evaluate_run(run_dir: Path, song: str | None = None, write: bool = True) -> dict | None:
    """Evalúa una corrida con armonia.json y line_diagnostics.json; guarda evaluacion_armonia.json y su .csv."""
    run_dir = Path(run_dir)
    song = song or M.song_key(run_dir.name)
    if song is None or not (run_dir / "armonia.json").exists() or not (run_dir / "line_diagnostics.json").exists():
        return None
    H = json.loads((run_dir / "armonia.json").read_text(encoding="utf-8"))
    J = json.loads((run_dir / "line_diagnostics.json").read_text(encoding="utf-8"))
    cycles = (H.get("resumen") or {}).get("ciclos") or {                  # los mismos ciclos que usó la armonía del cuaderno
        v: [dict(start=c["start_s"], end=c["end_s"], period=c["period_s"]) for c in cs] for v, cs in (J.get("cycles_n") or {}).items()}
    r = evaluate(song, H["compases"], J["raw_high"], cycles=cycles, resumen=H.get("resumen"), tonic_pc24=H.get("tonica_pc24"))
    if write:
        detail = r.pop("compases", [])
        (run_dir / "evaluacion_armonia.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        if detail:
            with open(run_dir / "evaluacion_armonia_por_compas.csv", "w", newline="", encoding="utf-8") as fh:
                wr = csv.DictWriter(fh, fieldnames=list(detail[0]))
                wr.writeheader()
                wr.writerows(detail)
    return r
