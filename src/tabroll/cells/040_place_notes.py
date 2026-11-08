"""Celda 77 del notebook original. Descripcion asociada: **`place_notes`**: coloca las notas de una voz en la rejilla del compás y resuelve las que se solapan..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def place_notes(raw, pos, nb, tonic_midi, grid):
    notes = []

    for t0, t1, p in raw:
        o = max(round(float(pos(t0)) / grid) * grid, 0.0)
        e = round(float(pos(t1)) / grid) * grid

        if o >= nb:
            continue
        d, c = max(grid, e - o), (p - tonic_midi) * 100.0

        if notes and o < notes[-1].onset + notes[-1].dur - 1e-9:     # solapadas por la cuantización
            if o <= notes[-1].onset + 1e-9:                          # misma casilla: se conserva la más larga
                if d > notes[-1].dur:
                    notes[-1] = Note(o, d, c)
                continue

            notes[-1].dur = o - notes[-1].onset

        notes.append(Note(o, d, c))

    return notes
