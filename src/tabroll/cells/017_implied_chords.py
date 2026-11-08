"""Celda 31 del notebook original. Descripcion asociada: **`implied_chords`**: Completa los tramos sin acorde medido con la raíz de `chord_roots` y la calidad de las notas que suenan. Los acordes deducidos se muestran entre paréntesis..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def implied_chords(measured, roots, lines, offset, pos, sr, hop, n_beats, tonic_midi, sc, g=0.5, min_share=0.15, min_frames=3, bridge=2.0):

    beat = np.floor(pos(np.arange(len(lines[0])) * hop / sr)).astype(int)
    Q = np.round((np.array(lines) - offset) / g) * g

    busy = np.zeros(n_beats, bool)
    voiced = beat[np.isfinite(Q).any(axis=0)]
    voiced = voiced[(voiced >= 0) & (voiced < n_beats)]

    empty = np.bincount(voiced, minlength=n_beats) < min_frames

    for c in measured:
        busy[int(np.floor(c.onset)):int(np.ceil(c.onset + c.dur))] = True

    chords, i = list(measured), 0

    while i < n_beats:
        if busy[i] or empty[i]:
            i += 1
            continue

        j = i
        while j + 1 < n_beats and not busy[j + 1] and not empty[j + 1] and roots[j + 1] == roots[i]:
            j += 1

        v = Q[:, (beat >= i) & (beat <= j)]
        v = v[np.isfinite(v)]
        i, j = j + 1, i

        if not len(v):
            continue

        rel = np.mod(v - roots[j], 12) * 100.0
        rel = rel[rel > 0]
        den = max(len(rel), 0.2 * len(v))
        base = 100.0 * ((roots[j] - tonic_midi) % 12)
        tones = [base]

        if len(rel):
            share = lambda c: np.sum(np.abs(rel - c) < 1) / den
            for options in ((200, 300, 350, 400, 500), (600, 700, 800)):
                best = max(options, key=share)

                if share(best) >= min_share:
                    tones.append(base + best)

        numeral, name = label_chord(Chord(j, i - j, tones), sc)
        chords.append(Chord(float(j), float(i - j), tones, numeral=f"({numeral})", name=f"({name})"))

    pcs = lambda c: {t % 1200 for t in c.tones}
    merged = []

    for c in sorted(chords, key=lambda c: c.onset):                # misma raíz junto a un acorde medido: no es un cambio
        a = merged[-1] if merged else None

        if a and (a.name or c.name) and a.tones[0] % 1200 == c.tones[0] % 1200 and (pcs(a) <= pcs(c) or pcs(c) <= pcs(a)):
            keep = a if (a.name is None or (c.name is not None and len(a.tones) >= len(c.tones))) else c
            merged[-1] = Chord(a.onset, c.onset + c.dur - a.onset, keep.tones, numeral=keep.numeral, name=keep.name)
        else:
            merged.append(c)

    for a, b in zip(merged, merged[1:]):
        if 0 < b.onset - (a.onset + a.dur) < bridge:
            a.dur = b.onset - a.onset

    return merged
