from pathlib import Path

import numpy as np
from scipy.ndimage import median_filter, uniform_filter1d

CELLS = Path(__file__).parents[1] / "src" / "tabroll" / "cells"


def funciones():
    ns = dict(np=np, median_filter=median_filter, uniform_filter1d=uniform_filter1d)
    for name in ("stft_mag", "pitch_salience", "harmonic_part", "stereo_salience"):
        exec((CELLS / f"{name}.py").read_text(encoding="utf-8"), ns)
    return ns


def test_con_cache_da_lo_mismo_que_sin_cache():
    ns, sr, nfft, hop = funciones(), 22050, 4096, 512
    t = np.arange(int(2.5 * sr)) / sr
    bajo = 0.6 * np.sin(2 * np.pi * 82.4 * t)                            # al centro: L - R lo cancela
    guitarra = sum(0.3 / h * np.sin(2 * np.pi * 329.6 * h * t) for h in range(1, 6))
    stereo = np.stack([bajo + guitarra, bajo + 0.2 * guitarra]).astype(np.float32)
    M = ns["stft_mag"](stereo.mean(axis=0), nfft, hop)
    S, cand = ns["pitch_salience"](M, sr, nfft)
    sin = [ns["stereo_salience"](S, M, stereo, cand, sr, nfft, hop, gamma=g) for g in (0.7, 0.0)]
    cache = {}
    con = [ns["stereo_salience"](S, M, stereo, cand, sr, nfft, hop, gamma=g, cache=cache) for g in (0.7, 0.0)]
    assert set(cache) == {"lateral", "Sm"}
    assert all(np.array_equal(a, b) for a, b in zip(sin, con))
    assert not np.array_equal(con[0], S)                                 # sí usó el canal lateral
