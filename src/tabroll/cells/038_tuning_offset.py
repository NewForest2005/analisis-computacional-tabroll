"""Celda 73 del notebook original. Descripcion asociada: **`tuning_offset`**: Mide la desafinación global (en semitonos) en los parciales de las notas estables, con media circular sobre el grid de `step` cents. Usa el grid de semitonos para distinguir un desfase real de un cuarto de tono, y devuelve 0 si no hay evidencia clara..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def tuning_offset(M, midi, sr, n_fft, step, H=6, fmin=120.0, fmax=3000.0, min_conf=0.1):
    df = sr / n_fft
    g = step / 100.0

    a, b = np.roll(midi, 2), np.roll(midi, -2)                                                        # solo fotogramas de notas estables
    t = np.flatnonzero(np.isfinite(midi) & (np.abs(a - midi) < 0.3) & (np.abs(b - midi) < 0.3))
    f0 = 440.0 * 2 ** ((midi[t] - 69) / 12)
    m, w = [], []

    for h in range(1, H + 1):
        sel = (f0 * h >= fmin) & (f0 * h <= fmax)
        if not sel.any():
            continue

        tt, ff = t[sel], f0[sel] * h
        idx = np.round(ff / df).astype(int)[:, None] + np.arange(-2, 3)[None, :]
        k = idx[np.arange(len(tt)), np.argmax(M[idx, tt[:, None]], axis=1)]

        l, c, r = (np.log(M[k + d, tt] + 1e-6) for d in (-1, 0, 1))
        den = l - 2 * c + r
        peak = (den < 0) & (c >= l) & (c >= r)                              # interpola la posición exacta del parcial
        pitch = 69 + 12 * np.log2((k + 0.5 * (l - r) / np.where(den == 0, -1, den)) * df / (h * 440.0))

        good = peak & (np.abs(pitch - midi[tt]) < 0.45)
        m.append(pitch[good])
        w.append(M[k[good], tt[good]])

    if not m or not sum(len(x) for x in m):
        return 0.0

    m, w = np.concatenate(m), np.concatenate(w)
    z = (w * np.exp(2j * np.pi * m / g)).sum() / w.sum()

    if np.abs(z) < min_conf:                                     # sin evidencia clara no se corrige
        return 0.0

    off = float(np.angle(z) / (2 * np.pi) * g)

    if step < 100:                                               # desfase real o cuarto de tono: decide la rejilla de semitonos
        opts = [off + k * g for k in range(-3, 4) if abs(off + k * g) <= 0.5 + 1e-9]
        off = max(opts, key=lambda o: ((w * np.cos(2 * np.pi * (m - o))).sum() / w.sum(), -abs(o)))

    return off
