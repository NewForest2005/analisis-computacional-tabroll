"""Celda 47 del notebook original. Descripcion asociada: Pulso (beat tracking).

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def onset_envelopes(y, sr, hop=256, n_fft=2048):
    P = stft_mag(y, n_fft, hop) ** 2
    fb, centres = mel_bank(sr, n_fft)
    L = 10 * np.log10(fb @ P + 1e-10)

    L = np.maximum(L, L.max() - 80)
    d = np.maximum(0, np.diff(L, axis=1, prepend=L[:, :1]))

    return d.mean(axis=0), d[centres < 250].mean(axis=0)
