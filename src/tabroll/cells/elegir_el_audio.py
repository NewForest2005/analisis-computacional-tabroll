"""**`name_key`**: Normaliza nombres quitando mayúsculas y tildes. **`find_song`**: Busca y selecciona un audio en la carpeta del proyecto, ignorando stems y archivos ocultos; con `SONG` elige la coincidencia, y con `None` el audio más reciente.
"""

# @title 1) Elegir el audio

SONG = None                                   # parte del nombre de la canción, sin importar mayúsculas ni tildes (por ejemplo 'Fabienk'); None = el audio más reciente
AUDIO_FOLDER = 'Angine de Poitrine Audios'    # carpeta de los audios, en la raíz del proyecto

import unicodedata

try:
    from google.colab import files
    IN_COLAB_HARMONY = True

except ImportError:
    IN_COLAB_HARMONY = False

BASE_DIR = Path('/content') if IN_COLAB_HARMONY else next((d for d in (Path.cwd(), *Path.cwd().parents) if (d / 'pyproject.toml').is_file()), Path.cwd())   # raíz del proyecto
AUDIO_DIR = BASE_DIR / AUDIO_FOLDER if (BASE_DIR / AUDIO_FOLDER).is_dir() else (BASE_DIR if IN_COLAB_HARMONY else Path.cwd())

if IN_COLAB_HARMONY:
    print('Sube la canción y, si las tienes, sus pistas _guitar y _bass de Demucs.')

    for filename, data in files.upload().items():
        (AUDIO_DIR / filename).write_bytes(data)

audio_ext = {'.mp3','.wav','.flac','.ogg','.m4a','.aiff','.aif'}
is_stem = lambda p: re.search(r'(^|_)(guitar|bass|other|drums|vocals|piano)( \(\d+\))?$', p.stem.lower())


def name_key(text):
    return ''.join(ch for ch in unicodedata.normalize('NFKD', str(text).casefold()) if not unicodedata.combining(ch))


def find_song(folder, song=None):
    found = sorted((p for p in folder.rglob('*') if p.is_file() and not p.name.startswith('.') and p.suffix.lower() in audio_ext and not is_stem(p)),
                   key=lambda p: name_key(p.relative_to(folder)))

    if not found:
        raise FileNotFoundError(f'No hay audios MP3, WAV, FLAC, OGG, M4A o AIFF en {folder}.')

    if song is None:
        return max(found, key=lambda p: p.stat().st_mtime), found

    key = name_key(song)
    hits = [p for p in found if key in name_key(p.relative_to(folder))]
    hits = [p for p in hits if key in (name_key(p.name), name_key(p.stem))] or hits                       # el nombre exacto gana

    if len(hits) > 1:
        hits = [p for p in hits if re.search(r'off?ici(al|el)', name_key(p.stem))] or hits                  # entre las versiones de una canción, el audio oficial

    if len(hits) > 1:
        preferred = [p for p in hits if name_key(p.stem).startswith(key) and 'official audio' in name_key(p.stem)]
        hits = preferred if len(preferred) == 1 else hits

    if len(hits) != 1:
        listed = '\n  '.join(str(p.relative_to(folder)) for p in (hits or found))
        raise FileNotFoundError(f"'{song}' " + ('coincide con varios audios; escribe más del nombre:' if hits else f'no coincide con ningún audio de {folder.name}. Hay:') + f'\n  {listed}')

    return hits[0], found


audio_path, audio_candidates = find_song(AUDIO_DIR, SONG)

print(f'Audios en {AUDIO_DIR}:')
for p in audio_candidates[:40]:
    print(('  → ' if p == audio_path else '    ') + str(p.relative_to(AUDIO_DIR)))

if len(audio_candidates) > 40:
    print(f'    ... y {len(audio_candidates) - 40} más')

if SONG is None and len(audio_candidates) > 1:
    print("Es el más reciente. Para elegir otro, escribe parte de su nombre en SONG, por ejemplo SONG = 'Fabienk'.")

print(f'Audio seleccionado: {audio_path.name}')
