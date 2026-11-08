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

Cada archivo comienza con una descripción que dice de qué celda del notebook viene. El prefijo del nombre es el orden de la celda entre las celdas de código. Por ejemplo:

- `005_find_stem.py`: función `find_stem`.
- `007_configuracion.py`: configuración de separación de stems.
- `023_stft_mag.py`: función de análisis espectral.
- `076_render_song_graphic.py`: función de renderizado.
- `093_configuracion.py` y `094_configuracion.py`: celdas finales de ejecución/visualización.

Las celdas que contienen varias funciones auxiliares permanecen juntas para no romper el contexto local de la celda original; el inventario completo de sus elementos está en [`cell-index.md`](cell-index.md). Esto mantiene la extracción fiel y permite refactorizarlas posteriormente sin perder trazabilidad.
