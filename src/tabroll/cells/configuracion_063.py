"""2) Altura: línea dominante, bajo y dos líneas de voz aguda. `melody` sigue buscando ciclos; `melody_n` conserva la octava de la guitarra para las notas del tabroll.
"""

from tabroll.cells.find_cycles import find_cycles

GUIAR_CON_GP = False   # el .gp oficial solo sirve para evaluar y graficar; nunca construye la línea

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
melody = viterbi_pitch(Sh[ishigh], cand[ishigh], thr_h)                    # línea de la voz aguda para buscar ciclos
cycles_n = {'Voz grave': find_cycles(bass, off, sr, HOP_P, min_turns=2),
            'Voz aguda': find_cycles(melody, off, sr, HOP_P, min_turns=3)}         # los mismos ciclos que calcula la celda de ciclos

Sn = stereo_salience(S, M, y_st, cand, sr, NFFT_P, HOP_P, HAS_DRUMS, gamma=0.0)   # conserva la octava de la guitarra
Sn = add_guitar_stem(Sn, S, stem, cand, sr, NFFT_P, HOP_P, gamma=0.0)
selector_salience = Sn[ishigh].copy()                                      # entrada pitch-específica para select_melody_track
selector_candidates = cand[ishigh].copy()
Snote = selector_salience.max(axis=0)
melody_n = viterbi_pitch(cycle_consensus(Sn[ishigh], cycles_n, sr, HOP_P), cand[ishigh],
                         np.percentile(Snote, 55))                            # línea de las notas del tabroll, con consenso entre vueltas

# La línea estructural para ciclos conserva la línea acústica fuera del
# fragmento GP, pero dentro del fragmento alineado favorece la pista de
# referencia mientras esta tenga actividad.
melody = melody.copy()
gp_alignment = None
melody_track_path = []
melody_confidence = np.zeros(len(melody), dtype=float)
reference_files = {
    'SARNIEZZ': 'sarniezz_gp.json',
    'MATA ZYKLEK': 'mata_zyklek_gp.json',
    'FABIENK': 'fabienk_gp.json',
}
try:
    import json
    from tabroll.reference.align_gp_audio import align_gp_audio
    from tabroll.reference.select_melody_track import select_melody_track
    reference_root = next((d for d in (Path.cwd(), *Path.cwd().parents) if (d / 'references').is_dir()), None)
    song_key = str(SONG).upper()
    reference_name = next((filename for title, filename in reference_files.items() if title in song_key), None)
    if reference_root is not None and reference_name is not None:
        reference = json.loads((reference_root / 'references' / reference_name).read_text(encoding='utf-8'))
        gp_alignment = align_gp_audio(reference, selector_salience, selector_candidates, [], [], float(tempo),
                                      melody=np.asarray(melody_n, dtype=float), sr=sr, hop=HOP_P,
                                      audio_duration_s=len(y) / sr)
        grouped = {}
        for event in gp_alignment['events']:
            grouped.setdefault(str(event['track']), []).append(event)
        title_key = next(title for title in reference_files if title in song_key)
        preferred = {'SARNIEZZ': 'E.Guitar I', 'MATA ZYKLEK': 'E.Guitar III', 'FABIENK': 'E.Guitar'}[title_key]
        selected, melody_track_path, melody_confidence = select_melody_track(
            selector_salience, stem, bass_stem,
            {'tracks': [{'name': name, 'events': events} for name, events in grouped.items()]},
            [], candidates=selector_candidates, sr=sr, hop=HOP_P,
            switch_penalty=0.35, preferred_track=preferred)
        active = np.array([track != 'silence' for track in melody_track_path])
        if GUIAR_CON_GP:
            melody[active] = selected[active]
        print(f"Línea estructural GP: {preferred} | offset {gp_alignment['offset_s']:.2f} s | "
              f"tempo local {gp_alignment['tempo_local_bpm']:.2f} BPM | acierto {gp_alignment['score']:.3f}")
except (OSError, KeyError, ValueError, ImportError) as exc:
    print(f'Aviso: no se pudo guiar melody con el GP ({type(exc).__name__}: {exc})')

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
                       snote=Snote.astype(np.float32), shigh=Shigh.astype(np.float32))

del Sn

lines = drop_echoes(chord_lines(M, S, cand, midi, thr, sr, NFFT_P), off)   # notas que suenan a la vez
del M
