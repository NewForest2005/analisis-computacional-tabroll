"""**`cycle_bar`**: Devuelve el compás que domina dentro de un ciclo, es decir, el más frecuente entre los compases que empiezan en él. Así cada ciclo se cuenta y se dibuja con su propio compás y no con el más común de toda la canción.
"""

def cycle_bar(cyc, lens, bt, default):

    starts = bt[np.minimum(np.r_[0, np.cumsum(lens)[:-1]].astype(int), len(bt) - 1)]
    inside = [L for L, t in zip(lens, starts) if cyc.start <= t < cyc.end]           # compases que empiezan dentro del ciclo

    return max(set(inside), key=inside.count) if inside else default
