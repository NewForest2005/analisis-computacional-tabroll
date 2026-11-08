"""Celda 161 del notebook original. Descripcion asociada: **`name_cycles`**: Da la misma letra a los ciclos con las mismas notas y los hace empezar en el mismo punto..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def name_cycles(cycles, min_match=0.6):
    known = []

    for c in sorted(cycles, key=lambda c: c.start):
        for o in known:
            r = max(c.period, o.period) / min(c.period, o.period)

            if abs(r - round(r)) > 0.03:
                continue

            short, long_ = sorted((c.pitch, o.pitch), key=len)   # el ciclo corto se repite hasta medir lo mismo que el largo
            m = len(long_)
            a = np.nan_to_num(short, nan=-99.0)[np.arange(m) % len(short)]

            def match(s):
                x = np.roll(a, s)
                ok = (x > 0) & np.isfinite(long_)
                return np.mean(np.abs(x - long_)[ok] < 0.3) if ok.any() else 0.0

            hits = [match(s) for s in range(m)]

            if max(hits) >= min_match:
                s = int(np.argmax(hits))
                s = s if len(c.pitch) <= len(o.pitch) else -s                                   # empieza en el mismo punto que su primera aparición

                c.label, c.pitch, c.attack = o.label, np.roll(c.pitch, s), np.roll(c.attack, s)
                c.entry -= s * c.period / c.slots

                break
        else:
            c.label = chr(65 + len(known))
            known.append(c)

    return cycles
