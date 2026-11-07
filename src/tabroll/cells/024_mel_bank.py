"""Celda 45 del notebook original. Descripcion asociada: **`mel_bank`**: Crea un banco de `n` filtros triangulares en escala mel y devuelve `(filtros, frecuencias centrales)`..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def mel_bank(sr, n_fft, n=48, fmin=40.0, fmax=9000.0):
    fr = np.linspace(0, sr / 2, n_fft // 2 + 1)

    m = lambda f: 2595 * np.log10(1 + f / 700)
    im = lambda v: 700 * (10 ** (v / 2595) - 1)

    pts = im(np.linspace(m(fmin), m(fmax), n + 2))
    fb = np.zeros((n, len(fr)))

    for i in range(n):
        l, c, r = pts[i], pts[i + 1], pts[i + 2]
        fb[i] = np.maximum(0, np.minimum((fr - l) / (c - l), (r - fr) / (r - c)))

    return fb, pts[1:-1]
