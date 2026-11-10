"""Armonía en 24-EDO, paso 3: el círculo armónico, su figura y lo que hace falta para compararlo.

Cambios en el cuaderno:
1. Si todavía está `CENTRO = 'auto'` (zip del paso 2 anterior), el centro por defecto pasa a ser la tónica de la celda
   de tonalidad, que coincide con el oído del autor en las cinco canciones.
2. `harmony_layers`: la 3.ª neutra cuenta como intervalo intermedio, igual que la 2.ª neutra; los intervalos neutros van
   todos a «intermedio».
3. Celdas nuevas al final: `harmony_circle`, `draw_harmony_circle` y una celda que calcula el círculo y guarda su figura.
4. `chord24`: el bajo se elige sobre el perfil redondeado, igual que la fundamental, para que un empate entre dos notas
   de bajo se resuelva igual en cualquier máquina.

Uso, desde la raíz del repo (con los pasos 1 y 2 ya aplicados):
    python scripts/agregar_armonia_paso3.py
    make extract
    make test

Se puede correr más de una vez: si un cambio ya está, lo deja como está.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
MARKER = "## Círculo armónico (paso 3)"

OLD_DEFAULT = "CENTRO = 'auto'   # 'auto': medida de centro en 24-EDO | 'cuaderno': la tónica de 12 clases de arriba | o una nota: 'E', 'D+', ..."
NEW_DEFAULT = ("CENTRO = 'cuaderno'   # 'cuaderno': la tónica de la celda de tonalidad (coincide con el oído en las 5 canciones) | "
               "'auto': medida de centro en 24-EDO | o una nota: 'E', 'D+', ...")
OLD_BASS = "alternativa=int(np.argsort(-best)[1]), bajo=int(b.argmax()) if tb > 0 else None,"
NEW_BASS = "alternativa=int(np.argsort(-best)[1]), bajo=int(np.round(b, 9).argmax()) if tb > 0 else None,"
OLD_KINDS = "    kinds = {10: 'fuerte', 6: 'débil', 7: 'débil', 8: 'débil', 2: 'color', 4: 'color', 12: 'color', 1: 'deslizamiento'}"
NEW_KINDS = "    kinds = {10: 'fuerte', 6: 'débil', 8: 'débil', 2: 'color', 4: 'color', 12: 'color', 1: 'deslizamiento'}   # neutros: intermedio"

CELLS = [
    ("markdown", MARKER + """

El círculo es la huella armónica de la canción: 24 posiciones de cuarto de tono contadas desde el centro, con la
tónica arriba. Una canción de 12 tonos ocupa solo las posiciones pares. Cada capa se guarda por separado, para poder
comparar el círculo con el de cualquier otra canción o estilo, de 12 o de 24 tonos:

- **Perfiles.** El perfil del bajo, el de la voz aguda y el de las fundamentales (tiempo × confianza).
- **Fundamentales por ciclo.** Cada ciclo distinto del bajo cuenta una vez, así un riff que dura tres minutos no tapa
  el resto.
- **Transiciones.** Los pasos entre fundamentales.
- **Movimientos y calidades.**
- **Ritmo armónico.** Los cambios de fundamental por compás.

Solo cuentan los compases confiables."""),
    ("markdown", "**`harmony_circle`**: Calcula las capas del círculo armónico a partir de la armonía por compás y del centro. Todo queda normalizado: cada perfil suma 1, y las transiciones también."),
    ("code", """import numpy as np

def harmony_circle(bars, center_pc24, min_conf=0.5):
    names = ['1', '1+', '♭2', '♭2+', '2', '2+', '♭3', '♭3+', '3', '3+', '4', '4+',
             '♯4', '♯4+', '5', '5+', '♭6', '♭6+', '6', '6+', '♭7', '♭7+', '7', '7+']
    kinds = {10: 'fuerte', 6: 'débil', 8: 'débil', 2: 'color', 4: 'color', 12: 'color', 1: 'deslizamiento'}   # neutros: intermedio
    rel = lambda v: np.roll(np.asarray(v, float), -center_pc24)
    norm = lambda v: (v / v.sum()).round(4).tolist() if v.sum() > 0 else [0.0] * 24
    dur = lambda b: b['fin_s'] - b['inicio_s']
    ok = [b for b in bars if b.get('fundamental_pc24') is not None and b.get('confianza', 0) >= min_conf]
    bajo, aguda, fund = np.zeros(24), np.zeros(24), np.zeros(24)
    for b in bars:
        bajo += rel(b['perfil_bajo']) * b.get('confianza', 0)
        aguda += rel(b['perfil_aguda']) * b.get('confianza', 0)
    grupos = {}
    for b in ok:
        r = (b['fundamental_pc24'] - center_pc24) % 24
        fund[r] += dur(b) * b['confianza']
        grupos.setdefault(b.get('ciclo_bajo') or f"compás {b['compas']}", np.zeros(24))[r] += dur(b)
    por_ciclo = sum((g / g.sum() for g in grupos.values()), np.zeros(24))
    trans = np.zeros((24, 24))
    mov = dict.fromkeys(['fuerte', 'débil', 'color', 'deslizamiento', 'intermedio'], 0.0)
    by = {b['compas']: b for b in ok}
    pares = cambios = 0
    for k, b in by.items():
        a = by.get(k - 1)
        if a is None:
            continue
        pares += 1
        r0, r1 = (a['fundamental_pc24'] - center_pc24) % 24, (b['fundamental_pc24'] - center_pc24) % 24
        if r0 != r1:
            cambios += 1
            trans[r0, r1] += 1
            mov[kinds.get(min((r1 - r0) % 24, (r0 - r1) % 24), 'intermedio')] += 1
    cal = {}
    for b in ok:
        cal[b['calidad']] = cal.get(b['calidad'], 0.0) + dur(b)
    total = sum(dur(b) for b in bars) or 1.0
    return dict(formato='tabroll-circulo-24edo-v1', centro_pc24=int(center_pc24), posiciones=names,
                perfil_bajo=norm(bajo), perfil_aguda=norm(aguda), fundamentales=norm(fund), fundamentales_por_ciclo=norm(por_ciclo),
                transiciones=(trans / max(trans.sum(), 1)).round(4).tolist(),
                movimientos={k: round(v / max(cambios, 1), 3) for k, v in mov.items()},
                calidades={k: round(v / (sum(cal.values()) or 1), 3) for k, v in sorted(cal.items(), key=lambda kv: -kv[1])},
                cambios_por_compas=round(cambios / max(pares, 1), 3), cambios=cambios, ciclos_distintos=len(grupos),
                tiempo_confiable=round(100 * sum(dur(b) for b in ok) / total, 1))"""),
    ("markdown", "**`draw_harmony_circle`**: Dibuja el círculo con la tónica arriba.\n\n"
     "- **Hacia afuera (azul):** las fundamentales.\n"
     "- **Hacia adentro (naranja):** el perfil del bajo.\n"
     "- **Arcos grises:** los cambios de fundamental; el grosor indica cuántas veces ocurren.\n\n"
     "Las posiciones de cuarto de tono van en gris claro."),
    ("code", """import numpy as np
from pathlib import Path

def draw_harmony_circle(circle, path, title=None):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.patches import Circle, Patch, PathPatch, Wedge
    from matplotlib.path import Path as MPath
    INK, MUTED, GRID, SURF = '#0b0b0b', '#898781', '#e1e0d9', '#fcfcfb'
    ROOT, BASS, TRANS = '#2a78d6', '#eb6834', '#52514e'
    ang = lambda k: np.pi / 2 - 2 * np.pi * k / 24                          # tónica arriba, en el sentido del reloj
    f, b = np.asarray(circle['fundamentales']), np.asarray(circle['perfil_bajo'])
    fm, bm = max(f.max(), 1e-9), max(b.max(), 1e-9)
    fig, ax = plt.subplots(figsize=(7, 7.8), facecolor=SURF)
    ax.set_facecolor(SURF)
    ax.add_patch(Circle((0, 0), 1.0, fill=False, lw=1, color=GRID))
    for k in range(24):
        a, w = np.degrees(ang(k)), 360 / 24 - 2.5                            # 2.5° de separación entre cuñas
        if f[k] > 0:
            ax.add_patch(Wedge((0, 0), 1.0 + 0.45 * f[k] / fm, a - w / 2, a + w / 2, width=0.45 * f[k] / fm, color=ROOT, lw=0))
        if b[k] > 0:
            ax.add_patch(Wedge((0, 0), 1.0, a - w / 2, a + w / 2, width=0.35 * b[k] / bm, color=BASS, lw=0))
        ax.text(1.62 * np.cos(ang(k)), 1.62 * np.sin(ang(k)), circle['posiciones'][k], ha='center', va='center',
                fontsize=10 if k % 2 == 0 else 8, color=INK if k % 2 == 0 else MUTED)
    T = np.asarray(circle['transiciones'])
    if T.max() > 0:
        for i, j in zip(*np.nonzero(T)):
            p0 = 0.6 * np.array([np.cos(ang(i)), np.sin(ang(i))])
            p1 = 0.6 * np.array([np.cos(ang(j)), np.sin(ang(j))])
            ax.add_patch(PathPatch(MPath([p0, 0.25 * (p0 + p1), p1], [MPath.MOVETO, MPath.CURVE3, MPath.CURVE3]), fill=False,
                                   color=TRANS, lw=0.5 + 3.5 * T[i, j] / T.max(), alpha=0.35 + 0.5 * T[i, j] / T.max()))
    ax.set_xlim(-1.9, 1.9)
    ax.set_ylim(-2.05, 1.95)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(title or f"Círculo armónico: {circle.get('cancion', '')}", color=INK, fontsize=13, loc='left')
    mov = ', '.join(f'{k} {round(100 * v)}%' for k, v in circle['movimientos'].items() if v > 0) or 'sin cambios'
    ax.text(-1.9, -1.98, f"Centro {circle.get('centro', '')} | modo {circle.get('modo', '')} | confiable {circle['tiempo_confiable']}% del tiempo\\n"
                         f"Movimientos: {mov} | cambios por compás {circle['cambios_por_compas']}", fontsize=8.5, color='#52514e', va='bottom')
    ax.legend(handles=[Patch(color=ROOT, label='Fundamentales'), Patch(color=BASS, label='Bajo'),
                       Line2D([], [], color=TRANS, lw=2, label='Cambios de fundamental')],
              loc='upper right', bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=8.5, labelcolor=INK)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=SURF)
    plt.close(fig)
    return Path(path)"""),
    ("markdown", "Círculo armónico de la canción (`circulo`) y su figura `circulo_armonico.png` en la carpeta de imágenes. `run_song.py` guarda el círculo en `circulo.json`."),
    ("code", """circulo = harmony_circle(armonia, tonic_pc24)
circulo.update(cancion=audio_path.stem, centro=PC24_NAMES[tonic_pc24], modo=armonia_resumen['modo']['nombre'])
ruta_circulo = draw_harmony_circle(circulo, OUTPUT_DIR / 'circulo_armonico.png')
fuertes = sorted(zip(circulo['posiciones'], circulo['fundamentales']), key=lambda kv: -kv[1])[:4]
print(f"Círculo armónico: {ruta_circulo.name} | fundamentales: " + ', '.join(f'{g} {100 * v:.0f}%' for g, v in fuertes if v > 0) +
      f" | {circulo['cambios']} cambios | {circulo['ciclos_distintos']} ciclos distintos")"""),
]


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
    run = [c for c in cells if c["cell_type"] == "code" and "center24_by_layer(raw_bass" in src(c)]
    lay = [c for c in cells if c["cell_type"] == "code" and "def harmony_layers(" in src(c)]
    if not run or not lay:
        print("No encontré las celdas del paso 2: aplica primero scripts/agregar_armonia_paso2.py.")
        return 1
    if OLD_DEFAULT in src(run[0]):
        run[0]["source"] = src(run[0]).replace(OLD_DEFAULT, NEW_DEFAULT).splitlines(keepends=True)
        done.append("centro por defecto: la tónica de la celda de tonalidad")
    if OLD_KINDS in src(lay[0]):
        lay[0]["source"] = src(lay[0]).replace(OLD_KINDS, NEW_KINDS).splitlines(keepends=True)
        done.append("harmony_layers: los intervalos neutros cuentan como intermedios")
    for c in cells:
        if c["cell_type"] == "code" and "def chord24(" in src(c) and OLD_BASS in src(c):
            c["source"] = src(c).replace(OLD_BASS, NEW_BASS).splitlines(keepends=True)
            done.append("chord24: el bajo se redondea antes de elegirlo, como la fundamental (empates iguales en cualquier máquina)")
    if any(MARKER in src(c) for c in cells if c["cell_type"] == "markdown"):
        done.append("círculo: las celdas ya estaban")
    else:
        cells.extend(_cell(k, t) for k, t in CELLS)
        done.append("círculo: harmony_circle, draw_harmony_circle y la celda de ejecución agregadas al final")
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("\n".join(done))
    print("Ahora: make extract && make test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

