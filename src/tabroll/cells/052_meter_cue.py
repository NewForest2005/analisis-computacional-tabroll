"""Celda 101 del notebook original. Descripcion asociada: meter_cue: mide, pulso a pulso, cuánto se parecen los ataques (sobre todo de la batería) a los de L pulsos después. Donde la canción va en 7/8 se parecen cada 7 corcheas, y donde va en 2/4, cada 4. Así segment_bars sabe qué compás elegir en cada región de una canción que cambia de métrica..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def meter_cue(bt, oenv, fps, lengths, win=28):
    w = int(0.05 * fps)
    x = _zs(np.array([oenv[max(0, b - w):b + w + 1].max() for b in np.round(bt * fps).astype(int)]))
    cue = {}

    for L in lengths:                                                              # ¿los golpes se repiten cada L pulsos aquí?
        r = np.zeros(len(x))
        for i in range(len(x)):
            a = x[max(0, i - win // 2):i + win // 2]
            b = x[max(0, i - win // 2) + L:i + win // 2 + L]
            n = min(len(a), len(b))
            if n > 8 and a[:n].std() > 0 and b[:n].std() > 0:
                r[i] = np.corrcoef(a[:n], b[:n])[0, 1]
        cue[L] = r

    return cue
