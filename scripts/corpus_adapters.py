"""Adaptadores comunes para los corpus de armonía usados por las pruebas de estilo.

Cada adaptador devuelve grados relativos a la tónica, en la misma escala de 12 clases,
además de transiciones entre fundamentales. Los archivos originales permanecen en
``references/corpus/raw`` y no se ejecutan.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "references" / "corpus" / "raw"
GRADOS = ("I", "♭II", "II", "♭III", "III", "IV", "♯IV", "V", "♭VI", "VI", "♭VII", "VII")
ROMAN = {"I": 0, "II": 2, "III": 4, "IV": 5, "V": 7, "VI": 9, "VII": 11}


def _stats(values: list[int]) -> dict:
    counts = Counter(v % 12 for v in values)
    transitions = Counter(zip(values, values[1:]))
    total = sum(counts.values()) or 1
    return {
        "n": len(values),
        "roots": {GRADOS[k]: counts[k] / total for k in range(12)},
        "transitions": {f"{a}:{b}": n for (a, b), n in transitions.items()},
    }


def _roman_value(token: str) -> int | None:
    m = re.fullmatch(r"([b♭#♯]?)(VII|VI|V|IV|III|II|I)(?:\d+)?", token, re.I)
    if not m:
        return None
    value = ROMAN[m.group(2).upper()]
    if m.group(1) in ("b", "♭"):
        value -= 1
    elif m.group(1) in ("#", "♯"):
        value += 1
    return value % 12


def rock() -> dict | None:
    folder = RAW / "rock_corpus_v2-1" / "rs200_harmony"
    values: list[int] = []
    for path in sorted(folder.glob("*_dt.har")):
        for line in path.read_text(encoding="latin-1").splitlines():
            if not line.startswith("Br"):
                continue
            for token in re.findall(r"(?<![A-Za-z])(?:[b♭#♯]?)(?:VII|VI|V|IV|III|II|I)(?:\d+)?", line):
                value = _roman_value(token)
                if value is not None:
                    values.append(value)
    return _stats(values) if values else None


def kostka_payne() -> dict | None:
    path = RAW / "kostka_payne" / "kp-chord-list"
    if not path.exists():
        return None
    values: list[int] = []
    for line in path.read_text(encoding="latin-1").splitlines():
        if not line.strip() or line.startswith("%") or line.startswith("-"):
            continue
        fields = line.split()
        if len(fields) >= 6:
            try:
                values.append(int(fields[3]))
            except ValueError:
                pass
    return _stats(values) if values else None


def _pitch(name: str) -> int | None:
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}.get(name[0].upper())
    if base is None:
        return None
    if len(name) > 1 and name[1] in ("#", "♯"):
        base += 1
    elif len(name) > 1 and name[1] in ("b", "♭", "-"):
        base -= 1
    return base % 12


def irealb() -> dict | None:
    folder = RAW / "irealb-v1.0" / "iRb_v1-0"
    values: list[int] = []
    for path in sorted(folder.glob("*.jazz")):
        tonic = 0
        for line in path.read_text(encoding="latin-1", errors="ignore").splitlines():
            key = re.match(r"\*([A-G](?:#|b|-)?):", line)
            if key:
                tonic = _pitch(key.group(1)) or 0
                continue
            chord = re.match(r"\d+([A-G](?:#|b|-)?)(?::|\s|$)", line)
            if chord:
                root = _pitch(chord.group(1))
                if root is not None:
                    values.append((root - tonic) % 12)
    return _stats(values) if values else None


def load_references() -> dict[str, dict]:
    """Carga los tres corpus disponibles bajo una interfaz común."""
    out = {}
    for name, loader in (("rock", rock), ("classical", kostka_payne), ("jazz", irealb)):
        stats = loader()
        if stats:
            out[name] = stats
    return out


def transition_share(stats: dict | None, interval: int) -> float | None:
    """Proporción de transiciones con un intervalo ascendente de 12-EDO."""
    if not stats:
        return None
    total = sum(stats.get("transitions", {}).values())
    if not total:
        return None
    n = 0
    for pair, count in stats["transitions"].items():
        a, b = (int(x) for x in pair.split(":", 1))
        if (b - a) % 12 == interval % 12:
            n += count
    return n / total
