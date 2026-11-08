"""**`stem_active`**: Mide cuánto suena la pista guitar durante un ciclo, comparado con su nivel habitual. Los ciclos de la voz aguda en los que la guitarra casi no suena (menos del 20 %) se descartan.
"""

def stem_active(stem, cyc, sr, win=0.5):
    hop = int(win * sr)
    r = np.sqrt(np.mean(stem[:len(stem) // hop * hop].reshape(-1, hop) ** 2, axis=1))
    return np.median(r[int(cyc.start / win):int(cyc.end / win)]) / np.percentile(r, 75)
