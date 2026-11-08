"""**`sec_at`**: Convierte una posición en pulsos a segundos.
"""

def sec_at(beat):
    if beat < 0:
        return float(beat_times[0] + beat * spb)

    if beat > nb - 1:
        return float(beat_times[-1] + (beat - (nb - 1)) * spb)

    return float(np.interp(beat, np.arange(nb), beat_times))
