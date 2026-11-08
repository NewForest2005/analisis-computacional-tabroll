"""Celda 107 del notebook original. Descripcion asociada: **`chord_roots`**: Raíz del acorde en cada pulso, por Viterbi sobre 12 clases de altura, con inercia al cambio y una penalización suave a las raíces fuera de la escala..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def chord_roots(H, tonic_pc, steps_semi, stay=0.8, off_scale=0.7):
    n = len(H)
    scale_pcs = {(tonic_pc + s) % 12 for s in steps_semi}
    tot = H.sum(axis=1)
    ref = np.percentile(tot[tot > 0], 75) if (tot > 0).any() else 1.0

    wgt = np.clip(tot / ref, 0, 1)                                  # pulsos sin evidencia -> emisión plana
    Hn = H / np.maximum(tot[:, None], 1e-9)
    emis = np.log(0.05 + wgt[:, None] * Hn)
    emis -= off_scale * np.array([0.0 if pc in scale_pcs else 1.0 for pc in range(12)])[None, :]

    D = np.zeros((n, 12))
    B = np.zeros((n, 12), int)
    D[0] = emis[0] + np.where(np.arange(12) == tonic_pc, 0.5, 0.0)

    for i in range(1, n):
        top = int(np.argmax(D[i - 1]))
        stay_sc = D[i - 1] + stay
        use_stay = stay_sc >= D[i - 1][top]
        D[i] = np.where(use_stay, stay_sc, D[i - 1][top]) + emis[i]
        B[i] = np.where(use_stay, np.arange(12), top)

    path = np.zeros(n, int)
    path[-1] = int(np.argmax(D[-1]))

    for i in range(n - 1, 0, -1):
        path[i - 1] = B[i, path[i]]

    return path
