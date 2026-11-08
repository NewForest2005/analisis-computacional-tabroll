"""**`cycle_subdivision`**: Elige en cuántas casillas se divide el pulso de la canción.
"""

def cycle_subdivision(line, offset, cycles, sr, hop, beat, options=(1, 2, 3, 4, 6), keep=0.75):
    fit = np.zeros(len(options))
    total = 0

    for c in cycles:
        phi = note_changes(line, offset, c, sr, hop)
        total += len(phi)
        for i, s in enumerate(options):
            fit[i] += np.abs(np.exp(2j * np.pi * phi * round(c.period / beat * 2) / 2 * s).sum())

    if total == 0:
        return options[0]

    return options[int(np.argmax(fit >= keep * fit.max()))]             # el grid más grueso que explica los cambios
