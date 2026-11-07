"""Celda 87 del notebook original.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def key_alternatives(h, tonic_pc, mode, near=0.92):
    weight = lambda t, st: h[t] + 0.5 * h[(t + 7) % 12] + 0.3 * h[(t + st[2]) % 12]
    notes = {(tonic_pc + s) % 12 for s in MODES[mode]}
    ref, out = weight(tonic_pc, MODES[mode]), []

    for t in sorted(notes):                                          # mismas 7 notas, otra nota de reposo
        for name, st in MODES.items():
            if (t, name) != (tonic_pc, mode) and {(t + s) % 12 for s in st} == notes and weight(t, st) >= near * ref:
                out.append((t, name))

    return out
