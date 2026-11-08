"""Celda 169 del notebook original. Descripcion asociada: **`cycle_song`**: Convierte un ciclo en una canción de una sola vuelta para dibujarla..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def cycle_song(cyc, scale, tonic_midi, bar=4):

    p, N, step = cyc.pitch, cyc.slots, 1 / cyc.sub
    notes, i = [], 0

    while i < N:
        j = i
        while j + 1 < N and p[j + 1] == p[i] and not cyc.attack[j + 1]:
            j += 1
        if np.isfinite(p[i]):
            notes.append(Note(i * step, (j - i + 1) * step, (p[i] - tonic_midi) * 100.0))
        i = j + 1

    beats = N * step

    lens = [bar] * int(beats // bar) if beats % bar == 0 else [beats]

    # lens = [4] * int(beats // 4) if beats % 4 == 0 else [beats]

    return Song(scale, notes, [], measures_from_lengths(lens, grid=step, accent=1.0))
