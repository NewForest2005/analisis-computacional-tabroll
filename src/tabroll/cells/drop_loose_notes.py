"""**`drop_loose_notes`**: Quita las notas cortas, de hasta 3 cuadros (menos de `max_dur` segundos), que no reaparecen a la misma altura una vuelta antes y una vuelta después del ciclo que las contiene. En un ciclo, una nota real vuelve en las vueltas vecinas; un pedazo suelto de `extract_notes` casi nunca. Las notas más largas y las que están fuera de los ciclos no se tocan. `tol` es cuánto puede correrse el ataque entre vueltas.
"""

import numpy as np

def drop_loose_notes(notes, cycles, max_dur=0.08, tol=0.075):
    spans = [c for group in cycles.values() for c in group]
    starts = np.array([n[0] for n in notes], dtype=float)
    pitches = np.array([n[2] for n in notes], dtype=float)

    def returns(t, p):                                                        # ¿hay una nota igual que empieza en t?
        return bool(np.any((np.abs(starts - t) < tol) & (np.abs(pitches - p) < 0.26)))

    kept = []
    for a, b, p in notes:
        cover = [c for c in spans if c.start <= a < c.end]
        if b - a >= max_dur or not cover:
            kept.append((a, b, p))
            continue
        period = max(cover, key=lambda c: c.period).period                    # el ciclo más largo que la contiene
        if returns(a - period, p) and returns(a + period, p):
            kept.append((a, b, p))
    return kept
