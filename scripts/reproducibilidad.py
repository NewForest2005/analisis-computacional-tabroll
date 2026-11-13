"""Paso 1 del plan de trabajo: reproducibilidad.

Uso:
    python scripts/reproducibilidad.py
    make extract
    make test

Fija la semilla de Demucs, elimina del cuaderno la guía opcional por `.gp` y quita los presets comentados por canción.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"

SEP_EDITS = (
    ("def separate_stems(audio, kinds=('guitar', 'bass'), model_name='htdemucs_6s'):\n",
     "def separate_stems(audio, kinds=('guitar', 'bass'), model_name='htdemucs_6s', semilla=0):\n"),
    ("    import torch\n    from demucs_infer.pretrained import get_model\n",
     "    import random\n    import torch\n    from demucs_infer.pretrained import get_model\n"),
    ("    with torch.no_grad():\n        out = apply_model(model, wav[None], device=device)[0].cpu()\n",
     "    random.seed(semilla)                                                                  # Demucs desplaza el audio al azar antes de separar:\n"
     "    torch.manual_seed(semilla)                                                            # con la semilla fija, las pistas salen siempre iguales\n"
     "    with torch.no_grad():\n        out = apply_model(model, wav[None], device=device)[0].cpu()\n"),
)
DOC_SEP_OLD = "La primera vez instala demucs-infer y descarga el modelo."
DOC_SEP_NEW = ("La primera vez instala demucs-infer y descarga el modelo. Demucs desplaza el audio una cantidad al azar antes de "
               "separar; con `semilla` fija (0 por defecto), dos separaciones del mismo audio en la misma máquina dan las mismas pistas.")
GP_FLAG = re.compile(r"^GUIAR_CON_GP = .*\n\n?", re.M)
GP_START = "# La línea estructural para ciclos conserva"
GP_END = "no se pudo guiar melody con el GP"
DOC_GP = re.compile(r"Guía opcional con el GP\..*?(?=\n\n|\Z)", re.S)
DOC_GP_NEW = "El `.gp` oficial no interviene en la línea: solo se usa después, en `run_song.py`, para medir."
SELECTOR_OLD = "# entrada pitch-específica para select_melody_track"
SELECTOR_NEW = "# run_song.py la guarda en line_diagnostics.json"
PRESETS = re.compile(r"^# Para [^\n]*\n(?:# [A-Za-z_][^\n]*\n)+\n?", re.M)
DOC_PRESET = re.compile(r" Para Fabienk, \(7, 5, 4, 2\)[^\n]*")
DOC_SET = ("\n\n- Para probar otro valor en una sola corrida, sin tocar el cuaderno: "
           "`python scripts/run_song.py <canción> --set GRID=0.5`.")


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]
    src = lambda c: "".join(c["source"])
    put = lambda c, text: c.__setitem__("source", text.splitlines(keepends=True))
    code = lambda pred: [i for i, c in enumerate(cells) if c["cell_type"] == "code" and pred(src(c))]
    done = []

    sep = code(lambda s: s.startswith("def separate_stems("))
    line = code(lambda s: "melody_n = viterbi_pitch(consenso_n" in s)
    sets = code(lambda s: s.startswith("KEY_OVERRIDE"))
    if not all(len(x) == 1 for x in (sep, line, sets)):
        print("No encontré la celda de separate_stems, la de la línea («2) Altura») o la de ajustes; no cambié nada.")
        return 1

    i = sep[0]
    s = src(cells[i])
    for old, new in SEP_EDITS:
        if new in s:
            continue
        if old not in s:
            print("La celda de separate_stems no tiene el texto que esperaba; no la cambié.")
            return 1
        s = s.replace(old, new)
    if s != src(cells[i]):
        put(cells[i], s)
        md = cells[i - 1]
        if md["cell_type"] == "markdown" and DOC_SEP_NEW not in src(md):
            put(md, src(md).replace(DOC_SEP_OLD, DOC_SEP_NEW))
        done.append("separate_stems con semilla")

    i = line[0]
    s = src(cells[i])
    if "GUIAR_CON_GP" in s or GP_START in s:
        s = GP_FLAG.sub("", s)
        a, b = s.find(GP_START), s.find(GP_END)
        if a < 0 or b < a:
            print("No encontré el principio y el final del bloque del .gp en la celda de la línea; no la cambié.")
            return 1
        b = s.index("\n", b) + 1
        if s[b:b + 1] == "\n":
            b += 1
        s = (s[:a] + s[b:]).replace(SELECTOR_OLD, SELECTOR_NEW)
        if "GUIAR_CON_GP" in s or "reference_files" in s:
            print("Después de quitar el bloque, la celda de la línea todavía nombra el .gp; revísala a mano.")
            return 1
        put(cells[i], s)
        md = cells[i - 1]
        if md["cell_type"] == "markdown":
            put(md, DOC_GP.sub(DOC_GP_NEW, src(md)))
        done.append("la línea sin el bloque del .gp")

    i = sets[0]
    s = src(cells[i])
    if PRESETS.search(s):
        put(cells[i], re.sub(r"\n{3,}", "\n\n", PRESETS.sub("", s)))
        md = cells[i - 1]
        if md["cell_type"] == "markdown" and DOC_SET.strip() not in src(md):
            put(md, DOC_PRESET.sub("", src(md).rstrip("\n")) + DOC_SET)
        done.append("ajustes sin presets por canción")

    if not done:
        print("El cuaderno ya tenía la semilla en Demucs y no nombraba la partitura.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
