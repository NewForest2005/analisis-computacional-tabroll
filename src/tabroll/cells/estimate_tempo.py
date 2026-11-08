"""**`estimate_tempo`**: Tempo (BPM) por autocorrelación de la envolvente de ataques, con un prior suave hacia ~120 BPM.
"""


def estimate_tempo(oenv, fps, lo=60, hi=200):
    x = oenv - oenv.mean()
    n = 1 << (2 * len(x) - 1).bit_length()

    ac = np.fft.irfft(np.abs(np.fft.rfft(x, n)) ** 2)[:len(x)]
    ac = ac / (ac[0] + 1e-12)
    bpms = np.arange(lo, hi + 0.25, 0.25)
    lags = fps * 60 / bpms

    at = lambda l: np.interp(l, np.arange(len(ac)), ac)
    score = at(lags) + 0.5 * at(2 * lags) + 0.25 * at(4 * lags)
    prior = np.exp(-0.5 * (np.log2(bpms / 120) / 0.8) ** 2)

    return float(bpms[np.argmax(score * prior)])
