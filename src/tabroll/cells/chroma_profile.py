"""**`chroma_profile`**: Perfil de 12 clases de altura de todo el espectro (acordes, bajo y melodía), sobre el espectro blanqueado y corregido con `offset`.
"""

def chroma_profile(M, sr, n_fft, fmin=60.0, fmax=2000.0, offset=0.0):
    f = np.arange(M.shape[0]) * sr / n_fft
    sel = (f >= fmin) & (f <= fmax)

    Lm = np.log1p(M[sel] * 20.0)
    W = np.maximum(Lm - uniform_filter1d(Lm, size=48, axis=0, mode='nearest'), 0)
    pcs = np.round(12 * np.log2(f[sel] / 440.0) + 69 - offset).astype(int) % 12
    prof = np.array([W[pcs == pc].sum() for pc in range(12)])

    return prof / max(prof.sum(), 1e-9)
