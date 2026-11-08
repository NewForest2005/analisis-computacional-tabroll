"""Celda 122 del notebook original. Descripcion asociada: 2) Altura: línea dominante, bajo y voz aguda. La voz aguda usa el canal lateral y, si existe, la pista `guitar` de Demucs..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

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

Sh = stereo_salience(S, M, y_st, cand, sr, NFFT_P, HOP_P, HAS_DRUMS)
Sh = add_guitar_stem(Sh, S, stem, cand, sr, NFFT_P, HOP_P)

Shigh = Sh[ishigh].max(axis=0); thr_h = np.percentile(Shigh, 55)
melody = viterbi_pitch(Sh[ishigh], cand[ishigh], thr_h)

lines = drop_echoes(chord_lines(M, S, cand, midi, thr, sr, NFFT_P), off)   # notas que suenan a la vez
del M
