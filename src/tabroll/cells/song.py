"""**`Song`**: Reúne la escala, las notas, los acordes y los compases de una canción.
"""

@dataclass
class Song:
    scale: Scale
    notes: list[Note]
    chords: list[Chord]
    measures: list[Measure]
