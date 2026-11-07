"""Celda 163 del notebook original. Descripcion asociada: **`cycle_anchor`**: Busca el ciclo vecino con el que este debe compartir su inicio..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def cycle_anchor(cyc, prev, others, gap=2.0, min_score=0.8):

    best = max(others, key=lambda o: min(cyc.end, o.end) - max(cyc.start, o.start), default=None)

    if best is not None and min(cyc.end, best.end) > max(cyc.start, best.start) and best.score >= min_score:
        return best.entry

    return prev.entry if prev is not None and cyc.start - prev.end < gap and prev.score >= min_score else None
