"""Celda 63 del notebook original. Descripcion asociada: **`add_guitar_stem`**: mezcla la saliencia de la voz aguda con la pista `guitar` de Demucs. Si no hay pista, deja la saliencia igual..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def add_guitar_stem(Sh, S, stem, cand, sr, nfft, hop, weight=0.7, split=47.0):
    if stem is None:
        return Sh

    Sg = pitch_salience(stft_mag(stem, nfft, hop), sr, nfft)[0]
    hi = cand >= split
    level = lambda X: np.percentile(X[hi].max(axis=0), 90)

    out = Sh.copy()
    out[hi] = ((1 - weight) * np.maximum(Sh[hi], 0) / level(Sh) + weight * np.maximum(Sg[hi], 0) / level(Sg)) * level(S)
    return out
