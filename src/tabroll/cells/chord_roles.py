"""**`chord_roles`**: Cifrado, grado, función, inversión y papel de la voz aguda de cada compás. El cifrado va en números romanos sobre el centro: mayúscula para mayor, minúscula para menor, «+» sube un cuarto de tono, «aum» es aumentado, «n» tercera neutra, «5» sin tercera, «°» disminuido. Cada grado lleva su nombre (tónica, supertónica, mediante, subdominante, dominante, superdominante, subtónica o sensible) y su clase según Piston (cap. 5): tonales I, IV y V; casi tonal II; modales III y VI; el VII se absorbe en el V. La función sigue las familias de Riemann y Piston (tabla `GRADOS`) y se escribe con la calidad del acorde. Los grados de cuarto de tono no tienen función tradicional y quedan como neutros. La inversión dice dónde está el bajo respecto del acorde; si está a un cuarto de tono de una nota del acorde, cuenta como esa nota y se marca. La voz aguda usa su perfil del compás: la nota que más suena, qué es dentro del acorde y qué parte de su tiempo cae en notas del acorde. El eje sigue a Lendvai: tónica, subdominante y dominante agrupadas por terceras menores (el grado en semitonos módulo 3), con su rama: polo, contrapolo (a un tritono del polo) o rama secundaria. Un grado de cuarto de tono queda entre dos ejes (D–S para ♭2+), en uno de los tres ejes neutros de 24-EDO.
"""

# @title chord_roles
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
EJES = {0: 'tónica', 1: 'dominante', 2: 'subdominante'}                # ejes de Lendvai: grado (en semitonos) módulo 3
POLOS = {0: 0, 1: 7, 2: 5}                                             # polo de la rama principal de cada eje
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
                       papel_aguda=None, aguda_en_acorde=None, eje=None, eje_corto=None, rama=None)
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
        if cuarto:                                                     # entre dos ejes: los ejes neutros de 24-EDO
            lo, hi = EJES[d % 3], EJES[(d + 1) % 3]
            eje, eje_corto, rama = f'entre {lo} y {hi}', f'{LETRA[lo]}–{LETRA[hi]}', None
        else:
            eje, rel = EJES[d % 3], (d - POLOS[d % 3]) % 12
            eje_corto, rama = LETRA[eje], 'polo' if rel == 0 else 'contrapolo' if rel == 6 else 'rama secundaria'
        row.update(grado24=q, cifrado=cifrado, nombre_grado=nombre, clase_grado=clase, funcion=funcion, matiz=matiz,
                   funcion_corta=corta, funcion_texto=texto, inversion=inversion, cifra_bajo=cifra, nota_aguda=nota,
                   papel_aguda=papel, aguda_en_acorde=en_acorde, eje=eje, eje_corto=eje_corto, rama=rama)
        out.append(row)
    return out
