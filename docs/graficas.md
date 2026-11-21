# Distribución de las gráficas comparativas

Las gráficas de `scripts/comparacion/` fijaban los márgenes como fracciones de la figura
(`subplots_adjust(left=0.14, top=0.84, …)`). Esas fracciones no conocen el largo de los textos ni el número de filas,
así que las etiquetas largas se cortaban, las leyendas caían sobre los datos y quedaban franjas vacías que crecían con
el alto de la figura. Los retoques a mano se perdían en cada `make graficas`. Esta nota registra cómo se pasó la
distribución al código.

## 1. Módulo común: `scripts/comparacion/estilo_figuras.py`

- `figura(ancho, alto_cuerpo, titulo, subtitulo, nota)` arma la figura en tres franjas: encabezado, cuerpo y pie.
  El alto del encabezado y del pie se calcula en pulgadas a partir de las líneas de texto, así que no crece con la
  figura. Los textos largos se parten solos según el ancho (`partir`).
- El cuerpo usa `layout="constrained"`: matplotlib mide etiquetas, títulos, barras de color y leyendas
  (`loc="outside …"`) antes de ubicarlos.
- `revisar(fig)` dibuja la figura y devuelve los problemas de distribución:
  - un texto que se sale de la figura;
  - dos textos que se montan (incluye marcas de los ejes y leyendas);
  - una leyenda o un texto suelto sobre el área de un gráfico;
  - una franja horizontal vacía de más de 0.6 in (`huecos`).
- `guardar(fig, ruta)` revisa, guarda e imprime cada problema como «aviso de distribución».
- `sin_repetidas(handles)` quita entradas de leyenda con la misma etiqueta.

## 2. Línea base

`revisar` sobre las cuatro gráficas tal como las generaba el código, con las corridas actuales:

| Gráfica | Problemas |
|---|---|
| `figuras_album_a_clasificacion` | 3 franjas vacías (0.7-0.8 in); leyenda con «sin vecino» repetido |
| `comparacion_tarjetas` | 5 franjas vacías (hasta 4.3 in); figura de 16.5 × 38.4 in |
| `verosimilitud_mapa` | leyenda sobre el gráfico; «★ Angine de Poitrine» montado sobre la marca 0.2 |
| `verosimilitud_matriz` | la nota se sale de la figura por la derecha |
| `ciclos_metricos` | 4 franjas vacías (hasta 3.1 in); una columna de 36 filas, 10.5 × 74 in |

## 3. Figuras rehechas

Cada figura quedó separada en una función que devuelve la figura (para probarla) y otra que la guarda con
`estilo_figuras.guardar`. Con las corridas actuales, las cinco salen sin avisos.

| Gráfica | Función | Cambio | Tamaño antes → después |
|---|---|---|---|
| Clasificación del álbum | `figuras_album.figura_clasificacion` | Dos subfiguras (mapa de calor y barras) con título propio; barra de color pegada al mapa; leyenda debajo de las barras sin la entrada «Sin vecino» repetida; resumen «Percentil ≥ 5…» como subtítulo del gráfico inferior; notas al pie | 12.5 × 9.9 → 12.5 × 9 in |
| Tarjetas | `comparar_tarjetas.dibujar` | Los seis paneles en una fila con las canciones compartidas en el eje vertical (formato apaisado para diapositiva); leyenda en una fila sobre los paneles; títulos y ejes partidos al ancho del panel; marcas del eje solo hasta el máximo | 16.5 × 38.4 → 21 × 10.1 in |
| Matriz de verosimilitud | `verosimilitud_estilos.figura_matriz` | Escala en el subtítulo; corpus y nota «¼ %» al pie, partidos al ancho | 10.6 × 23.9 → 11.2 × 18 in |
| Mapa de fundamentales | `verosimilitud_estilos.figura_mapa` | Leyenda a la derecha, fuera de los datos; sin el símbolo repetido en las etiquetas («★ ★») | 10 × 8.5 → 12 × 8.9 in |
| Ciclos métricos | `ciclos_metricos.dibujar` | Cuadrícula de 4 columnas con ejes compartidos, ordenada por artista; nombre de la canción como título de cada panel; leyenda en una fila | 10.5 × 74.4 → 16 × 11.9 in |

`figuras_album.guardar` ahora pasa por `estilo_figuras.guardar`, así que las demás figuras del álbum también avisan
si algo se monta. Todavía avisan `_b_perfil` (4 franjas vacías) y `_f_bucle_compas` (5), que siguen con márgenes fijos.

## 4. Corridas que entran a las gráficas

`scripts/graficas_completas.py` toma la corrida más reciente de cada canción. Las corridas con pistas de BS-RoFormer
(`…_roformer`) quedan fuera: Demucs sigue siendo el separador por defecto (ver `docs/separacion_roformer.md`).

## 5. Prueba automática

`tests/test_figuras_distribucion.py` arma las cinco figuras con datos sintéticos del tamaño real (6 canciones de la
banda, 36 en total, nombres largos) y exige que `revisar` no encuentre problemas. Otra prueba comprueba que `revisar`
sí detecta una leyenda sobre los datos, dos textos montados y un texto que se sale. Corre con `make test`.

## Cómo seguir

Para pasar otra gráfica al mismo esquema:

1. Separar el dibujo en una función que devuelva la figura.
2. Crearla con `figura(ancho, alto_cuerpo, titulo, subtitulo, nota)` y dibujar en el cuerpo (`cuerpo.subplots()`,
   `cuerpo.subfigures()`); leyendas con `cuerpo.legend(loc="outside …")`.
3. Guardarla con `guardar` y añadir un caso a `tests/test_figuras_distribucion.py`.

Quedan con márgenes fijos: `figuras_album` (b-f), `microtonal`, `pruebas_de_estilo`, `verosimilitud_por_bloques`,
`equivalencias_edo`, `comparar_repertorio` y `radar_ritmico`.
