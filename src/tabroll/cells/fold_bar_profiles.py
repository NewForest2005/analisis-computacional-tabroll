"""**`fold_bar_profiles`**: Suma el perfil de cada compás sobre todas las vueltas del ciclo que lo contiene, en el mismo punto del ciclo. Devuelve también cuántas vueltas sumó y cuánto se parecen entre sí (acuerdo, de 0 a 1). Un compás que no está dentro de ningún ciclo usa solo su propio perfil.
"""

import numpy as np

def fold_bar_profiles(spans, table, cycles, min_dur=0.0):
    get = lambda c, k: c[k] if isinstance(c, dict) else getattr(c, k)
    cos = lambda x, y: float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y))) if x.any() and y.any() else 0.0
    prof, info = [], []
    for t0, t1 in spans:
        mid = 0.5 * (t0 + t1)
        c = next((c for c in cycles if get(c, 'start') <= mid < get(c, 'end')), None)
        if c is None:
            prof.append(table.profile(t0, t1, min_dur))
            info.append(dict(ciclo=None, vueltas=1, acuerdo=None))
            continue
        P, cs, ce = get(c, 'period'), get(c, 'start'), get(c, 'end')
        turns = [table.profile(t0 + k * P, t1 + k * P, min_dur)
                 for k in range(-int((t0 - cs) / P) - 1, int((ce - t1) / P) + 2)
                 if t0 + k * P >= cs - 0.05 and t1 + k * P <= ce + 0.05]
        H = np.sum(turns, axis=0) if turns else table.profile(t0, t1, min_dur)
        full = [h for h in turns if h.any()]
        prof.append(H)
        info.append(dict(ciclo=get(c, 'label') or None, vueltas=max(len(turns), 1),
                         acuerdo=float(np.mean([cos(h, H) for h in full])) if len(full) >= 2 else None))
    return np.array(prof).reshape(-1, 24), info
