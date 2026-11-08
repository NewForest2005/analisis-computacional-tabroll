"""**`mask_line`**: Borra de `M` los armónicos de una línea de altura, para dejar a la vista las demás notas que suenan a la vez.
"""

def mask_line(M, line, sr, n_fft, width=3, n_harm=64):
    M2 = M.copy()
    df = sr / n_fft
    t = np.flatnonzero(np.isfinite(line))
    f = 440.0 * 2 ** ((line[t] - 69) / 12)

    for h in range(1, n_harm + 1):
        b = np.round(f * h / df).astype(int)
        ok = b < M.shape[0] - width - 1
        for d in range(-width, width + 1):
            M2[b[ok] + d, t[ok]] = 0

    return M2
