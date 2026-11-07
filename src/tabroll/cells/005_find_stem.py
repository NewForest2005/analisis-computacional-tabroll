"""Celda 6 del notebook original. Descripcion asociada: find_stem: busca, entre los audios subidos, la pista de un instrumento que corresponde a la canción elegida (por ejemplo Canción_guitar.mp3 para Canción.mp3). Si no la encuentra, devuelve None..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def find_stem(audio, kind):
    hits = [p for p in BASE_DIR.rglob('*') if p.is_file() and p.suffix.lower() in audio_ext and p.stem.startswith(f'{audio.stem}_{kind}')]
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None
