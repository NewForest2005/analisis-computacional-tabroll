"""Celda 75 del notebook original. Descripcion asociada: **`extract_notes`**: Segmenta el contorno en notas: corta en cada ataque y en cada cambio de altura. Devuelve `[(t_inicio_s, t_fin_s, altura MIDI)]`, con la altura cuantizada a la rejilla de `step` cents..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def extract_notes(midi, Smax, onsets_t, sr, hop, offset, step):
    g = step / 100.0
    hop_t = hop / sr
    T = len(midi)
    ok = np.isfinite(midi)

    decayed = Smax < 0.35 * maximum_filter1d(Smax, size=9)     # la nota se "apago"
    qraw = np.where(ok, np.round((midi - offset) / g) * g, np.nan)
    qs = median_filter(np.where(ok, qraw, 0.0), size=3, mode='nearest')
    qs = np.where(ok & ~decayed, qs, np.nan)

    cut = np.zeros(T, bool)
    cut[0] = True
    cut[1:] |= ~((qs[1:] == qs[:-1]) | (np.isnan(qs[1:]) & np.isnan(qs[:-1])))
    cut[np.clip(np.round(onsets_t / hop_t).astype(int), 0, T - 1)] = True

    starts = np.flatnonzero(cut)
    ends = np.r_[starts[1:], T]
    notes = []

    for a, b in zip(starts, ends):
        if np.isnan(qs[a:b]).all() or (b - a) < 2:
            continue

        raw = midi[a:b][np.isfinite(qs[a:b])]
        p = np.round((np.median(raw) - offset) / g) * g
        notes.append((a * hop_t, b * hop_t, float(p)))

    return notes
