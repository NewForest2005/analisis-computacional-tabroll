"""Limpieza de notas sueltas en las dos voces. Se puede correr más de una vez: lo que ya está aplicado no se toca.

Uso:
    python scripts/limpiar_notas.py
    make extract
    make test

`extract_notes` corta una nota nueva en cada ataque y en cada cambio de altura, y deja muchos pedazos de menos de 80 ms
que no son notas de la partitura. En los tramos con ciclo, una nota real vuelve a la misma altura una vuelta antes y
una después; un pedazo suelto casi nunca. Cambios:

1. Celda nueva `drop_loose_notes`, después de `extract_notes`: quita las notas de hasta 3 cuadros (menos de 80 ms) que
   no reaparecen en las dos vueltas vecinas del ciclo. Las notas más largas y las que están fuera de los ciclos no se
   tocan.
2. La celda que saca las notas la aplica a la voz grave y a la voz aguda, y dice cuántas quitó.

Medido sobre las corridas del paso 3, contra las partituras corregidas:
    melodía principal  Mata Zyklek 63.7 → 66.8   Sarniezz 43.4 → 46.2   Fabienk 44.0 → 45.4
    bajo               Mata Zyklek 78.7 → 82.9   Sarniezz 75.3 → 78.7   Fabienk 63.8 → 69.3
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
MARKER = "**`drop_loose_notes`**"

DOC = ("**`drop_loose_notes`**: Quita las notas cortas, de hasta 3 cuadros (menos de `max_dur` segundos), que no "
       "reaparecen a la misma altura una vuelta antes y una vuelta después del ciclo que las contiene. En un ciclo, una "
       "nota real vuelve en las vueltas vecinas; un pedazo suelto de `extract_notes` casi nunca. Las notas más largas y "
       "las que están fuera de los ciclos no se tocan. `tol` es cuánto puede correrse el ataque entre vueltas.")

CODE = '''import numpy as np

def drop_loose_notes(notes, cycles, max_dur=0.08, tol=0.075):
    spans = [c for group in cycles.values() for c in group]
    starts = np.array([n[0] for n in notes], dtype=float)
    pitches = np.array([n[2] for n in notes], dtype=float)

    def returns(t, p):                                                        # ¿hay una nota igual que empieza en t?
        return bool(np.any((np.abs(starts - t) < tol) & (np.abs(pitches - p) < 0.26)))

    kept = []
    for a, b, p in notes:
        cover = [c for c in spans if c.start <= a < c.end]
        if b - a >= max_dur or not cover:
            kept.append((a, b, p))
            continue
        period = max(cover, key=lambda c: c.period).period                    # el ciclo más largo que la contiene
        if returns(a - period, p) and returns(a + period, p):
            kept.append((a, b, p))
    return kept'''

OLD_RUN = "raw_high = extract_notes(np.where(gate_h, melody_n, np.nan), Snote, onsets_h, sr, HOP_P, off, MICRO_STEP)\n"
NEW_RUN = (OLD_RUN +
           "n_bass, n_high = len(raw_bass), len(raw_high)\n"
           "raw_bass, raw_high = drop_loose_notes(raw_bass, cycles_n), drop_loose_notes(raw_high, cycles_n)   # pedazos sueltos fuera\n"
           "print(f'Notas sueltas quitadas: {n_bass - len(raw_bass)} en la voz grave y {n_high - len(raw_high)} en la voz aguda')\n")


def _cell(kind: str, text: str) -> dict:
    cell = {"id": uuid.uuid4().hex[:12], "cell_type": kind, "metadata": {}, "source": text.splitlines(keepends=True)}
    if kind == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]
    src = lambda c: "".join(c["source"])
    done = []
    ex = [i for i, c in enumerate(cells) if c["cell_type"] == "code" and src(c).startswith("def extract_notes(")]
    run = [c for c in cells if c["cell_type"] == "code" and OLD_RUN in src(c)]
    if len(ex) != 1 or len(run) != 1:
        print("No encontré `extract_notes` o la celda que saca las notas de las dos voces.")
        return 1
    if not any(MARKER in src(c) for c in cells if c["cell_type"] == "markdown"):
        cells[ex[0] + 1:ex[0] + 1] = [_cell("markdown", DOC), _cell("code", CODE)]
        done.append("celda nueva drop_loose_notes")
    if "drop_loose_notes(raw_bass" not in src(run[0]):
        run[0]["source"] = src(run[0]).replace(OLD_RUN, NEW_RUN).splitlines(keepends=True)
        done.append("la celda de notas quita los pedazos sueltos de las dos voces")
    if not done:
        print("El cuaderno ya tenía la limpieza.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())

