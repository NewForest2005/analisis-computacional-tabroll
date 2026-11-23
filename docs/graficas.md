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

`make graficas-diapositivas` deja además en `diapositivas/` estas gráficas, que usan las diapositivas 14, 17 y 18:

| Archivo | Script | Qué muestra |
|---|---|---|
| `1a_armonia_matriz_rock_pop` | `verosimilitud_estilos.py --estilos rock,pop` | La matriz de la banda con solo rock y pop, que se lee a media diapositiva. Los percentiles no cambian. |
| `formula_js` | `figuras_presentacion.py` | Las fundamentales de «My Name Is Mud» (Primus) frente al centro del rock y su distancia de Jensen-Shannon (0.15). |
| `formula_percentil` | `figuras_presentacion.py` | Las distancias de las piezas del rock a su centro; «My Name Is Mud» (p = 37.2, área verde) y «Jerry Was a Race Car Driver» (p = 2.2). |
| `formula_repeticion` | `figuras_presentacion.py` | R(ℓ) de «Jerry Was a Race Car Driver», con el pico en 8 corcheas (un compás de 4/4). |
| `formula_campos` | `figuras_presentacion.py` | Solo la geometría de los dos campos de quintas (sin datos de ninguna canción). |
| `acierto_herramienta` | `figuras_presentacion.py` | Melodía, bajo, fundamental y fundamental en compases confiables, por canción. |

Las cuatro gráficas de fórmulas se ilustran con Primus (la comparación propia) y no con la banda: la diapositiva 14 es
metodología y no debe adelantar los resultados de las diapositivas 19 a 21.

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

## 10. Círculo de 24-EDO interactivo en la presentación

`web/circulo24/` (página y `circulo24.js`) anima las notas de una corrida sobre las 24 clases de altura, con el audio
sincronizado. `make presentacion-circulo` exporta a `presentacion/circulo24/` el fragmento de Mata Zyklek de 42 a 72 s
(entra el riff en la guitarra 3, luego en la guitarra 4 con el bajo), y la sub-diapositiva 20 · 3 lo muestra en un iframe.

Elección del fragmento, con `scripts/comparacion/probar_circulo24.py` (cuadro a cuadro, contra la referencia corregida
de oído de `references/mata_zyklek_loops.py`; `--barrido` recorre la canción en ventanas de 30 s):

| Fragmento | Voz aguda: mismo grado | Voz grave: mismo grado | Cuartos de tono (referencia · círculo) |
|---|---:|---:|---|
| 162–192 s (el anterior) | 69.0 % | 86.8 % | 25 % · 38 % |
| 42–72 s (el actual) | 86.9 % | 94.4 % | 23 % · 17 % |

- El anterior se había elegido por tener más cuartos de tono, pero la mitad de ellos eran errores: es la melodía 1,
  donde el cuaderno da el Fa un cuarto de tono abajo (Mi+) y el Ré un cuarto de tono arriba (Ré+). El arbitraje a
  ciegas de oído ya había decidido que esas notas son Fa y Ré, como en la partitura. Además, en el corte (165–191 s) el
  bajo 1 suelto quedó fuera de la referencia por dudoso, y el círculo pintaba ahí 8.5 s de Ré grave sin poder comprobarlo.
- En el actual los cuartos de tono son reales (Sol#+, el ♭2+ del riff). Cuando falla, el círculo se queda corto: lee
  Sol#+ como Sol, no inventa cuartos de tono.
- Sincronía (revisada el 23-nov con `scripts/comparacion/sincronia_circulo24.py`, que prueba el paquete exportado, el
  mismo que abre la diapositiva):
  - Las tres pistas recortadas duran 30.00 s y coinciden al milisegundo con el audio original.
  - Las notas del cuaderno iban adelantadas. Su espectro usa una ventana de 4096 muestras (186 ms) centrada, que ya
    «ve» la nota cuando empieza a cubrirla. Corriendo las notas de 5 en 5 ms, el mejor acuerdo con el audio fue: voz
    grave +55 ms (pYIN y ataques coinciden); voz aguda +50 ms con pYIN (meseta de 35 a 70 ms) y +75 ms con los ataques.
  - En la canción entera no hay deriva (la pendiente del desfase es casi 0): es un corrimiento fijo, no un error de escala.
  - `exportar_circulo24.py` atrasa las notas al exportar (`--desfase-aguda 0.060`, `--desfase-grave 0.055`) y lo anota
    en `datos.js` (`desfase_notas`). Después, el mejor desfase es −10 ms en la aguda y 0 ms en la grave, dentro del
    paso de medida; pYIN coincide con el círculo en el 72 % (aguda) y el 80 % (grave) de los cuadros, frente a 64 % y
    67 % antes.
- Notas sueltas: el círculo mostraba un Do (3 notas de 0.12 a 0.14 s) que no está en la referencia de oído: errores de
  quinta (Do es el tercer armónico de Fa; en el bajo, una quinta bajo Sol). `--min-uso 0.02 --max-suelta 0.15` quita
  las notas de menos de 0.15 s de grados que suman menos del 2 % del tiempo de la voz; en este fragmento quita
  exactamente esas tres. Con todo, la melodía exportada da el mismo grado que la referencia de oído en el 90 % del
  tiempo (aguda) y el 88 % (grave), y no muestra ningún grado ausente de la referencia.
- Estilo: fuentes y colores de la plantilla; amarillo = grado regular y azul = cuarto de tono, como en la gráfica 2b;
  voz aguda en rojo y grave en verde (antes azul, que se confundía con el cuarto de tono).
- Disposición nueva «quintas (dos campos)», además de la cromática: el anillo exterior es el ciclo de quintas de los
  grados regulares y el interior el de los cuartos de tono, como en la 2b. Se elige en la página o con
  `?disposicion=quintas`; la diapositiva empieza así.
- Dentro de la presentación: tema claro, solo la clave de colores (la explicación va en la leyenda de la diapositiva),
  pausa al cambiar de diapositiva y las flechas del teclado siguen pasando diapositivas.
- `exportar_circulo24.py --recortar` corta cada pista al fragmento con ffmpeg (unos 600 KB por pista) y escribe
  `audio_inicio = 0` en `datos.js`.
- Errores corregidos: sin audio, el reloj propio nunca avanzaba (`!usarAudio` en vez de `!usarAudio()`); la barra
  espaciadora con un botón enfocado se activaba dos veces; al cambiar de pista mientras sonaba quedaba en «Pausa» sin
  sonido; guitarra y bajo juntos se desfasaban (ahora se realinean si se separan más de 60 ms); el anillo interior y
  las huellas en cero se veían porque la opacidad del CSS pisaba el atributo SVG.

## 11. Figuras del primer cuaderno (diapositiva 9)

Las imágenes que guardó el primer cuaderno tenían letra demasiado pequeña para la diapositiva.
`scripts/comparacion/figuras_cuaderno_original.py <audio_arrays.npz>` las vuelve a dibujar con letra de 12-13 pt y los
colores de la plantilla, con los mismos cálculos:
- el contorno pYIN del bajo de Sarniezz (fmin Do2, fmax Do7, ventana de 2048);
- la desviación en cents respecto del semitono más cercano (sale entre −50 y +50, como en el cuaderno);
- la matriz de confusión de la red por sección, copiada de la salida del cuaderno (3 de 7 aciertos).

`audio_arrays.npz` viene de `todos_los_outputs_sarniezz.zip` del primer cuaderno (no está en el repositorio). El contorno
se guarda en `outputs/.f0_cuaderno_original.npz` para no recalcularlo.

La figura de la diapositiva 7 (`cuaderno_original_sarniezz.png`) era una captura del primer cuaderno con letra ilegible.
Ahora la dibuja el mismo script con `--partitura mxl/score.xml` (del mismo zip).
- Solo queda el piano roll. La segunda mitad, la misma partitura leída como MusicXML, era igual y se quitó.
- Muestra las primeras 64 negras (`--hasta`), 77 de las 196 notas, para que no queden apretadas; las alturas son las
  escritas, como las leía el cuaderno.
- El eje del original decía «pulsos de negra» pero estaba en semicorcheas (`divisions` = 4: llegaba a ~600). El nuevo
  está en negras (~152).
- La leyenda de la diapositiva perdió el párrafo «Primera idea del trabajo de grado».

La red por sección del primer cuaderno (diapositivas 7 y 9), según `CMA_Angine_de_Poitrine_corregido.ipynb`:

| Paso | Detalle |
|---|---|
| Datos | 28 fragmentos del bajo de Sarniezz (27 de 10 s y uno de 9.1 s), etiquetados a mano en `etiquetas_sarniezz.csv`: verso 7, riff 6, puente 5, clímax 4, intro 3, outro 3 |
| Rasgos | 13 MFCC por fragmento (librosa, `n_fft` = 2048, `hop_length` = 512); media y desviación de cada uno: 26 números |
| Modelo | `StandardScaler` + `MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=1234)` |
| Partición | `train_test_split` estratificado, 25 % de prueba, semilla 1234: 21 de entrenamiento y 7 de prueba |
| Resultado | 3 de 7 aciertos (43 %) |

Los MFCC resumen la forma del espectro en bandas Mel: describen el timbre, no la nota. Con 21 ejemplos para 6 secciones
y un timbre del bajo casi igual en toda la canción, no bastan para reconocer la sección. En la diapositiva 7 se glosan
como «13 coeficientes del espectro que describen el timbre, no la nota».

## 12. El algoritmo completo (diapositiva 16)

La diapositiva 16 junta todo el método antes del repositorio. Las diapositivas siguientes se corrieron un número.
- **Principal:** el diagrama de bloques del póster (`02_diagrama_bloques.png`), rehecho en HTML con los colores de la
  plantilla. Tiene tres etapas: señal, núcleo del looper (en amarillo) y estructura y estilo. Cada bloque dice en qué
  diapositiva se explicó.
  - Añade dos pasos que el póster no tenía: la atracción al registro de la melodía y la limpieza de notas sueltas.
  - Añade también el tabroll como salida.
- **Sub-diapositiva:** el pseudocódigo, de 15 líneas. Sus parámetros vienen del código:

| Paso | Parámetros | Módulo |
|---|---|---|
| Separación | `htdemucs_6s`, semilla 0 | `separate_stems.py` |
| Saliencia | H = 10, α = 0.82, candidatos cada 25 cents | `pitch_salience.py` |
| Ciclos | autocorrelación, periodos de 1 a 16 s | `find_cycles.py` |
| Consenso | media de la misma fase en ±3 vueltas (ciclos ≥ 2 s) | `configuracion_064.py` |
| Registro | w = 0.7 + 0.3·exp(−½((m − r)/12)²), r = mediana del Viterbi de base | `configuracion_064.py` |
| Viterbi | salto 0.01 por paso de 25 cents | `viterbi_pitch.py` |
| Notas sueltas | menos de 80 ms y sin repetición a ±1 vuelta | `drop_loose_notes.py` |
| Compases | programación dinámica, L de 2 a 8 pulsos | `segment_bars.py` |
| Acorde | 8 calidades en 24-EDO, bajo + 0.6·aguda; κ = p(fundamental)·acuerdo·cobertura | `chord24.py`, `harmony_by_bar.py` |
| Test | k = 5 vecinos (Jensen-Shannon), umbral 5 %, error medido en Primus | `verosimilitud_por_bloques.py` |

El pie de cada sub-diapositiva puede llevar un nombre propio con `data-sub` (aquí «pseudocódigo»). Sin él, dice «gráfica n».

## 13. El tabroll de Fabienk en la diapositiva 10

La diapositiva 10 compara Hooktheory con el tabroll. Se usa la página 32 de Fabienk, de 4:42 a 4:52 (melodía «Fabien»
con la segunda voz en el loop), de la corrida más reciente con Demucs. Se eligió comparando cada página después de las
3:00 con la partitura corregida de oído (`references/fabienk_partitura.py`, alineada como en `melodia.py`):

| Página | Tramo | Voz aguda: misma nota que la melodía | Notas en alguna guitarra | Cuartos de tono en la partitura |
|---|---|---:|---:|---:|
| 25 | 3:43-3:53 | 73 % | 34 de 48 | 4 de 11 |
| 32 | 4:42-4:52 | 78 % | 53 de 59 | 6 de 8 |
| 33 | 4:52-5:01 | 80 % | 48 de 52 | 3 de 4 |

La 25, la primera elegida (vuelve la guitarra), marcaba cuartos de tono que la partitura no tiene: Fa+ y Fa♯+ donde
suena Sol, y Do♯+ donde suena Re. La 32 tiene la melodía principal y casi todos sus cuartos de tono están en la
partitura. De 3:07 a 3:34 no suena la guitarra.

Entera, la página quedaba a una quinta parte de su tamaño y no se leían las notas de la izquierda.
`zoom_guitarra` (en `scripts/presentacion_imagenes.py`) la rehace:
- Recorta el registro de la guitarra, de Re♯3+ a Mi4+, y estira las filas al doble.
- Rehace la columna de notas con letra grande: las notas regulares a la izquierda y los cuartos de tono («+», en azul) a
  la derecha, como la regla de la diapositiva 8. Al lado va el grado de Mi dórico en color.
- Rehace también la cabecera de pulsos («6 pulsos», en español) y la franja de acordes: cifrado romano con su índice,
  función en palabras («Tónica relativa», «Dominante modal», en lugar de «T rel.» y «D modal»; en dos renglones si no
  cabe; «(menor)» debajo cuando el cuaderno la escribe en minúscula, como «t») y nombre del acorde, todo con letra grande. Los datos salen de `armonia.json` (con `harmony_labels`, como en
  el cuaderno). Los compases de la página se reparten como `_pages` (hasta 21 pulsos), con el tempo de `salida.txt`.
- Se detiene si las líneas de octava no están donde espera o si los compases no caben en la página.

## Cómo seguir

Para pasar otra gráfica al mismo esquema:

1. Separar el dibujo en una función que devuelva la figura.
2. Crearla con `figura(ancho, alto_cuerpo, titulo, subtitulo, nota)` y dibujar en el cuerpo (`cuerpo.subplots()`,
   `cuerpo.subfigures()`); leyendas con `cuerpo.legend(loc="outside …")`.
3. Guardarla con `guardar` y añadir un caso a `tests/test_figuras_distribucion.py`.

Quedan con márgenes fijos: `figuras_album` (b-f), `microtonal`, `pruebas_de_estilo`, `verosimilitud_por_bloques`,
`equivalencias_edo`, `comparar_repertorio` y `radar_ritmico`.
