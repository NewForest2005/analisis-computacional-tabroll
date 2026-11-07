"""Celda 89 del notebook original. Descripcion asociada: **`parse_key`**: Convierte una tonalidad en `(pc, modo)`; por ejemplo, `('E', 'dorian')`, `('F#', 'minor')` o `('Bb', 'major')`..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def parse_key(spec):
    tonic, mode = spec
    pc = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[tonic[0].upper()]
    pc += sum(1 if c in '#♯' else -1 for c in tonic[1:] if c in '#♯b♭')
    mode = {'major': 'ionian', 'minor': 'aeolian'}.get(mode.lower(), mode.lower())

    return pc % 12, mode
