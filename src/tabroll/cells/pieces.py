"""**`pieces`**: Divide un evento en las barras de compás y devuelve `[(inicio, fin), ...]`, un tramo por cada compás que toca.
"""

def pieces(onset: float, dur: float, measures: Sequence[Measure]) -> list[tuple[float, float]]:

    end, out = onset + dur, []
    for m in measures:
        a, b = max(onset, m.start), min(end, m.start + m.beats)
        if b - a > 1e-9:
            out.append((a, b))
    return out
