"""Celda 15 del notebook original. Descripcion asociada: **`accidental`**: Alteración de `k` pasos. Usa ♯ y ♭ cuando un paso equivale a un semitono (12-TET); en otra afinación usa flechas ↑ y ↓, y cada flecha equivale a un paso..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

# afinacion
def accidental(k: int, unit: float) -> str:

    if k == 0:
        return ""
    sharp, flat = ("♯", "♭") if abs(unit - 100) < 1e-6 else ("↑", "↓")
    if abs(k) > 3:
        return f"{sharp if k > 0 else flat}{abs(k)}"
    return (sharp if k > 0 else flat) * abs(k)
