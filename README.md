# Tabroll 24-EDO: análisis computacional de Angine de Poitrine

![Python](https://img.shields.io/badge/python-3.10–3.12-blue)
![Afinación](https://img.shields.io/badge/afinación-24--EDO-orange)

Herramienta de transcripción y análisis en **24-EDO** (cuartos de tono) a partir del audio, aplicada al álbum de la
banda microtonal Angine de Poitrine. Desde la grabación produce notas en cuartos de tono, compases, un acorde por compás
y un **tabroll**: un piano roll de 24 filas por octava con los acordes debajo. Después compara cada canción con corpus de
estilos (rock, jazz, práctica común, pop, radif persa, indostánica) para responder si la banda es un estilo existente o
una recombinación nueva.

Trabajo de grado · Facultad de Ciencias, Departamento de Matemáticas · Universidad Nacional de Colombia, sede Bogotá.

## Resultados principales

| Dimensión | Resultado |
|---|---|
| Armonía | 37.5 % de los casos sin vecino en ningún corpus, frente a 5.2 % en rock real |
| Melodía | 2 grados en cuarto de tono concentran entre el 48 y el 82 % de los cuartos de tono de cada canción |
| Metro | ciclos de dos compases de 5 y de 7 (picos en 20 y 28 corcheas) |
| Acierto | fundamental del acorde: 85 % en compases confiables; melodía: 49 % (media de 4 canciones) |

El detalle y la fuente de cada cifra están en [`docs/defensa/`](docs/defensa) y [`docs/guion_defensa.md`](docs/guion_defensa.md).

## Estructura del repositorio

```text
analisis-computacional-tabroll/
├── notebooks/            Tabroll_Angine_de_Poitrine.ipynb: fuente de verdad del análisis
├── src/tabroll/cells/    una celda del notebook = un módulo (generados, no se editan a mano)
├── scripts/
│   ├── run_song.py       corre el notebook completo sobre una canción
│   ├── extract_cells.py  regenera src/tabroll/cells/ desde el notebook
│   ├── evaluar_melodia.py, completar_evaluacion.py, parse_gp.py   evaluación contra partituras
│   ├── todo.py, graficas_completas.py, presentacion_imagenes.py   lotes y gráficas
│   ├── separar_roformer.py                                        separación alternativa (BS-RoFormer)
│   ├── comparacion/      corpus, verosimilitud por bloques, ciclos métricos, figuras del álbum
│   ├── cuaderno/         pasos ya aplicados al notebook (armonía 24-EDO, funciones, ejes de Lendvai…)
│   └── diagnostico/      diagnósticos de la melodía, el looper y Basic Pitch
├── references/           partituras corregidas de oído, Guitar Pro y corpus de estilos
├── docs/                 notas de método, glosario, guion, referencias, artículo, póster y defensa
├── presentacion/         presentación de la defensa (reveal.js, funciona sin conexión)
├── web/                  círculo de 24-EDO interactivo
├── tests/                pruebas (pytest)
├── trabajo/              materiales y diagnósticos archivados
└── Makefile
```

`outputs/`, el audio y las pistas separadas no se suben a git.

## Instalación

Requiere Python 3.10–3.12 y, para separar guitarra y bajo, `ffmpeg`.

```bash
make install      # crea .venv e instala el proyecto con las dependencias de desarrollo
make demucs       # opcional: Demucs para la separación de fuentes
```

En macOS Intel conviene Python 3.12 (`brew install python@3.12 ffmpeg`). El proyecto fija `numpy==1.26.4`,
`librosa==0.10.2.post1`, `scipy==1.14.1`, `matplotlib==3.9.4`, `numba==0.62.1` y `llvmlite==0.45.1`, que tienen ruedas
binarias para esa plataforma y evitan que Demucs use NumPy 2.x. Demucs corre en CPU (varios minutos por canción) con
semilla fija.

## Uso

Los audios van en `Angine de Poitrine Audios/`. Para analizar una canción sin abrir Jupyter:

```bash
.venv/bin/python scripts/run_song.py Fabienk
.venv/bin/python scripts/run_song.py "Mata Zyklek" --set "BAR_LENGTHS=(5, 4, 2)"
```

Cada corrida queda en `outputs/<fecha>_<hora>_<canción>/`:

| Archivo | Contenido |
|---|---|
| `harmony_outputs/` | tabroll por páginas, imagen completa y mapa de ciclos |
| `resumen.md`, `resumen.json` | tempo, tonalidad, compases, ciclos, capas y huellas SHA-256 del audio usado |
| `salida.txt` | todo lo que imprime el notebook, con el tiempo de cada celda |

Si las pistas `<canción>_guitar` y `<canción>_bass` no existen junto al audio, Demucs las crea y las guarda. El notebook
no se modifica: los ajustes se aplican solo a esa corrida.

| Opción | Para qué |
|---|---|
| `--set VARIABLE=valor` | cambia una variable del notebook en esa corrida; se puede repetir |
| `--guitar ruta --bass ruta` | usa pistas con otro nombre o en otra carpeta |
| `--sin-pistas` | analiza solo la mezcla, sin pistas ni Demucs |
| `--separador roformer` | usa las pistas de BS-RoFormer ([`docs/separacion_roformer.md`](docs/separacion_roformer.md)) |
| `--nombre etiqueta` | agrega una etiqueta al nombre de la carpeta |
| `--conservar N` | deja solo las N corridas más recientes |

## Reproducir los resultados

| Comando | Qué hace |
|---|---|
| `make run-sarniezz` | analiza Sarniezz de punta a punta |
| `make todo` | corre todas las canciones |
| `make graficas` | gráficas comparativas de la banda, los repertorios y los corpus |
| `make graficas-diapositivas` | solo las gráficas de la presentación |
| `make presentacion` | sirve la presentación en `http://localhost:8000` (notas del orador con la tecla S) |
| `make presentacion-imagenes` | copia a `presentacion/img/` las gráficas y el tabroll más recientes |
| `make presentacion-video` | descarga el fragmento de KEXP de la diapositiva 2 |
| `make defensa` | PDF con los puntos de la defensa |

`make help` lista todos los objetivos.

## Desarrollo

El notebook es la fuente de verdad. Los módulos de `src/tabroll/cells/` se generan desde él: el cambio se hace en la
celda y después se regenera.

```bash
make extract   # regenera los módulos y docs/cell-index.md
make check     # verifica la extracción (sin escribir), la sintaxis y las dependencias
make test      # todas las pruebas (unos 3 minutos)
```

`make extract` guarda la huella de cada módulo en `src/tabroll/cells/.extraccion.json`. Si un módulo se editó a mano, se
detiene y lo lista: hay que pasar el cambio al notebook o descartarlo con `scripts/extract_cells.py --force`.
`tests/test_extracted_cells.py` falla si notebook y módulos no coinciden.

## Documentación

| Documento | Contenido |
|---|---|
| [`docs/architecture.md`](docs/architecture.md), [`docs/cell-index.md`](docs/cell-index.md) | organización del código y correspondencia notebook ↔ módulos |
| [`docs/armonia.md`](docs/armonia.md) | armonía en 24-EDO: fundamentales, calidades de Piston, funciones de Riemann y ejes de Lendvai |
| [`docs/evaluacion_melodia.md`](docs/evaluacion_melodia.md), [`docs/analisis_melodico.md`](docs/analisis_melodico.md) | evaluación y análisis de la melodía |
| [`docs/corpus_estilos.md`](docs/corpus_estilos.md), [`docs/verosimilitud_por_bloques.md`](docs/verosimilitud_por_bloques.md) | corpus usados, método de comparación y sus límites |
| [`docs/graficas.md`](docs/graficas.md) | cómo se generan y leen las gráficas |
| [`docs/leyendas_figuras.md`](docs/leyendas_figuras.md) | pies de figura de la presentación, para el artículo |
| [`docs/glosario.md`](docs/glosario.md), [`docs/guion_defensa.md`](docs/guion_defensa.md) | glosario y guion de la defensa |
| [`docs/referencias_compiladas.md`](docs/referencias_compiladas.md) | bibliografía, corpus y fuentes |
| [`docs/escrito/`](docs/escrito) | borrador del escrito del trabajo de grado (LaTeX y PDF; `make escrito`) |
| [`docs/articulo/`](docs/articulo), [`docs/poster/`](docs/poster), [`docs/formulas/`](docs/formulas) | artículo, póster y resumen de fórmulas (LaTeX y PDF) |

## Datos y licencias

El audio de la banda no se distribuye. Los corpus de `references/corpus/` conservan la licencia de su fuente: antes de
redistribuirlos hay que revisarla (ver [`docs/corpus_estilos.md`](docs/corpus_estilos.md)). Los pesos de BS-RoFormer SW no
declaran licencia y se usan solo con fines académicos.

## Cómo citar

> Forero Rosales, S. (2026). *Análisis computacional de la banda Angine de Poitrine*. Departamento de Matemáticas,
> Facultad de Ciencias, Universidad Nacional de Colombia, sede Bogotá.
