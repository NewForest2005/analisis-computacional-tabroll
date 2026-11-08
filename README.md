# Análisis Computacional — Tabroll para Angine de Poitrine

Repositorio profesional para el análisis computacional de audio y la generación de un piano roll armónico/melódico estilo TheoryTab.

El notebook original se conserva en [`notebooks/Tabroll_Angine_de_Poitrine.ipynb`](notebooks/Tabroll_Angine_de_Poitrine.ipynb). Sus 94 celdas de código fueron extraídas en módulos Python independientes dentro de [`src/tabroll/cells`](src/tabroll/cells). Cuando una celda define una función principal, el archivo usa el nombre de esa función; las celdas de configuración, clases o varias funciones usan un nombre descriptivo y mantienen el número de celda original.

## Estructura

- `notebooks/`: fuente interactiva original.
- `src/tabroll/cells/`: extracción ordenada, una celda de código por archivo.
- `docs/cell-index.md`: inventario y trazabilidad entre notebook y módulos.
- `docs/architecture.md`: cómo se separan funciones, clases, inicialización, configuración y ejecución.
- `scripts/extract_cells.py`: regenera la extracción cuando cambia el notebook.
- `tests/`: validaciones estructurales básicas.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Demucs es opcional y solo se necesita para separar guitarra y bajo. La ejecución completa requiere además `ffmpeg` disponible en el sistema.

## Uso

La extracción conserva el orden de ejecución del notebook. Para reproducir el análisis completo, abrir el notebook en Jupyter/Colab y ejecutar las celdas en orden. Los módulos extraídos funcionan como una base auditable para migrar progresivamente el flujo a una API Python más desacoplada.

## Calidad

```bash
python -m compileall -q src
pytest
```

Los comandos de shell propios de Jupyter se conservan como comentarios en el módulo correspondiente para que todos los archivos `.py` sean sintácticamente válidos.

## Regenerar los módulos

El número del nombre de cada archivo corresponde al orden entre las celdas de código, no al índice absoluto del notebook. Por ejemplo, `005_find_stem.py` proviene de la celda 6 del notebook.

Si se modifica el notebook, regenerar los módulos con:

```bash
python scripts/extract_cells.py
```
