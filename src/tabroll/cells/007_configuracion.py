"""Celda 10 del notebook original. Descripcion asociada: Separar guitarra y bajo: si junto con la canción no subiste sus pistas _guitar y _bass, Demucs las saca del mismo audio y las descarga para que la próxima vez las subas con la canción y no haya que separar de nuevo. Con SEPARATE = False el análisis usa solo la mezcla..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

SEPARATE = True          # False = no separar; usa solo las pistas _guitar y _bass que hayas subido con la canción
DOWNLOAD_STEMS = True    # descarga las pistas para subirlas la próxima vez y no tener que separar de nuevo

import importlib.util, subprocess, sys

GUITAR_STEM, BASS_STEM = find_stem(audio_path, 'guitar'), find_stem(audio_path, 'bass')

if SEPARATE and not (GUITAR_STEM and BASS_STEM):
    stems = separate_stems(audio_path)
    GUITAR_STEM, BASS_STEM = stems['guitar'], stems['bass']

    if DOWNLOAD_STEMS and IN_COLAB_HARMONY:
        for p in stems.values():
            files.download(str(p))

print(f'Pista de guitarra: {GUITAR_STEM.name if GUITAR_STEM else "ninguna"}')
print(f'Pista de bajo: {BASS_STEM.name if BASS_STEM else "ninguna"}')
