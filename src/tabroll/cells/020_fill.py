"""Celda 38 del notebook original. Descripcion asociada: **`_fill`**: Dibuja un rectángulo del color del grado o, entre dos grados, rayas diagonales de los dos colores vecinos. El ancho de las rayas es proporcional a la posición de la altura entre ambos grados..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def _fill(ax, x, y, w, h, cols, z, period):
    c_lo, c_hi, f = cols
    base = Rectangle((x, y), w, h, fc=c_lo, ec="none", zorder=z)
    ax.add_patch(base)

    if f > 0.01 and c_lo != c_hi:
        bw, t = period * f, x - h

        while t < x + w:
            poly = Polygon([(t, y + h), (t + bw, y + h), (t + bw + h, y), (t + h, y)], closed=True, fc=c_hi, ec="none", zorder=z + 0.01)

            ax.add_patch(poly)
            poly.set_clip_path(base)

            t += period
