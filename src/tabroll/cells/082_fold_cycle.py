"""Celda 159 del notebook original. Descripcion asociada: **`fold_cycle`**: Superpone las vueltas del ciclo y elige la nota de cada casilla, de la voz grave o de la aguda..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def fold_cycle(S, cand, line, offset, cyc, sr, hop, beat, sub, voice='grave', anchor=None, top=55.0, split=47.0, rho=0.45, octave=0.8, weak=0.8, alone=0.6, floor=0.3, g=0.5, stereo=False):

    dt = hop / sr
    fr = np.arange(int(cyc.start / dt), int(cyc.end / dt))
    N = int(round(round(cyc.period / beat * 2) / 2 * sub))
    q = cyc.period / N

    phi = note_changes(line, offset, cyc, sr, hop)                                                                # la rejilla se alinea con los cambios de nota
    t0 = cyc.start + (np.angle(np.exp(2j * np.pi * phi * N).sum()) / (2 * np.pi) * q if len(phi) else 0.0)

    pos = (fr * dt - t0) / q
    slot = np.floor(pos).astype(int)
    keep = ((pos - slot) >= 0.2) & ((pos - slot) < 0.8)

    turn, cell = (slot[keep] - slot[keep].min()) // N, slot[keep] % N
    A = np.zeros((len(cand), turn.max() + 1, N), np.float32)
    W = np.zeros((turn.max() + 1, N))

    np.add.at(W, (turn, cell), 1)

    for k, c, f in zip(turn, cell, fr[keep]):
        A[:, k, c] += S[:, f]

    full = W.min(axis=1) > 0
    F = np.median(A[:, full] / W[full][None], axis=1) if full.any() else A.sum(axis=1) / np.maximum(W.sum(axis=0), 1)

    band = cand <= top if voice == 'grave' else cand >= split                                                     # cada vuelta vota con su saliencia, sin seguir una línea
    c_band, F_band = cand[band], F[band]
    peak = F_band.max(axis=0)

    best = np.argmax(F_band, axis=0) if voice == 'grave' else smooth_path(F_band, c_band)

    if voice != 'grave':
        for k in range(N):                                                                                        # el segundo armónico de la guitarra no es la nota
            j = np.argmin(np.abs(c_band - c_band[best[k]] + 12))
            if abs(c_band[j] - c_band[best[k]] + 12) < 0.2 and F_band[j, k] >= octave * peak[k]:
                best[k] = j

    raw = c_band[best]
    pitch = np.round((raw - offset) / g) * g
    pitch[peak < rho * np.percentile(peak, 90)] = np.nan

    if voice != 'grave':                                                                                          # un armónico débil del bajo tampoco
        low = cand <= top
        d = np.mod(raw - cand[low][np.argmax(F[low], axis=0)], 12)
        harm = np.min(np.abs(d[:, None] - np.array([0, 3.86, 7, 9.69, 12])), axis=1) < 0.6

        pitch[harm & (peak < weak * np.median(peak[~harm] if (~harm).any() else peak))] = np.nan

        if stereo:                                                       # sin el bajo, lo que queda bajo el piso no suena
            quiet = floor * np.percentile(S[band].max(axis=0), 90)
            pitch[peak < quiet] = np.nan

            if np.median(peak) < quiet:
                pitch[:] = np.nan

            on = np.isfinite(pitch)
            cyc.doubled = float(np.mean(np.minimum(d, 12 - d)[on] < 0.6)) if on.any() else 1.0

        else:
            own = np.median(peak) >= alone * np.median(F[low].max(axis=0))   # muy por debajo del bajo solo quedan sus armónicos
            cyc.doubled = float(np.mean(harm)) if own else 1.0

    for k in range(N):                                                                                            # la cola de una nota no es otra nota; un salto de octava suelto tampoco
        a, b = pitch[k - 1], pitch[(k + 1) % N]

        if np.isfinite(a) and np.isfinite(pitch[k]) and abs(pitch[k] - a) <= 0.5 and peak[k] < 0.6 * peak[k - 1]:
            pitch[k] = np.nan

        elif np.isfinite(b) and np.isfinite(pitch[k]) and abs(pitch[k] - b) <= 0.5 and peak[k] < 0.6 * peak[(k + 1) % N]:
            pitch[k] = b

        elif a == b and abs(pitch[k] - a) == 12:
            pitch[k] = a

        elif np.isnan(a) and abs(pitch[k] - b) <= 0.5 and pitch[(k + 2) % N] == b:                                # ataque tras un silencio
            pitch[k] = b

    edge = ((pos - slot) < 0.1) | ((pos - slot) >= 0.9)                                                           # ¿la nota se vuelve a atacar o sigue sonando?
    near = np.round(pos[edge]).astype(int) % N
    I = np.clip(np.searchsorted(cand, pitch[near] + offset), 0, len(cand) - 1)

    ok = np.isfinite(pitch[near])
    D, C = np.zeros(N), np.zeros(N)
    np.add.at(D, near[ok], S[I[ok], fr[edge][ok]])

    np.add.at(C, near[ok], 1)
    held = D / np.maximum(C, 1)
    level = F[np.clip(np.searchsorted(cand, np.nan_to_num(pitch) + offset), 0, len(cand) - 1), np.arange(N)]

    attack = held < 0.85 * level

    if anchor is None:                                                                                            # el ciclo empieza donde el patrón entra en la canción
        ks = np.arange(-2 * N, 2 * N)

        tf = np.clip(np.round((t0 + (ks + 0.5) * q) / dt).astype(int), 0, S.shape[1] - 1)
        now = np.round((c_band[np.argmax(S[band][:, tf], axis=0)] - offset) / g) * g
        want = pitch[ks % N]

        hit = np.where(np.isfinite(want), np.abs(now - want) < 0.75, S[band][:, tf].max(axis=0) < rho * np.percentile(peak, 90)) * 2.0 - 1.0
        jump = np.array([hit[k:k + N].sum() - hit[max(k - N, 0):k].sum() if t0 + ks[k] * q >= -q else -np.inf for k in range(N, 3 * N)])
        first = int(ks[N + int(np.argmax(jump))])

        while np.isnan(pitch[first % N]) and np.isfinite(pitch).any():
            first += 1

        if sub > 1:                                                                                              # y sobre el pulso, no a medio pulso
            on = np.bincount(np.flatnonzero(np.isfinite(pitch) & (pitch != np.roll(pitch, 1))) % sub, minlength=sub)

            if on.max() >= 1.5 * np.median(on):
              first += (int(np.argmax(on)) - first) % sub

    else:                                                                                                         # o sigue el pulso del ciclo vecino
        first = int(round((anchor - t0) / q)) % N

    cyc.pitch, cyc.attack = np.roll(pitch, -first), np.roll(attack, -first)
    cyc.slots, cyc.sub, cyc.entry = N, sub, float(t0 + first * q)
    return cyc.pitch
