"""**`stereo_salience`**: Calcula la saliencia de la voz aguda con el canal central y el lateral, para sacar el bajo sin perder la octava de la guitarra. `gamma` es cuánto se descuenta, en el canal lateral, la huella de una nota una octava más grave. En el lateral (`L − R`) el bajo ya se canceló, así que con `gamma=0.0` la guitarra conserva su fundamental.
"""

def stereo_salience(S, M, stereo, cand, sr, nfft, hop, drums=True, split=47.0, min_side=0.01, gamma=0.7):
    if stereo.ndim == 1:
        return S

    Mx = stft_mag((stereo[0] - stereo[1]) / 2, nfft, hop)                # el bajo va al centro: L - R lo cancela
    f = np.arange(M.shape[0]) * sr / nfft
    band = (f >= 300) & (f < 4000)

    if np.sum(Mx[band] ** 2) < min_side * np.sum(M[band] ** 2):          # audio casi mono: no hay canal lateral útil
        return S

    Sm = pitch_salience(harmonic_part(M), sr, nfft)[0] if drums else S
    Sx = pitch_salience(harmonic_part(Mx) if drums else Mx, sr, nfft, gamma=gamma)[0]
    hi = cand >= split
    gain = np.percentile(Sm[hi].max(axis=0), 90) / np.percentile(Sx[hi].max(axis=0), 90)

    Sh = S.copy()
    Sh[hi] = np.sqrt(np.maximum(Sm[hi], 0) * np.maximum(Sx[hi], 0) * gain)   # debe sonar en los dos canales
    return Sh
