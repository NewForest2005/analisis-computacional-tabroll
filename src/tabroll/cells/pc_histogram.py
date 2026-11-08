"""**`pc_histogram`**: Histograma de 12 clases de altura; una nota de cuarto de tono se reparte entre sus dos vecinas.
"""

def pc_histogram(pitches, weights):
    h = np.zeros(12)

    for p, w in zip(pitches, weights):
        lo = int(np.floor(p))
        fr = p - lo
        h[lo % 12] += w * (1 - fr)
        h[(lo + 1) % 12] += w * fr

    return h / max(h.sum(), 1e-9)
