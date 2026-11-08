"""**`_rows`**: Ventana vertical de la página: octavas completas que contienen sus notas, mínimo 3 como en Hooktheory.
"""

def _rows(page_notes, prev, extra=3):
    if not page_notes:
        return prev

    r = [_row_of(nt) for nt in page_notes]

    if FINE_ROWS:                                                                # solo las filas que usa la música
        return (int(np.floor(min(r))) - extra, int(np.ceil(max(r))) + extra)

    o_lo, o_hi = int(np.floor(min(r) / _n)), int(np.floor(max(r) / _n))

    while o_hi - o_lo + 1 < 3:
        if (o_lo + o_hi) / 2 > _median_oct: o_lo -= 1
        else: o_hi += 1

    return (o_lo * _n - extra, o_hi * _n + _n - 1 + extra)
