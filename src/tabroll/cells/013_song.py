"""Celda 23 del notebook original. Descripcion asociada: **`Song`**: Reúne la escala, las notas, los acordes y los compases de una canción..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

@dataclass
class Song:
    scale: Scale
    notes: list[Note]
    chords: list[Chord]
    measures: list[Measure]
