"""2) Altura: línea dominante, bajo y dos líneas de voz aguda. `melody` sigue buscando ciclos; `melody_n` conserva la octava de la guitarra para las notas del tabroll.
"""

from tabroll.cells.find_cycles import find_cycles

if True:
    def cycle_consensus(S, cycles, sr, hop, turns=3, min_period=2.0):
        """Promedia la saliencia con cuadros equivalentes de vueltas vecinas."""
        T = S.shape[1]
        fps = sr / hop
        per = np.zeros(T)
        lo = np.zeros(T, int)
        hi = np.zeros(T, int)
        for c in (c for group in cycles.values() for c in group):
            if c.period < min_period:
                continue
            a, b = int(c.start * fps), min(int(c.end * fps), T)
            if a >= b:
                continue
            update = c.period > per[a:b]
            per[a:b] = np.where(update, c.period, per[a:b])
            lo[a:b] = np.where(update, a, lo[a:b])
            hi[a:b] = np.where(update, b, hi[a:b])
        out = S.copy()
        for t in np.flatnonzero(per > 0):
            period_frames = per[t] * fps
            indices = [t] + [j for k in range(-turns, turns + 1) if k
                             for j in [int(round(t + k * period_frames))] if lo[t] <= j < hi[t]]
            if len(indices) >= 3:
                out[:, t] = S[:, indices].mean(axis=1)
        return out

    def effect_ambiguity(S, candidates):
        """Marca cuadros con varias alturas fuertes, posibles efectos o capas superpuestas."""
        values = np.maximum(np.asarray(S, dtype=float), 0.0)
        up = np.vstack([np.zeros_like(values[:1]), values[:-1]])
        down = np.vstack([values[1:], np.zeros_like(values[-1:])])
        local = np.where((values >= up) & (values >= down), values, 0.0)
        order = np.argsort(-local, axis=0)[:8]
        result = np.zeros(values.shape[1], dtype=float)
        for t in range(values.shape[1]):
            peak = local[order[0, t], t] + 1e-9
            selected = []
            for row in order[:, t]:
                if local[row, t] < 0.62 * peak:
                    break
                pitch = candidates[row]
                if all(abs(pitch - other) >= 1.5 for other in selected):
                    selected.append(pitch)
            result[t] = np.clip((len(selected) - 1) / 3.0, 0.0, 1.0)
        return result

    def _cycle_repeat_score(line, cycles, sr, hop):
        """Acuerdo de la línea con la misma fase de vueltas vecinas del ciclo."""
        values = np.asarray(line, dtype=float)
        score = np.full(len(values), np.nan, dtype=float)
        fps = sr / hop
        for group in cycles.values():
            for cycle in group:
                a = max(0, int(cycle.start * fps))
                b = min(len(values), int(cycle.end * fps))
                period = max(1, int(round(cycle.period * fps)))
                for t in range(a, b):
                    peers = [j for j in (t - period, t + period) if a <= j < b]
                    if np.isfinite(values[t]) and peers:
                        matches = [abs(values[t] - values[j]) <= 0.3 for j in peers if np.isfinite(values[j])]
                        if matches:
                            score[t] = float(np.mean(matches))
        return score

    def melodic_24edo_score(line, cycles, sr, hop):
        """Combina movimiento conjunto y repetición de la línea en 24-EDO."""
        values = np.asarray(line, dtype=float)
        continuity = np.full(len(values), np.nan, dtype=float)
        finite = np.isfinite(values[:-1]) & np.isfinite(values[1:])
        steps = np.abs(np.diff(values) * 2.0)
        continuity[:-1] = np.where(finite, np.exp(-np.maximum(steps - 3.0, 0.0) / 3.0), np.nan)
        repeat = _cycle_repeat_score(values, cycles, sr, hop)
        return np.nanmean(np.vstack([continuity, repeat]), axis=0)

    def harmonic_12edo_score(melody_line, bass_line):
        """Puntúa si la relación simultánea cae en la subrejilla 12-EDO."""
        melody_values = np.asarray(melody_line, dtype=float)
        bass_values = np.asarray(bass_line, dtype=float)
        score = np.full(len(melody_values), np.nan, dtype=float)
        valid = np.isfinite(melody_values) & np.isfinite(bass_values)
        interval_24 = np.rint(np.abs(melody_values - bass_values) * 2.0).astype(int)
        score[valid] = (interval_24[valid] % 2 == 0).astype(float)
        return score

    def microtonal_residual_score(line):
        """Distancia normalizada de la línea respecto a la rejilla de 12-EDO."""
        values = np.asarray(line, dtype=float)
        score = np.full(len(values), np.nan, dtype=float)
        valid = np.isfinite(values)
        score[valid] = np.minimum(np.abs(values[valid] - np.rint(values[valid])) * 2.0, 1.0)
        return score

M = stft_mag(y, NFFT_P, HOP_P)
S, cand = pitch_salience(M, sr, NFFT_P)

stem = load_stem(GUITAR_STEM, len(y), sr)
bass_stem = load_stem(BASS_STEM, len(y), sr)

Smax = S.max(axis=0); thr = np.percentile(Smax, 55)
midi = viterbi_pitch(S, cand, thr)                                         # línea dominante de todo el registro
isbass = cand <= 55.0                                                      # bajo: hasta G3

Sb = S if bass_stem is None else pitch_salience(stft_mag(bass_stem, NFFT_P, HOP_P), sr, NFFT_P)[0]   # con pista bass, sin batería
Sbass = Sb[isbass].max(axis=0); thr_b = np.percentile(Sbass, 55)
bass = viterbi_pitch(Sb[isbass], cand[isbass], thr_b)

off = tuning_offset(M, midi, sr, NFFT_P, MICRO_STEP)                       # desafinación global respecto a A=440 (en semitonos)
chroma = chroma_profile(M, sr, NFFT_P, offset=off)                         # perfil tonal de todo el espectro

ishigh = cand >= 47.0                                                      # voz aguda: desde B2

cache_sal = {}                                                             # lo que comparten las dos saliencias
Sh = stereo_salience(S, M, y_st, cand, sr, NFFT_P, HOP_P, HAS_DRUMS, cache=cache_sal)
Sh = add_guitar_stem(Sh, S, stem, cand, sr, NFFT_P, HOP_P)

Shigh = Sh[ishigh].max(axis=0); thr_h = np.percentile(Shigh, 55)
melody = viterbi_pitch(Sh[ishigh], cand[ishigh], thr_h)                    # línea de la voz aguda para buscar ciclos
cycles_n = {'Voz grave': find_cycles(bass, off, sr, HOP_P, min_turns=2),
            'Voz aguda': find_cycles(melody, off, sr, HOP_P, min_turns=3)}         # los mismos ciclos que calcula la celda de ciclos

Sn = stereo_salience(S, M, y_st, cand, sr, NFFT_P, HOP_P, HAS_DRUMS, gamma=0.0, cache=cache_sal)   # conserva la octava de la guitarra
Sn = add_guitar_stem(Sn, S, stem, cand, sr, NFFT_P, HOP_P, gamma=0.0)
del cache_sal
selector_salience = Sn[ishigh].copy()                                      # run_song.py la guarda en line_diagnostics.json
selector_candidates = cand[ishigh].copy()
Snote = selector_salience.max(axis=0)
consenso_n = cycle_consensus(Sn[ishigh], cycles_n, sr, HOP_P)
melody_n_baseline = viterbi_pitch(consenso_n, cand[ishigh], np.percentile(Snote, 55))
registro_n = (float(np.nanmedian(melody_n_baseline)) if np.isfinite(melody_n_baseline).any()
              else float(np.median(cand[ishigh])))                         # registro típico de la melodía en esta canción
atraccion_n = 0.7 + 0.3 * np.exp(-0.5 * ((cand[ishigh] - registro_n) / 12.0) ** 2)   # atracción suave a ese registro, no a lo más agudo
melody_n = viterbi_pitch(consenso_n * atraccion_n[:, None], cand[ishigh], np.percentile(Snote, 55))
effect_ambiguity_n = effect_ambiguity(consenso_n, cand[ishigh])
melodic_24edo = melodic_24edo_score(melody_n, cycles_n, sr, HOP_P)
harmonic_12edo = harmonic_12edo_score(melody_n, bass)
microtonal_residual = microtonal_residual_score(melody_n)
melodic_24edo_baseline = melodic_24edo_score(melody_n_baseline, cycles_n, sr, HOP_P)
harmonic_12edo_baseline = harmonic_12edo_score(melody_n_baseline, bass)
microtonal_residual_baseline = microtonal_residual_score(melody_n_baseline)

if True:
    def top_peaks(S, cand, k=5):
        """Los k máximos locales en altura de cada cuadro: pitch y fuerza (T, k)."""
        up = np.vstack([np.zeros_like(S[:1]), S[:-1]])
        dn = np.vstack([S[1:], np.zeros_like(S[-1:])])
        values = np.where((S >= up) & (S >= dn), S, 0.0)
        indices = np.argsort(-values, axis=0)[:k]
        return cand[indices].T.astype(np.float32), np.take_along_axis(values, indices, axis=0).T.astype(np.float32)

pn, vn = top_peaks(Sn[ishigh], cand[ishigh])
ph, vh = top_peaks(Sh[ishigh], cand[ishigh])
line_candidates = dict(pitch_n=pn, val_n=vn, pitch_h=ph, val_h=vh,
                       snote=Snote.astype(np.float32), shigh=Shigh.astype(np.float32),
                       effect_ambiguity=effect_ambiguity_n.astype(np.float32),
                       melodic_24edo=melodic_24edo.astype(np.float32),
                       harmonic_12edo=harmonic_12edo.astype(np.float32),
                       microtonal_residual=microtonal_residual.astype(np.float32))

del Sn

lines = drop_echoes(chord_lines(M, S, cand, midi, thr, sr, NFFT_P), off)   # notas que suenan a la vez
del M
