"""Celda 34 del notebook original. Descripcion asociada: **`Style`**: Estilo del gráfico, con medidas en píxeles..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

@dataclass
class Style:
    px_per_beat: float = 216.0
    row_h: float = 22.0
    left: float = 118.0
    right_pad: float = 24.0
    gap: float = 4.0
    header_h: float = 84.0
    strip_h: float = 84.0
    strip_gap: float = 10.0
    note_inset: float = 2.0
    bar_h: float = 11.0
    radius: float = 10.0
    stripe_period: float = 12.0
