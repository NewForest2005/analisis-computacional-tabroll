"""**`chord_progressions`**: Progresiones entre compases, en cada cambio de fundamental. Para cada uno: la progresión («♭III → ♭VII»), el movimiento de la fundamental según Piston (pp. 22-24: quinta abajo, como V-I, la más fuerte; quinta arriba, como IV-I; tercera abajo; tercera arriba, la más débil; segunda; tritono; o microtonal), qué tan usual es según su tabla de progresiones (pp. 21-22), leída por número de grado (♭VII como VII), y el paso entre ejes de Lendvai: adelante (T→S→D→T, como V-I o I-IV), atrás (T→D→S→T, como I-V o IV-I), dentro del mismo eje (sustitución por tercera menor o tritono), en el mismo eje neutro o microtonal. Con `menor` se agregan los añadidos de Piston para el modo menor (p. 45). Da dos resúmenes, uno al lado del otro: `confiables` (compases con confianza ≥ `min_conf`) y `todos` (todos los compases con acorde). Cada uno dice qué parte de los cambios va por quintas y por ejes, las progresiones más frecuentes, las progresiones con nombre (cadencias y progresiones conocidas, por sus fundamentales) y los vaivenes entre dos acordes. Las columnas de cada compás salen de los confiables.
"""

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
EJE_DE = {0: 'T', 1: 'D', 2: 'S'}                                      # eje de Lendvai: grado en semitonos módulo 3


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

    def eje(q):                                                        # T, S, D, o T–D, D–S, S–T entre dos ejes
        return EJE_DE[(q // 2) % 3] if q % 2 == 0 else f'{EJE_DE[(q // 2) % 3]}–{EJE_DE[(q // 2 + 1) % 3]}'

    def paso(q0, q):                                                   # paso entre ejes de Lendvai
        if q0 % 2 or q % 2:
            return 'mismo eje neutro' if q0 % 6 == q % 6 else 'microtonal'
        a0, a1 = (q0 // 2) % 3, (q // 2) % 3
        if a0 == a1:
            return 'mismo eje (sustitución)'
        return 'adelante (T→S→D→T)' if (a0 - a1) % 3 == 1 else 'atrás (T→D→S→T)'

    def recorrido(umbral):                                             # cambios entre los compases con confianza ≥ umbral
        seq, marcas = [], {}                                           # seq: (fila, grado en cuartos de tono, cifrado)
        usados = 0
        for i, r in enumerate(armonia):
            if r.get('cifrado') is None or r.get('grado24') is None or (r.get('confianza') or 0) < umbral:
                continue
            usados += 1
            q = r['grado24']
            if seq and seq[-1][1] == q:                                # misma fundamental: no hay cambio
                continue
            if seq:
                q0 = seq[-1][1]
                prog, ejes = f'{seq[-1][2]} → {r["cifrado"]}', f'{eje(q0)} → {eje(q)}'
                if q0 % 2 or q % 2:
                    marcas[i] = (prog, 'microtonal', 'fuera de la tabla', paso(q0, q), ejes)
                else:
                    marcas[i] = (prog, MOVIMIENTOS[(q // 2 - q0 // 2) % 12], uso(q0 // 2, q // 2), paso(q0, q), ejes)
            seq.append((i, q, r['cifrado']))

        cambios = list(marcas.values())
        n = len(cambios) or 1
        share = lambda k: {key: round(100.0 * v / n, 1) for key, v in Counter(c[k] for c in cambios).most_common()}
        grados = [q for _, q, _ in seq]
        con_nombre = {}
        for name, pat in CON_NOMBRE.items():
            p24 = [2 * x for x in pat]
            hits = [seq[k][0] for k in range(len(seq) - len(p24) + 1) if grados[k:k + len(p24)] == p24]
            if hits:
                con_nombre[name] = dict(veces=len(hits), compases=[armonia[i]['compas'] for i in hits[:10]])
        vaiven = Counter()
        for k in range(len(seq) - 3):
            if grados[k] == grados[k + 2] and grados[k + 1] == grados[k + 3]:
                vaiven[' ↔ '.join(sorted((seq[k][2], seq[k + 1][2])))] += 1
        quintas = sum(1 for c in cambios if c[1].startswith('quinta'))
        frecuentes = [[p, c] for p, c in Counter(c[0] for c in cambios).most_common(8)]
        return marcas, dict(umbral=umbral, compases=usados, cambios=len(cambios), por_quintas=round(100.0 * quintas / n, 1),
                            movimientos=share(1), uso_piston=share(2), ejes=share(3),
                            pasos_de_eje=dict(Counter(c[4] for c in cambios).most_common(6)), frecuentes=frecuentes,
                            con_nombre=con_nombre, vaivenes=dict(vaiven.most_common(5)))

    marcas, confiables = recorrido(min_conf)
    _, todos = recorrido(0.0)
    out = []
    for i, r in enumerate(armonia):
        prog, mov, usual, paso_eje, ejes = marcas.get(i, (None,) * 5)
        out.append(dict(r, progresion=prog, movimiento=mov, uso_piston=usual, eje_cambio=ejes, paso_eje=paso_eje))
    return out, dict(confiables=confiables, todos=todos)
