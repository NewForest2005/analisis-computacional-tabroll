"""**`detect_key`**: Devuelve `(tónica_pc, modo)`: el conjunto de 7 notas que mejor cubre el histograma, con la clase más tónica como tónica.
"""

def detect_key(h, hb=None):
    best = None

    for t in range(12):
        for name, st in MODES.items():

            cover = h[[(t + s) % 12 for s in st]].sum()
            tonic = h[t] + 0.5 * h[(t + 7) % 12] + 0.3 * h[(t + st[2]) % 12]
            sc = cover + 0.35 * tonic

            if best is None or sc > best[0]:
                best = (sc, t, name)

    if hb is None:
        return best[1], best[2]

    rest = lambda t, st: hb[t] + 0.5 * hb[(t + 7) % 12] + 0.3 * hb[(t + st[2]) % 12]
    notes = {(best[1] + s) % 12 for s in MODES[best[2]]}             # mismas 7 notas: la tónica es donde reposa el bajo
    _, t, name = max((rest(t, st), t, name) for t in notes for name, st in MODES.items() if {(t + s) % 12 for s in st} == notes)

    return t, name
