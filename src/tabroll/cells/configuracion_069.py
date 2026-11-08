"""**`extract_notes`**: La voz grave corta sus notas en los ataques graves de la pista `bass` y la voz aguda en los de la pista `guitar`. En la mezcla manda la batería: partía las notas largas del bajo y no marcaba las notas repetidas de la guitarra. Sin pistas, se usan los ataques de la mezcla, como antes.
"""

onsets = detect_onsets(oenv, fps)
onsets_b = onsets if bass_stem is None else detect_onsets(onset_envelopes(bass_stem, sr)[1], fps, height=0.6, win=0.3)   # ataques graves de la pista bass
raw_bass = extract_notes(bass, Sbass, onsets_b, sr, HOP_P, off, MICRO_STEP)
onsets_h = onsets if stem is None else detect_onsets(onset_envelopes(stem, sr)[0], fps, height=0.3, win=0.3)   # ataques de la guitarra sola
raw_high = extract_notes(np.where(guitar_gate(stem, len(melody_n), HOP_P, sr), melody_n, np.nan), Snote, onsets_h, sr, HOP_P, off, MICRO_STEP)
notes = sorted(place_notes(raw_bass, pos, nb, tonic_midi, GRID) + place_notes(raw_high, pos, nb, tonic_midi, GRID), key=lambda n: n.onset)

song = Song(scale, notes, chords, measures)

print(f'Tempo aproximado: {tempo:.1f} BPM | notas: {len(notes)} | acordes: {len(chords)} | compases: {len(measures)}')
print(f'Tonalidad: {scale.names[0]} {mode} ({" ".join(scale.names)}) | desafinación: {off*100:+.0f} cents')

if key_alts:
    print('Tonalidad dudosa: ' + ', '.join(f'{make_scale(t, m)[0].names[0]} {m}' for t, m in key_alts) + ' pesa casi lo mismo; puedes elegirla con KEY_OVERRIDE')

print('Compases por duración: ' + ', '.join(f'{L} pulsos ×{n}' for L, n in sorted(Counter(lens).items())))
