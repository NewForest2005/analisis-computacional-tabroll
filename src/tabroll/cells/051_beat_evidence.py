"""Celda 99 del notebook original. Descripcion asociada: **`beat_evidence`**: Evidencia de inicio de compás en cada pulso: golpe grave, golpe general y cambio de bajo..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def beat_evidence(bt, oenv, olow, fps, H):
    w = int(0.05 * fps)
    bf = np.round(bt * fps).astype(int)
    at = lambda x: np.array([x[max(0, b - w):b + w + 1].max() for b in bf])
    chg = np.zeros(len(bt))

    for i in range(1, len(bt)):
        a, b = H[i - 1], H[i]

        if a.sum() > 0 and b.sum() > 0:
            chg[i] = 1 - (a @ b) / (np.linalg.norm(a) * np.linalg.norm(b))

    return _zs(at(olow)) + 0.5 * _zs(at(oenv)) + 0.8 * _zs(chg)
