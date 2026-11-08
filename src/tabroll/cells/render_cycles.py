"""**`render_cycles`**: El parámetro bar puede ser un número fijo o una función que devuelva el compás de cada ciclo.
"""

def render_cycles(cycles, scale, tonic_midi, bar=4, filename='ciclo'):

    style = Style(px_per_beat=PX_PER_BEAT, row_h=ROW_H, header_h=70, strip_h=8, gap=4)
    rows, paths = (_median_oct * _n - _n, _median_oct * _n + 2 * _n - 1), []

    for lab in sorted({c.label for c in cycles}):
        c = max((c for c in cycles if c.label == lab), key=lambda c: c.end - c.start)   # la versión más larga de cada ciclo
        s = cycle_song(c, scale, tonic_midi, bar(c) if callable(bar) else bar)        # cada ciclo con su propio compás

        if not s.notes:
            continue

        path = OUTPUT_DIR / f'{filename}_{lab}.png'
        fig = render(s, str(path), rows=_rows(s.notes, rows), style=style)
        plt.close(fig); paths.append(path)

        print(f'Ciclo {lab} · {c.period:.3f} s · {_mmss(c.start)} – {_mmss(c.end)}')

        display(IPyImage(filename=str(path)))

    return paths
