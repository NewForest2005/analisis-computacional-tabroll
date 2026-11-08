"""Celda 6 del notebook original. Descripcion asociada: **`find_stem`**: Busca en la carpeta de audios, y en sus subcarpetas, la pista de un instrumento de la canción elegida. Para `Canción.mp3` busca un archivo que empiece por `Canción_guitar` o `Canción_bass`, sin importar mayúsculas ni tildes. Si hay varias, prefiere la que está en la misma carpeta que la canción y, entre esas, la más reciente. Si no encuentra ninguna, devuelve `None`..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def find_stem(audio, kind):
    key = name_key(f'{audio.stem}_{kind}')
    hits = [p for p in AUDIO_DIR.rglob('*') if p.is_file() and not p.name.startswith('.') and p.suffix.lower() in audio_ext and name_key(p.stem).startswith(key)]

    return max(hits, key=lambda p: (p.parent == audio.parent, p.stat().st_mtime)) if hits else None
