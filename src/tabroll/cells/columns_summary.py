"""**`columns_summary`**: Resumen de las columnas principales de los compases confiables, ponderado por duración: qué es la nota en el acorde, intervalo con el bajo, forma del arco, pulso en que cae, cumbres, qué parte cae dentro del acorde y, en cada ciclo de la voz aguda, su columna y su arco más frecuentes.
"""

from collections import Counter


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
                cumbres=share(lambda r: r.get('cumbre'), 5), por_ciclo=ciclos)
