"""Celda 157 del notebook original. Descripcion asociada: smooth_path.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def smooth_path(F, notes, cost=0.05, free=2.0):
    E = np.log(np.maximum(F / (F.max(axis=0) + 1e-9), 1e-3))                    # qué tan cerca está cada nota de la más fuerte de su casilla
    jump = cost * np.maximum(np.abs(notes[:, None] - notes[None, :]) - free, 0)   # saltar lejos cuesta; un tono o menos no
    E3 = np.tile(E, 3)                                                             # el ciclo da la vuelta
    score, back = E3[:, 0].copy(), np.zeros(E3.shape, int)

    for t in range(1, E3.shape[1]):
        m = score[:, None] - jump
        back[:, t] = np.argmax(m, axis=0)
        score = m[back[:, t], np.arange(len(notes))] + E3[:, t]

    path = np.zeros(E3.shape[1], int)
    path[-1] = np.argmax(score)

    for t in range(E3.shape[1] - 1, 0, -1):
        path[t - 1] = back[path[t], t]

    N = F.shape[1]
    return path[N:2 * N]
