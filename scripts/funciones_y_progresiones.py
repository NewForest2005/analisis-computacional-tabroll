"""Paso H1b del análisis armónico: nombres de los grados, función con su calidad y progresiones.

Uso:
    python scripts/funciones_y_progresiones.py
    make extract
    make test

Cambia las celdas del paso H1 (`chord_roles`, `roles_summary`) y agrega `chord_progressions`:
- cada compás trae el nombre del grado (tónica, supertónica, mediante, subdominante, dominante, superdominante,
  subtónica o sensible; rebajado, elevado, neutro, alto o bajo según el caso) y su clase según Piston (tonal, casi
  tonal, modal, alterado, se absorbe en V, neutro);
- la función se escribe con la calidad del acorde: «subdominante menor», «dominante menor (modal, sin sensible)»;
- el bajo a un cuarto de tono de una nota del acorde cuenta como esa nota, y se marca;
- en cada cambio de fundamental: la progresión, el movimiento de la fundamental según Piston (pp. 22-24) y qué tan
  usual es según su tabla de progresiones (pp. 21-22, con los añadidos del menor de la p. 45); en el resumen, las
  progresiones más frecuentes, las que tienen nombre y los vaivenes.
Se puede correr más de una vez: lo que ya está aplicado no se toca.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"

DOC_ROLES = ("**`chord_roles`**: Cifrado, grado, función, inversión y papel de la voz aguda de cada compás. El cifrado va en "
             "números romanos sobre el centro: mayúscula para mayor, minúscula para menor, «+» sube un cuarto de tono, «aum» "
             "es aumentado, «n» tercera neutra, «5» sin tercera, «°» disminuido. Cada grado lleva su nombre (tónica, "
             "supertónica, mediante, subdominante, dominante, superdominante, subtónica o sensible) y su clase según Piston "
             "(cap. 5): tonales I, IV y V; casi tonal II; modales III y VI; el VII se absorbe en el V. La función sigue las "
             "familias de Riemann y Piston (tabla `GRADOS`) y se escribe con la calidad del acorde. Los grados de cuarto de "
             "tono no tienen función tradicional y quedan como neutros. La inversión dice dónde está el bajo respecto del "
             "acorde; si está a un cuarto de tono de una nota del acorde, cuenta como esa nota y se marca. La voz aguda usa "
             "su perfil del compás: la nota que más suena, qué es dentro del acorde y qué parte de su tiempo cae en notas del "
             "acorde.")

CODE_ROLES = '''# @title chord_roles
import numpy as np

from tabroll.cells.chord24 import CHORDS24
from tabroll.cells.harmony_by_bar import DEG24_NAMES, PC24_NAMES

ROMAN12 = ['I', '♭II', 'II', '♭III', 'III', 'IV', '♯IV', 'V', '♭VI', 'VI', '♭VII', 'VII']
SUFIJO = {'M': '', 'm': '', 'n': 'n', '5': '5', 'dism': '°', 'aum': 'aum', 'sus2': 'sus2', 'sus4': 'sus4'}
CALIDAD = {'M': 'mayor', 'm': 'menor', 'n': 'de tercera neutra', '5': 'sin tercera', 'dism': 'disminuida',
           'aum': 'aumentada', 'sus2': 'sus2', 'sus4': 'sus4'}
GRADOS = {   # semitonos sobre el centro: (nombre del grado, clase según Piston, función, matiz)
    0: ('tónica', 'tonal', 'tónica', ''),
    1: ('supertónica rebajada', 'alterado', 'subdominante', 'napolitana'),
    2: ('supertónica', 'casi tonal', 'subdominante', ''),
    3: ('mediante rebajada', 'modal', 'tónica', 'relativa'),
    4: ('mediante', 'modal', 'tónica', 'relativa'),
    5: ('subdominante', 'tonal', 'subdominante', ''),
    6: ('subdominante elevada', 'alterado', 'sin función', 'tritono'),
    7: ('dominante', 'tonal', 'dominante', ''),
    8: ('superdominante rebajada', 'modal', 'subdominante', 'mixtura'),
    9: ('superdominante', 'modal', 'tónica', 'relativa'),
    10: ('subtónica', 'modal', 'dominante', 'modal, sin sensible'),
    11: ('sensible', 'se absorbe en V', 'dominante', 'sensible'),
}
NEUTROS = {1: 'tónica alta', 3: 'supertónica neutra', 5: 'supertónica alta', 7: 'mediante neutra', 9: 'mediante alta',
           11: 'subdominante alta', 13: 'dominante baja', 15: 'dominante alta', 17: 'superdominante neutra',
           19: 'superdominante alta', 21: 'séptimo grado neutro', 23: 'sensible alta'}
LETRA = {'tónica': 'T', 'subdominante': 'S', 'dominante': 'D', 'neutra': 'N', 'sin función': '—'}
TERCERAS, QUINTAS, SEPTIMAS = (4, 6, 7, 8, 10), (12, 14, 16), (20, 21, 22)   # en cuartos de tono sobre la fundamental


def chord_roles(armonia, tonic_pc24):
    def member(rel, iv):                                               # qué nota del acorde es rel, con 1/4 de tono de tolerancia
        for tol in (0, 1):
            for x in iv:
                if min((rel - x) % 24, (x - rel) % 24) == tol:
                    return x, tol == 1
        return None, False

    out = []
    for row in armonia:
        row = dict(row)
        root, cal = row.get('fundamental_pc24'), row.get('calidad')
        if root is None or cal not in CHORDS24:
            row.update(grado24=None, cifrado=None, nombre_grado=None, clase_grado=None, funcion=None, matiz=None,
                       funcion_corta=None, funcion_texto=None, inversion=None, cifra_bajo=None, nota_aguda=None,
                       papel_aguda=None, aguda_en_acorde=None)
            out.append(row)
            continue
        q = (root - tonic_pc24) % 24
        d, cuarto = q // 2, q % 2
        menor = cal in ('m', 'dism')
        roman = ROMAN12[d]
        acc, num = (roman[0], roman[1:]) if roman[0] in '♭♯' else ('', roman)
        cifrado = acc + (num.lower() if menor else num) + ('+' if cuarto else '') + SUFIJO[cal]

        if cuarto:                                                     # grado de cuarto de tono: sin función tradicional
            nombre, clase = NEUTROS[q], 'neutro (24-EDO)'
            funcion, matiz = 'neutra', f'entre {DEG24_NAMES[q - 1]} y {DEG24_NAMES[(q + 1) % 24]}'
        else:
            nombre, clase, funcion, matiz = GRADOS[d]
            if d == 2 and cal == 'M':
                funcion, matiz = 'dominante', 'dominante de la dominante (V/V)'
            elif d == 7:
                matiz = 'con sensible' if cal in ('M', 'aum') else 'modal, sin sensible'
            elif d == 11 and cal == 'dism':
                matiz = 'sensible, dominante sin fundamental'
        letra = LETRA[funcion]
        corta = letra.lower() if menor and letra in ('T', 'S', 'D') else letra
        texto = f'{funcion} {CALIDAD[cal]}' + (f' ({matiz})' if matiz else '')

        iv = CHORDS24[cal]
        tonos = sorted({(root + i) % 24 for i in iv})
        b = row.get('bajo_pc24')
        if b is None:
            inversion, cifra = None, None
        else:
            rb = (b - root) % 24
            x, cerca = member(rb, iv)
            marca = ' (bajo a 1/4 de tono)' if cerca else ''
            if x == 0:
                inversion, cifra = 'fundamental' + marca, ''
            elif x in TERCERAS:
                inversion, cifra = '1.ª inversión' + marca, '6'
            elif x in QUINTAS:
                inversion, cifra = '2.ª inversión' + marca, '6/4'
            elif rb in SEPTIMAS:
                inversion, cifra = 'séptima en el bajo', '4/2'
            else:
                inversion, cifra = 'bajo fuera del acorde', '/' + str(row.get('bajo'))

        pa = np.asarray(row.get('perfil_aguda') or [], float)
        if pa.size == 24 and pa.sum() > 0:
            top = int(pa.argmax())
            ra = (top - root) % 24
            if ra == 0:
                papel = 'fundamental'
            elif ra in iv and ra in (6, 7, 8):
                papel = 'tercera'
            elif ra in iv and ra == 4:
                papel = 'segunda (sus2)'
            elif ra in iv and ra == 10:
                papel = 'cuarta (sus4)'
            elif ra in iv:
                papel = 'quinta'
            else:
                papel = f'fuera del acorde ({DEG24_NAMES[ra]} sobre la fundamental)'
            nota, en_acorde = PC24_NAMES[top], round(100.0 * float(pa[tonos].sum() / pa.sum()), 1)
        else:
            nota = papel = en_acorde = None
        row.update(grado24=q, cifrado=cifrado, nombre_grado=nombre, clase_grado=clase, funcion=funcion, matiz=matiz,
                   funcion_corta=corta, funcion_texto=texto, inversion=inversion, cifra_bajo=cifra, nota_aguda=nota,
                   papel_aguda=papel, aguda_en_acorde=en_acorde)
        out.append(row)
    return out'''

DOC_SUMMARY = ("**`roles_summary`**: Reparto del tiempo de los compases confiables por función (familia y con su calidad), "
               "nombre y clase del grado, inversión, cifrado y papel de la voz aguda (en %, de mayor a menor), y qué parte "
               "de la voz aguda cae dentro del acorde, ponderada por la duración de cada compás.")

CODE_SUMMARY = '''def roles_summary(armonia, min_conf=0.5):
    ok = [r for r in armonia if r.get('funcion') and (r.get('confianza') or 0) >= min_conf]
    dur = lambda r: r['fin_s'] - r['inicio_s']
    total = sum(dur(r) for r in ok) or 1.0

    def share(key):
        acc = {}
        for r in ok:
            if r.get(key) is not None:
                acc[r[key]] = acc.get(r[key], 0.0) + dur(r)
        return {k: round(100.0 * v / total, 1) for k, v in sorted(acc.items(), key=lambda kv: -kv[1])}

    en = [(r['aguda_en_acorde'], dur(r)) for r in ok if r.get('aguda_en_acorde') is not None]
    peso = sum(w for _, w in en)
    return dict(funciones=share('funcion'), funciones_detalle=share('funcion_texto'), nombres_grado=share('nombre_grado'),
                clases_grado=share('clase_grado'), inversiones=share('inversion'), cifrados=share('cifrado'),
                papeles_aguda=share('papel_aguda'),
                aguda_en_acorde=round(sum(a * w for a, w in en) / peso, 1) if peso else None,
                compases_confiables=len(ok))'''

DOC_PROG = ("**`chord_progressions`**: Progresiones entre compases confiables, en cada cambio de fundamental. Para cada uno: "
            "la progresión («♭III → ♭VII»), el movimiento de la fundamental según Piston (pp. 22-24: quinta abajo, como "
            "V-I, la más fuerte; quinta arriba, como IV-I; tercera abajo; tercera arriba, la más débil; segunda; tritono; o "
            "microtonal) y qué tan usual es según su tabla de progresiones (pp. 21-22), leída por número de grado (♭VII "
            "como VII). Con `menor` se agregan los añadidos de Piston para el modo menor (p. 45). Devuelve las filas y un "
            "resumen: qué parte de los cambios va por quintas, las progresiones más frecuentes, las progresiones con nombre "
            "(cadencias y progresiones conocidas, por sus fundamentales) y los vaivenes entre dos acordes.")

CODE_PROG = '''# @title chord_progressions
from collections import Counter

DIATONICO = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 7: 5, 8: 6, 9: 6, 10: 7, 11: 7}      # el ♯IV (6) no tiene grado diatónico
PISTON = {1: ({4, 5}, {6}, {2, 3}), 2: ({5}, {4, 6}, {1, 3}), 3: ({6}, {4}, {1, 2, 5}), 4: ({5}, {1, 2}, {3, 6}),
          5: ({1}, {4, 6}, {2, 3}), 6: ({2, 5}, {3, 4}, {1}), 7: ({1, 3}, {6}, {2, 4, 5})}
USOS = ('usual', 'a veces', 'menos a menudo')
MOVIMIENTOS = {5: 'quinta abajo (como V-I)', 7: 'quinta arriba (como IV-I)', 8: 'tercera abajo', 9: 'tercera abajo',
               3: 'tercera arriba', 4: 'tercera arriba', 1: 'segunda', 2: 'segunda', 10: 'segunda', 11: 'segunda',
               6: 'tritono'}
CON_NOMBRE = {   # semitonos de cada fundamental sobre el centro
    'cadencia auténtica V-I': (7, 0), 'cadencia plagal IV-I': (5, 0), 'cadencia rota V-VI': (7, 9),
    'cadencia rota V-♭VI': (7, 8), 'cadencia modal ♭VII-I': (10, 0), 'cadencia eólica ♭VI-♭VII-I': (8, 10, 0),
    'cadencia andaluza i-♭VII-♭VI-V': (0, 10, 8, 7), 'II-V-I': (2, 7, 0), 'I-IV-V': (0, 5, 7), 'IV-V-I': (5, 7, 0),
    'I-V-vi-IV': (0, 7, 9, 5), 'I-vi-IV-V': (0, 9, 5, 7), 'vi-IV-I-V': (9, 5, 0, 7),
    'i-♭VI-♭III-♭VII': (0, 8, 3, 10), 'círculo de quintas vi-ii-V-I': (9, 2, 7, 0)}


def chord_progressions(armonia, menor=False, min_conf=0.5):
    def uso(d0, d1):                                                   # qué tan usual es d0 → d1 en la tabla de Piston
        a, b = DIATONICO.get(d0), DIATONICO.get(d1)
        if a is None or b is None:
            return 'fuera de la tabla'
        fila = PISTON[a]
        if menor:                                                      # añadidos de Piston para el modo menor (p. 45)
            if a in (1, 3):
                fila = (fila[0] | {7}, fila[1], fila[2])
            elif a == 7:
                fila = ({3}, {6}, {4}) if d0 == 10 else ({1}, set(), set())
        for nombre, grupo in zip(USOS, fila):
            if b in grupo:
                return nombre
        return 'fuera de la tabla'

    out = [dict(r, progresion=None, movimiento=None, uso_piston=None) for r in armonia]
    seq = []                                                           # (fila, grado en cuartos de tono, cifrado)
    for i, r in enumerate(out):
        if r.get('cifrado') is None or r.get('grado24') is None or (r.get('confianza') or 0) < min_conf:
            continue
        q = r['grado24']
        if seq and seq[-1][1] == q:                                    # misma fundamental: no hay cambio
            continue
        if seq:
            q0 = seq[-1][1]
            r['progresion'] = f'{seq[-1][2]} → {r["cifrado"]}'
            if q0 % 2 or q % 2:
                r['movimiento'], r['uso_piston'] = 'microtonal', 'fuera de la tabla'
            else:
                r['movimiento'] = MOVIMIENTOS[(q // 2 - q0 // 2) % 12]
                r['uso_piston'] = uso(q0 // 2, q // 2)
        seq.append((i, q, r['cifrado']))

    cambios = [r for r in out if r['progresion']]
    n = len(cambios) or 1
    share = lambda key: {k: round(100.0 * v / n, 1) for k, v in Counter(r[key] for r in cambios).most_common()}
    grados = [q for _, q, _ in seq]
    con_nombre = {}
    for name, pat in CON_NOMBRE.items():
        p24 = [2 * x for x in pat]
        hits = [seq[k][0] for k in range(len(seq) - len(p24) + 1) if grados[k:k + len(p24)] == p24]
        if hits:
            con_nombre[name] = dict(veces=len(hits), compases=[out[i]['compas'] for i in hits[:10]])
    vaiven = Counter()
    for k in range(len(seq) - 3):
        if grados[k] == grados[k + 2] and grados[k + 1] == grados[k + 3]:
            vaiven[' ↔ '.join(sorted((seq[k][2], seq[k + 1][2])))] += 1
    quintas = sum(1 for r in cambios if r['movimiento'].startswith('quinta'))
    frecuentes = [[p, c] for p, c in Counter(r['progresion'] for r in cambios).most_common(8)]
    return out, dict(cambios=len(cambios), por_quintas=round(100.0 * quintas / n, 1), movimientos=share('movimiento'),
                     uso_piston=share('uso_piston'), frecuentes=frecuentes, con_nombre=con_nombre,
                     vaivenes=dict(vaiven.most_common(5)))'''

TAIL_MARK = "chord_progressions(armonia"
TAIL = '''

modo_menor = '♭3' in [x.strip() for x in armonia_resumen['modo']['nombre'].split(',')]
armonia, armonia_resumen['progresiones'] = chord_progressions(armonia, menor=modo_menor)
pr = armonia_resumen['progresiones']
print('         grados: ' + ', '.join(f'{k} {v:.0f}%' for k, v in list(fx['nombres_grado'].items())[:5]))
print(f"         progresiones: {pr['cambios']} cambios, {pr['por_quintas']:.0f}% por quintas | tabla de Piston: " +
      ', '.join(f'{k} {v:.0f}%' for k, v in pr['uso_piston'].items()))
print('         más frecuentes: ' + ', '.join(f'{p} ×{n}' for p, n in pr['frecuentes'][:5]))
nombradas = [f"{k} ×{v['veces']}" for k, v in pr['con_nombre'].items()] + [f'vaivén {k} ×{v}' for k, v in pr['vaivenes'].items()]
if nombradas:
    print('         con nombre: ' + ', '.join(nombradas))
'''


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
    done = []

    def replace_pair(prefix, marker, doc, code, label):
        idx = [i for i, c in enumerate(cells) if c["cell_type"] == "markdown" and src(c).startswith(prefix)]
        if len(idx) != 1 or idx[0] + 1 >= len(cells) or marker not in src(cells[idx[0] + 1]):
            return None
        i = idx[0]
        if src(cells[i]) != doc or src(cells[i + 1]) != code:
            cells[i]["source"] = doc.splitlines(keepends=True)
            cells[i + 1]["source"] = code.splitlines(keepends=True)
            done.append(label)
        return i

    i_roles = replace_pair("**`chord_roles`**", "def chord_roles(", DOC_ROLES, CODE_ROLES, "chord_roles con nombres de grado")
    i_sum = replace_pair("**`roles_summary`**", "def roles_summary(", DOC_SUMMARY, CODE_SUMMARY, "roles_summary")
    if i_roles is None or i_sum is None:
        print("No encontré las celdas del paso H1. Corre antes scripts/agregar_funciones.py.")
        return 1
    if any(src(c).startswith("**`chord_progressions`**") for c in cells if c["cell_type"] == "markdown"):
        if replace_pair("**`chord_progressions`**", "def chord_progressions(", DOC_PROG, CODE_PROG, "chord_progressions") is None:
            print("La celda chord_progressions no está como la dejó este script.")
            return 1
    else:
        cells[i_sum + 2:i_sum + 2] = [_cell("markdown", DOC_PROG), _cell("code", CODE_PROG)]
        done.append("celda nueva chord_progressions")
    run = [c for c in cells if c["cell_type"] == "code" and "armonia_resumen['funciones'] = roles_summary(armonia)" in src(c)]
    if len(run) != 1:
        print("No encontré la celda de armonía del paso H1.")
        return 1
    if TAIL_MARK not in src(run[0]):
        run[0]["source"] = (src(run[0]).rstrip("\n") + TAIL).splitlines(keepends=True)
        done.append("la celda de armonía calcula e imprime las progresiones")
    if not done:
        print("El cuaderno ya tenía el paso H1b.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
