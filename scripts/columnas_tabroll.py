"""Paso H3b: las notas columna dibujadas en el tabroll24.

Uso:
    python scripts/columnas_tabroll.py
    make extract
    make test

En cada compás del tabroll24, la columna principal se marca con un anillo dorado en la nota aguda y otro en el bajo,
unidos por una línea vertical: la columna. Las columnas de los demás pulsos llevan un anillo blanco fino en la nota
aguda. Cambios en el cuaderno:
1. `melodic_columns` guarda la altura de la nota aguda y del bajo de cada columna (`midi`, `bajo_midi`).
2. `render` acepta `columns` y las dibuja sobre las notas; `render_song_graphic` las reparte por página.
3. La celda del tabroll24 arma las columnas desde `armonia` y las pasa al dibujo.
Se puede correr más de una vez: lo que ya está aplicado no se toca.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"

COLS_OLD = "            cols[j] = dict(pulso=j + 1, t=round(a, 3), aguda=nombre(p), bajo=None if pb is None else nombre(pb),\n"
COLS_NEW = ("            cols[j] = dict(pulso=j + 1, t=round(a, 3), midi=round(p, 2), bajo_midi=None if pb is None else round(pb, 2),\n"
            "                           aguda=nombre(p), bajo=None if pb is None else nombre(pb),\n")
DOC_COLS_OLD = "la columna del pulso (`columnas`, «1 D3/D2 · 2 E3/E2 …», y `columnas_pulso`)."
DOC_COLS_NEW = ("la columna del pulso (`columnas`, «1 D3/D2 · 2 E3/E2 …», y `columnas_pulso`, con la altura MIDI de la nota "
                "aguda y del bajo para dibujarla).")

RENDER_DEF_OLD = ("def render(song: Song, path: Optional[str] = None, view: Optional[tuple[float, float]] = None, "
                  "rows: Optional[tuple[int, int]] = None, playhead: Optional[float] = None, style: Optional[Style] = None):\n")
RENDER_DEF_NEW = ("def render(song: Song, path: Optional[str] = None, view: Optional[tuple[float, float]] = None, "
                  "rows: Optional[tuple[int, int]] = None, playhead: Optional[float] = None, style: Optional[Style] = None,\n"
                  "           columns: Optional[list] = None):\n")
RENDER_MARK = "    # Franja de acordes + nombres\n"
RENDER_COLUMNS = '''    # notas columna: anillo en la nota aguda y en el bajo, unidos por una línea (la principal, en dorado)
    for c in columns or []:
        x = X(c["onset"]) + st.row_h * 0.6
        if x < st.left or x > W:
            continue
        ys = []
        for cents in (c["cents"], c.get("bajo")):
            if cents is not None:
                r, _ = sc.locate(cents)
                if lo - 0.5 <= r <= hi + 0.5:
                    ys.append(ymid(r))
        if not ys:
            continue
        if c.get("principal"):
            if len(ys) == 2 and abs(ys[0] - ys[1]) > 1:
                ax.plot([x, x], ys, color=GOLD, lw=2.0, alpha=0.9, zorder=9, solid_capstyle="round")
            ax.scatter([x] * len(ys), ys, s=(st.row_h * 0.62) ** 2, facecolors="none", edgecolors=GOLD, linewidths=2.0, zorder=9.5)
        else:
            ax.scatter([x], ys[:1], s=(st.row_h * 0.5) ** 2, facecolors="none", edgecolors="#f2f2f2", linewidths=0.9,
                       alpha=0.8, zorder=9.5)

'''
DOC_RENDER = ("**`render`**: Dibuja la canción y devuelve la figura. `columns` (opcional) son notas columna: un anillo en "
              "la nota aguda y otro en el bajo, unidos por una línea; la principal de cada compás va en dorado.")

GRAPH_DEF_OLD = "def render_song_graphic(start_s=0.0, duration_s=VIEW_SECONDS, filename='angine_harmony', show=True, chords=None):\n"
GRAPH_DEF_NEW = ("def render_song_graphic(start_s=0.0, duration_s=VIEW_SECONDS, filename='angine_harmony', show=True, chords=None,\n"
                 "                        columns=None):\n")
GRAPH_CALL_OLD = "        fig = render(Song(view_scale, page_notes, page_chords, pm), str(path), rows=rows, style=style)\n"
GRAPH_CALL_NEW = ("        page_columns = [c for c in (columns or []) if a <= c['onset'] < b]\n"
                  "        fig = render(Song(view_scale, page_notes, page_chords, pm), str(path), rows=rows, style=style,\n"
                  "                     columns=page_columns)\n")
DOC_GRAPH = ("**`render_song_graphic`**: Dibuja la canción o un tramo (`start_s`, `duration_s`) por páginas, las guarda en "
             "`OUTPUT_DIR` y devuelve sus rutas. `chords` cambia los acordes de la franja (si no se da, usa `view_chords`) "
             "y `columns` agrega notas columna.")

RUN24_OLD = "tabroll24 = render_song_graphic(filename='tabroll24', show=MOSTRAR_TABROLL24, chords=acordes24)"
RUN24_NEW = '''columnas24 = [dict(onset=round(float(pos(c['t'])) / GRID) * GRID, cents=(c['midi'] - tonic_midi) * 100.0,
                   bajo=None if c['bajo_midi'] is None else (c['bajo_midi'] - tonic_midi) * 100.0,
                   principal=c['pulso'] == r['columna_pulso'])
              for r in armonia for c in r.get('columnas_pulso') or []]
tabroll24 = render_song_graphic(filename='tabroll24', show=MOSTRAR_TABROLL24, chords=acordes24, columns=columnas24)'''
DOC_RUN24 = ("Tabroll con la armonía en 24-EDO: `tabroll24_pNN.png` por página y `tabroll24_completo.png` en la carpeta de "
             "imágenes. Las notas columna van marcadas: la principal de cada compás con anillos dorados en la nota aguda "
             "y en el bajo, unidos por una línea; las de los demás pulsos, con un anillo blanco fino. "
             "`MOSTRAR_TABROLL24 = True` muestra aquí cada página.")


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]
    src = lambda c: "".join(c["source"])
    put = lambda c, text: c.__setitem__("source", text.splitlines(keepends=True))
    idx = lambda pred: [i for i, c in enumerate(cells) if c["cell_type"] == "code" and pred(src(c))]
    done = []

    cols, rend = idx(lambda s: "def melodic_columns(" in s), idx(lambda s: s.startswith("def render(song: Song"))
    graph, run = idx(lambda s: s.startswith("def render_song_graphic(")), idx(lambda s: "harmony_labels(armonia, tonic_midi)" in s)
    if not all(len(x) == 1 for x in (cols, rend, graph, run)):
        print("Falta alguna celda. Corre antes scripts/tabroll_armonia24.py y scripts/notas_columna.py.")
        return 1

    def edit(i, old, new, label, doc=None, doc_old=None):
        s = src(cells[i])
        if new in s:
            return True
        if old not in s:
            print(f"No encontré lo que esperaba en la celda de {label}; no la cambié.")
            return False
        put(cells[i], s.replace(old, new))
        md = cells[i - 1]
        if md["cell_type"] == "markdown" and doc:
            put(md, src(md).replace(doc_old, doc) if doc_old else doc)
        done.append(label)
        return True

    ok = (edit(cols[0], COLS_OLD, COLS_NEW, "melodic_columns guarda las alturas", DOC_COLS_NEW, DOC_COLS_OLD)
          and edit(rend[0], RENDER_DEF_OLD, RENDER_DEF_NEW, "render acepta columnas", DOC_RENDER)
          and edit(rend[0], RENDER_MARK, RENDER_COLUMNS + RENDER_MARK, "render dibuja las columnas")
          and edit(graph[0], GRAPH_DEF_OLD, GRAPH_DEF_NEW, "render_song_graphic acepta columnas", DOC_GRAPH)
          and edit(graph[0], GRAPH_CALL_OLD, GRAPH_CALL_NEW, "render_song_graphic reparte las columnas por página")
          and edit(run[0], RUN24_OLD, RUN24_NEW, "el tabroll24 dibuja las columnas", DOC_RUN24))
    if not ok:
        return 1
    if not done:
        print("El cuaderno ya tenía las columnas en el tabroll24.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
