"""Ajustes del círculo armónico después del paso 3. Se puede correr más de una vez: lo que ya está aplicado no se toca.

Uso:
    python scripts/ajustar_circulo.py
    make extract

Ajuste 1, compases sin ciclo. En `fundamentales_por_ciclo` cada ciclo distinto del bajo cuenta una vez. Antes, cada
compás sin ciclo contaba también como un ciclo entero: en Mata Zyklek, 30 de sus 33 "ciclos" eran compases sueltos, y
cada uno pesaba lo mismo que el ciclo B, que dura 166 s. Ahora todos los compases sin ciclo forman un solo grupo, que
cuenta como un ciclo más. El círculo dice además qué parte del tiempo confiable queda fuera de los ciclos
(`tiempo_sin_ciclo`), y `ciclos_distintos` cuenta solo los ciclos de verdad.

Ajuste 1b, figura fuera del cuaderno. `draw_harmony_circle` usaba pyplot y dependía de que la celda 2 fijara
`matplotlib.use("Agg")`. Ahora la figura se arma con `matplotlib.figure.Figure`, sin abrir ventanas ni depender del
backend, para que `comparar_circulos.py --actualizar` pueda rehacer figuras ya existentes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"

FIXES = [
    ("harmony_circle", "def harmony_circle(", [
        ("""        grupos.setdefault(b.get('ciclo_bajo') or f"compás {b['compas']}", np.zeros(24))[r] += dur(b)""",
         """        grupos.setdefault(b.get('ciclo_bajo') or SIN_CICLO, np.zeros(24))[r] += dur(b)   # los compases sin ciclo van juntos"""),
        ("""    dur = lambda b: b['fin_s'] - b['inicio_s']\n""",
         """    dur = lambda b: b['fin_s'] - b['inicio_s']\n    SIN_CICLO = 'sin ciclo'\n"""),
        ("""    return dict(formato='tabroll-circulo-24edo-v1',""",
         """    t_ok = sum(dur(b) for b in ok)
    sin_ciclo = float(grupos[SIN_CICLO].sum()) if SIN_CICLO in grupos else 0.0
    return dict(formato='tabroll-circulo-24edo-v2',"""),
        ("""cambios=cambios, ciclos_distintos=len(grupos),""",
         """cambios=cambios, ciclos_distintos=len(set(grupos) - {SIN_CICLO}),
                tiempo_sin_ciclo=round(100 * sin_ciclo / t_ok, 1) if t_ok else 0.0,"""),
    ]),
    ("draw_harmony_circle", "def draw_harmony_circle(", [
        ("    import matplotlib.pyplot as plt\n",
         "    from matplotlib.figure import Figure        # sin pyplot: no abre ventanas ni depende del backend\n"),
        ("    fig, ax = plt.subplots(figsize=(7, 7.8), facecolor=SURF)\n",
         "    fig = Figure(figsize=(7, 7.8), facecolor=SURF)\n    ax = fig.add_subplot()\n"),
        ("    plt.close(fig)\n", ""),
    ]),
    ("la celda que dibuja el círculo", "ruta_circulo = draw_harmony_circle(", [
        ("""f" | {circulo['cambios']} cambios | {circulo['ciclos_distintos']} ciclos distintos")""",
         """f" | {circulo['cambios']} cambios | {circulo['ciclos_distintos']} ciclos distintos"
      f" | {circulo['tiempo_sin_ciclo']:.0f}% del tiempo fuera de ciclos")"""),
    ]),
]
DOC_OLD = "Todo queda normalizado: cada perfil suma 1, y las transiciones también."
DOC_NEW = ("Todo queda normalizado: cada perfil suma 1, y las transiciones también. En `fundamentales_por_ciclo` cada "
           "ciclo distinto del bajo cuenta una vez, y los compases sin ciclo cuentan juntos como un ciclo más.")


def src(c):
    return "".join(c["source"])


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells, done = nb["cells"], []
    for what, marker, pairs in FIXES:
        found = [c for c in cells if c["cell_type"] == "code" and marker in src(c)]
        if len(found) != 1:
            print(f"No encontré {what} (esperaba una celda, hay {len(found)}). Corre antes agregar_armonia_paso3.py.")
            return 1
        c, changed = found[0], False
        for old, new in pairs:
            if old in src(c) and (not new or new not in src(c)):
                c["source"] = src(c).replace(old, new, 1).splitlines(keepends=True)
                changed = True
        done += [what] if changed else []
    for c in cells:
        if c["cell_type"] == "markdown" and src(c).startswith("**`harmony_circle`**") and DOC_NEW not in src(c):
            c["source"] = src(c).replace(DOC_OLD, DOC_NEW).splitlines(keepends=True)
            done.append("la descripción de harmony_circle")
    if not done:
        print("El cuaderno ya tenía los ajustes.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Ajustes aplicados en: " + ", ".join(done) + ".\nAhora corre: make extract")
    return 0


if __name__ == "__main__":
    sys.exit(main())

