"""**`harmony_labels`**: Etiquetas de cada compás para la franja del tabroll. El cifrado sigue la convención del tabroll: sus2, sus4 y 5 (sin tercera) van abajo; n (tercera neutra), ° y aum van arriba; «+» sube un cuarto de tono. La inversión se escribe como bajo cifrado: ⁶ y ⁶₄ apilados, o 6/4 arriba si la calidad ya ocupa un índice. El nombre usa las notas en 24-EDO con barra para el bajo («Dsus2/F♯»). La anotación es la función (T, S, D, N; en minúscula si el acorde es menor) con su matiz corto, en el color de la función, y el eje de Lendvai cuando no coincide con la función («D sens. · eje S»). Los compases con confianza menor que `min_conf` van entre paréntesis. `tones` está en cents sobre la tónica del tabroll (`tonic_midi`), para que la franja tome el color del grado.
"""

from tabroll.cells.chord24 import CHORDS24
from tabroll.cells.chord_roles import SUFIJO
from tabroll.cells.harmony_by_bar import PC24_NAMES

COLOR_FUNCION = {'tónica': '#f2d49b', 'subdominante': '#86b9ea', 'dominante': '#ef8f80', 'neutra': '#c9adf2',
                 'sin función': '#9a9aa0'}
MATIZ_CORTO = {'relativa': 'rel.', 'napolitana': 'nap.', 'mixtura': 'mixt.', 'tritono': 'tt', 'modal, sin sensible': 'modal',
               'con sensible': 'sens.', 'sensible': 'sens.', 'sensible, dominante sin fundamental': 'sens.',
               'dominante de la dominante (V/V)': 'V/V'}
INDICES = {'M': ('', ''), 'm': ('', ''), '5': ('5', ''), 'sus2': ('sus2', ''), 'sus4': ('sus4', ''), 'n': ('', 'n'),
           'dism': ('', '°'), 'aum': ('', 'aum')}                     # (subíndice, superíndice) de cada calidad
EN_NOMBRE = {'M': '', 'm': 'm', '5': '5', 'sus2': 'sus2', 'sus4': 'sus4', 'n': 'n', 'dism': '°', 'aum': 'aum'}


def harmony_labels(armonia, tonic_midi, min_conf=0.5):
    nota = lambda q: PC24_NAMES[q % 24].replace('#', '♯')
    cero = 2 * (tonic_midi % 12)                                       # la escala del tabroll cuenta desde su tónica
    out = []
    for row in armonia:
        cal, root = row.get('calidad'), row.get('fundamental_pc24')
        if row.get('cifrado') is None or root is None or cal not in CHORDS24:
            continue
        cif = row['cifrado']
        base = cif[:len(cif) - len(SUFIJO[cal])].replace('+', '{+}')   # {+}: un cuarto de tono, sin espacios de operador
        sub, sup = INDICES[cal]
        fig = row.get('cifra_bajo') or ''
        fig = fig if fig in ('6', '6/4', '4/2') else ''
        if '/' in fig and not sub and not sup:                          # bajo cifrado apilado: ⁶₄, ⁴₂
            num = base + '^{%s}_{%s}' % tuple(fig.split('/'))
        else:
            sup += ('\\,' if sup and fig else '') + fig                 # «n 6»: calidad y bajo cifrado, separados
            num = base + (f'_{{{sub}}}' if sub else '') + (f'^{{{sup}}}' if sup else '')
        nombre = nota(root) + EN_NOMBRE[cal]
        b = row.get('bajo_pc24')
        if b is not None and b != root:
            nombre += '/' + nota(b)
        if (row.get('confianza') or 0) < min_conf:
            num, nombre = f'({num})', f'({nombre})'
        out.append(dict(compas=row['compas'], numeral=num, name=nombre,
                        annot=f"{row.get('funcion_corta') or ''} {MATIZ_CORTO.get(row.get('matiz') or '', '')}".strip()
                        + (f" · eje {row['eje_corto']}" if row.get('eje_corto') and row.get('eje') != row.get('funcion') else ''),
                        annot_color=COLOR_FUNCION.get(row.get('funcion'), '#9a9aa0'),
                        tones=[50.0 * ((root - cero) % 24 + i) for i in CHORDS24[cal]]))
    return out
