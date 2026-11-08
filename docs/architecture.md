# Organización del código

La extracción mantiene una relación uno a uno con el notebook:

```text
notebooks/Tabroll_Angine_de_Poitrine.ipynb
        │
        └── src/tabroll/cells/
            ├── celdas de inicialización y librerías
            ├── celdas de configuración
            ├── una función o clase por celda cuando corresponde
            ├── celdas de análisis de audio
            ├── celdas de renderizado
            └── celdas de ejecución y visualización final
```

Cada módulo comienza únicamente con la descripción de la función o del propósito de la celda. Los módulos de funciones y clases no llevan el número de la celda en el nombre. Por ejemplo:

- `find_stem.py`: función `find_stem`.
- `separar_guitarra_y_bajo_con_demucs.py`: configuración de separación de stems.
- `stft_mag.py`: función de análisis espectral.
- `render_song_graphic.py`: función de renderizado.
- `configuracion_093.py` y `configuracion_094.py`: celdas finales de ejecución/visualización.

Las celdas que contienen varias funciones auxiliares permanecen juntas para no romper el contexto local de la celda original; el inventario completo de sus elementos y el número original de celda están en [`cell-index.md`](cell-index.md). Esto mantiene la extracción fiel sin poner el número en el nombre del módulo.
