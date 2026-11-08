"""Correcciones verificadas de la referencia de Sarniezz.

La partitura MusicXML escribe la última nota del primer compás del riff como
Mi medio bemol. En la notación de cuartos de tono usada por el proyecto, esa
altura es enarmónica de Re# medio sostenido (Re#+), no de Re# natural.
"""

# Alturas expresadas en semitonos respecto de Do, incluyendo cuartos de tono.
FIRST_RIFF_LAST_NOTE = 3.5  # Re#+ = Re# + 1/4 de tono
SOURCE_NOTE = "E-0.5"
CORRECTED_NOTE = "D#+"


def pitch(name: str) -> float:
    """Convierte una nota escrita simple a semitonos relativos a Do."""
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    if name == "D#+":
        return base["D"] + 1.5
    raise ValueError(f"Nota no soportada: {name}")
