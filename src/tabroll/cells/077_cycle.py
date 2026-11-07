"""Celda 149 del notebook original. Descripcion asociada: **`Cycle`**: Patrón de notas que se repite en una voz durante un tramo de la canción..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


@dataclass
class Cycle:
    start: float
    end: float
    period: float
    score: float
    pitch: Optional[np.ndarray] = None
    label: str = ""
    doubled: float = 0.0
    attack: Optional[np.ndarray] = None
    slots: int = 0
    sub: int = 2
    entry: float = 0.0
