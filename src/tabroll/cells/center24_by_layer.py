"""**`center24_by_layer`**: Centro en 24-EDO, medido por capa como propone Piston para la música sin dominante. En cada capa (bajo y voz aguda) se suman tres partes, con el mismo peso:
"""

import numpy as np

def center24_by_layer(raw_bass, raw_high, cycles, w_bass=2.0):
    get = lambda c, k: c[k] if isinstance(c, dict) else getattr(c, k)

    def layer(notes, cyc):
        notes = sorted((float(n[0]), float(n[1]), float(n[2])) for n in notes)
        pcs = [int(round(p * 2)) % 24 for a, b, p in notes]
        tiempo, bordes, regresos = np.zeros(24), np.zeros(24), np.zeros(24)
        for (a, b, p), c in zip(notes, pcs):
            tiempo[c] += b - a
        T = np.array([n[0] for n in notes])
        for cy in cyc:
            s, e, P = get(cy, 'start'), get(cy, 'end'), get(cy, 'period')
            k = s
            while P > 0 and k + P <= e + 0.05:                                  # una vuelta cada periodo
                i0, i1 = np.searchsorted(T, k - 0.05), np.searchsorted(T, k + P - 0.05)
                if i1 > i0:
                    bordes[pcs[i0]] += 1
                    bordes[pcs[i1 - 1]] += 1
                k += P
        last = {}
        for i, c in enumerate(pcs):
            if c in last and i - last[c] >= 3:                                  # vuelve tras al menos dos notas
                regresos[c] += 1
            last[c] = i
        parts = [x / x.sum() for x in (tiempo, bordes, regresos) if x.sum() > 0]
        return sum(parts) / len(parts) if parts else np.zeros(24)

    sb = layer(raw_bass, cycles.get('Voz grave', []))
    sh = layer(raw_high, cycles.get('Voz aguda', []))
    total = (w_bass * sb + sh) / (w_bass + 1)
    order = np.argsort(-total)
    return dict(centro_pc24=int(order[0]), centro_bajo_pc24=int(sb.argmax()), centro_aguda_pc24=int(sh.argmax()),
                margen=round(float((total[order[0]] - total[order[1]]) / max(total[order[0]], 1e-9)), 3),
                puntaje=np.round(total, 4).tolist())
