"""Celda 57 del notebook original. Descripcion asociada: Altura (línea dominante).

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def pitch_salience(M, sr, n_fft, m_lo=26.0, m_hi=100.0, step_c=25.0, H=10, alpha=0.82, gamma=0.7, gamma_max=64.0):
    df = sr / n_fft
    Lm = np.log1p(M * 20.0)

    W = np.maximum(Lm - uniform_filter1d(Lm, size=48, axis=0, mode='nearest'), 0)
    W /= (W.max() + 1e-9)

    cand = np.arange(m_lo, m_hi + 1e-9, step_c / 100.0)
    f0 = 440.0 * 2 ** ((cand - 69) / 12)

    S = np.zeros((len(cand), M.shape[1]), np.float32)
    vmin = np.full_like(S, np.inf)                             # armónico más débil de cada candidato

    gsum = np.zeros(len(cand), np.float32)                     # peso de los armónicos disponibles

    for h in range(1, H + 1):
        pos = f0 * h / df
        ok = pos < M.shape[0] - 2
        i0 = np.floor(pos[ok]).astype(int)

        fr = (pos[ok] - i0).astype(np.float32)
        g = alpha ** (h - 1)
        v = W[i0] * (1 - fr)[:, None] + W[i0 + 1] * fr[:, None]
        S[ok] += g * v

        vmin[ok] = np.minimum(vmin[ok], v)
        gsum[ok] += g

    S += (gsum.max() - gsum)[:, None] * vmin                   # completa los armónicos que no caben bajo Nyquist

    bajo = np.full_like(S, np.inf)                             # huella de una nota una octava más grave

    for k in (0.5, 1.5):
        pos = f0 * k / df
        i0 = np.floor(pos).astype(int)

        fr = (pos - i0).astype(np.float32)
        bajo = np.minimum(bajo, W[i0] * (1 - fr)[:, None] + W[i0 + 1] * fr[:, None])

    bajo[cand > gamma_max] = 0                                 # arriba, los armónicos del bajo imitan esa huella
    S = np.maximum(S - gamma * gsum[:, None] * bajo, 0)

    return S, cand
