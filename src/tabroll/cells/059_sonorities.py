"""Celda 115 del notebook original. Descripcion asociada: **`sonorities`**: Sigue cada nota por separado y crea un `Chord` cuando dos o más notas distintas se sostienen a la vez durante al menos `min_beats` pulsos, aunque otra línea se mueva debajo. Une huecos de hasta `bridge` pulsos y ordena las notas de grave a agudo, así que la más grave queda como raíz. Si solo suena una línea o una octava, no crea acorde..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def sonorities(lines, offset, pos, sr, hop, n_beats, tonic_midi, step, g=0.5, keep=0.5, min_beats=1.0, bridge=0.5):
    n_slots = int(round(n_beats / step))
    n_pcs = int(round(12 / g))
    slot = np.floor(pos(np.arange(len(lines[0])) * hop / sr) / step).astype(int)
    Q = np.round((np.array(lines) - offset) / g) * g                                  # voces × fotogramas

    frames = np.zeros(n_slots)
    active = np.zeros((n_pcs, n_slots))
    lowest = np.full((n_pcs, n_slots), np.inf)

    for t in np.flatnonzero((slot >= 0) & (slot < n_slots)):
        frames[slot[t]] += 1
        v = Q[:, t][np.isfinite(Q[:, t])]
        for p in v:
            i = int(round(np.mod(p, 12) / g)) % n_pcs
            lowest[i, slot[t]] = min(lowest[i, slot[t]], p)
        for i in {int(round(np.mod(p, 12) / g)) % n_pcs for p in v}:
            active[i, slot[t]] += 1

    on = active >= keep * np.maximum(frames, 1)
    gap, need = int(round(bridge / step)), int(round(min_beats / step))

    for i in range(n_pcs):                                                             # cada nota se sigue por separado
        idx = np.flatnonzero(on[i])
        runs = np.split(idx, np.flatnonzero(np.diff(idx) > gap + 1) + 1) if len(idx) else []
        on[i] = False
        for r in runs:
            if r[-1] - r[0] + 1 >= need:
                on[i, r[0]:r[-1] + 1] = True

    sets = [tuple(np.flatnonzero(on[:, k]).tolist()) for k in range(n_slots)]
    chords, i = [], 0

    while i < n_slots:
        j = i
        while j + 1 < n_slots and sets[j + 1] == sets[i]:
            j += 1
        if len(sets[i]) >= 2 and (j - i + 1) >= need:
            low = lowest[list(sets[i]), i:j + 1].min(axis=1)
            tones = sorted(100.0 * (p - tonic_midi) for p in low if np.isfinite(p))
            if len(tones) >= 2:
                chords.append(Chord(i * step, (j - i + 1) * step, tones))
        i = j + 1

    return chords
