"""Celda 120 del notebook original. Descripcion asociada: 1)  Pulso real de la grabación: los compases se miden en pulsos reales, no en una rejilla fija desde t=0..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


oenv, olow = onset_envelopes(y, sr); fps = sr / 256

tempo = TEMPO_OVERRIDE or estimate_tempo(oenv, fps)
beat_times = track_beats(oenv, fps, tempo)

if BEAT_DIV > 1:                                                                             # pulso más fino que el seguido (en 7/8, corcheas)
    beat_times = np.interp(np.arange((len(beat_times) - 1) * BEAT_DIV + 1) / BEAT_DIV, np.arange(len(beat_times)), beat_times)

if len(beat_times) < 8:                                                                      # audio muy corto: grid de tempo constante
    beat_times = np.arange(0.0, len(y) / sr, 60.0 / tempo)

if len(beat_times) < 4:
    raise ValueError('El audio es demasiado corto para analizarlo.')

spb = float(np.median(np.diff(beat_times))); tempo = 60.0 / spb
pos = make_beat_map(beat_times); nb = len(beat_times)
GRID = note_grid(detect_onsets(oenv, fps), pos, GRID)                                       # en 6/8 o 12/8 las notas van a tercios de pulso
