"""Celda 29 del notebook original. Descripcion asociada: Etiquetado de acordes.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

_THIRDS = {"sus2": 200, "min": 300, "neu": 350, "maj": 400, "sus4": 500}
_FIFTHS = {"dim": 600, "perf": 700, "aug": 800}
_SEVENTHS = {"h7": 969, "7": 1000, "M7": 1100}
_DYADS = {100: "m2", 150: "n2", 200: "2", 300: "m3", 350: "n3", 400: "3", 500: "4", 600: "tt",
          700: "5", 800: "m6", 850: "n6", 900: "6", 1000: "m7", 1050: "n7", 1100: "7"}


def _closest(rel: Sequence[float], table: dict, lo: float, hi: float, tol: float):
    best = None

    for v in rel:
        if lo <= v <= hi:
            for kind, c in table.items():
                d = abs(v - c)
                if d <= tol and (best is None or d < best[0]):
                    best = (d, kind)

    return best[1] if best else None



def label_chord(ch: Chord, sc: Scale, tol: float = 35.0) -> tuple[str, str]:
    root = ch.tones[0]
    base, acc = sc.spell(root)
    deg = base % sc.n

    rn = ROMAN[deg] if sc.n <= len(ROMAN) else str(deg + 1)
    rname = sc.degree_name(deg) + acc
    third = fifth = seventh = None

    if abs(sc.period - 1200) < 1:
        rel = sorted((t - root) % sc.period for t in ch.tones[1:])
        third = _closest(rel, _THIRDS, 150, 540, tol)
        fifth = _closest(rel, _FIFTHS, 550, 850, tol)
        seventh = _closest(rel, _SEVENTHS, 900, 1150, tol)

    lower = third == "min"
    sub = third if third in ("sus2", "sus4") else ""
    sup = ("°" if fifth == "dim" else "+" if fifth == "aug" else "") \
        + ("n" if third == "neu" else "") + (seventh or "")

    numeral = acc + (rn.lower() if lower else rn)
    numeral += f"_{{{sub}}}" if sub else ""
    numeral += f"^{{{sup}}}" if sup else ""

    if len(ch.tones) == 2 and abs(sc.period - 1200) < 1:                   # díada: se nombra por su intervalo
        iv = rel[0]
        kind = min(_DYADS, key=lambda c: abs(c - iv))
        kind = _DYADS[kind] if abs(kind - iv) <= tol else f"{iv:.0f}c"
        return f"{acc}{rn}_{{{kind}}}", f"{rname}_{{{kind}}}"

    name = rname
    name += "m" if third == "min" and fifth != "dim" else ""
    name += "°" if fifth == "dim" else "+" if fifth == "aug" else ""
    name += (f"_{{{sub}}}" if sub else "") + (f"^{{{seventh}}}" if seventh else "")

    return numeral, name

def _plain_len(s: str) -> float:
    sup = re.findall(r"[_^]\{([^}]*)\}", s)

    return len(re.sub(r"[_^]\{[^}]*\}", "", s)) + 0.55 * sum(len(x) for x in sup)


def _mathtext(s: str) -> str:
    return s if "$" in s else "$\\mathrm{" + s + "}$"
