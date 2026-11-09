"""**`Cycle`**: Patrón de notas que se repite en una voz durante un tramo de la canción.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np

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
