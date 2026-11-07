"""Celda 91 del notebook original. Descripcion asociada: **`spell_scale`**: Nombres de las 7 notas con letras consecutivas (E dórico → E F♯ G A B C♯ D)..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def spell_scale(tonic_pc, steps_semi):
    best = None

    for li in range(7):
        names, cost = [], 0

        for k, s in enumerate(steps_semi):
            l2 = (li + k) % 7
            a = ((tonic_pc + s) - _NAT[l2] + 6) % 12 - 6
            cost += abs(a) + (9 if abs(a) > 1 else 0)
            names.append(_LETTERS[l2] + ('♯' * a if a > 0 else '♭' * -a))

        if best is None or cost < best[0]:
            best = (cost, names)

    return best[1]
