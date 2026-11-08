"""Celda 93 del notebook original. Descripcion asociada: **`make_scale`**: `Scale` de tabroll con los 7 grados del modo; lo que cae entre grados se dibuja rayado (microtonal o cromático)..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def make_scale(tonic_pc, mode):
    st = MODES[mode]
    names = spell_scale(tonic_pc, st)
    tonic_midi = 60 + (tonic_pc - 60) % 12                  # tónica entre C4 y B4 (E -> E4 = 64)

    sc = Scale([100.0 * s for s in st], period=1200.0, names=names, tonic_name=names[0], tonic_octave=tonic_midi // 12 - 1, accidental_unit=100.0, tol=20.0)

    return sc, tonic_midi
