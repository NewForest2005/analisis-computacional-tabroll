"""**`bar_spans`**: Inicio y fin en segundos de cada compás, a partir de los pulsos reales y de la longitud de cada compás en pulsos.
"""

import numpy as np

def bar_spans(beat_times, lens):
    bt = np.asarray(beat_times, float)
    spb = float(np.median(np.diff(bt)))
    idx = np.concatenate([[0.0], np.cumsum(lens)]).astype(float)
    t = np.interp(idx, np.arange(len(bt)), bt)
    over = idx > len(bt) - 1
    t[over] = bt[-1] + (idx[over] - (len(bt) - 1)) * spb                     # el último compás termina un pulso después
    return [(float(a), float(b)) for a, b in zip(t[:-1], t[1:]) if b > a]
