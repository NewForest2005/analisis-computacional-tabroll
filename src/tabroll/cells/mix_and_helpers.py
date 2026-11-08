"""**`mix`**, **`lighten`** y **`palette`**: Mezclan dos colores, aclaran un color y generan una paleta de `n` colores a partir de la de Hooktheory.
"""

plt.rcParams["mathtext.fontset"] = "dejavuserif"

BG = "#131215"
GOLD = "#e0a03a"

# Usamos la paleta de color de Hooktheory.com: grados 1, ..., 7
HT_COLORS = ["#9d6229", "#a69837", "#68ac38", "#468fb4", "#832fb6", "#992597", "#992e1f"]
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]


# colores
def mix(c1: str, c2: str, t: float) -> str:
    a, b = to_rgb(c1), to_rgb(c2)
    return to_hex(tuple(x + (y - x) * t for x, y in zip(a, b)))


def lighten(c: str, t: float = 0.3) -> str:
    return mix(c, "#ffffff", t)


def palette(n: int) -> list[str]:
    out = []
    for i in range(n):
        p = i * 7 / n
        k = int(p)
        out.append(mix(HT_COLORS[k % 7], HT_COLORS[(k + 1) % 7], p - k))
    return out
