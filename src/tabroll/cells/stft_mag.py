"""Espectros
"""

def stft_mag(x, n_fft, hop):

    pad = n_fft // 2
    xp = np.pad(x, (pad, pad), mode='reflect').astype(np.float32)
    n = 1 + (len(xp) - n_fft) // hop
    win = np.hanning(n_fft + 1)[:-1].astype(np.float32)
    out = np.empty((n_fft // 2 + 1, n), np.float32)

    for s in range(0, n, 2000):
        e = min(n, s + 2000)
        idx = np.arange(s, e)[:, None] * hop + np.arange(n_fft)[None, :]
        out[:, s:e] = np.abs(np.fft.rfft(xp[idx] * win, axis=1)).T

    return out
