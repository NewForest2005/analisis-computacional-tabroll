"""Paso H3 del análisis armónico: notas columna de cada compás.

Uso:
    python scripts/notas_columna.py
    make extract
    make test

En cada compás (un cuadro del tabroll), las notas columna son las notas de la voz aguda que sostienen el arco de la
melodía, con el bajo que suena debajo de cada una. Cada nota recibe un peso con cuatro reglas de preferencia, a la
manera de la reducción de Lerdahl y Jackendoff: dónde cae el ataque, si es nota del acorde del compás, cuánto dura y si
es un punto alto o bajo del contorno. En cada pulso queda la nota de más peso (la columna del pulso) y la de más peso del
compás es la columna principal. Cambios en el cuaderno, antes del tabroll24:
1. Celdas nuevas `melodic_columns` y `columns_summary`.
2. Celda nueva que agrega las columnas a `armonia` y su resumen a `armonia_resumen['columnas']`, e imprime el resumen.
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

DOC_H3 = ("## Notas columna (paso H3)\n\n"
          "En cada compás (un cuadro del tabroll), las notas de la voz aguda que sostienen el arco de la melodía y el bajo "
          "que suena debajo de cada una: la columna. Responde qué notas sostienen el arco, qué son en el acorde, cómo se "
          "apoyan en el bajo (intervalo) y qué forma tiene el arco en cada compás y en cada ciclo de la voz aguda.")

DOC_COLUMNS = ("**`melodic_columns`**: Notas columna de cada compás. Cada nota de la voz aguda recibe un peso con cuatro "
               "reglas de preferencia, a la manera de la reducción de Lerdahl y Jackendoff: dónde cae el ataque (primer "
               "pulso 1, mitad del compás 0.85, otro pulso 0.7, corchea 0.45, el resto 0.3), si es nota del acorde del "
               "compás (1; a un cuarto de tono, 0.7; fuera, 0.2), cuánto dura (hasta un pulso) y si es un punto alto o "
               "bajo del contorno (`PESOS` las combina). En cada pulso queda la nota de más peso con el bajo que suena en "
               "ese momento: la columna del pulso (`columnas`, «1 D3/D2 · 2 E3/E2 …», y `columnas_pulso`). La de más peso "
               "del compás es la columna principal: nota aguda, bajo, intervalo entre los dos, qué es la nota en el acorde "
               "y en qué pulso cae. El arco dice la forma de la voz aguda en el compás: arco (sube y baja), valle, "
               "asciende, desciende o plano, con su cumbre y su ámbito en semitonos. Las notas de menos de `min_beats` "
               "pulsos no cuentan si hay otras.")

DOC_COL_SUMMARY = ("**`columns_summary`**: Resumen de las columnas principales de los compases confiables, ponderado por "
                   "duración: qué es la nota en el acorde, intervalo con el bajo, forma del arco, pulso en que cae, "
                   "cumbres, qué parte cae dentro del acorde y, en cada ciclo de la voz aguda, su columna y su arco más "
                   "frecuentes.")

DOC_RUN_H3 = ("Notas columna de la canción: agrega las columnas a cada compás de `armonia` y su resumen a "
              "`armonia_resumen['columnas']`; `run_song.py` las guarda en `armonia.json` y en `armonia_por_compas.csv`.")

CODE_COLUMNS = '''import numpy as np

from tabroll.cells.chord24 import CHORDS24
from tabroll.cells.harmony_by_bar import DEG24_NAMES, PC24_NAMES

PESOS = dict(metrica=0.3, acorde=0.35, duracion=0.2, contorno=0.15)   # reglas de preferencia: dónde cae el ataque, si es
PAPELES = {0: 'fundamental', 4: 'segunda (sus2)', 6: 'tercera', 7: 'tercera', 8: 'tercera', 10: 'cuarta (sus4)',
           12: 'quinta', 14: 'quinta', 16: 'quinta'}                    # del acorde, cuánto dura y si es un punto alto o bajo


def melodic_columns(armonia, raw_bass, raw_high, lens, min_beats=0.2):
    pc = lambda m: int(round(2 * m)) % 24                              # altura MIDI (con cuartos de tono) → clase de 24
    nombre = lambda m: PC24_NAMES[pc(m)] + str(int(round(2 * m)) // 24 - 1)
    high, bass = sorted(map(tuple, raw_high)), sorted(map(tuple, raw_bass))
    b_ini = np.array([n[0] for n in bass]) if bass else np.zeros(0)

    def bajo_en(t, beat):                                              # la nota del bajo que suena en t
        k = int(np.searchsorted(b_ini, t + 0.05, side='right')) - 1
        if k >= 0 and bass[k][1] > t:
            return bass[k][2]
        k += 1                                                         # o la que entra poco después
        return bass[k][2] if k < len(bass) and bass[k][0] - t < 0.5 * beat else None

    out = []
    for row, nb in zip(armonia, lens):
        row = dict(row)
        t0, t1 = row['inicio_s'], row['fin_s']
        nb = max(int(round(nb)), 1)
        beat = (t1 - t0) / nb
        en_compas = [n for n in high if t0 - 0.03 <= n[0] < t1 - 0.03]
        notas = [n for n in en_compas if n[1] - n[0] >= min_beats * beat] or en_compas
        if not notas:
            row.update(columna=None, columna_aguda=None, columna_bajo=None, columna_intervalo=None, columna_papel=None,
                       columna_en_acorde=None, columna_pulso=None, columna_peso=None, columnas=None, columnas_pulso=[],
                       arco=None, cumbre=None, ambito_st=None)
            out.append(row)
            continue

        root, cal = row.get('fundamental_pc24'), row.get('calidad')
        iv = CHORDS24.get(cal, ()) if root is not None else ()
        alturas = [n[2] for n in notas]
        cols = {}
        for i, (a, b, p) in enumerate(notas):
            pos = (a - t0) / beat
            j = min(max(int(np.floor(pos + 0.15)), 0), nb - 1)          # el pulso al que pertenece el ataque
            if abs(pos - round(pos)) <= 0.15:
                metrica = 1.0 if j == 0 else 0.85 if nb % 2 == 0 and j == nb // 2 else 0.7
            else:
                metrica = 0.45 if abs(2 * pos - round(2 * pos)) <= 0.15 else 0.3
            if iv:                                                     # qué es la nota en el acorde del compás
                rel = (pc(p) - root) % 24
                x = min(iv, key=lambda x: min((rel - x) % 24, (x - rel) % 24))
                dist = min((rel - x) % 24, (x - rel) % 24)
                acorde = 1.0 if dist == 0 else 0.7 if dist == 1 else 0.2
                papel = (PAPELES[x] + (' (a 1/4 de tono)' if dist else '')) if dist <= 1 else f'fuera del acorde ({DEG24_NAMES[rel]})'
            else:
                dist, acorde, papel = None, 0.5, None
            vecinos = alturas[max(i - 1, 0):i] + alturas[i + 1:i + 2]
            if len(alturas) == 1:
                contorno = 1.0
            elif len(vecinos) == 1:
                contorno = 0.8                                         # primera o última nota del compás
            else:
                contorno = 1.0 if p > max(vecinos) or p < min(vecinos) else 0.6
            peso = (PESOS['metrica'] * metrica + PESOS['acorde'] * acorde + PESOS['duracion'] * min(1.0, (b - a) / beat)
                    + PESOS['contorno'] * contorno)
            if j in cols and cols[j]['peso'] >= peso:
                continue
            pb = bajo_en(a, beat)
            cols[j] = dict(pulso=j + 1, t=round(a, 3), aguda=nombre(p), bajo=None if pb is None else nombre(pb),
                           intervalo=None if pb is None else DEG24_NAMES[(pc(p) - pc(pb)) % 24], papel=papel,
                           en_acorde=None if dist is None else dist <= 1, peso=round(peso, 3))

        prin = max(cols.values(), key=lambda c: c['peso'])
        hi, lo = int(np.argmax(alturas)), int(np.argmin(alturas))
        ini, fin = alturas[0], alturas[-1]
        sube = alturas[hi] - max(ini, fin) if 0 < hi < len(alturas) - 1 else 0.0
        baja = min(ini, fin) - alturas[lo] if 0 < lo < len(alturas) - 1 else 0.0
        if max(sube, baja) >= 1:
            arco = 'arco' if sube >= baja else 'valle'
        else:
            arco = 'asciende' if fin - ini >= 1 else 'desciende' if ini - fin >= 1 else 'plano'
        row.update(columna=f"{prin['aguda']} sobre {prin['bajo']}" if prin['bajo'] else prin['aguda'],
                   columna_aguda=prin['aguda'], columna_bajo=prin['bajo'], columna_intervalo=prin['intervalo'],
                   columna_papel=prin['papel'], columna_en_acorde=prin['en_acorde'], columna_pulso=prin['pulso'],
                   columna_peso=prin['peso'],
                   columnas=' · '.join(f"{j + 1} {cols[j]['aguda']}/{cols[j]['bajo'] or '–'}" if j in cols else f'{j + 1} –'
                                       for j in range(nb)),
                   columnas_pulso=[cols[j] for j in sorted(cols)], arco=arco, cumbre=nombre(alturas[hi]),
                   ambito_st=round(float(max(alturas) - min(alturas)), 1))
        out.append(row)
    return out'''

CODE_COL_SUMMARY = '''from collections import Counter


def columns_summary(armonia, min_conf=0.5):
    ok = [r for r in armonia if r.get('columna') and (r.get('confianza') or 0) >= min_conf]
    dur = lambda r: r['fin_s'] - r['inicio_s']
    total = sum(dur(r) for r in ok) or 1.0
    papel = lambda r: (r.get('columna_papel') or 'sin acorde').split(' (')[0]   # sin el detalle entre paréntesis

    def share(valor, top=None):
        acc = Counter()
        for r in ok:
            if valor(r) is not None:
                acc[valor(r)] += dur(r)
        return {str(k): round(100.0 * v / total, 1) for k, v in acc.most_common(top)}

    ciclos = {}
    for c in sorted({r['ciclo_aguda'] for r in ok if r.get('ciclo_aguda')}):
        rs = [r for r in ok if r.get('ciclo_aguda') == c]
        col, n = Counter(f"{r['columna']} ({papel(r)})" for r in rs).most_common(1)[0]
        ciclos[c] = dict(compases=len(rs), columna=col, veces=n, arco=Counter(r['arco'] for r in rs).most_common(1)[0][0])
    return dict(compases=len(ok), papeles=share(papel), intervalos=share(lambda r: r.get('columna_intervalo'), 6),
                arcos=share(lambda r: r.get('arco')), pulsos=share(lambda r: r.get('columna_pulso')),
                en_acorde=share(lambda r: r.get('columna_en_acorde')).get('True', 0.0),
                cumbres=share(lambda r: r.get('cumbre'), 5), por_ciclo=ciclos)'''

CODE_RUN_H3 = '''armonia = melodic_columns(armonia, raw_bass, raw_high, lens)
armonia_resumen['columnas'] = columns_summary(armonia)
cs = armonia_resumen['columnas']
print(f"Columnas ({cs['compases']} compases confiables): la nota principal es " +
      ', '.join(f'{k} {v:.0f}%' for k, v in cs['papeles'].items()) + f" | dentro del acorde {cs['en_acorde']:.0f}% | "
      'en el pulso ' + ', '.join(f'{k}: {v:.0f}%' for k, v in list(cs['pulsos'].items())[:3]))
print('          intervalo con el bajo: ' + ', '.join(f'{k} {v:.0f}%' for k, v in cs['intervalos'].items()) +
      ' | arcos: ' + ', '.join(f'{k} {v:.0f}%' for k, v in cs['arcos'].items()))
if cs['por_ciclo']:
    print('          por ciclo de la voz aguda: ' + '; '.join(
        f"{c}: {d['columna']} ×{d['veces']}/{d['compases']}, {d['arco']}" for c, d in cs['por_ciclo'].items()))'''


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
    pares = ((DOC_COLUMNS, CODE_COLUMNS, "def melodic_columns("), (DOC_COL_SUMMARY, CODE_COL_SUMMARY, "def columns_summary("),
             (DOC_RUN_H3, CODE_RUN_H3, "armonia = melodic_columns(armonia"))
    found = [[i for i, c in enumerate(cells) if c["cell_type"] == "code" and mark in src(c)] for _, _, mark in pares]
    if all(len(f) == 1 for f in found):
        for (doc, code, mark), (i,) in zip(pares, found):
            if src(cells[i]) != code or src(cells[i - 1]) != doc:
                put(cells[i - 1], doc)
                put(cells[i], code)
                done.append(mark.replace("def ", "").rstrip("("))
    elif not any(found):
        head = [i for i, c in enumerate(cells) if c["cell_type"] == "markdown" and src(c).startswith(H2_HEADER)]
        run = [c for c in cells if c["cell_type"] == "code" and "armonia_resumen['progresiones'] = chord_progressions(" in src(c)]
        if len(head) != 1 or len(run) != 1:
            print("No encontré la celda de armonía o el encabezado del tabroll24. Corre antes scripts/tabroll_armonia24.py.")
            return 1
        new = [_cell("markdown", DOC_H3)]
        for doc, code, _ in pares:
            new += [_cell("markdown", doc), _cell("code", code)]
        cells[head[0]:head[0]] = new
        done.append("celdas nuevas melodic_columns, columns_summary y la de columnas, antes del tabroll24")
    else:
        print("Las celdas de las notas columna están incompletas; restaura el cuaderno desde git y vuelve a correr.")
        return 1
    if not done:
        print("El cuaderno ya tenía las notas columna.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
