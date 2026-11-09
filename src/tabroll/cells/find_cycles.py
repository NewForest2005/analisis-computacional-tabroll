"""**`find_cycles`**: Busca qué periodos se repiten en una voz y en qué tramos de la canción.
"""

import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.signal import find_peaks
from tabroll.cells.cycle import Cycle

def find_cycles(line, offset, sr, hop, win_s=30.0, step_s=5.0, max_s=16.0, min_s=1.0, min_score=0.55, near=0.06, tau=0.5, g=0.5, tol=2, min_turns=2):

    dt = hop / sr
    v = np.isfinite(line)
    x = np.full(len(line), -1)

    x[v] = np.round((line[v] - offset) / g).astype(int)
    T, W, H = len(x), int(win_s / dt), int(step_s / dt)

    def curve(i):
        seg = x[i:i + W]

        if (seg >= 0).mean() < 0.1:
            return None

        n = 1 << int(np.ceil(np.log2(2 * len(seg))))
        ac = lambda b: np.fft.irfft(np.abs(np.fft.rfft(b.astype(float), n)) ** 2, n)[:len(seg)]
        num = sum(ac(seg == c) for c in np.unique(seg[seg >= 0]))
        L = min(int(max_s / dt), len(seg) // 2)

        return uniform_filter1d(num[:L + 1] / np.maximum(ac(seg >= 0)[:L + 1], 1.0), 3)

    def score(p):
        a, b = np.zeros(T, bool), np.zeros(T, bool)

        for k in range(p - tol, p + tol + 1):
            a[:-k] |= (x[:-k] == x[k:]) & v[:-k]
            b[:-k] |= v[k:] & v[:-k]

        s = int(max(2 * p, 4.0 / dt))
        den = uniform_filter1d((b | np.roll(b, p)).astype(float), s)

        return np.where(den >= 0.2, uniform_filter1d((a | np.roll(a, p)).astype(float), s) / np.maximum(den, 1e-3), 0.0)

    count = {}

    for i in range(0, max(T - W // 2, 1), H):
        c = curve(i)

        if c is None:
            continue

        pk, _ = find_peaks(c, height=min_score, distance=int(0.15 / dt), prominence=0.04)

        for p in pk[pk * dt >= min_s]:
            k = next((q for q in count if abs(q - p) <= max(2, 0.015 * p)), p)
            count[k] = count.get(k, 0) + 1

    P = sorted(p for p, n in count.items() if n >= 2)

    if not P:
        return []

    R = np.array([score(p) for p in P])
    top = R.max(axis=0)

    label = np.where(top >= min_score, np.argmax(R >= (top - near)[None, :], axis=0), -1)

    secs, i = [], 0

    while i < T:
        j = i
        while j + 1 < T and label[j + 1] == label[i]:
            j += 1
        if label[i] >= 0:
            secs.append([i, j + 1, int(label[i])])
        i = j + 1

    def merge():
        k = 0

        while k + 1 < len(secs):
            a, b = secs[k], secs[k + 1]
            if a[2] == b[2] and b[0] - a[1] <= max(2 * P[a[2]], 8.0 / dt):
                a[1] = b[1]
                del secs[k + 1]
            else:
                k += 1

    merge()
    changed, rounds = True, 0

    while changed and rounds < 50:                                                                 # tope por si dos reglas se contradicen
        changed, rounds = False, rounds + 1

        for k, s in enumerate(secs):
            own = R[s[2], s[0]:s[1]].mean()

            for n in (k - 1, k + 1):
                if 0 <= n < len(secs) and secs[n][1] - secs[n][0] > s[1] - s[0] and P[secs[n][2]] < P[s[2]]:
                    r = P[s[2]] / P[secs[n][2]]

                    if abs(r - round(r)) < 0.05 and R[secs[n][2], s[0]:s[1]].mean() >= own - 0.12:
                        s[2] = secs[n][2]
                        changed = True
                        break

                if 0 <= n < len(secs) and s[1] - s[0] < 3 * P[s[2]] and P[secs[n][2]] > P[s[2]]:            # tramo corto que el periodo largo del vecino también explica
                    r = P[secs[n][2]] / P[s[2]]

                    if abs(r - round(r)) < 0.05 and R[secs[n][2], s[0]:s[1]].mean() >= own - 0.12:
                        s[2] = secs[n][2]
                        changed = True
                        break
        merge()

    out = []

    for i, j, l in secs:
        p, seg = P[l], x[i:j]
        cnt = np.unique(seg[seg >= 0], return_counts=True)[1]

        if j - i < 3 * p or not len(cnt) or cnt.max() >= 0.9 * cnt.sum():                           # al menos 3 vueltas y más de una nota
            continue

        k = int(np.clip((j - i) // (2 * p), 1, 30.0 / (p * dt) + 1))                                # afina el periodo con un retardo largo

        lags = np.arange(k * p - k, k * p + k + 1)
        hits = [np.mean(seg[:-L] == seg[L:]) if L < len(seg) else 0 for L in lags]
        fine = float(lags[int(np.argmax(hits))] / k)

        K = int((j - i) / fine)                                                                     # vueltas del ciclo, una por fila

        turn = x[(i + np.outer(np.arange(K), fine) + np.arange(int(fine))[None, :]).astype(int)]

        def same(a, b):
            ok = (turn[a] >= 0) & (turn[b] >= 0)

            return ok.mean() < 0.1 or np.mean(turn[a][ok] == turn[b][ok]) >= tau

        cuts = [0] + [n for n in range(1, K - 1)                                                    # el patrón cambia y sigue distinto (no es un adorno)
                      if not same(n, n - 1) and not same(n + 1, n - 1) and same(n, n + 1)] + [K]

        while min_turns > 2 and len(cuts) > 2 and min(np.diff(cuts)) < min_turns:   # dos vueltas no bastan para una voz en mezcla
            short = int(np.argmin(np.diff(cuts)))
            del cuts[short + 1 if short + 1 < len(cuts) - 1 else short]

        for a, b in zip(cuts, cuts[1:]):
            if b - a >= 2:
                i2, j2 = int(i + a * fine), int(i + b * fine)
                out.append(Cycle(i2 * dt, j2 * dt, fine * dt, float(R[l, i2:j2].mean())))

    return out
