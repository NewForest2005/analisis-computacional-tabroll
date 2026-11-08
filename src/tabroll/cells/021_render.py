"""Celda 40 del notebook original. Descripcion asociada: **`render`**: Dibuja la canción y devuelve la figura..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def render(song: Song, path: Optional[str] = None, view: Optional[tuple[float, float]] = None, rows: Optional[tuple[int, int]] = None, playhead: Optional[float] = None, style: Optional[Style] = None):

    st = style or Style()
    sc, n, ms = song.scale, song.scale.n, song.measures

    tl = Timeline(ms, st.px_per_beat, st.gap)
    b0, b1 = view or (ms[0].start, ms[-1].start + ms[-1].beats)
    shift = tl.x(b0) - st.left

    def X(b, side="start"):
        return tl.x(b, side) - shift

    W = int(X(b1, "end") + st.right_pad)
    vis = [m for m in ms if m.start < b1 and m.start + m.beats > b0]

    # extension vertical de octavas
    if rows is None:
        rr = [sc.locate(nt.cents)[0] for nt in song.notes]
        lo = (math.floor(min(rr)) // n) * n
        hi = (math.ceil(max(rr)) // n) * n + n - 1

    else:
        lo, hi = rows

    roll_top = st.header_h
    roll_h = (hi - lo + 1) * st.row_h
    strip_top = roll_top + roll_h + st.strip_gap
    panel_bot = strip_top + st.strip_h

    H = int(panel_bot + 58)

    # fila (puede ser fraccionaria) -> pixel y de su centro
    def ymid(r):
        return roll_top + (hi - r + 0.5) * st.row_h

    fig = plt.figure(figsize=(W / 100, H / 100), dpi=100, facecolor=BG)

    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")

    # tamano de cuadros, bandas de fila por color de grado, malla, encabezado
    first_panel_x = None

    for m in vis:
        xa, xb = X(m.start), X(m.start + m.beats, "end")
        first_panel_x = xa if first_panel_x is None else first_panel_x

        panel = FancyBboxPatch((xa, roll_top), xb - xa, panel_bot - roll_top, boxstyle=f"round,pad=0,rounding_size={st.radius}",  fc=BG, ec="none", zorder=1)
        ax.add_patch(panel)

        for r in range(lo, hi + 1):
            band = Rectangle((xa, ymid(r) - st.row_h / 2), xb - xa, st.row_h, fc=mix(BG, sc.colors[r % n], 0.25 if not sc.degrees or sc.degrees[r % n] else 0.12), ec="none", zorder=1.1)

            ax.add_patch(band)
            band.set_clip_path(panel)

        ys = [roll_top + k * st.row_h for k in range(1, hi - lo + 1)]
        ax.hlines(ys, xa, xb, colors="#000000", alpha=0.35, lw=0.8, zorder=1.2)

        oct_y = [ymid(r) + st.row_h / 2 for r in range(lo + 1, hi + 1) if r % n == 0]
        ax.hlines(oct_y, xa, xb, colors="#8d8d92", lw=1.0, zorder=1.25)

        if sc.tuning:
            ghosts = []

            for o in range(lo // n - 1, hi // n + 2):
                for t in sc.tuning:
                    r, on_degree = sc.locate(o * sc.period + t)

                    if not on_degree and lo - 0.5 <= r <= hi + 0.5:
                        ghosts.append(ymid(r))

            ax.hlines(ghosts, xa, xb, colors="#ffffff", alpha=0.16, lw=0.7, linestyles=(0, (1.5, 3.0)), zorder=1.28)

        if m.grid > 0:
            gx = [X(m.start + k * m.grid) for k in range(1, int(m.beats / m.grid - 1e-6) + 1)]
            ax.vlines(gx, roll_top, roll_top + roll_h, colors="#000000", alpha=0.30, lw=1.0, zorder=1.3)

        if m.accent:
            ax_ = [X(m.start + k * m.accent) for k in range(1, int(m.beats / m.accent - 1e-6) + 1)]
            ax.vlines(ax_, roll_top, panel_bot, colors="#9a9aa0", alpha=0.75, lw=1.2, zorder=1.4)

        ax.add_patch(FancyBboxPatch((xa, roll_top), xb - xa, panel_bot - roll_top, boxstyle=f"round,pad=0,rounding_size={st.radius}",
                                    fc="none", ec="#7a7a80", lw=1.0, zorder=6))

        # encabezado: corchete dorado degradado + "N pulsos"
        L, N = min(xb - xa, 260.0), 40

        segs = [[(xa + L * k / N, 22), (xa + L * (k + 1) / N, 22)] for k in range(N)]
        segs += [[(xa, 22 + (roll_top - 22) * k / 16), (xa, 22 + (roll_top - 22) * (k + 1) / 16)] for k in range(16)]

        al = [1 - 0.9 * k / N for k in range(N)] + [1 - 0.85 * k / 16 for k in range(16)]

        ax.add_collection(LineCollection(segs, colors=[(*to_rgb(GOLD), a) for a in al], linewidths=2.6, zorder=7))

        ax.text(xa + 16, 52, f"{m.beats:g} beats", color="white", fontsize=13, fontweight="bold", va="center", zorder=7)

    # etiquetas de octava (E4, E3...): primer panel visible, debajo de las notas
    if first_panel_x is not None:
        for r in range(lo, hi + 1):
            if r % n == 0:
                ax.text(first_panel_x + 6, ymid(r), f"{sc.tonic_name}{sc.tonic_octave + r // n}", color="#a7a7ab", fontsize=10.5, fontweight="bold", va="center", zorder=1.5)

    # notas (melodia)
    for nt in song.notes:
        row, _ = sc.locate(nt.cents)

        if not (lo - 0.5 <= row <= hi + 0.5):
            continue
        cols = sc.colors_for(nt.cents)

        for a, b in pieces(nt.onset, nt.dur, ms):
            x0, x1 = X(a) + st.note_inset, X(b, "end") - st.note_inset

            if x1 < st.left - 8 or x0 > W:
                continue
            _fill(ax, x0, ymid(row) - (st.row_h - 2) / 2, x1 - x0, st.row_h - 2, cols, 4, st.stripe_period)

    # Franja de acordes + nombres
    for ch in song.chords:

        auto_num, auto_name = label_chord(ch, sc)
        numeral, name = ch.numeral or auto_num, ch.name or auto_name
        cols = sc.colors_for(ch.tones[0])

        pcs = pieces(ch.onset, ch.dur, ms)
        widths = [X(b, "end") - X(a) for a, b in pcs]
        main = widths.index(max(widths)) if widths else 0

        for j, ((a, b), w) in enumerate(zip(pcs, widths)):
            x0, x1 = X(a) + 1.5, X(b, "end") - 1.5

            if x1 < st.left - 8 or x0 > W:
                continue

            ax.add_patch(Rectangle((x0, strip_top), x1 - x0, st.strip_h, fc="#28292e", ec="none", zorder=3))
            _fill(ax, x0, strip_top, x1 - x0, st.bar_h, cols, 3.2, st.stripe_period)
            _fill(ax, x0, strip_top + st.strip_h - st.bar_h, x1 - x0, st.bar_h, cols, 3.2, st.stripe_period)

            if j != main and w < 60:
                continue

            cx, cy = (x0 + x1) / 2, strip_top + st.strip_h / 2
            fs = max(6.5, min(26.0, 0.95 * w / max(_plain_len(numeral), 1)))
            ax.text(cx, cy - (4 if ch.annot else 0), _mathtext(numeral), color="#e9e9ec", fontsize=fs, ha="center", va="center", zorder=8)

            if ch.annot:
                ax.text(cx, cy + 0.9 * fs + 3, ch.annot, color="#9a9aa0", fontsize=6.5, ha="center", va="center", zorder=8)

            nfs = max(6.5, min(15.0, 1.0 * w / max(_plain_len(name), 1)))
            label = f"$\\mathsf{{{name}}}$" if re.search(r"[_^]\{", name) else name
            ax.text(cx, panel_bot + 26, label, color="#ececee", fontsize=nfs, ha="center", va="center", zorder=8)

    # linea de reproduccion
    if playhead is not None and b0 <= playhead <= b1:
        ax.add_patch(Rectangle((X(playhead) - 1.5, roll_top), 3, panel_bot - roll_top, fc="white", ec="none", zorder=20))

    # Eje izquierdo (para las notas)
    ax.add_patch(Rectangle((0, 0), st.left - 8, H, fc=BG, ec="none", zorder=40))

    for r in range(lo, hi + 1):
      idx = r % n
      fs = min(12.0, 0.68 * st.row_h)
      name = sc.degree_name(idx)

      ax.text(st.left - 78, ymid(r), sc.degrees[idx] if sc.degrees else str(idx + 1), color=lighten(sc.colors[idx], 0.3), fontsize=fs, fontweight="bold", va="center", zorder=41)
      ax.text(st.left - 52, ymid(r), f"$\\mathsf{{{name}}}$" if "_{" in name else name, color="#eaeaea", fontsize=fs, va="center", zorder=41)

    if path:
        fig.savefig(path, dpi=100, facecolor=BG)

    return fig
