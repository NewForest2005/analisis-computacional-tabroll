"""Desplazamiento de campos (Hába) y uso de los cuartos de tono: pone a prueba con datos lo que dicen los analistas.

Uso:
    python scripts/campos_haba.py <corridas de la banda> [--control <Primus>] [--comparar <King Gizzard>] \
        [--permutaciones 500] --salida outputs/campos_haba

En 24-EDO la quinta mide 14 pasos y mcd(14, 24) = 2: el círculo de quintas se parte en dos campos, los 12 grados
regulares (pares) y los 12 en cuarto de tono (impares). Hába armonizaba dentro de un solo campo y pasaba de uno al otro
por la melodía («desplazamiento de campos»). Levi McClain y David Bennett sostienen que Angine de Poitrine hace lo mismo:
microtonalidad horizontal y casi nunca vertical, cuartos de tono como notas de paso, por grado conjunto. Medidas:

1. Mezcla vertical V: en una rejilla de 20 ms, la fracción del tiempo en que suenan la voz aguda y el bajo y están en
   campos distintos. Modelo nulo: se desplaza el bajo en bloque un tiempo al azar (≥ 2 s, circular), lo que conserva
   cuántos cuartos de tono tiene cada voz y su ritmo, pero rompe su coordinación. p = fracción de desplazamientos con V
   igual o menor que la observada: p chico = evitan mezclar campos más de lo que daría el azar.
   V por compás: la línea de tiempo para ver si la mezcla aparece al final de las secciones.
2. Cruce horizontal H: fracción de los pasos melódicos de cada voz que cambian de campo.
3. Grado conjunto: de los pasos que llegan a un cuarto de tono o salen de él, fracción de un cuarto de tono (50 c) y de
   un semitono o menos (≤ 100 c).
4. Posición métrica: fracción de las notas en cuarto de tono y de las regulares que empiezan en un pulso o en el primer
   pulso del compás. Modelo nulo: se barajan las etiquetas de campo entre las notas (las posiciones quedan).
   p chico = los cuartos de tono caen en tiempo fuerte menos de lo que daría el azar.
5. Resolución: fracción de notas en cuarto de tono seguidas de una nota regular a un paso (≤ 100 c).

En Primus (sin cuartos de tono) todo cuarto de tono es error de medición: sus cifras son el piso de cada medida.
Escribe <salida>.md, <salida>.csv, <salida>.json y <salida>_compases.csv (V por compás).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import numpy as np

DT = 0.02


def nombre(run: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", run)
    n = re.sub(r"(angine_de_poitrine_|king_gizzard_|primus_|_audio_off\w*|_official_audio|_repro|_cache|_\d{4}_\w+$)", "", n)
    return n.replace("_", " ").strip().capitalize()


def leer(run: Path) -> dict:
    H = json.loads((run / "armonia.json").read_text(encoding="utf-8"))
    J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
    bpm = float(J.get("tempo_bpm") or 120.0)
    voz = lambda k: [(float(n["start_s"]), float(n["end_s"]), int(round(float(n["midi"]) * 2))) for n in J.get(k) or []
                     if float(n["end_s"]) > float(n["start_s"])]
    compases = [(b["inicio_s"], b["fin_s"], b.get("compas")) for b in H["compases"]]
    return dict(aguda=sorted(voz("raw_high")), bajo=sorted(voz("raw_bass")), compases=compases, pulso=60.0 / bpm)


def rejilla(notas: list, n: int) -> np.ndarray:
    """Por cuadro de 20 ms: campo de la nota que suena (0 regular, 1 cuarto de tono) o −1."""
    g = np.full(n, -1, dtype=np.int8)
    for a, e, q in notas:
        g[int(a / DT):min(n, int(e / DT))] = q % 2
    return g


def mezcla(a: np.ndarray, b: np.ndarray) -> float:
    ambas = (a >= 0) & (b >= 0)
    return float(((a != b) & ambas).sum() / ambas.sum()) if ambas.sum() else float("nan")


def pasos(notas: list, hueco: float = 0.5) -> list[tuple[int, int]]:
    """(q anterior, q siguiente) de notas seguidas de una voz, con menos de `hueco` s de silencio entre ellas."""
    return [(notas[i][2], notas[i + 1][2]) for i in range(len(notas) - 1) if notas[i + 1][0] - notas[i][1] < hueco]


def pulsos(compases: list, pulso: float) -> tuple[np.ndarray, np.ndarray]:
    ts, inicios = [], []
    for t0, t1, _ in compases:
        L = max(1, int(round((t1 - t0) / pulso)))
        ts += list(t0 + (t1 - t0) * np.arange(L) / L)
        inicios.append(t0)
    return np.array(ts), np.array(inicios)


def en(ts: np.ndarray, t: float, tol: float) -> bool:
    if not len(ts):
        return False
    i = np.searchsorted(ts, t)
    return any(abs(ts[j] - t) <= tol for j in (i - 1, i) if 0 <= j < len(ts))


def medir(run: Path, perm: int, rng: np.random.Generator) -> tuple[dict, list]:
    d = leer(run)
    fin = max([e for _, e, _ in d["aguda"] + d["bajo"]] + [0])
    n = int(fin / DT) + 1
    A, B = rejilla(d["aguda"], n), rejilla(d["bajo"], n)
    V = mezcla(A, B)
    nulos = []
    for _ in range(perm):
        s = int(rng.integers(int(2 / DT), max(int(2 / DT) + 1, n - int(2 / DT))))
        nulos.append(mezcla(A, np.roll(B, s)))
    nulos = np.array([x for x in nulos if x == x])
    p_v = float((nulos <= V).mean()) if len(nulos) else float("nan")

    todos = pasos(d["aguda"]) + pasos(d["bajo"])
    H = float(np.mean([(x % 2) != (y % 2) for x, y in todos])) if todos else float("nan")
    con_q = [(x, y) for x, y in todos if x % 2 or y % 2]
    paso_q = float(np.mean([abs(x - y) == 1 for x, y in con_q])) if con_q else float("nan")
    paso_st = float(np.mean([abs(x - y) <= 2 for x, y in con_q])) if con_q else float("nan")
    sal = [(x, y) for x, y in pasos(d["aguda"]) if x % 2]
    resuelve = float(np.mean([y % 2 == 0 and abs(x - y) <= 2 for x, y in sal])) if sal else float("nan")

    ts, ini = pulsos(d["compases"], d["pulso"])
    tol = 0.12 * d["pulso"]
    notas = d["aguda"]
    campo = np.array([q % 2 for _, _, q in notas])
    fuerte = np.array([en(ts, a, tol) for a, _, _ in notas])
    primero = np.array([en(ini, a, tol) for a, _, _ in notas])

    def dif(lab: np.ndarray, pos: np.ndarray) -> float:
        if lab.sum() == 0 or (1 - lab).sum() == 0:
            return float("nan")
        return float(pos[lab == 1].mean() - pos[lab == 0].mean())

    obs_f, obs_p = dif(campo, fuerte), dif(campo, primero)
    nul_f = np.array([dif(rng.permutation(campo), fuerte) for _ in range(perm)])
    p_f = float((nul_f <= obs_f).mean()) if obs_f == obs_f else float("nan")

    por_compas = []
    for t0, t1, c in d["compases"]:
        i0, i1 = int(t0 / DT), min(n, int(t1 / DT))
        a, b = A[i0:i1], B[i0:i1]
        ambas = (a >= 0) & (b >= 0)
        por_compas.append(dict(compas=c, inicio_s=round(t0, 2), fin_s=round(t1, 2),
                               mezcla=round(float(((a != b) & ambas).sum() / ambas.sum()), 3) if ambas.sum() >= 5 else "",
                               cuartos=round(float(((a == 1) | (b == 1)).sum() / max(1, ((a >= 0) | (b >= 0)).sum())), 3)))
    r = dict(cancion=nombre(run.name), corrida=run.name,
             cuartos_aguda=round(100 * float((campo == 1).mean()), 1) if len(campo) else None,
             mezcla_vertical=round(100 * V, 1), mezcla_nula=round(100 * float(nulos.mean()), 1) if len(nulos) else None,
             p_mezcla=round(p_v, 3), cruce_horizontal=round(100 * H, 1),
             paso_cuarto=round(100 * paso_q, 1), paso_semitono=round(100 * paso_st, 1), resuelve_por_paso=round(100 * resuelve, 1),
             cuartos_en_pulso=round(100 * float(fuerte[campo == 1].mean()), 1) if (campo == 1).any() else None,
             regulares_en_pulso=round(100 * float(fuerte[campo == 0].mean()), 1) if (campo == 0).any() else None,
             cuartos_en_primer_pulso=round(100 * float(primero[campo == 1].mean()), 1) if (campo == 1).any() else None,
             regulares_en_primer_pulso=round(100 * float(primero[campo == 0].mean()), 1) if (campo == 0).any() else None,
             dif_pulso=round(100 * obs_f, 1) if obs_f == obs_f else None, dif_primer_pulso=round(100 * obs_p, 1) if obs_p == obs_p else None,
             p_pulso=round(p_f, 3))
    return r, por_compas


def unicas(lista: list[Path]) -> list[Path]:
    """Una corrida por canción (la más reciente) y solo las que tienen armonia.json."""
    por = {}
    for r in sorted(lista, key=lambda r: r.name):
        if (r / "armonia.json").exists():
            por[nombre(r.name)] = r
    return list(por.values())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--control", nargs="*", type=Path, default=[])
    ap.add_argument("--comparar", nargs="*", type=Path, default=[])
    ap.add_argument("--permutaciones", type=int, default=500)
    ap.add_argument("--salida", default="outputs/campos_haba")
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    filas, compases, vistos = [], [], set()
    for grupo, lista in (("banda", a.corridas), ("control", a.control), ("comparar", a.comparar)):
        for run in unicas(lista):
            if nombre(run.name) in vistos:
                continue
            vistos.add(nombre(run.name))
            r, pc = medir(run, a.permutaciones, rng)
            r["grupo"] = grupo
            filas.append(r)
            compases += [dict(cancion=r["cancion"], grupo=grupo, **x) for x in pc]
            print(f"[{grupo}] {r['cancion']}: mezcla vertical {r['mezcla_vertical']} % (azar {r['mezcla_nula']} %, p {r['p_mezcla']}) · "
                  f"cruce horizontal {r['cruce_horizontal']} % · paso de ¼ {r['paso_cuarto']} %, ≤ semitono {r['paso_semitono']} % · "
                  f"en pulso: ¼ {r['cuartos_en_pulso']} % vs regulares {r['regulares_en_pulso']} % (p {r['p_pulso']}) · "
                  f"resuelve por paso {r['resuelve_por_paso']} %")
    cols = list(filas[0])
    with open(a.salida + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["grupo"] + [c for c in cols if c != "grupo"])
        w.writeheader()
        w.writerows(filas)
    with open(a.salida + "_compases.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(compases[0]))
        w.writeheader()
        w.writerows(compases)
    Path(a.salida + ".json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
    md = ["# Desplazamiento de campos y uso de los cuartos de tono", "",
          "| Grupo | Canción | ¼ en voz aguda | Mezcla vertical (azar, p) | Cruce horizontal | Paso de ¼ / ≤ semitono | ¼ en pulso vs regulares (p) | Resuelve por paso |",
          "|---|---|---|---|---|---|---|---|"]
    for r in filas:
        md.append(f"| {r['grupo']} | {r['cancion']} | {r['cuartos_aguda']} % | {r['mezcla_vertical']} % ({r['mezcla_nula']} %, {r['p_mezcla']}) | "
                  f"{r['cruce_horizontal']} % | {r['paso_cuarto']} / {r['paso_semitono']} % | {r['cuartos_en_pulso']} vs {r['regulares_en_pulso']} % ({r['p_pulso']}) | "
                  f"{r['resuelve_por_paso']} % |")
    Path(a.salida + ".md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"→ {a.salida}.md/.csv/.json, {a.salida}_compases.csv")


if __name__ == "__main__":
    main()
