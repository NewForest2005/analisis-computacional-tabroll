"""**`layer_changes`**: Compara cada instante de la pista guitar con el mismo instante una vuelta de loop antes. Si aparece sonido que antes no estaba, entró una capa; si desaparece, salió. Devuelve esos cambios y el nivel de la guitarra para la fila “Capas” del mapa.
"""

def layer_changes(x, period, sr, hop, n_fft, win=2.0, thr=0.3, quiet=0.08, lo=150.0, hi=4000.0):
    M = stft_mag(x, n_fft, hop)
    f = np.arange(M.shape[0]) * sr / n_fft
    X = np.sqrt(M[(f >= lo) & (f < hi)])
    dt = hop / sr
    L = period / dt
    l0, a = int(L), L - int(L)

    prev = np.zeros_like(X)                                                        # el mismo instante, una vuelta de loop antes
    prev[:, l0 + 1:] = (1 - a) * X[:, 1:-l0] + a * X[:, :-l0 - 1]
    smooth = lambda v: uniform_filter1d(v, int(win / dt))

    total = smooth(X.sum(axis=0))
    new = smooth(np.maximum(X - prev, 0).sum(axis=0)) / (total + 1e-9)            # suena ahora y no sonaba una vuelta antes
    gone = smooth(np.maximum(prev - X, 0).sum(axis=0)) / (smooth(prev.sum(axis=0)) + 1e-9)
    new[:l0 + 1] = gone[:l0 + 1] = 0

    level = total / np.percentile(total, 95)
    before = np.r_[np.zeros(l0), level[:-l0]]
    found, events = [], []

    for kind, v, on in (('entra', new, level > quiet), ('sale', gone, before > quiet)):
        edges = np.flatnonzero(np.diff(np.r_[0, ((v > thr) & on).astype(int), 0]))
        for i, j in zip(edges[::2], edges[1::2]):
            if (j - i) * dt >= 0.25 * period:                                      # dura al menos un cuarto de vuelta
                found.append((v[i:j].max(), max(i * dt - win / 2, 0.0), kind))

    for _, t, kind in sorted(found, reverse=True):                                 # de dos cambios seguidos queda el más claro
        if not any(k == kind and abs(t - s) < period / 2 for s, k in events):
            events.append((t, kind))

    return sorted(events), level
