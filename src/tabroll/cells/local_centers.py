"""**`local_centers`**: Centro de cada tramo. Los tramos son los ciclos de la voz principal (el bajo si tiene ciclos, si no la voz aguda) y los huecos entre ellos, con al menos `min_compases` compases. En cada tramo, el centro se mide con `center24_by_layer` sobre las notas y los ciclos del tramo, y el modo con `mode24` sobre sus compases. Cada centro se compara con el de la canción (`tonic_pc24`) y con el del tramo anterior. Un tramo con margen menor que `margen_min` queda como dudoso («?»). Agrega a cada compás `tramo` y `centro_local`, y devuelve los tramos y los cambios de centro.
"""

from collections import Counter
from types import SimpleNamespace

from tabroll.cells.center24_by_layer import center24_by_layer
from tabroll.cells.harmony_by_bar import DEG24_NAMES, PC24_NAMES
from tabroll.cells.mode24 import mode24

SALTOS = {0: 'mismo centro', 5: 'quinta abajo', 7: 'quinta arriba', 3: 'tercera menor arriba', 9: 'tercera menor abajo',
          4: 'tercera mayor arriba', 8: 'tercera mayor abajo', 2: 'segunda arriba', 10: 'segunda abajo', 1: 'semitono arriba',
          11: 'semitono abajo', 6: 'tritono'}


def local_centers(armonia, raw_bass, raw_high, cycles, tonic_pc24, min_compases=4, margen_min=0.1):
    mmss = lambda t: f'{int(t // 60)}:{int(t % 60):02d}'
    get = lambda c, k: c[k] if isinstance(c, dict) else getattr(c, k)
    principal = 'Voz grave' if cycles.get('Voz grave') else 'Voz aguda'
    segs = sorted((float(get(c, 'start')), float(get(c, 'end')), float(get(c, 'period')), get(c, 'label') or '?')
                  for c in cycles.get(principal, []))
    fin_cancion = armonia[-1]['fin_s'] if armonia else 0.0
    tramos, t = [], armonia[0]['inicio_s'] if armonia else 0.0
    for a, b, P, l in segs:
        if a - t > 0:
            tramos.append((t, a, None, '—'))
        tramos.append((a, b, P, l))
        t = max(t, b)
    if fin_cancion - t > 0:
        tramos.append((t, fin_cancion, None, '—'))

    def relacion(q):
        if q % 2:
            return f'microtonal ({DEG24_NAMES[q]})'
        return SALTOS[q // 2] + ('' if q == 0 or (q // 2) % 3 else ', mismo eje de Lendvai')

    out = [dict(r, tramo=None, centro_local=None) for r in armonia]
    lista, previo = [], None
    for a, b, P, l in tramos:
        idx = [k for k, r in enumerate(armonia) if a - 0.05 <= (r['inicio_s'] + r['fin_s']) / 2 < b + 0.05]
        if len(idx) < min_compases:
            continue
        dentro = lambda notas: [n for n in notas if a - 0.05 <= n[0] < b + 0.05]
        tr_cycles = {principal: [SimpleNamespace(start=a, end=b, period=P)] if P else []}
        otra = 'Voz aguda' if principal == 'Voz grave' else 'Voz grave'
        tr_cycles[otra] = [SimpleNamespace(start=max(a, float(get(c, 'start'))), end=min(b, float(get(c, 'end'))),
                                              period=float(get(c, 'period'))) for c in cycles.get(otra, [])
                           if float(get(c, 'start')) < b and float(get(c, 'end')) > a]
        c24 = center24_by_layer(dentro(raw_bass), dentro(raw_high), tr_cycles)
        centro = c24['centro_pc24']
        q = (centro - tonic_pc24) % 24
        seguro = c24['margen'] >= margen_min
        tr = dict(inicio=mmss(a), fin=mmss(b), inicio_s=round(a, 2), fin_s=round(b, 2), ciclo=l, compases=len(idx),
                  centro=PC24_NAMES[centro], grado=DEG24_NAMES[q], margen=c24['margen'], seguro=seguro,
                  modo=mode24([armonia[k] for k in idx], centro)['nombre'], respecto_del_centro=relacion(q),
                  desde_el_anterior=None if previo is None else relacion((centro - previo) % 24))
        lista.append(tr)
        previo = centro
        for k in idx:
            out[k].update(tramo=f'{tr["inicio"]} {l}', centro_local=tr['centro'] + ('' if seguro else '?'))

    seguros = [x for x in lista if x['seguro']]
    dur = lambda x: x['fin_s'] - x['inicio_s']
    total = sum(dur(x) for x in lista) or 1.0
    cambios = [x for x in lista[1:] if x['desde_el_anterior'] != 'mismo centro']
    return out, dict(voz=principal, tramos=lista,
                     centro_estable=round(100.0 * sum(dur(x) for x in lista if x['grado'] == '1') / total, 1),
                     modulaciones=len([x for x in cambios if x['seguro']]),
                     cambios_de_centro=dict(Counter(x['desde_el_anterior'] for x in cambios)),
                     centros=dict(Counter(x['centro'] for x in seguros)),
                     tramos_dudosos=len(lista) - len(seguros))
