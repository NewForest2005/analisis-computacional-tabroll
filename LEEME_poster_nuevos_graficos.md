# LEEME — contenido actualizado para el póster

## 1. Qué va en la introducción

Este trabajo analiza computacionalmente la microtonalidad, los ciclos y la estructura armónica y rítmica de Angine de Poitrine, con énfasis en su uso de 24-EDO. El audio y las transcripciones se comparan con corpus de rock, jazz y músicas microtonales para distinguir rasgos propios de la banda, estilos existentes y posibles síntesis nuevas.

## 2. Qué va en la metodología

Incluir, de forma esquemática:

- Audio oficial y transcripciones MusicXML/MIDI como entradas.
- Separación de guitarra y bajo, detección de la frecuencia fundamental y conversión a MIDI fraccionario.
- Cuantización de alturas en 24-EDO, donde cada paso equivale a 50 cents.
- Extracción de perfiles de armonía, escala, cuartos de tono, metro y ciclos rítmicos.
- Comparación con corpus mediante distribuciones de rasgos, distancia Jensen--Shannon y vecinos del corpus.
- Resumen de resultados mediante percentiles, bloques de rasgos, radares y mapas.

### Fórmulas opcionales para la metodología

**Escala de tono logarítmica**

\[
c=1200\log_2\left(\frac{f}{f_0}\right)
\]

Convierte la razón entre dos frecuencias en una distancia de altura medida en cents.

**Transformada de Fourier**

\[
X[k]=\sum_{n=0}^{N-1}x[n]e^{-2\pi i kn/N}
\]

Descompone el audio en frecuencias para analizar su contenido espectral.

**Divergencia Jensen--Shannon**

\[
D_{\mathrm{JS}}(p,q)=\frac{1}{2}D_{\mathrm{KL}}(p\|m)+\frac{1}{2}D_{\mathrm{KL}}(q\|m),
\qquad m=\frac{p+q}{2}
\]

Compara distribuciones de rasgos y cuantifica la distancia entre una canción y un corpus.

## 3. Qué va en los resultados

### Clasificación del álbum por corpus

**Archivo:** figuras_album_a_clasificacion.png

Ubicar como primera gráfica de resultados. Muestra el percentil medio de tipicidad de cada canción frente a seis corpus; el azul más oscuro indica mayor parecido estadístico. La franja inferior resume qué corpus gana en armonía, escala, metro y cuartos de tono.

**Texto breve:**  
«El álbum presenta afinidades distintas según el bloque: la armonía, la escala, el metro y los cuartos de tono no necesariamente apuntan al mismo corpus.»

### Estructura rítmica comparada

**Archivo:** radar_ritmico_comparado.png

Ubicar después de la clasificación del álbum, en la sección de resultados rítmicos. Cada color representa una banda y cada eje muestra un rasgo rítmico; la distancia al centro indica su intensidad relativa.

**Texto breve:**  
«Angine de Poitrine combina compases cambiantes, ostinatos y ciclos desiguales; el perfil se compara con las medianas de las bandas de referencia.»

### Posición según fundamentales armónicas

**Archivo:** verosimilitud_mapa.png

Ubicar junto a las gráficas de comparación armónica o como cierre de resultados. Los puntos de fondo son piezas de los corpus; su color identifica el corpus, mientras las estrellas representan Angine de Poitrine y los rombos representan Primus.

**Texto breve:**  
«La posición resume la cercanía entre las distribuciones de fundamentales armónicas de las canciones y las de los corpus comparados.»

## 4. Qué va en perspectivas

Incluir como líneas futuras:

- Ampliar el análisis a todas las canciones disponibles de Angine de Poitrine.
- Mejorar la estimación automática de melodía y separar con mayor precisión las capas instrumentales.
- Comparar más corpus microtonales y añadir otros sistemas EDO.
- Evaluar la estabilidad de los resultados con distintas ventanas, semillas y métodos de transcripción.
- Desarrollar una representación conjunta que relacione microtonalidad, armonía, métrica y timbre.

## 5. Texto corto de conclusiones

Angine de Poitrine no se explica por un único estilo: su identidad aparece en la combinación de microtonalidad, ciclos rítmicos y relaciones armónicas. Las comparaciones muestran afinidades parciales con varios corpus, pero también una síntesis propia que depende del nivel musical analizado.

## Nota de diseño

Mantener títulos explícitos, ejes explicados, paletas visibles y una descripción breve debajo de cada gráfica; evitar repetir la misma explicación matemática en varias figuras.
