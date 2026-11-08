"""**`_pages`**: Agrupa compases completos en páginas de hasta `BEATS_PER_PAGE` pulsos.
"""

def _pages(ms):
    out, cur, tot = [], [], 0

    for m in ms:
        if cur and tot + m.beats > BEATS_PER_PAGE:
            out.append(cur); cur, tot = [], 0

        cur.append(m); tot += m.beats

    return out + ([cur] if cur else [])
