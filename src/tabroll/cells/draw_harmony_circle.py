"""**`draw_harmony_circle`**: Dibuja el círculo con la tónica arriba.
"""

import numpy as np
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
    ax.text(-1.9, -1.98, f"Centro {circle.get('centro', '')} | modo {circle.get('modo', '')} | confiable {circle['tiempo_confiable']}% del tiempo\n"
                         f"Movimientos: {mov} | cambios por compás {circle['cambios_por_compas']}", fontsize=8.5, color='#52514e', va='bottom')
    ax.legend(handles=[Patch(color=ROOT, label='Fundamentales'), Patch(color=BASS, label='Bajo'),
                       Line2D([], [], color=TRANS, lw=2, label='Cambios de fundamental')],
              loc='upper right', bbox_to_anchor=(1.02, 1.0), frameon=False, fontsize=8.5, labelcolor=INK)
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor=SURF)
    plt.close(fig)
    return Path(path)
