"""**`parse_scl`**: Lee un archivo Scala `.scl` y devuelve `(alturas en cents desde 0.0, periodo en cents)`.
"""

def parse_scl(text: str) -> tuple[list[float], float]:
    lines = [l.strip() for l in text.splitlines() if not l.lstrip().startswith("!")]
    count = int(lines[1].split()[0])
    cents = [0.0]

    for item in lines[2:2 + count]:
        tok = item.split()[0]

        if "." in tok:
            cents.append(float(tok))

        elif "/" in tok:
            a, b = tok.split("/")
            cents.append(1200 * math.log2(int(a) / int(b)))

        else:
            cents.append(1200 * math.log2(int(tok)))

    period = cents.pop()

    return cents, period
