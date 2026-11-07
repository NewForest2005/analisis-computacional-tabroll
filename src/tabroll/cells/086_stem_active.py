"""Celda 167 del notebook original.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def stem_active(stem, cyc, sr, win=0.5):
    hop = int(win * sr)
    r = np.sqrt(np.mean(stem[:len(stem) // hop * hop].reshape(-1, hop) ** 2, axis=1))
    return np.median(r[int(cyc.start / win):int(cyc.end / win)]) / np.percentile(r, 75)
