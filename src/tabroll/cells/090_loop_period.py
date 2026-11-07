"""Celda 175 del notebook original. Descripcion asociada: loop_period:.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def loop_period(groups):
    by = {}
    for c in [c for g in groups.values() for c in g]:
        by.setdefault(round(c.period, 1), []).append(c)

    best = max(by.values(), key=lambda cs: sum(c.end - c.start for c in cs))    # el periodo que más tiempo cubre
    return float(np.median([c.period for c in best]))
