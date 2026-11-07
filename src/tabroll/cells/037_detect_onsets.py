"""Celda 71 del notebook original. Descripcion asociada: Notas.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def detect_onsets(oenv, fps):
    z = oenv - uniform_filter1d(oenv, int(fps), mode='nearest')
    z = z / (z.std() + 1e-9)
    pk, _ = find_peaks(z, height=0.6, prominence=0.5, distance=max(1, int(0.06 * fps)))

    return pk / fps
