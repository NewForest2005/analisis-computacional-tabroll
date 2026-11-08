"""Celda 51 del notebook original. Descripcion asociada: **`track_beats`**: Seguimiento de pulso por programación dinámica (Ellis, 2007). Devuelve los tiempos de pulso en segundos..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def track_beats(oenv, fps, bpm, tight=400.0):
    period = 60.0 * fps / bpm
    o = oenv / (oenv.std() + 1e-9)
    n = len(o)

    score, back = o.copy(), -np.ones(n, int)
    offs = np.arange(int(round(period * 0.5)), int(round(period * 2.0)) + 1)
    pen = -tight * np.log(offs / period) ** 2

    for i in range(n):
        j = i - offs
        ok = j >= 0

        if ok.any():
            cand = score[j[ok]] + pen[ok]
            k = int(np.argmax(cand))
            score[i] = o[i] + cand[k]
            back[i] = j[ok][k]

    tail = min(int(period * 2), n)
    end = int(np.argmax(score[-tail:])) + n - tail
    b = [end]

    while back[b[-1]] >= 0:
        b.append(back[b[-1]])

    return np.array(b[::-1]) / fps
