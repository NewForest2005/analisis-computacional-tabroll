"""**`drop_echoes`**: Limpia las líneas adicionales; quita las notas que ya aparecen en las líneas anteriores dentro de ±`near` fotogramas, porque suelen ser restos de la ventana de análisis, y las que duran menos de `min_frames` fotogramas.
"""

def drop_echoes(lines, offset, near=9, min_frames=3):
    T = len(lines[0])
    pcs = [np.where(np.isfinite(l), np.round((np.nan_to_num(l) - offset) * 2).astype(int) % 24, -1) for l in lines]
    out = [lines[0]]
    seen = np.zeros((24, T), bool)
    t = np.flatnonzero(pcs[0] >= 0)
    seen[pcs[0][t], t] = True

    for p, l in zip(pcs[1:], lines[1:]):
        block = maximum_filter1d(seen.astype(np.uint8), size=2 * near + 1, axis=1) > 0
        block = block | np.roll(block, 1, axis=0) | np.roll(block, -1, axis=0)            # tolerancia de un cuarto de tono

        ok = p >= 0
        ok[ok] &= ~block[p[ok], np.flatnonzero(ok)]

        i = 0
        while i < T:                                                                      # debe sostenerse varios fotogramas
            j = i
            if ok[i]:
                while j + 1 < T and ok[j + 1] and p[j + 1] == p[i]:
                    j += 1
                if j - i + 1 < min_frames:
                    ok[i:j + 1] = False
            i = j + 1

        out.append(np.where(ok, l, np.nan))
        t = np.flatnonzero(ok)
        seen[p[t], t] = True

    return out
