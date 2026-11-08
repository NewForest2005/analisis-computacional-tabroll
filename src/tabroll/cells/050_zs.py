"""Celda 97 del notebook original. Descripcion asociada: Compases (longitud variable).

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def _zs(v, win=31):
    r = v - uniform_filter1d(v, win, mode='nearest')
    return r / (r.std() + 1e-9)
