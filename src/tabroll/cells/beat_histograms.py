"""Acordes
"""

def beat_histograms(track, weight, pos, sr, hop, n_beats):
    H = np.zeros((n_beats, 12))
    t = np.arange(len(track)) * hop / sr
    bi = np.clip(np.floor(pos(t)).astype(int), 0, n_beats - 1)
    ok = np.isfinite(track)
    lo = np.floor(track[ok]).astype(int)

    fr = track[ok] - lo
    w = weight[ok]

    np.add.at(H, (bi[ok], lo % 12), w * (1 - fr))
    np.add.at(H, (bi[ok], (lo + 1) % 12), w * fr)

    return H
