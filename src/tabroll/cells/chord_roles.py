"""**`chord_roles`**: Cifrado, función, inversión y papel de la voz aguda de cada compás. El cifrado va en números romanos sobre el centro: mayúscula para mayor, minúscula para menor, «+» sube un cuarto de tono, «aum» es aumentado, «n» tercera neutra, «5» sin tercera, «°» disminuido. La función sigue las familias de Riemann y Piston (tabla `FUNCIONES`): los grados de cuarto de tono no tienen función tradicional y quedan como neutros. La inversión dice dónde está el bajo respecto del acorde. La voz aguda usa su perfil del compás: la nota que más suena, qué es dentro del acorde y qué parte de su tiempo cae en notas del acorde.
"""

import numpy as np

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
    return out
