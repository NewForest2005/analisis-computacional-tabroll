"""Celda 21 del notebook original. Descripcion asociada: Modelo de la canción.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


@dataclass
class Note:
    onset: float
    dur: float
    cents: float


@dataclass
class Chord:
    onset: float
    dur: float
    tones: list[float]
    numeral: Optional[str] = None
    name: Optional[str] = None
    annot: Optional[str] = None


@dataclass
class Measure:
    start: float
    beats: float
    grid: float = 1.0
    accent: Optional[float] = None
