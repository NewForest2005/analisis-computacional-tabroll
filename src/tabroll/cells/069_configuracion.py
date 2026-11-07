"""Celda 134 del notebook original. Descripcion asociada: 8) Notas de la voz grave y la voz aguda en pulsos (cuantizadas a GRID) y modelo final..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


onsets = detect_onsets(oenv, fps)
raw_bass = extract_notes(bass, Sbass, onsets, sr, HOP_P, off, MICRO_STEP)
raw_high = extract_notes(np.where(guitar_gate(stem, len(melody), HOP_P, sr), melody, np.nan), Shigh, onsets, sr, HOP_P, off, MICRO_STEP)
notes = sorted(place_notes(raw_bass, pos, nb, tonic_midi, GRID) + place_notes(raw_high, pos, nb, tonic_midi, GRID), key=lambda n: n.onset)

song = Song(scale, notes, chords, measures)

print(f'Tempo aproximado: {tempo:.1f} BPM | notas: {len(notes)} | acordes: {len(chords)} | compases: {len(measures)}')
print(f'Tonalidad: {scale.names[0]} {mode} ({" ".join(scale.names)}) | desafinación: {off*100:+.0f} cents')

if key_alts:
    print('Tonalidad dudosa: ' + ', '.join(f'{make_scale(t, m)[0].names[0]} {m}' for t, m in key_alts) + ' pesa casi lo mismo; puedes elegirla con KEY_OVERRIDE')

print('Compases por duración: ' + ', '.join(f'{L} pulsos ×{n}' for L, n in sorted(Counter(lens).items())))
