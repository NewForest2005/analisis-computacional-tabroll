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

## 6. Un símbolo y un color por artista en el mapa

El mapa de fundamentales dibujaba como estrella toda canción que no fuera de Primus. Con las 36 canciones, King
Gizzard, Zappa, King Crimson y Gentle Giant salían como estrellas, aunque la leyenda decía que eran Angine de Poitrine
(33 estrellas en vez de 6).

- `estilo_figuras.artista(corrida)` reconoce el artista por el nombre de la carpeta de la corrida (la misma regla que
  ya usaba `ciclos_metricos.py`, que ahora la llama desde ahí).
- `estilo_figuras.SIMBOLO_ARTISTA` fija símbolo y color, distintos de los colores de los corpus del fondo: Angine de
  Poitrine ★ negro, Primus ◆ violeta, King Gizzard ▲ magenta, Frank Zappa ■ cian, King Crimson ✚ gris azulado y
  Gentle Giant ✖ amarillo.
- La estrella de la banda es más grande (`s=200`) que los demás símbolos (`s=60`) y se dibuja encima.
- La leyenda solo lista los artistas presentes, así que la versión para diapositiva (banda y Primus) no cambia.

Angor y «Flying Microtonal Banana» son pedales sobre I (100 % de la fundamental en I, sin cambios): caen en el mismo
punto y la estrella tapa el triángulo.

## 7. Gráficas de la presentación

`make graficas-diapositivas` (`scripts/graficas_completas.py --clave`; `make graficas-clave` es un alias) corre solo
los scripts de las seis gráficas elegidas para la defensa. Deja las salidas normales en
`outputs/graficas_clave_<fecha>_<hora>/`, las versiones para diapositiva en `fuente_diapositivas/` y las seis finales,
numeradas, en `diapositivas/`. Tarda unos 5-6 minutos.

| Diapositiva | Eje | Izquierda | Derecha |
|---|---|---|---|
| 1 | Armonía: fuera de todos los corpus | `1a_armonia_matriz_verosimilitud` | `1b_armonia_mapa_fundamentales` |
| 2 | Melodía: cuartos de tono como grados fijos | `2a_melodia_uso_cuartos_de_tono` | `2b_melodia_circulo_24edo` |
| 3 | Síntesis: un híbrido | `3a_sintesis_ciclos_metricos` | `3b_sintesis_clasificacion_album` |

Las versiones para diapositiva usan la opción `--diapositiva` de cada script; sin ella, las gráficas de las 36
canciones salen igual que antes.

| Gráfica | Versión para diapositiva |
|---|---|
| 1a matriz | Solo las 6 canciones de la banda (el script corre solo con sus corridas; los percentiles no cambian). |
| 1b mapa | La banda frente a Primus. Estrellas más grandes (`s=260`, del tamaño visual de los rombos) y rombos más pequeños (`s=50`). La leyenda no cambia. |
| 2a cuartos de tono | Solo las 6 canciones; título de 15 pt en negrita; leyenda debajo del eje para no tapar las cifras. |
| 2b círculo | Sin cambios (ya muestra solo la banda). |
| 3a ciclos | Solo las 6 canciones, en 3 columnas; marcas del eje horizontal y su rótulo («Distancia ℓ entre repeticiones (corcheas)») en cada panel. |
| 3b clasificación | Sin cambios (ya muestra solo la banda). |

## 8. Gráficas de apoyo para la presentación

`make graficas-diapositivas` deja además en `diapositivas/` estas gráficas, que usan las diapositivas 13, 16 y 17:

| Archivo | Script | Qué muestra |
|---|---|---|
| `1a_armonia_matriz_rock_pop` | `verosimilitud_estilos.py --estilos rock,pop` | La matriz de la banda con solo rock y pop, que se lee a media diapositiva. Los percentiles no cambian. |
| `formula_js` | `figuras_presentacion.py` | Las fundamentales de Sarniezz frente al centro del rock y su distancia de Jensen-Shannon (0.52). |
| `formula_percentil` | `figuras_presentacion.py` | Las distancias de las piezas del rock a su centro; Mata Zyklek (p = 12, área verde) y Sarniezz (p = 0). |
| `formula_repeticion` | `figuras_presentacion.py` | R(ℓ) de Fabienk, con el pico en 28 corcheas. |
| `formula_campos` | `figuras_presentacion.py` | El círculo de 24-EDO de Mata Zyklek. |
| `acierto_herramienta` | `figuras_presentacion.py` | Melodía, bajo, fundamental y fundamental en compases confiables, por canción. |

- Las mini-gráficas de las fórmulas no llevan título: lo pone la diapositiva.
- El percentil del histograma es el de las fundamentales solas; la matriz promedia ese y el de los cambios de
  fundamental (en Mata Zyklek coinciden porque es un pedal).
- La fórmula de R(ℓ) en la diapositiva es la que usa el código (`ciclos_metricos.repeticion`): 0.7 × la fracción de
  corcheas con la misma clase de altura ℓ corcheas después + 0.3 × la coincidencia de ataques. No es la
  autocorrelación de `docs/formulas/`.
- El acierto se mide en las corridas congeladas `_repro`, las mismas de `docs/evaluacion_melodia.md` y
  `docs/armonia.md` (melodía 66.4, 46.2, 44.9 y 36.8; fundamental 95.4, 81.6 y 57.5). Otras corridas dan cifras
  algo distintas (por ejemplo, las `_cache` dan 66.5 y 45.4 en melodía).

`make presentacion-imagenes` copia a `presentacion/img/` todo lo que hay en la carpeta `diapositivas/` más reciente.

## 9. Versiones para diapositiva sin textos

En la presentación, el subtítulo y las notas al pie de cada gráfica van como leyenda HTML debajo de la imagen, para que
el gráfico se vea más grande. Con `--diapositiva`:

- `verosimilitud_estilos.py`: matriz y mapa sin subtítulo ni nota; la leyenda «Corpus y bandas» del mapa sube de 9 a
  11.5 pt.
- `ciclos_metricos.py`: sin subtítulo ni nota (además de las 3 columnas y las marcas en cada panel).
- `figuras_album.py`: solo hace la clasificación (a) y el círculo de 24-EDO (c). La clasificación va sin subtítulo ni
  nota; el círculo, sin subtítulo ni nota al pie, con la paleta en una franja de 3 columnas y los círculos de cada
  canción más grandes (con los rótulos y las líneas de paso del panel grande).

`make graficas-diapositivas` usa estas versiones para 1a, 1b, 2b, 3a y 3b; la 2a no tenía subtítulo ni nota.

La mini-gráfica del percentil lleva leyenda: gris, las piezas del rock; verde claro, las que quedan más lejos que Mata
Zyklek (su percentil).

## Cómo seguir

Para pasar otra gráfica al mismo esquema:

1. Separar el dibujo en una función que devuelva la figura.
2. Crearla con `figura(ancho, alto_cuerpo, titulo, subtitulo, nota)` y dibujar en el cuerpo (`cuerpo.subplots()`,
   `cuerpo.subfigures()`); leyendas con `cuerpo.legend(loc="outside …")`.
3. Guardarla con `guardar` y añadir un caso a `tests/test_figuras_distribucion.py`.

Quedan con márgenes fijos: `figuras_album` (b-f), `microtonal`, `pruebas_de_estilo`, `verosimilitud_por_bloques`,
`equivalencias_edo`, `comparar_repertorio` y `radar_ritmico`.
