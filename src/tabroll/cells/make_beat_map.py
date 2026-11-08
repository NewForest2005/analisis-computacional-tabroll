"""**`make_beat_map`**: Convierte segundos en posición en pulsos (0 = primer pulso), con extrapolación antes y después.
"""

def make_beat_map(bt):
    idx = np.arange(len(bt), dtype=float)
    ibi0, ibi1 = bt[1] - bt[0], bt[-1] - bt[-2]

    def pos(t):
        t = np.asarray(t, float)
        p = np.interp(t, bt, idx)
        p = np.where(t < bt[0], (t - bt[0]) / ibi0, p)
        return np.where(t > bt[-1], idx[-1] + (t - bt[-1]) / ibi1, p)

    return pos
