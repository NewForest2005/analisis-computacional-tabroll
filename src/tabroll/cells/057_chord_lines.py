"""Celda 111 del notebook original. Descripcion asociada: **`chord_lines`**: Busca hasta `n_lines` líneas simultáneas, borrando en cada paso los armónicos de la línea anterior. Compensa los armónicos compartidos entre notas, como en las quintas, y descarta las que suenan más de `min_db` dB por debajo de la línea principal. Devuelve una lista de contornos; el primero es `main`..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def chord_lines(M, S, cand, main, thr, sr, n_fft, n_lines=3, rho=1.0, min_db=-15.0, H=10, alpha=0.82):
    Smax = S.max(axis=0) + 1e-9
    lines, M2 = [main], M
    frames = np.arange(S.shape[1])
    df = sr / n_fft

    def level(line):                                             # nivel real de una línea, sumando sus armónicos
        f = 440.0 * 2 ** ((np.nan_to_num(line, nan=200.0) - 69) / 12)
        a = sum(M[np.clip(np.round(f * h / df).astype(int), 0, M.shape[0] - 1), frames] for h in range(1, 7))
        return np.where(np.isfinite(line), a, 0.0)

    top = level(main)

    for _ in range(n_lines - 1):
        M2 = mask_line(M2, lines[-1], sr, n_fft)
        S2, _ = pitch_salience(M2, sr, n_fft)
        l = viterbi_pitch(S2, cand, thr)
        i = np.clip(np.rint((np.nan_to_num(l, nan=cand[0]) - cand[0]) / (cand[1] - cand[0])).astype(int), 0, len(cand) - 1)
        f2 = 440.0 * 2 ** ((cand[i] - 69) / 12)

        free = np.zeros(len(f2))                                 # parte de la nota que no comparte armónicos
        total = 0.0
        for h in range(1, H + 1):
            shared = np.zeros(len(f2), bool)
            for prev in lines:
                f1 = 440.0 * 2 ** ((np.nan_to_num(prev, nan=200.0) - 69) / 12)
                r = f2 * h / f1
                shared |= np.abs(r - np.round(r)) * f1 < 3.5 * df
            free += alpha ** (h - 1) * ~shared
            total += alpha ** (h - 1)

        need = rho * Smax * np.maximum(free / total, 0.5)
        keep = (S2[i, frames] >= need) & (level(l) >= 10 ** (min_db / 20) * top)  # descarta cuerdas que solo resuenan
        lines.append(np.where(keep, l, np.nan))

    return lines
