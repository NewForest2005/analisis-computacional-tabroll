# Análisis Computacional — Tabroll para Angine de Poitrine

En este repositorio se encuentra el código fundamental para el análisis computacional de audio y la generación de un piano roll armónico/melódico estilo TheoryTab.

El notebook original se conserva en [`notebooks/Tabroll_Angine_de_Poitrine.ipynb`](notebooks/Tabroll_Angine_de_Poitrine.ipynb). Cada una de sus celdas de código se extrae a un módulo Python independiente dentro de [`src/tabroll/cells`](src/tabroll/cells); el inventario actualizado, con el número de celda original, está en [`docs/cell-index.md`](docs/cell-index.md). **El notebook es la fuente de verdad**: los cambios se hacen en el notebook y después se regeneran los módulos (ver [Regenerar los módulos](#regenerar-los-módulos)). Las celdas que definen una función o clase usan ese nombre como archivo (`find_stem.py`, `scale.py`, `render_song_graphic.py`); las celdas con varias funciones o configuración usan un nombre descriptivo.

## Estructura

- `notebooks/`: fuente interactiva original.
- `src/tabroll/cells/`: extracción ordenada, una celda de código por archivo.
- `docs/cell-index.md`: inventario y trazabilidad entre notebook y módulos.
- `docs/architecture.md`: cómo se separan funciones, clases, inicialización, configuración y ejecución.
- `docs/*.md`: notas de análisis (armonía, melodía, corpus y estilos, verosimilitud por bloques, evolución de la tesis).
- `docs/articulo/`: artículo final en LaTeX y su PDF.
- `docs/poster/`: póster en LaTeX (`poster_version_1_Santi.tex` incrusta `poster_original.pdf`), su PDF y `LEEME_nuevos_graficos.md` con el contenido propuesto por sección.
- `docs/defensa/`: puntos para la defensa ordenados, con la fuente de cada cifra (`make defensa` genera el PDF y lo copia a `~/Downloads`).
- `docs/formulas/`: resumen de fórmulas (tono logarítmico, Mel, Fourier, MFCC, KL, repetición temporal) en LaTeX y PDF.
- `docs/referencias_compiladas.md`: bibliografía y fuentes del proyecto, compiladas.
- `references/partituras/`: partituras y archivos Guitar Pro de referencia.
- `references/corpus/`: corpus y datos de comparación estilística.
- `trabajo/`: materiales de trabajo y diagnósticos archivados.
- `docs/historial/`: historial auxiliar de la investigación.
- `scripts/`: flujo principal.
  - `run_song.py`: corre el notebook completo sobre una canción y guarda los resultados en `outputs/`.
  - `todo.py` y `graficas_completas.py`: corren todas las canciones y reúnen las gráficas (`make todo`, `make graficas`).
  - `extract_cells.py`: regenera la extracción cuando cambia el notebook (`--check` solo verifica).
  - `parse_gp.py`, `evaluar_melodia.py` y `completar_evaluacion.py`: partituras Guitar Pro y evaluación contra ellas.
  - `separar_roformer.py`: separación alternativa con BS-RoFormer SW en un entorno aparte (ver
    [`docs/separacion_roformer.md`](docs/separacion_roformer.md)); `run_song.py --separador roformer` usa esas pistas.
- `scripts/cuaderno/`: pasos del análisis que modifican el notebook (armonía en 24-EDO, funciones, ejes de Lendvai,
  notas columna, análisis melódico, limpieza de notas…). Ya están aplicados; se pueden volver a correr sin duplicar cambios.
- `scripts/diagnostico/`: diagnósticos de la línea melódica, las capas del looper, Basic Pitch y el ruido de muestreo.
- `scripts/comparacion/`: comparación con corpus y repertorios (estilos, verosimilitud por bloques, campos de Hába,
  ciclos métricos, equivalencias EDO) y gráficas comparativas (tarjetas, tiras de ciclos, radares, figuras del álbum).
  `estilo_figuras.py` compone las figuras sin solapes y avisa si algo se monta (ver [`docs/graficas.md`](docs/graficas.md)).
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

Demucs funciona sin GPU. En un Mac Intel se ejecuta por CPU y puede tardar varios minutos por canción; las pistas quedan guardadas junto al audio y no se vuelven a separar en ejecuciones posteriores. La separación usa una semilla fija: dos separaciones del mismo audio en la misma máquina dan las mismas pistas.

## Uso

La extracción conserva el orden de ejecución del notebook. Para reproducir el análisis completo, abrir el notebook en Jupyter/Colab y ejecutar las celdas en orden. Los módulos extraídos funcionan como una base auditable para migrar progresivamente el flujo a una API Python más desacoplada.

## Correr una canción desde la terminal

```bash
.venv/bin/python scripts/run_song.py Fabienk
.venv/bin/python scripts/run_song.py "Mata Zyklek" --set "BAR_LENGTHS=(5, 4, 2)"
```

Si se ejecuta con `python3` global y existe `.venv`, el script se reinicia automáticamente usando el entorno del
proyecto. También se puede activar el entorno antes: `source .venv/bin/activate` y después usar `python`.

Se puede indicar una ruta o una parte del nombre dentro de `Angine de Poitrine Audios/`. Corre todas las celdas del notebook sobre esa canción, sin abrir Jupyter, y guarda la corrida en `outputs/<fecha>_<hora>_<canción>/`:

- `harmony_outputs/`: tabroll por páginas, imagen completa, mapa de ciclos y ciclos.
- `salida.txt`: todo lo que imprime el notebook, los avisos y el tiempo de cada celda.
- `resumen.md`: tempo, tonalidad, compases, ciclos y capas, para leer o pegar en el chat.
- `resumen.json`: lo mismo en formato estructurado, para comparar corridas.
  Guarda la huella SHA-256 de la mezcla y de las dos pistas (`pistas.sha256`): dos corridas con las mismas huellas usaron exactamente el mismo audio.

Las pistas `<canción>_guitar` y `<canción>_bass` se buscan junto a la canción. Si no están, Demucs las crea y quedan guardadas junto a la canción para la próxima vez. El notebook no se modifica: los cambios se aplican solo a esa corrida.

| Opción | Para qué |
|---|---|
| `--preset nombre` | Aplica un preset de la celda de ajustes, si la trae; hoy no trae ninguno (`--presets` los lista). |
| `--set GRID=0.5` | Cambia una variable del notebook en esa corrida; se puede repetir. |
| `--guitar ruta --bass ruta` | Usa pistas con otro nombre o en otra carpeta. |
| `--sin-pistas` | Analiza solo la mezcla: no usa pistas ni corre Demucs. |
| `--nombre prueba-grid` | Agrega una etiqueta al nombre de la carpeta. |
| `--conservar 10` | Después de correr, deja solo las 10 corridas más recientes. |

`outputs/` no se sube a git. Para compartir una corrida, se puede subir solo su resumen con `git add -f outputs/<corrida>/resumen.md`.

## Calidad

```bash
make check   # extracción al día (sin escribir nada), sintaxis y dependencias
make test    # todas las pruebas (unos 3 minutos)
```

Los comandos de shell propios de Jupyter se conservan como comentarios en el módulo correspondiente para que todos los archivos `.py` sean sintácticamente válidos.

## Makefile

Con el audio de Sarniezz dentro de `Angine de Poitrine Audios/`, el análisis completo se ejecuta con:

```bash
make run-sarniezz
```

Ese objetivo instala Demucs, comprueba FFmpeg y ejecuta el notebook sobre `Angine de Poitrine - Sarniezz (audio officiel).mp3`. Si las pistas correspondientes `_guitar` y `_bass` no existen, Demucs las genera junto al audio. El resultado queda en `outputs/`, con `harmony_outputs/`, gráficos Tabroll, gráficos de ciclos, mapa de capas, `salida.txt`, `resumen.md` y `resumen.json`.

## Regenerar los módulos

Los módulos de `src/tabroll/cells/` se generan desde el notebook: **no los edites a mano**. Haz el cambio en la celda del notebook y regenera:

```bash
make extract                                        # regenera módulos y docs/cell-index.md
.venv/bin/python scripts/extract_cells.py --check   # solo informa diferencias, no escribe
```

La extracción guarda en `src/tabroll/cells/.extraccion.json` la huella de cada módulo que escribe. Si un módulo cambió a mano desde la última extracción, `make extract` se detiene y lista esos archivos en lugar de borrar el cambio. Hay dos salidas:

- Pasar el cambio a la celda correspondiente del notebook y volver a correr `make extract` (lo normal).
- Descartar el cambio manual con `.venv/bin/python scripts/extract_cells.py --force`.

La prueba `tests/test_extracted_cells.py` falla si notebook y módulos no coinciden.
