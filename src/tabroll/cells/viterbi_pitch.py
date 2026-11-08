"""**`viterbi_pitch`**: Contorno de altura por Viterbi. Los estados son las alturas candidatas más un estado sin altura (`NaN`).
"""

def viterbi_pitch(S, cand, thr, jump_cost=0.01, max_jump=96, switch_cost=1.0):
    nC, T = S.shape
    emis = np.log1p(S / (thr + 1e-9))
    unv = 0.25

    B = np.empty((nC + 1, T), np.int16)
    prev = np.concatenate([emis[:, 0], [unv]]).astype(np.float32)
    B[:, 0] = np.arange(nC + 1)

    pen = (-jump_cost * np.abs(np.arange(-max_jump, max_jump + 1))).astype(np.float32)
    ar = np.arange(nC)
    padded = np.full(nC + 2 * max_jump, -1e9, np.float32)
    win = sliding_window_view(padded, 2 * max_jump + 1)         # win[i, k] = prev[i + k - max_jump]

    for t in range(1, T):
        padded[max_jump:max_jump + nC] = prev[:nC]
        sc = win + pen
        k = sc.argmax(axis=1)

        best = sc[ar, k]
        arg = (ar + k - max_jump).astype(np.int16)
        from_u = prev[nC] - switch_cost

        use_u = from_u > best
        best = np.where(use_u, from_u, best)
        arg = np.where(use_u, nC, arg)

        bv = int(np.argmax(prev[:nC]))

        if prev[bv] - switch_cost > prev[nC]:
            un_best, un_arg = prev[bv] - switch_cost, bv
        else:
            un_best, un_arg = prev[nC], nC
        prev = np.concatenate([best + emis[:, t], [un_best + unv]]).astype(np.float32)
        B[:, t] = np.concatenate([arg, [un_arg]])

    path = np.empty(T, int)
    path[-1] = int(np.argmax(prev))

    for t in range(T - 1, 0, -1):
        path[t - 1] = B[path[t], t]

    return np.where(path < nC, cand[np.minimum(path, nC - 1)], np.nan)
