"""**`has_motion`**: Descarta los tramos que son una sola nota sostenida; un ritmo sobre una nota sí cuenta como ciclo.
"""

def has_motion(cyc):

    p = cyc.pitch[np.isfinite(cyc.pitch)]

    return len(p) > 0 and (np.isnan(cyc.pitch).mean() > 0.2 or np.unique(p, return_counts=True)[1].max() < 0.85 * len(p))
