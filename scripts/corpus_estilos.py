"""Pasa los corpus de estilo a un formato común: por pieza, el reparto de las fundamentales en 12 grados respecto de la
tónica (ponderado por duración) y la lista de cambios de fundamental. Solo se usa para comparar.

Uso:
    python scripts/corpus_estilos.py            # escribe references/corpus/estilos_por_pieza.json

Corpus (en references/corpus/raw/):
- rock: Rolling Stone 200 (de Clercq y Temperley), rs200_harmony/*.har. Cada canción la anotaron dos analistas (dt y
  tdc); se usan las dos y cada una pesa la mitad. Un compás vale 1 y se reparte entre los acordes que tiene; «.» alarga el
  acorde anterior y un compás vacío también. Los numerales ya son relativos a la tonalidad del momento.
- clasica: Kostka-Payne (Temperley 2009), kp-chord-list-2 (con el 6/4 cadencial reanalizado). Columna 4: fundamental
  relativa a la tónica; duración = fin − inicio.
- jazz: iRealPro (Shanahan y Broze), iRb_v1-0/*.jazz, formato Humdrum **jazz. La tonalidad va en «*G:» («*g:» si es menor)
  y puede cambiar; la duración es la figura (2. = blanca con puntillo, etc.).
- pop: los 9 álbumes de Hooktheory (albumes_progresiones.csv): un bucle por tema, cada acorde vale 1.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "references" / "corpus" / "raw"
ROM = {"I": 0, "II": 2, "III": 4, "IV": 5, "V": 7, "VI": 9, "VII": 11}
LETRA = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def raiz_romana(tok: str, menor: bool = False) -> int | None:
    """Fundamental (0-11) de un numeral como «bVII», «V7/vi», «#iv°»; None si no es un acorde."""
    partes = tok.split("/")
    total = 0
    for k, p in enumerate(reversed(partes)):
        m = re.match(r"([#b♭♯]*)([ivIV]+)", p)
        if not m or m.group(2).upper() not in ROM:
            return None
        r = ROM[m.group(2).upper()] + sum(-1 if c in "b♭" else 1 for c in m.group(1))
        if menor and k == 0 and not m.group(1) and m.group(2).upper() in ("III", "VI", "VII"):
            r -= 1
        total += r
    return total % 12


def leer_har(path: Path) -> list[tuple[int, float]]:
    """(fundamental, duración en compases) de un archivo .har del RS 200, en orden."""
    defs = {}
    for linea in path.read_text(encoding="latin-1").splitlines():
        linea = linea.split("%")[0].strip()
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", linea)
        if m:
            defs[m.group(1)] = m.group(2)

    def expandir(texto: str, prof: int = 0) -> list[str]:
        out = []
        for tok in texto.split():
            m = re.fullmatch(r"\$([A-Za-z0-9_]+)(?:\*(\d+))?", tok)
            if m and prof < 20:
                sub = expandir(defs.get(m.group(1), ""), prof + 1)
                out += sub * int(m.group(2) or 1)
            else:
                out.append(tok)
        return out

    toks = expandir(defs.get("S", ""))
    compases, actual = [], []
    for tok in toks:
        m = re.fullmatch(r"\|(?:\*(\d+))?", tok)
        if m:
            compases.append(actual)
            for _ in range(int(m.group(1) or 1) - 1):
                compases.append(list(actual))
            actual = []
        elif tok.startswith("["):
            continue
        else:
            actual.append(tok)
    if actual:
        compases.append(actual)
    out, prev = [], None
    for c in compases:
        if not c:
            if prev is not None:
                out.append((prev, 1.0))
            continue
        w = 1.0 / len(c)
        for tok in c:
            if tok == ".":
                r = prev
            elif tok.upper().startswith("R"):
                prev = None
                continue
            else:
                r = raiz_romana(tok)
            if r is not None:
                out.append((r, w))
                prev = r
    return out


def leer_jazz(path: Path) -> list[tuple[int, float]]:
    out, ton = [], None
    for linea in path.read_text(encoding="latin-1").splitlines():
        m = re.fullmatch(r"\*([A-Ga-g])([#-]*):.*", linea.strip())
        if m:
            ton = (LETRA[m.group(1).upper()] + m.group(2).count("#") - m.group(2).count("-")) % 12
            continue
        m = re.match(r"^(\d+)(\.*)([A-G])([#-]*)", linea.strip())
        if m and ton is not None:
            d = 1.0 / int(m.group(1)) if int(m.group(1)) else 2.0
            d *= 1.5 ** len(m.group(2))
            r = (LETRA[m.group(3)] + m.group(4).count("#") - m.group(4).count("-") - ton) % 12
            out.append((r, d))
    return out


def leer_kp(path: Path) -> dict[str, list[tuple[int, float]]]:
    piezas, nombre = {}, None
    for linea in path.read_text(encoding="latin-1").splitlines():
        if linea.startswith("%"):
            nombre = linea[1:].strip()
            piezas[nombre] = []
            continue
        c = linea.split()
        if len(c) >= 7 and nombre:
            piezas[nombre].append((int(c[3]) % 12, float(c[1]) - float(c[0])))
    return piezas


def leer_pop(path: Path) -> dict[str, list[tuple[int, float]]]:
    piezas = {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            seq = [raiz_romana(b.split("/")[0] if "/" not in b.split()[0] else b, r["modo"] == "menor") for b in r["acordes_base"].split()]
            seq = [x for x in seq if x is not None]
            if seq:
                piezas[f"{r['artista']} – {r['tema']}" if "tema" in r else f"{r['artista']} {len(piezas)}"] = [(x, 1.0) for x in seq]
    return piezas


def resumen(seq: list[tuple[int, float]]) -> dict:
    """Reparto de fundamentales (12) y cambios de fundamental (de, a) de una secuencia."""
    dist = [0.0] * 12
    for r, d in seq:
        dist[r] += d
    s = sum(dist) or 1.0
    cambios = []
    prev = None
    for r, d in seq:
        if prev is not None and r != prev:
            cambios.append((prev, r))
        prev = r
    return dict(fundamentales=[round(x / s, 5) for x in dist], cambios=cambios)


def main() -> None:
    corpus = {"rock": {}, "clasica": {}, "jazz": {}, "pop": {}}
    for f in sorted((RAW / "rock_corpus_v2-1" / "rs200_harmony").glob("*.har")):
        seq = leer_har(f)
        if len(seq) >= 4:
            corpus["rock"][f.stem] = resumen(seq)
    for nombre, seq in leer_kp(RAW / "kostka_payne" / "kp-chord-list-2").items():
        if len(seq) >= 4:
            corpus["clasica"][nombre] = resumen(seq)
    for f in sorted((RAW / "irealb-v1.0" / "iRb_v1-0").glob("*.jazz")):
        seq = leer_jazz(f)
        if len(seq) >= 4:
            corpus["jazz"][f.stem] = resumen(seq)
    pop = RAIZ / "references" / "corpus" / "albumes_progresiones.csv"
    if pop.exists():
        for k, seq in leer_pop(pop).items():
            corpus["pop"][k] = resumen(seq)
    dest = RAIZ / "references" / "corpus" / "estilos_por_pieza.json"
    dest.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    for k, v in corpus.items():
        tot = [0.0] * 12
        for p in v.values():
            tot = [a + b for a, b in zip(tot, p["fundamentales"])]
        s = sum(tot) or 1
        print(f"{k}: {len(v)} piezas · fundamentales " + " ".join(f"{g}:{100 * x / s:.1f}" for g, x in zip(
            ["I", "♭II", "II", "♭III", "III", "IV", "♯IV", "V", "♭VI", "VI", "♭VII", "VII"], tot) if 100 * x / s >= 1))
    print(f"→ {dest}")


if __name__ == "__main__":
    main()
