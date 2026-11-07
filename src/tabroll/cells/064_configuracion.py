"""Celda 124 del notebook original. Descripcion asociada: 3) Notas: cada ataque o cambio de altura inicia una nota; alturas cuantizadas a pasos de MICRO_STEP cents..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


raw_notes = extract_notes(midi, Smax, detect_onsets(oenv, fps), sr, HOP_P, off, MICRO_STEP)

if not raw_notes:
    raise ValueError('No se detectaron notas en el audio.')

arr = np.array(raw_notes)
