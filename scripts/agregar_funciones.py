"""Paso H1 del análisis armónico: cifrado, función, inversión y voz aguda en cada compás.

Uso:
    python scripts/agregar_funciones.py
    make extract
    make test

Agrega a cada fila de `armonia` (un compás):
- cifrado: grado en números romanos con la calidad (mayúscula = mayor, minúscula = menor; «+» sube un cuarto de tono,
  como en el resto del proyecto; «aum» = aumentado, para no confundirlo con el cuarto de tono);
- función: tónica, subdominante, dominante, neutra (grados de cuarto de tono) o sin función, con un matiz (relativa,
  napolitana, modal, sensible, secundaria) y la letra corta al estilo de Riemann (minúscula si el acorde es menor);
- inversión: dónde está el bajo respecto del acorde, con su cifra (6, 6/4, 4/2 o /nota);
- voz aguda: su nota principal en el compás, su papel en el acorde y qué parte de su tiempo cae dentro del acorde.
Y al resumen (`armonia_resumen['funciones']`), el reparto del tiempo confiable por función, inversión y cifrado.

Celdas nuevas `chord_roles` y `roles_summary`, después de `harmony_layers`; la celda de armonía las usa. Se puede correr
más de una vez: lo que ya está aplicado no se toca.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"

DOC_ROLES = ("**`chord_roles`**: Cifrado, función, inversión y papel de la voz aguda de cada compás. El cifrado va en números "
             "romanos sobre el centro: mayúscula para mayor, minúscula para menor, «+» sube un cuarto de tono, «aum» es "
             "aumentado, «n» tercera neutra, «5» sin tercera, «°» disminuido. La función sigue las familias de Riemann y "
             "Piston (tabla `FUNCIONES`): los grados de cuarto de tono no tienen función tradicional y quedan como neutros. "
             "La inversión dice dónde está el bajo respecto del acorde. La voz aguda usa su perfil del compás: la nota que "
             "más suena, qué es dentro del acorde y qué parte de su tiempo cae en notas del acorde.")

CODE_ROLES = '''import numpy as np

from tabroll.cells.chord24 import CHORDS24
from tabroll.cells.harmony_by_bar import DEG24_NAMES, PC24_NAMES

ROMAN12 = ['I', '♭II', 'II', '♭III', 'III', 'IV', '♯IV', 'V', '♭VI', 'VI', '♭VII', 'VII']
SUFIJO = {'M': '', 'm': '', 'n': 'n', '5': '5', 'dism': '°', 'aum': 'aum', 'sus2': 'sus2', 'sus4': 'sus4'}
FUNCIONES = {0: ('tónica', ''), 1: ('subdominante', 'napolitana'), 2: ('subdominante', ''),
             3: ('tónica', 'relativa'), 4: ('tónica', 'relativa'), 5: ('subdominante', ''),
             6: ('sin función', 'tritono'), 7: ('dominante', ''), 8: ('subdominante', 'relativa'),
             9: ('tónica', 'relativa'), 10: ('dominante', 'modal, subtónica'), 11: ('dominante', 'sensible')}
LETRA = {'tónica': 'T', 'subdominante': 'S', 'dominante': 'D', 'neutra': 'N', 'sin función': '—'}
TERCERAS, QUINTAS, SEPTIMAS = (4, 6, 7, 8, 10), (12, 14, 16), (20, 21, 22)   # en cuartos de tono sobre la fundamental


def chord_roles(armonia, tonic_pc24):
    out = []
    for row in armonia:
        row = dict(row)
        root, cal = row.get('fundamental_pc24'), row.get('calidad')
        if root is None or cal not in CHORDS24:
            row.update(cifrado=None, funcion=None, matiz=None, funcion_corta=None, inversion=None, cifra_bajo=None,
                       nota_aguda=None, papel_aguda=None, aguda_en_acorde=None)
            out.append(row)
            continue
        q = (root - tonic_pc24) % 24
        d, cuarto = q // 2, q % 2
        menor = cal in ('m', 'dism')
        roman = ROMAN12[d]
        acc, num = (roman[0], roman[1:]) if roman[0] in '♭♯' else ('', roman)
        cifrado = acc + (num.lower() if menor else num) + ('+' if cuarto else '') + SUFIJO[cal]

        if cuarto:                                                     # grado de cuarto de tono: sin función tradicional
            funcion, matiz = 'neutra', f'entre {DEG24_NAMES[q - 1]} y {DEG24_NAMES[(q + 1) % 24]}'
        else:
            funcion, matiz = FUNCIONES[d]
            if d == 2 and cal == 'M':
                funcion, matiz = 'dominante', 'secundaria (V/V)'
            elif d == 7:
                matiz = 'con sensible' if cal == 'M' else 'modal, sin sensible'
        letra = LETRA[funcion]
        corta = letra.lower() if menor and letra in ('T', 'S', 'D') else letra

        iv = CHORDS24[cal]
        tonos = sorted({(root + i) % 24 for i in iv})
        b = row.get('bajo_pc24')
        if b is None:
            inversion, cifra = None, None
        else:
            rb = (b - root) % 24
            if rb == 0:
                inversion, cifra = 'fundamental', ''
            elif rb in iv and rb in TERCERAS:
                inversion, cifra = '1.ª inversión', '6'
            elif rb in iv and rb in QUINTAS:
                inversion, cifra = '2.ª inversión', '6/4'
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
        row.update(cifrado=cifrado, funcion=funcion, matiz=matiz, funcion_corta=corta, inversion=inversion,
                   cifra_bajo=cifra, nota_aguda=nota, papel_aguda=papel, aguda_en_acorde=en_acorde)
        out.append(row)
    return out'''

DOC_SUMMARY = ("**`roles_summary`**: Reparto del tiempo de los compases confiables por función, inversión, cifrado y papel de "
               "la voz aguda (en %, de mayor a menor), y qué parte de la voz aguda cae dentro del acorde, ponderada por la "
               "duración de cada compás.")

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
    return dict(funciones=share('funcion'), inversiones=share('inversion'), cifrados=share('cifrado'),
                papeles_aguda=share('papel_aguda'),
                aguda_en_acorde=round(sum(a * w for a, w in en) / peso, 1) if peso else None,
                compases_confiables=len(ok))'''

OLD_CALL = "armonia = harmony_by_bar(raw_bass, raw_high, beat_times, lens, cycles, tonic_pc24)\n"
NEW_CALL = OLD_CALL + "armonia = chord_roles(armonia, tonic_pc24)                                   # cifrado, función, inversión y voz aguda\n"
TAIL_MARK = "armonia_resumen['funciones'] = roles_summary(armonia)"
TAIL = ("\n\narmonia_resumen['funciones'] = roles_summary(armonia)\n"
        "fx = armonia_resumen['funciones']\n"
        "print('         funciones: ' + ', '.join(f'{k} {v:.0f}%' for k, v in fx['funciones'].items()) +\n"
        "      f\" | voz aguda dentro del acorde: {fx['aguda_en_acorde']}%\")\n"
        "print('         inversiones: ' + ', '.join(f'{k} {v:.0f}%' for k, v in fx['inversiones'].items()))\n"
        "print('         cifrados: ' + ', '.join(f'{k} {v:.0f}%' for k, v in list(fx['cifrados'].items())[:6]))\n")


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
    lay = [i for i, c in enumerate(cells) if c["cell_type"] == "code" and "def harmony_layers(" in src(c)]
    run = [c for c in cells if c["cell_type"] == "code" and OLD_CALL in src(c)]
    if len(lay) != 1 or len(run) != 1:
        print("No encontré la celda de `harmony_layers` o la celda de armonía. Corre antes los pasos de armonía.")
        return 1
    if not any(src(c).startswith("**`chord_roles`**") for c in cells if c["cell_type"] == "markdown"):
        new = [_cell("markdown", DOC_ROLES), _cell("code", CODE_ROLES), _cell("markdown", DOC_SUMMARY), _cell("code", CODE_SUMMARY)]
        cells[lay[0] + 1:lay[0] + 1] = new
        done.append("celdas nuevas chord_roles y roles_summary")
    cell = run[0]
    if "armonia = chord_roles(" not in src(cell):
        cell["source"] = src(cell).replace(OLD_CALL, NEW_CALL).splitlines(keepends=True)
        done.append("la celda de armonía calcula cifrado, función e inversión")
    if TAIL_MARK not in src(cell):
        cell["source"] = (src(cell).rstrip("\n") + TAIL).splitlines(keepends=True)
        done.append("la celda de armonía imprime el resumen de funciones")
    if not done:
        print("El cuaderno ya tenía el paso H1.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
