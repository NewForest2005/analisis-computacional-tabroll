"""Celda 67 del notebook original.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def guitar_gate(stem, n_frames, hop, sr, floor_db=-30.0, bridge=1.5, min_gap=6.0):
    on = np.ones(n_frames, bool)
    if stem is None:
        return on

    x = np.pad(stem, (0, max(n_frames * hop - len(stem), 0)))[:n_frames * hop]
    r = maximum_filter1d(np.sqrt(np.mean(x.reshape(n_frames, hop) ** 2, axis=1)), int(sr / hop))   # nivel en ventanas de 1 s
    quiet = (20 * np.log10(r / np.percentile(r, 90) + 1e-9) < floor_db).astype(np.uint8)

    k = int(bridge * sr / hop)
    quiet = 1 - maximum_filter1d(1 - maximum_filter1d(quiet, k), k)                                # une silencios separados por destellos cortos
    d = np.diff(np.r_[0, quiet, 0].astype(int))

    for a, b in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
        if (b - a) * hop / sr >= min_gap:                                                          # solo silencios largos: ahí no hay guitarra
            on[a:b] = False

    return on
