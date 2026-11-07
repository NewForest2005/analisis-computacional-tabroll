"""Celda 3 del notebook original.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


# @title 1) Subir el audio

try:
    from google.colab import files
    IN_COLAB_HARMONY = True

except ImportError:
    IN_COLAB_HARMONY = False

BASE_DIR = Path('/content') if IN_COLAB_HARMONY else Path.cwd()

if IN_COLAB_HARMONY:
    print('Sube la canción y, si la tienes, su pista guitar de Demucs.')

    for filename, data in files.upload().items():
        (BASE_DIR / filename).write_bytes(data)

audio_ext = {'.mp3','.wav','.flac','.ogg','.m4a','.aiff','.aif'}
is_stem = lambda p: re.search(r'(^|_)(guitar|bass|other|drums|vocals|piano)( \(\d+\))?$', p.stem.lower())

audio_candidates = [p for p in BASE_DIR.rglob('*') if p.is_file() and p.suffix.lower() in audio_ext and not is_stem(p)]

if not audio_candidates: raise FileNotFoundError('Sube un audio MP3, WAV, FLAC, OGG, M4A o AIFF.')

audio_path = max(audio_candidates, key=lambda p: p.stat().st_mtime)
print(f'Audio seleccionado: {audio_path.name}')
