"""**`add_guitar_stem`**: Mezcla la saliencia de la voz aguda con la pista `guitar` de Demucs; sin pista, la deja igual. `gamma` es cuánto se descuenta, en la pista de guitarra, la huella de la octava de abajo. Esa pista casi no tiene bajo: con `gamma=0.0` la guitarra conserva su octava aunque el bajo doble el riff una octava abajo.
"""

def add_guitar_stem(Sh, S, stem, cand, sr, nfft, hop, weight=0.7, split=47.0, gamma=0.7):
    if stem is None:
        return Sh

    Sg = pitch_salience(stft_mag(stem, nfft, hop), sr, nfft, gamma=gamma)[0]
    hi = cand >= split
    level = lambda X: np.percentile(X[hi].max(axis=0), 90)

    out = Sh.copy()
    out[hi] = ((1 - weight) * np.maximum(Sh[hi], 0) / level(Sh) + weight * np.maximum(Sg[hi], 0) / level(Sg)) * level(S)
    return out
