"""Celda 147 del notebook original. Descripcion asociada: **`render_song_graphic`**: Dibuja la canción o un tramo (`start_s`, `duration_s`) por páginas, las guarda en `OUTPUT_DIR` y devuelve sus rutas..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def render_song_graphic(start_s=0.0, duration_s=VIEW_SECONDS, filename='angine_harmony', show=True):

    end_s = len(y) / sr if duration_s is None else min(start_s + float(duration_s), len(y) / sr)
    b0, b1 = float(pos(max(0.0, float(start_s)))), float(pos(end_s))
    pages = _pages([m for m in song.measures if m.start + m.beats > b0 and m.start < b1])

    style = Style(px_per_beat=PX_PER_BEAT, row_h=ROW_H, header_h=70, strip_h=70, gap=4)
    paths, rows = [], (_median_oct * _n - _n, _median_oct * _n + 2 * _n - 1)

    if pages:                                                                                         # misma ventana vertical en todas las páginas
        ini, fin = pages[0][0].start, pages[-1][-1].start + pages[-1][-1].beats
        rows = _rows([nt for nt in song.notes if nt.onset < fin and nt.onset + nt.dur > ini], rows)

    for k, pm in enumerate(pages, 1):

        a, b = pm[0].start, pm[-1].start + pm[-1].beats
        page_notes = [nt for nt in song.notes if nt.onset < b and nt.onset + nt.dur > a]

        page_chords = [c for c in view_chords if c.onset < b and c.onset + c.dur > a]

        path = OUTPUT_DIR / f'{filename}_p{k:02d}.png'
        fig = render(Song(view_scale, page_notes, page_chords, pm), str(path), rows=rows, style=style)

        plt.close(fig); paths.append(path)

        if show:
            print(f'Página {k}/{len(pages)} · compases {_bar_no[id(pm[0])]}–{_bar_no[id(pm[-1])]} · '
                  f'{_mmss(sec_at(a))} – {_mmss(sec_at(b))} · pulsos por compás: {[m.beats for m in pm]}')
            display(IPyImage(filename=str(path)))

    if not paths:
        print('No hay compases en ese rango de tiempo.')

    elif len(paths) > 1:
        full = _stack(paths, filename)
        print(f'Guardado: {len(paths)} páginas en {OUTPUT_DIR} | imagen completa: {", ".join(f.name for f in full)}')

    else:
        print(f'Guardado: {paths[0]}')

    return paths
