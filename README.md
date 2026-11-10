# Análisis Computacional — Tabroll para Angine de Poitrine

En este repositorio se encuentra el código fundamental para el análisis computacional de audio y la generación de un piano roll armónico/melódico estilo TheoryTab.

El notebook original se conserva en [`notebooks/Tabroll_Angine_de_Poitrine.ipynb`](notebooks/Tabroll_Angine_de_Poitrine.ipynb). Sus 94 celdas de código fueron extraídas en módulos Python independientes dentro de [`src/tabroll/cells`](src/tabroll/cells). Las celdas que definen una función o clase usan ese nombre como archivo (`find_stem.py`, `scale.py`, `render_song_graphic.py`); las celdas con varias funciones o configuración usan un nombre descriptivo.

## Estructura

- `notebooks/`: fuente interactiva original.
- `src/tabroll/cells/`: extracción ordenada, una celda de código por archivo.
- `docs/cell-index.md`: inventario y trazabilidad entre notebook y módulos.
- `docs/architecture.md`: cómo se separan funciones, clases, inicialización, configuración y ejecución.
- `scripts/extract_cells.py`: regenera la extracción cuando cambia el notebook.
- `scripts/run_song.py`: corre el notebook completo sobre una canción y guarda los resultados en `outputs/`.
- `references/mata_zyklek_loops.py`: referencia anotada de loops y alturas para evaluar la melodía de Mata Zyklek.
- `tests/`: validaciones estructurales básicas.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Demucs es opcional y solo se necesita para separar guitarra y bajo. La ejecución completa requiere además `ffmpeg` disponible en el sistema.

### Requisitos en macOS Intel

El proyecto requiere Python 3.10–3.12. En Mac Intel se recomienda Python 3.12, porque `numpy==1.26.4` no ofrece una combinación compatible con Python 3.13 y algunas versiones de `llvmlite` tampoco ofrecen ruedas binarias para Intel. Si `python3 --version` muestra otra versión, instala una compatible y crea el entorno con ella:

```bash
brew install python@3.12
/usr/local/bin/python3.12 -m venv .venv
```

En Mac Intel se fija un conjunto compatible: `numpy==1.26.4`, `librosa==0.10.2.post1`, `scipy==1.14.1`, `matplotlib==3.9.4`, `numba==0.62.1` y `llvmlite==0.45.1`. Esta combinación evita que Torch/Demucs intente usar NumPy 2.x y conserva ruedas binarias para macOS Intel.

FFmpeg solo es necesario para Demucs: los MP3 pueden leerse sin él, pero Demucs lo usa para leer y guardar las pistas separadas.

```bash
brew install ffmpeg
```

Demucs funciona sin GPU. En un Mac Intel se ejecuta por CPU y puede tardar varios minutos por canción; las pistas quedan guardadas junto al audio y no se vuelven a separar en ejecuciones posteriores.

## Uso

La extracción conserva el orden de ejecución del notebook. Para reproducir el análisis completo, abrir el notebook en Jupyter/Colab y ejecutar las celdas en orden. Los módulos extraídos funcionan como una base auditable para migrar progresivamente el flujo a una API Python más desacoplada.

## Correr una canción desde la terminal

```bash
.venv/bin/python scripts/run_song.py Fabienk
.venv/bin/python scripts/run_song.py "Mata Zyklek" --preset mata_zyklek
```

Si se ejecuta con `python3` global y existe `.venv`, el script se reinicia automáticamente usando el entorno del
proyecto. También se puede activar el entorno antes: `source .venv/bin/activate` y después usar `python`.

Se puede indicar una ruta o una parte del nombre dentro de `Angine de Poitrine Audios/`. Corre todas las celdas del notebook sobre esa canción, sin abrir Jupyter, y guarda la corrida en `outputs/<fecha>_<hora>_<canción>/`:

- `harmony_outputs/`: tabroll por páginas, imagen completa, mapa de ciclos y ciclos.
- `salida.txt`: todo lo que imprime el notebook, los avisos y el tiempo de cada celda.
- `resumen.md`: tempo, tonalidad, compases, ciclos y capas, para leer o pegar en el chat.
- `resumen.json`: lo mismo en formato estructurado, para comparar corridas.

Las pistas `<canción>_guitar` y `<canción>_bass` se buscan junto a la canción. Si no están, Demucs las crea y quedan guardadas junto a la canción para la próxima vez. El notebook no se modifica: los cambios se aplican solo a esa corrida.

| Opción | Para qué |
|---|---|
| `--preset fabienk` | Aplica un preset de la celda de ajustes (`--presets` los lista). |
| `--set GRID=0.5` | Cambia una variable del notebook en esa corrida; se puede repetir. |
| `--guitar ruta --bass ruta` | Usa pistas con otro nombre o en otra carpeta. |
| `--sin-pistas` | Analiza solo la mezcla: no usa pistas ni corre Demucs. |
| `--nombre prueba-grid` | Agrega una etiqueta al nombre de la carpeta. |
| `--conservar 10` | Después de correr, deja solo las 10 corridas más recientes. |

`outputs/` no se sube a git. Para compartir una corrida, se puede subir solo su resumen con `git add -f outputs/<corrida>/resumen.md`.

## Calidad

```bash
python -m compileall -q src
pytest
```

Los comandos de shell propios de Jupyter se conservan como comentarios en el módulo correspondiente para que todos los archivos `.py` sean sintácticamente válidos.

## Makefile

Con el audio de Sarniezz dentro de `Angine de Poitrine Audios/`, el análisis completo se ejecuta con:

```bash
make run-sarniezz
```

Ese objetivo instala Demucs, comprueba FFmpeg y ejecuta el notebook sobre `Angine de Poitrine - Sarniezz (audio officiel).mp3`. Si las pistas correspondientes `_guitar` y `_bass` no existen, Demucs las genera junto al audio. El resultado queda en `outputs/`, con `harmony_outputs/`, gráficos Tabroll, gráficos de ciclos, mapa de capas, `salida.txt`, `resumen.md` y `resumen.json`.

## Regenerar los módulos

Si se modifica el notebook, regenerar los módulos con:

```bash
python scripts/extract_cells.py
```
