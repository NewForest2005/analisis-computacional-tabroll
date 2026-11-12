"""Paso M2 del análisis melódico: patrones de ciclo, sus variantes y por qué cada vuelta se acoge o no al patrón.

Uso:
    python scripts/patrones_ciclo.py
    make extract
    make test

Para cada ciclo (letra) de cada voz, todas sus vueltas se ponen una sobre otra en una rejilla de semicorcheas. El patrón
es la nota que aparece en cada casilla en al menos la mitad de las vueltas. Cada nota del patrón lleva su grado sobre el
centro y qué es en el acorde de ese momento (fundamental, tercera, quinta, inflexión de ¼ de tono o disonante, con la nota
a la que resuelve por grado). Cada vuelta se compara con el patrón: qué parte de sus notas coincide (se acoge) y, si no,
por qué: inflexión de ¼ de tono, cambio de octava, otras notas, notas omitidas o agregadas, transportada o cambia el
acorde. Cambios en el cuaderno, antes del tabroll24: celda nueva `cycle_patterns` y la celda que la aplica.
Se puede correr más de una vez: lo que ya está aplicado no se toca.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
H2_HEADER = "## Tabroll con la armonía en 24-EDO (paso H2)"

DOC_M2 = ("## Patrones de ciclo (paso M2)\n\n"
          "El patrón de cada ciclo de cada voz, con el grado y la función de sus notas, y por qué cada vuelta (y cada "
          "compás) se acoge o no a ese patrón.")

DOC_PATTERNS = ("**`cycle_patterns`**: Patrón de cada ciclo (letra) de cada voz. Las vueltas de una letra se ponen una "
                "sobre otra en una rejilla de `por_pulso` casillas por pulso (si una letra aparece con un periodo que es "
                "múltiplo de otro, se parte en vueltas del más corto). El patrón es la nota que aparece en cada casilla "
                "en al menos `presencia` de las vueltas. Cada nota del patrón lleva su posición (pulso.subdivisión), su "
                "grado sobre `tonic_pc24` y qué es en el acorde del momento: fundamental, 2.ª, 3.ª, 4.ª, 5.ª, inflexión "
                "de ¼ de tono o disonante, con la nota a la que resuelve si la siguiente está a un grado y es del acorde. "
                "Cada vuelta se compara con el patrón: la parte de sus notas que coincide (se acoge) y los motivos si no "
                "es igual: inflexión de ¼ de tono, cambio de octava, otras notas, notas omitidas, notas agregadas, "
                "transportada, cambios menores, o cambia el acorde respecto del más usual bajo esa letra. Un motivo de "
                "notas cuenta si toca al menos el 10 % del patrón. Devuelve las filas con `acoge_aguda`, `motivo_aguda`, "
                "`acoge_bajo` y `motivo_bajo` por compás, y el resumen por voz y letra, con los puntos donde más varía. "
                "`dentro` (opcional) limita las vueltas a un tramo, para la evaluación.")

DOC_RUN_M2 = ("Patrones de ciclo de la canción: agrega a cada compás cuánto se acoge al patrón y por qué, y el resumen a "
              "`armonia_resumen['patrones']`.")

CODE_PATTERNS = '''from collections import Counter

import numpy as np

from tabroll.cells.chord24 import CHORDS24
from tabroll.cells.harmony_by_bar import DEG24_NAMES, PC24_NAMES

PAPEL_CORTO = {0: 'fund.', 4: '2.ª', 6: '3.ª', 7: '3.ª', 8: '3.ª', 10: '4.ª', 12: '5.ª', 14: '5.ª', 16: '5.ª'}
CORTO = {'Voz aguda': 'aguda', 'Voz grave': 'bajo'}


def cycle_patterns(armonia, cycles, notes_by_voice, lens, tonic_pc24, por_pulso=4, presencia=0.5, dentro=None):
    pc = lambda m: int(round(2 * m)) % 24
    nombre = lambda m: PC24_NAMES[pc(m)] + str(int(round(2 * m)) // 24 - 1)
    beat = float(np.median([(r['fin_s'] - r['inicio_s']) / max(int(round(L)), 1) for r, L in zip(armonia, lens)]))
    inicios = np.array([r['inicio_s'] for r in armonia])

    def compases(t0, t1):                                              # compases que se cruzan con [t0, t1)
        return [k for k, r in enumerate(armonia) if r['inicio_s'] < t1 - 0.05 and r['fin_s'] > t0 + 0.05]

    def acorde_en(t):
        k = int(np.searchsorted(inicios, t, side='right')) - 1
        r = armonia[k] if 0 <= k < len(armonia) and t < armonia[k]['fin_s'] else None
        return (r['fundamental_pc24'], r['calidad'], r.get('cifrado')) if r and r.get('fundamental_pc24') is not None and r.get('calidad') in CHORDS24 else None

    def papel(p, ch):                                                  # qué es la nota en el acorde: fund., 3.ª, infl. o disonante
        if ch is None:
            return None, None
        rel = (pc(p) - ch[0]) % 24
        x = min(CHORDS24[ch[1]], key=lambda x: min((rel - x) % 24, (x - rel) % 24))
        dist = min((rel - x) % 24, (x - rel) % 24)
        return (PAPEL_CORTO[x], dist) if dist == 0 else ('infl. ¼', dist) if dist == 1 else ('disonante', dist)

    filas = {k: {} for k in range(len(armonia))}
    resumen = {}
    for voz, grupo in cycles.items():
        notas = sorted(map(tuple, notes_by_voice.get(voz) or []))
        ini = np.array([n[0] for n in notas]) if notas else np.zeros(0)
        segs = {}
        for c in grupo:
            segs.setdefault(c.label, []).append((float(c.start), float(c.end), float(c.period)))
        res_voz = {}
        for label, ss in sorted(segs.items()):
            p0 = min(p for _, _, p in ss)
            n_slots = max(4, int(round(p0 / beat * por_pulso)))
            pos = lambda s: f'{1 + s // por_pulso}.{1 + s % por_pulso}'   # pulso.subdivisión dentro de la vuelta
            vueltas = []
            for a, b, P in ss:
                m = max(1, int(round(P / p0)))
                sub = P / m                                            # una vuelta del patrón más corto de la letra
                t0 = a
                while t0 + 0.75 * sub <= b:
                    if dentro is None or dentro(t0, t0 + sub):
                        vueltas.append((t0, sub))
                    t0 += sub
            if len(vueltas) < 2:
                continue
            tn_all = []
            for t0, sub in vueltas:
                half = 0.5 * sub / n_slots
                j0, j1 = np.searchsorted(ini, t0 - half), np.searchsorted(ini, t0 + sub - half)
                tn = {}
                for a, b, p in notas[j0:j1]:
                    s = int(round((a - t0) / sub * n_slots)) % n_slots
                    if s not in tn or b - a > tn[s][1]:
                        tn[s] = (round(2 * p) / 2, b - a)
                tn_all.append({s: v[0] for s, v in tn.items()})
            patron = {}
            for s in range(n_slots):
                alturas = [tn[s] for tn in tn_all if s in tn]
                if len(alturas) >= presencia * len(tn_all):
                    patron[s] = Counter(alturas).most_common(1)[0][0]
            if not patron:
                continue

            usual = Counter(tuple(armonia[k].get('cifrado') for k in compases(t0, t0 + sub)) for t0, sub in vueltas).most_common(1)[0][0]
            detalle, cambios, motivos = [], Counter(), Counter()
            minimo = max(1, int(np.ceil(0.1 * len(patron))))                   # un motivo cuenta si toca al menos el 10 % del patrón
            for (t0, sub), tn in zip(vueltas, tn_all):
                subs = [(s, tn[s] - p) for s, p in patron.items() if s in tn and abs(tn[s] - p) >= 0.25]
                igual = sum(1 for s, p in patron.items() if s in tn and abs(tn[s] - p) < 0.25)
                falta = [s for s in patron if s not in tn]
                extra = [s for s in tn if s not in patron]
                acoge = igual / len(patron)
                razones = []
                if acoge >= 0.85 and len(extra) <= 0.15 * len(patron):
                    razones.append('igual al patrón')
                else:
                    deltas = Counter(round(d * 2) / 2 for _, d in subs)
                    if subs and len(subs) >= 0.6 * len(patron) and deltas.most_common(1)[0][1] >= 0.8 * len(subs):
                        razones.append(f'transportada {deltas.most_common(1)[0][0]:+g}')
                    else:
                        if sum(abs(d) == 0.5 for _, d in subs) >= minimo:
                            razones.append('inflexión de ¼ de tono')
                        if sum(abs(abs(d) - 12) < 0.25 for _, d in subs) >= minimo:
                            razones.append('cambio de octava')
                        if sum(abs(d) != 0.5 and abs(abs(d) - 12) >= 0.25 for _, d in subs) >= minimo:
                            razones.append('otras notas')
                    if len(falta) >= 0.25 * len(patron):
                        razones.append('notas omitidas')
                    if len(extra) >= 0.25 * len(patron):
                        razones.append('notas agregadas')
                    if not razones:
                        razones.append('cambios menores')
                for s, d in subs:                                      # puntos de variación: qué nota cambia y a cuál
                    cambios[f'{pos(s)} {nombre(patron[s])}→{nombre(patron[s] + d)}'] += 1
                aqui = tuple(armonia[k].get('cifrado') for k in compases(t0, t0 + sub))
                motivos.update(razones + (['cambia el acorde'] if aqui != usual else []))
                if aqui != usual:
                    razones = razones + ['cambia el acorde (' + ' '.join(str(x) for x in aqui) + ')']
                detalle.append(dict(t=round(t0, 2), acoge=round(100 * acoge, 1), motivos=razones))
                for k in compases(t0, t0 + sub):
                    filas[k].setdefault(voz, []).append((acoge, razones))

            notas_patron, disonantes, resueltas = [], 0, 0
            orden = sorted(patron)
            for i, s in enumerate(orden):
                p = patron[s]
                ch = Counter(acorde_en(t0 + s * sub / n_slots) for t0, sub in vueltas).most_common(1)[0][0]
                rol, _ = papel(p, ch)
                txt = f'{pos(s)} {nombre(p)} {DEG24_NAMES[(pc(p) - tonic_pc24) % 24]}' + (f' ({rol})' if rol else '')
                if rol == 'disonante':
                    disonantes += 1
                    q = patron[orden[(i + 1) % len(orden)]]
                    rol_q, _ = papel(q, ch)
                    if 0.25 <= abs(q - p) <= 2.25 and rol_q not in ('disonante', None):
                        resueltas += 1
                        txt = txt[:-1] + f' → {DEG24_NAMES[(pc(q) - tonic_pc24) % 24]})'
                notas_patron.append(txt)
            ultimo = DEG24_NAMES[(pc(patron[orden[-1]]) - tonic_pc24) % 24]
            n = len(vueltas)
            res_voz[label] = dict(
                periodo_s=round(p0, 3), vueltas=n, notas=len(patron), patron=' · '.join(notas_patron), slots=n_slots,
                patron_notas=[[s, patron[s]] for s in orden],
                acoge=round(float(np.mean([d['acoge'] for d in detalle])), 1),
                iguales=round(100.0 * sum('igual al patrón' in d['motivos'] for d in detalle) / n, 1),
                motivos={k: round(100.0 * v / n, 1) for k, v in motivos.most_common()},
                variacion=[[c, v] for c, v in cambios.most_common(4) if v >= 2],
                disonantes=disonantes, resuelven=round(100.0 * resueltas / disonantes, 1) if disonantes else None,
                termina=ultimo, cierra='en reposo' if ultimo in ('1', '5') else 'abierto',
                acorde_usual=' '.join(str(x) for x in usual), segmentos=[[round(a, 2), round(b, 2), round(P, 3)] for a, b, P in ss])
        resumen[voz] = res_voz

    out = []
    for k, row in enumerate(armonia):
        row = dict(row)
        for voz, corto in CORTO.items():
            vs = filas[k].get(voz)
            row[f'acoge_{corto}'] = round(100 * float(np.mean([a for a, _ in vs])), 1) if vs else None
            row[f'motivo_{corto}'] = '; '.join(dict.fromkeys(m for _, ms in vs for m in ms)) if vs else None
        out.append(row)
    return out, resumen'''

CODE_RUN_M2 = '''armonia, armonia_resumen['patrones'] = cycle_patterns(armonia, cycles, {'Voz aguda': raw_high, 'Voz grave': raw_bass},
                                                     lens, tonic_pc24)
for voz, pats in armonia_resumen['patrones'].items():
    print(f'Patrones de ciclo, {voz.lower()}:')
    for letra, d in pats.items():
        variacion = ', '.join(f'{c} ×{v}' for c, v in d['variacion'][:3])
        print(f"  {letra} ({d['periodo_s']:.2f} s, {d['vueltas']} vueltas, {d['notas']} notas, sobre {d['acorde_usual']}): se acoge "
              f"{d['acoge']:.0f}%, iguales {d['iguales']:.0f}% | motivos: " +
              ', '.join(f'{k} {v:.0f}%' for k, v in d['motivos'].items() if k != 'igual al patrón'))
        print(f"     patrón: {' · '.join(d['patron'].split(' · ')[:8])}{' …' if d['notas'] > 8 else ''}")
        res = f"{d['resuelven']:.0f}% de {d['disonantes']} disonantes resuelven por grado" if d['disonantes'] else 'sin disonantes'
        print(f"     {res}; termina en {d['termina']} ({d['cierra']})" + (f' | dónde varía: {variacion}' if variacion else ''))'''


def _cell(kind: str, text: str) -> dict:
    cell = {"id": uuid.uuid4().hex[:12], "cell_type": kind, "metadata": {}, "source": text.splitlines(keepends=True)}
    if kind == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]
    src = lambda c: "".join(c["source"])
    put = lambda c, text: c.__setitem__("source", text.splitlines(keepends=True))
    done = []
    pares = ((DOC_PATTERNS, CODE_PATTERNS, "def cycle_patterns("), (DOC_RUN_M2, CODE_RUN_M2, "= cycle_patterns(armonia"))
    found = [[i for i, c in enumerate(cells) if c["cell_type"] == "code" and mark in src(c)] for _, _, mark in pares]
    if all(len(f) == 1 for f in found):
        for (doc, code, mark), (i,) in zip(pares, found):
            if src(cells[i]) != code or src(cells[i - 1]) != doc:
                put(cells[i - 1], doc)
                put(cells[i], code)
                done.append("cycle_patterns" if mark.startswith("def") else "celda de patrones")
    elif not any(found):
        head = [i for i, c in enumerate(cells) if c["cell_type"] == "markdown" and src(c).startswith(H2_HEADER)]
        figs = [c for c in cells if c["cell_type"] == "code" and "= melodic_figures(armonia" in src(c)]
        if len(head) != 1 or len(figs) != 1:
            print("No encontré la celda de figuras melódicas o el encabezado del tabroll24. Corre antes scripts/figuras_melodicas.py.")
            return 1
        new = [_cell("markdown", DOC_M2)]
        for doc, code, _ in pares:
            new += [_cell("markdown", doc), _cell("code", code)]
        cells[head[0]:head[0]] = new
        done.append("celdas nuevas cycle_patterns y la de patrones, antes del tabroll24")
    else:
        print("Las celdas de los patrones de ciclo están incompletas; restaura el cuaderno desde git y vuelve a correr.")
        return 1
    if not done:
        print("El cuaderno ya tenía los patrones de ciclo.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
