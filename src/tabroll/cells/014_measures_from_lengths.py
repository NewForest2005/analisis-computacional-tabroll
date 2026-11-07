"""Celda 25 del notebook original. Descripcion asociada: **`measures_from_lengths`**: Crea compases consecutivos a partir de sus duraciones; por ejemplo, `[4, 4, 2, 4]`. Admite cambios de métrica..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def measures_from_lengths(lengths: Sequence[float], **kw) -> list[Measure]:
    out, t = [], 0.0
    for L in lengths:
        out.append(Measure(t, L, **kw))
        t += L
    return out
