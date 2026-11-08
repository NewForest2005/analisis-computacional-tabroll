"""6) Compases de longitud variable (2, 3, 4, 7... pulsos), estimados con los acentos graves y los cambios de bajo.
"""

if FORCE_BAR_BEATS is None:
    lens = segment_bars(beat_evidence(beat_times, oenv, olow, fps, Hb), BAR_LENGTHS, meter_cue(beat_times, oenv, fps, BAR_LENGTHS))

else:
    pattern = [FORCE_BAR_BEATS] if np.isscalar(FORCE_BAR_BEATS) else list(FORCE_BAR_BEATS)
    lens, k = [], 0
    while sum(lens) < nb:
        lens.append(int(pattern[k % len(pattern)])); k += 1
    lens[-1] -= sum(lens) - nb                                 # el último compás se recorta al final

measures = measures_from_lengths(lens, grid=0.5, accent=1.0)
