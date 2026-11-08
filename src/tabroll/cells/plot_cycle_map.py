"""**`plot_cycle_map`**: Dibuja en qué tramos de la canción aparece cada ciclo, por voz.
"""

def plot_cycle_map(groups, duration, filename='mapa_ciclos', layers=None):

    rows = len(groups) + (layers is not None)
    fig, ax = plt.subplots(figsize=(14, 0.9 + 0.9 * rows), facecolor=BG)
    ax.set_facecolor(BG)
    cmap = plt.get_cmap('tab10')

    for row, (voice, cycles) in enumerate(groups.items()):
        ax.text(-0.01 * duration, row, voice, color='white', ha='right', va='center', fontsize=10)

        for c in cycles:
            ax.add_patch(Rectangle((c.start, row - 0.36), c.end - c.start, 0.72, ec=BG, lw=1, alpha=0.45 if c.doubled >= 0.8 else 1.0,
                                   fc=cmap((ord(c.label) - 65) % 10)))
            if c.end - c.start > 0.035 * duration:
                ax.text((c.start + c.end) / 2, row, f'{c.label}  {c.period:.2f} s', color='white', ha='center', va='center', fontsize=9)

    if layers is not None:                                                         # capas de guitarra: nivel y cambios de loop
        events, level, dt = layers
        row = len(groups)
        ax.text(-0.01 * duration, row, 'Capas', color='white', ha='right', va='center', fontsize=10)
        ax.fill_between(np.arange(len(level)) * dt, row + 0.36, row + 0.36 - 0.72 * np.clip(level, 0, 1), color='0.5', lw=0)

        for t, kind in events:
            ax.plot(t, row - 0.45, '^' if kind == 'entra' else 'v', color='#50c878' if kind == 'entra' else '#e05050', ms=7)

    ax.set_xlim(0, duration)
    ax.set_ylim(rows - 0.5, -0.5)
    ax.set_yticks([])

    ax.set_xticks(np.arange(0, duration, 30))
    ax.set_xticklabels([_mmss(t) for t in np.arange(0, duration, 30)], color='white', fontsize=8)
    ax.tick_params(colors='white', length=3)

    for s in ax.spines.values():
        s.set_visible(False)

    path = OUTPUT_DIR / f'{filename}.png'
    fig.savefig(path, dpi=130, bbox_inches='tight', facecolor=BG)
    plt.close(fig)

    display(IPyImage(filename=str(path)))

    return path
