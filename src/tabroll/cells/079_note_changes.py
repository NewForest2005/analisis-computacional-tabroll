"""Celda 153 del notebook original. Descripcion asociada: **`note_changes`**: Encuentra en qué puntos del ciclo cambia la nota..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def note_changes(line, offset, cyc, sr, hop, g=0.5):
    dt = hop / sr
    a, b = int(cyc.start / dt), int(cyc.end / dt)
    n = int(round(cyc.period / dt))
    t = a + np.flatnonzero(np.isfinite(line[a:b]))
    if len(t) == 0:
        return np.zeros(0)

    u, idx = np.unique(np.round((line[t] - offset) / g).astype(int), return_inverse=True)
    votes = np.zeros((len(u), n))
    np.add.at(votes, (idx, np.floor(((t - a) * dt / cyc.period) % 1 * n).astype(int) % n), 1)
    best = np.argmax(uniform_filter1d(votes, 3, axis=1, mode='wrap'), axis=0)
    return np.flatnonzero(best != np.roll(best, 1)) / n
