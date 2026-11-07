"""Celda 103 del notebook original. Descripcion asociada: **`segment_bars`**: Puede recibir la pista de meter_cue. A cada compás posible de L pulsos le suma gamma · L · r, donde r es cuánto se repiten los golpes cada L pulsos en ese punto. Si no recibe la pista, funciona igual que antes..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def segment_bars(e, lengths, cue=None, gamma=1.0):
    beta, switch = 1.0, 0.8
    prior = {4: .45, 7: .15, 3: .12, 2: .08, 6: .08, 5: .06, 8: .08}

    lp = {L: math.log(prior.get(L, .03)) for L in lengths}
    N, Lmax = len(e), max(lengths)
    NEG = -1e18

    g = np.full((N + Lmax + 1, Lmax + 1), NEG)
    arg = np.zeros((N + Lmax + 1, Lmax + 1), int)

    for end in range(1, N + Lmax + 1):
        for L in lengths:
            s = end - L

            if s < 0 or s >= N:
                continue

            m = gamma * L * cue[L][s] if cue else 0.0      # pista de métrica: los golpes se repiten cada L pulsos desde s

            if s == 0:
                g[end, L], arg[end, L] = beta * e[0] + lp[L] + m, 0
                continue

            prev = [(g[s, Lp] - (switch if Lp != L else 0.0), Lp) for Lp in lengths if g[s, Lp] > NEG / 2]

            if prev:
                v, Lp = max(prev)
                g[end, L], arg[end, L] = beta * e[s] + lp[L] + m + v, Lp

    cands = [(g[end, L], end, L) for end in range(N, N + Lmax + 1) for L in lengths if g[end, L] > NEG / 2 and end - L < N]

    _, end, L = max(cands)
    out = []

    while True:
        out.append(int(L))
        s = end - L
        if s == 0:
            break
        L, end = arg[end, L], s

    out = out[::-1]
    out[-1] = int(N - (sum(out) - out[-1]))      # el último compás se recorta al final del audio

    if len(out) > 1 and out[-1] < 2:             # un compás final de 1 pulso se une al anterior
        out[-2] += out.pop()

    return out
