"""Celda 126 del notebook original. Descripcion asociada: 4) Tonalidad y modo detectados en cada canción -> escala de 7 grados como en Hooktheory..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


h = 0.5 * pc_histogram(arr[:, 2], arr[:, 1] - arr[:, 0]) + 0.5 * chroma     # notas de la línea + cromagrama
low = bass[np.isfinite(bass)] - off

hb = pc_histogram(low, np.ones(len(low)))                                  # dónde reposa el bajo

tonic_pc, mode = parse_key(KEY_OVERRIDE) if KEY_OVERRIDE else detect_key(h, hb)
key_alts = [] if KEY_OVERRIDE else key_alternatives(hb, tonic_pc, mode)

steps = MODES[mode]
scale, tonic_midi = make_scale(tonic_pc, mode)
