"""Pasos H1c y H2 del análisis armónico: progresiones en dos resúmenes y tabroll con la armonía en 24-EDO.

Uso:
    python scripts/tabroll_armonia24.py
    make extract
    make test

Cambios en el cuaderno:
1. `chord_progressions` da dos resúmenes, uno al lado del otro: solo los compases confiables y todos los compases. Las
   columnas de cada compás (`progresion`, `movimiento`, `uso_piston`) siguen saliendo de los confiables.
2. La celda de armonía imprime los dos resúmenes.
3. `Chord` tiene `annot_color`; `render` escribe la anotación de cada acorde más grande y en ese color;
   `render_song_graphic` acepta otra lista de acordes (`chords`).
4. Al final del cuaderno: la celda `harmony_labels` (cifrado con bajo cifrado, nombre con barra, función y color de cada
   compás) y la celda que dibuja el tabroll con esa armonía: `tabroll24_pNN.png` y `tabroll24_completo.png`.
Se puede correr más de una vez: lo que ya está aplicado no se toca.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"

DOC_PROG = ("**`chord_progressions`**: Progresiones entre compases, en cada cambio de fundamental. Para cada uno: la "
            "progresión («♭III → ♭VII»), el movimiento de la fundamental según Piston (pp. 22-24: quinta abajo, como V-I, "
            "la más fuerte; quinta arriba, como IV-I; tercera abajo; tercera arriba, la más débil; segunda; tritono; o "
            "microtonal) y qué tan usual es según su tabla de progresiones (pp. 21-22), leída por número de grado (♭VII "
            "como VII). Con `menor` se agregan los añadidos de Piston para el modo menor (p. 45). Da dos resúmenes, uno al "
            "lado del otro: `confiables` (compases con confianza ≥ `min_conf`) y `todos` (todos los compases con acorde). "
            "Cada uno dice qué parte de los cambios va por quintas, las progresiones más frecuentes, las progresiones con "
            "nombre (cadencias y progresiones conocidas, por sus fundamentales) y los vaivenes entre dos acordes. Las "
            "columnas de cada compás salen de los confiables.")

CODE_PROG = '''from collections import Counter

DIATONICO = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 7: 5, 8: 6, 9: 6, 10: 7, 11: 7}      # el ♯IV (6) no tiene grado diatónico
PISTON = {1: ({4, 5}, {6}, {2, 3}), 2: ({5}, {4, 6}, {1, 3}), 3: ({6}, {4}, {1, 2, 5}), 4: ({5}, {1, 2}, {3, 6}),
          5: ({1}, {4, 6}, {2, 3}), 6: ({2, 5}, {3, 4}, {1}), 7: ({1, 3}, {6}, {2, 4, 5})}
USOS = ('usual', 'a veces', 'menos a menudo')
MOVIMIENTOS = {5: 'quinta abajo (como V-I)', 7: 'quinta arriba (como IV-I)', 8: 'tercera abajo', 9: 'tercera abajo',
               3: 'tercera arriba', 4: 'tercera arriba', 1: 'segunda', 2: 'segunda', 10: 'segunda', 11: 'segunda',
               6: 'tritono'}
CON_NOMBRE = {   # semitonos de cada fundamental sobre el centro
    'cadencia auténtica V-I': (7, 0), 'cadencia plagal IV-I': (5, 0), 'cadencia rota V-VI': (7, 9),
    'cadencia rota V-♭VI': (7, 8), 'cadencia modal ♭VII-I': (10, 0), 'cadencia eólica ♭VI-♭VII-I': (8, 10, 0),
    'cadencia andaluza i-♭VII-♭VI-V': (0, 10, 8, 7), 'II-V-I': (2, 7, 0), 'I-IV-V': (0, 5, 7), 'IV-V-I': (5, 7, 0),
    'I-V-vi-IV': (0, 7, 9, 5), 'I-vi-IV-V': (0, 9, 5, 7), 'vi-IV-I-V': (9, 5, 0, 7),
    'i-♭VI-♭III-♭VII': (0, 8, 3, 10), 'círculo de quintas vi-ii-V-I': (9, 2, 7, 0)}


def chord_progressions(armonia, menor=False, min_conf=0.5):
    def uso(d0, d1):                                                   # qué tan usual es d0 → d1 en la tabla de Piston
        a, b = DIATONICO.get(d0), DIATONICO.get(d1)
        if a is None or b is None:
            return 'fuera de la tabla'
        fila = PISTON[a]
        if menor:                                                      # añadidos de Piston para el modo menor (p. 45)
            if a in (1, 3):
                fila = (fila[0] | {7}, fila[1], fila[2])
            elif a == 7:
                fila = ({3}, {6}, {4}) if d0 == 10 else ({1}, set(), set())
        for nombre, grupo in zip(USOS, fila):
            if b in grupo:
                return nombre
        return 'fuera de la tabla'

    def recorrido(umbral):                                             # cambios entre los compases con confianza ≥ umbral
        seq, marcas = [], {}                                           # seq: (fila, grado en cuartos de tono, cifrado)
        usados = 0
        for i, r in enumerate(armonia):
            if r.get('cifrado') is None or r.get('grado24') is None or (r.get('confianza') or 0) < umbral:
                continue
            usados += 1
            q = r['grado24']
            if seq and seq[-1][1] == q:                                # misma fundamental: no hay cambio
                continue
            if seq:
                q0 = seq[-1][1]
                prog = f'{seq[-1][2]} → {r["cifrado"]}'
                if q0 % 2 or q % 2:
                    marcas[i] = (prog, 'microtonal', 'fuera de la tabla')
                else:
                    marcas[i] = (prog, MOVIMIENTOS[(q // 2 - q0 // 2) % 12], uso(q0 // 2, q // 2))
            seq.append((i, q, r['cifrado']))

        cambios = list(marcas.values())
        n = len(cambios) or 1
        share = lambda k: {key: round(100.0 * v / n, 1) for key, v in Counter(c[k] for c in cambios).most_common()}
        grados = [q for _, q, _ in seq]
        con_nombre = {}
        for name, pat in CON_NOMBRE.items():
            p24 = [2 * x for x in pat]
            hits = [seq[k][0] for k in range(len(seq) - len(p24) + 1) if grados[k:k + len(p24)] == p24]
            if hits:
                con_nombre[name] = dict(veces=len(hits), compases=[armonia[i]['compas'] for i in hits[:10]])
        vaiven = Counter()
        for k in range(len(seq) - 3):
            if grados[k] == grados[k + 2] and grados[k + 1] == grados[k + 3]:
                vaiven[' ↔ '.join(sorted((seq[k][2], seq[k + 1][2])))] += 1
        quintas = sum(1 for c in cambios if c[1].startswith('quinta'))
        frecuentes = [[p, c] for p, c in Counter(c[0] for c in cambios).most_common(8)]
        return marcas, dict(umbral=umbral, compases=usados, cambios=len(cambios), por_quintas=round(100.0 * quintas / n, 1),
                            movimientos=share(1), uso_piston=share(2), frecuentes=frecuentes, con_nombre=con_nombre,
                            vaivenes=dict(vaiven.most_common(5)))

    marcas, confiables = recorrido(min_conf)
    _, todos = recorrido(0.0)
    out = []
    for i, r in enumerate(armonia):
        prog, mov, usual = marcas.get(i, (None, None, None))
        out.append(dict(r, progresion=prog, movimiento=mov, uso_piston=usual))
    return out, dict(confiables=confiables, todos=todos)'''

OLD_TAIL_START = "modo_menor = '♭3' in"
TAIL = '''modo_menor = '♭3' in [x.strip() for x in armonia_resumen['modo']['nombre'].split(',')]
armonia, armonia_resumen['progresiones'] = chord_progressions(armonia, menor=modo_menor)
print('         grados: ' + ', '.join(f'{k} {v:.0f}%' for k, v in list(fx['nombres_grado'].items())[:5]))
for clave, titulo in (('confiables', 'compases confiables'), ('todos', 'todos los compases')):
    pr = armonia_resumen['progresiones'][clave]
    print(f"         progresiones, {titulo} ({pr['compases']}): {pr['cambios']} cambios, {pr['por_quintas']:.0f}% por quintas | "
          'tabla de Piston: ' + ', '.join(f'{k} {v:.0f}%' for k, v in pr['uso_piston'].items()))
    print('           más frecuentes: ' + ', '.join(f'{p} ×{n}' for p, n in pr['frecuentes'][:5]))
    nombradas = [f"{k} ×{v['veces']}" for k, v in pr['con_nombre'].items()] + [f'vaivén {k} ×{v}' for k, v in pr['vaivenes'].items()]
    if nombradas:
        print('           con nombre: ' + ', '.join(nombradas))
'''

OLD_CHORD = "    annot: Optional[str] = None\n"
NEW_CHORD = "    annot: Optional[str] = None\n    annot_color: Optional[str] = None\n"

OLD_RENDER = '''            cx, cy = (x0 + x1) / 2, strip_top + st.strip_h / 2
            fs = max(6.5, min(26.0, 0.95 * w / max(_plain_len(numeral), 1)))
            ax.text(cx, cy - (4 if ch.annot else 0), _mathtext(numeral), color="#e9e9ec", fontsize=fs, ha="center", va="center", zorder=8)

            if ch.annot:
                ax.text(cx, cy + 0.9 * fs + 3, ch.annot, color="#9a9aa0", fontsize=6.5, ha="center", va="center", zorder=8)
'''
NEW_RENDER = '''            cx, cy = (x0 + x1) / 2, strip_top + st.strip_h / 2
            fs = max(6.5, min(18.0 if ch.annot else 26.0, 0.95 * w / max(_plain_len(numeral), 1)))
            ax.text(cx, cy - (10 if ch.annot else 0), _mathtext(numeral), color="#e9e9ec", fontsize=fs, ha="center", va="center", zorder=8)

            if ch.annot:                                                 # debajo del cifrado, sobre la barra inferior
                ax.text(cx, strip_top + st.strip_h - st.bar_h - 7, ch.annot, color=ch.annot_color or "#9a9aa0",
                        fontsize=8.0, fontweight="bold", ha="center", va="center", zorder=8)
'''

OLD_GRAPHIC_DEF = "def render_song_graphic(start_s=0.0, duration_s=VIEW_SECONDS, filename='angine_harmony', show=True):\n"
NEW_GRAPHIC_DEF = "def render_song_graphic(start_s=0.0, duration_s=VIEW_SECONDS, filename='angine_harmony', show=True, chords=None):\n"
OLD_GRAPHIC_CHORDS = "        page_chords = [c for c in view_chords if c.onset < b and c.onset + c.dur > a]\n"
NEW_GRAPHIC_CHORDS = "        page_chords = [c for c in (view_chords if chords is None else chords) if c.onset < b and c.onset + c.dur > a]\n"
DOC_GRAPHIC = ("**`render_song_graphic`**: Dibuja la canción o un tramo (`start_s`, `duration_s`) por páginas, las guarda en "
               "`OUTPUT_DIR` y devuelve sus rutas. `chords` cambia los acordes de la franja; si no se da, usa `view_chords`.")

DOC_H2 = ("## Tabroll con la armonía en 24-EDO (paso H2)\n\n"
          "El mismo tabroll, con la franja de acordes de la armonía por compás (`armonia`) en vez de la de 12 clases. En cada "
          "compás: el cifrado sobre el centro con su bajo cifrado (⁶ primera inversión, ⁶₄ segunda, ⁴₂ séptima en el bajo), "
          "la función con su color debajo, y el nombre del acorde con barra cuando el bajo no es la fundamental (G/D). Entre "
          "paréntesis van los compases de baja confianza. Las barras de la franja tienen el color del grado de la fundamental, "
          "como las filas del tabroll.")

DOC_LABELS = ("**`harmony_labels`**: Etiquetas de cada compás para la franja del tabroll. El cifrado sigue la convención "
              "del tabroll: sus2, sus4 y 5 (sin tercera) van abajo; n (tercera neutra), ° y aum van arriba; «+» sube un "
              "cuarto de tono. La inversión se escribe como bajo cifrado: ⁶ y ⁶₄ apilados, o 6/4 arriba si la calidad ya "
              "ocupa un índice. El nombre usa las notas en 24-EDO con barra para el bajo («Dsus2/F♯»). La anotación es la "
              "función (T, S, D, N; en minúscula si el acorde es menor) con su matiz corto, en el color de la función. Los "
              "compases con confianza menor que `min_conf` van entre paréntesis. `tones` está en cents sobre la tónica del "
              "tabroll (`tonic_midi`), para que la franja tome el color del grado.")

CODE_LABELS = '''from tabroll.cells.chord24 import CHORDS24
from tabroll.cells.chord_roles import SUFIJO
from tabroll.cells.harmony_by_bar import PC24_NAMES

COLOR_FUNCION = {'tónica': '#f2d49b', 'subdominante': '#86b9ea', 'dominante': '#ef8f80', 'neutra': '#c9adf2',
                 'sin función': '#9a9aa0'}
MATIZ_CORTO = {'relativa': 'rel.', 'napolitana': 'nap.', 'mixtura': 'mixt.', 'tritono': 'tt', 'modal, sin sensible': 'modal',
               'con sensible': 'sens.', 'sensible': 'sens.', 'sensible, dominante sin fundamental': 'sens.',
               'dominante de la dominante (V/V)': 'V/V'}
INDICES = {'M': ('', ''), 'm': ('', ''), '5': ('5', ''), 'sus2': ('sus2', ''), 'sus4': ('sus4', ''), 'n': ('', 'n'),
           'dism': ('', '°'), 'aum': ('', 'aum')}                     # (subíndice, superíndice) de cada calidad
EN_NOMBRE = {'M': '', 'm': 'm', '5': '5', 'sus2': 'sus2', 'sus4': 'sus4', 'n': 'n', 'dism': '°', 'aum': 'aum'}


def harmony_labels(armonia, tonic_midi, min_conf=0.5):
    nota = lambda q: PC24_NAMES[q % 24].replace('#', '♯')
    cero = 2 * (tonic_midi % 12)                                       # la escala del tabroll cuenta desde su tónica
    out = []
    for row in armonia:
        cal, root = row.get('calidad'), row.get('fundamental_pc24')
        if row.get('cifrado') is None or root is None or cal not in CHORDS24:
            continue
        cif = row['cifrado']
        base = cif[:len(cif) - len(SUFIJO[cal])].replace('+', '{+}')   # {+}: un cuarto de tono, sin espacios de operador
        sub, sup = INDICES[cal]
        fig = row.get('cifra_bajo') or ''
        fig = fig if fig in ('6', '6/4', '4/2') else ''
        if '/' in fig and not sub and not sup:                          # bajo cifrado apilado: ⁶₄, ⁴₂
            num = base + '^{%s}_{%s}' % tuple(fig.split('/'))
        else:
            sup += ('\\\\,' if sup and fig else '') + fig                 # «n 6»: calidad y bajo cifrado, separados
            num = base + (f'_{{{sub}}}' if sub else '') + (f'^{{{sup}}}' if sup else '')
        nombre = nota(root) + EN_NOMBRE[cal]
        b = row.get('bajo_pc24')
        if b is not None and b != root:
            nombre += '/' + nota(b)
        if (row.get('confianza') or 0) < min_conf:
            num, nombre = f'({num})', f'({nombre})'
        out.append(dict(compas=row['compas'], numeral=num, name=nombre,
                        annot=f"{row.get('funcion_corta') or ''} {MATIZ_CORTO.get(row.get('matiz') or '', '')}".strip(),
                        annot_color=COLOR_FUNCION.get(row.get('funcion'), '#9a9aa0'),
                        tones=[50.0 * ((root - cero) % 24 + i) for i in CHORDS24[cal]]))
    return out'''

DOC_RUN24 = ("Tabroll con la armonía en 24-EDO: `tabroll24_pNN.png` por página y `tabroll24_completo.png` en la carpeta de "
             "imágenes. `MOSTRAR_TABROLL24 = True` muestra aquí cada página.")

CODE_RUN24 = '''MOSTRAR_TABROLL24 = False                                              # las imágenes se guardan siempre

acordes24 = [Chord(song.measures[e['compas'] - 1].start, song.measures[e['compas'] - 1].beats, e['tones'],
                   numeral=e['numeral'], name=e['name'], annot=e['annot'], annot_color=e['annot_color'])
             for e in harmony_labels(armonia, tonic_midi) if e['compas'] <= len(song.measures)]
tabroll24 = render_song_graphic(filename='tabroll24', show=MOSTRAR_TABROLL24, chords=acordes24)'''


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
    put = lambda c, text: c.__setitem__("source", text.splitlines(keepends=True))
    code = lambda pred: [c for c in cells if c["cell_type"] == "code" and pred(src(c))]
    done = []

    md = [i for i, c in enumerate(cells) if c["cell_type"] == "markdown" and src(c).startswith("**`chord_progressions`**")]
    if len(md) != 1 or "def chord_progressions(" not in src(cells[md[0] + 1]):
        print("No encontré la celda chord_progressions. Corre antes scripts/funciones_y_progresiones.py.")
        return 1
    if src(cells[md[0] + 1]) != CODE_PROG or src(cells[md[0]]) != DOC_PROG:
        put(cells[md[0]], DOC_PROG)
        put(cells[md[0] + 1], CODE_PROG)
        done.append("chord_progressions con dos resúmenes")

    run = code(lambda s: OLD_TAIL_START in s and "roles_summary(armonia)" in s)
    if len(run) != 1:
        print("No encontré la celda de armonía con las progresiones.")
        return 1
    s = src(run[0])
    new = s[:s.index(OLD_TAIL_START)] + TAIL
    if new != s:
        put(run[0], new)
        done.append("la celda de armonía imprime los dos resúmenes")

    model = code(lambda s: "class Chord:" in s and OLD_CHORD in s)
    rend = code(lambda s: s.startswith("def render(song: Song"))
    graph = [i for i, c in enumerate(cells) if c["cell_type"] == "code" and src(c).startswith("def render_song_graphic(")]
    if len(model) != 1 or len(rend) != 1 or len(graph) != 1:
        print("No encontré la clase Chord, `render` o `render_song_graphic`.")
        return 1
    if "annot_color" not in src(model[0]):
        put(model[0], src(model[0]).replace(OLD_CHORD, NEW_CHORD))
        done.append("Chord.annot_color")
    if OLD_RENDER in src(rend[0]):
        put(rend[0], src(rend[0]).replace(OLD_RENDER, NEW_RENDER))
        done.append("render escribe la función en su color")
    elif NEW_RENDER not in src(rend[0]):
        print("La franja de acordes de `render` no está como esperaba; no la cambié.")
        return 1
    g = cells[graph[0]]
    if OLD_GRAPHIC_DEF in src(g):
        put(g, src(g).replace(OLD_GRAPHIC_DEF, NEW_GRAPHIC_DEF).replace(OLD_GRAPHIC_CHORDS, NEW_GRAPHIC_CHORDS))
        done.append("render_song_graphic acepta otros acordes")
    if NEW_GRAPHIC_CHORDS not in src(g):
        print("`render_song_graphic` no quedó como esperaba.")
        return 1
    prev = cells[graph[0] - 1]
    if prev["cell_type"] == "markdown" and src(prev).startswith("**`render_song_graphic`**") and src(prev) != DOC_GRAPHIC:
        put(prev, DOC_GRAPHIC)

    labels = [i for i, c in enumerate(cells) if c["cell_type"] == "code" and src(c).startswith("from tabroll.cells.chord24 import CHORDS24\nfrom tabroll.cells.chord_roles import SUFIJO")]
    if labels:
        i = labels[0]
        if src(cells[i]) != CODE_LABELS or src(cells[i - 1]) != DOC_LABELS:
            put(cells[i - 1], DOC_LABELS)
            put(cells[i], CODE_LABELS)
            done.append("harmony_labels")
        runs = [c for c in cells[i + 1:] if c["cell_type"] == "code" and "harmony_labels(armonia" in src(c)]
        if runs and src(runs[0]) != CODE_RUN24:
            put(runs[0], CODE_RUN24)
            done.append("celda del tabroll24")
    else:
        cells += [_cell("markdown", DOC_H2), _cell("markdown", DOC_LABELS), _cell("code", CODE_LABELS),
                  _cell("markdown", DOC_RUN24), _cell("code", CODE_RUN24)]
        done.append("celdas nuevas harmony_labels y tabroll24 al final")

    if not done:
        print("El cuaderno ya tenía los pasos H1c y H2.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
