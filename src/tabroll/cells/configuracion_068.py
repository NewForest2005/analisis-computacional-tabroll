"""7) Acordes: raíz por pulso (bajo + melodía) y calidad según las notas que suenan.
"""

roots = chord_roots(Hb + 0.6 * Hm, tonic_pc, steps)
measured = sonorities(lines, off, pos, sr, HOP_P, nb, tonic_midi, GRID)
chords = implied_chords(measured, roots, lines, off, pos, sr, HOP_P, nb, tonic_midi, scale)
