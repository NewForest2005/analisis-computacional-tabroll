"""**`stereo_salience`**: Calcula la saliencia de la voz aguda con el canal central y el lateral, para sacar el bajo sin perder la octava de la guitarra. `gamma` es cuánto se descuenta, en el canal lateral, la huella de una nota una octava más grave. En el lateral (`L − R`) el bajo ya se canceló, así que con `gamma=0.0` la guitarra conserva su fundamental. `cache` (un diccionario) guarda lo que no depende de `gamma`: el canal lateral ya filtrado y la saliencia del central. Dos llamadas con la misma canción y el mismo `cache` dan lo mismo que sin él, pero la segunda es mucho más rápida.
"""

def stereo_salience(S, M, stereo, cand, sr, nfft, hop, drums=True, split=47.0, min_side=0.01, gamma=0.7, cache=None):
    if stereo.ndim == 1:
        return S

    c = {} if cache is None else cache                                   # con cache, otra llamada reusa lo que no depende de gamma
    if 'lateral' not in c:
        Mx = stft_mag((stereo[0] - stereo[1]) / 2, nfft, hop)            # el bajo va al centro: L - R lo cancela
        f = np.arange(M.shape[0]) * sr / nfft
        band = (f >= 300) & (f < 4000)
        if np.sum(Mx[band] ** 2) < min_side * np.sum(M[band] ** 2):      # audio casi mono: no hay canal lateral útil
            c['lateral'] = None
        else:
            c['lateral'] = harmonic_part(Mx) if drums else Mx
            c['Sm'] = pitch_salience(harmonic_part(M), sr, nfft)[0] if drums else S
    if c['lateral'] is None:
        return S

    Sm = c['Sm']
    Sx = pitch_salience(c['lateral'], sr, nfft, gamma=gamma)[0]
    hi = cand >= split
    gain = np.percentile(Sm[hi].max(axis=0), 90) / np.percentile(Sx[hi].max(axis=0), 90)

    Sh = S.copy()
    Sh[hi] = np.sqrt(np.maximum(Sm[hi], 0) * np.maximum(Sx[hi], 0) * gain)   # debe sonar en los dos canales
    return Sh
