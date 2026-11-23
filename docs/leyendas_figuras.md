# Leyendas de las figuras

Textos que acompañaban las figuras de la presentación y que se quitaron de las diapositivas para dar espacio a las
gráficas. Se guardan aquí para usarlos como pies de figura en el artículo o en el documento escrito. En la presentación
siguen disponibles como notas del orador (tecla S).

Cada figura tiene dos tipos de texto:

- **Pie descriptivo:** qué muestra la figura y cómo se lee. Sirve como pie de figura en el escrito.
- **Pie de hallazgo:** la conclusión que se saca de la figura. En el escrito va mejor en el cuerpo del texto.

Las imágenes están en `presentacion/img/` y se regeneran con `make graficas-diapositivas` (ver [`graficas.md`](graficas.md)).

## Leyendas internas que se quitaron de las imágenes

En la versión de diapositiva (`--diapositiva`), las gráficas ya no llevan leyenda dentro de la imagen; solo conservan
las barras de color. La versión completa (`make graficas`) sí las conserva. Para el escrito conviene usar esa versión o
poner estas leyendas en el pie.

| Figura | Leyenda interna |
|---|---|
| 1b · mapa de fundamentales | Corpus y bandas: azul, rock (RS 200, 400 piezas); rojo, práctica común (Kostka-Payne, 46); verde, jazz (iRealPro, 1186); ocre, pop (Hooktheory, 121); estrella negra, Angine de Poitrine; rombo morado, Primus. Se quitó y después se recuperó: la diapositiva la vuelve a mostrar a la derecha |
| 2a · uso de los cuartos de tono | Naranja oscuro: como grado (estructural). Naranja claro: como inflexión (adorno) |
| 2b · círculo de 24-EDO | Círculo/anillo amarillo: grados regulares. Círculo/anillo azul: grados en cuarto de tono. Línea gris: transición dentro de un campo. Línea azul: transición entre campos. Punto grande: mayor tiempo melódico en el grado. Punto pequeño o tenue: menor uso del grado |
| 3a · ciclos métricos | Azul: Angine de Poitrine |
| 3b · clasificación por corpus | Barra de color: percentil medio de tipicidad, blanco = menor, azul oscuro = mayor. * Corpus con menos de 100 piezas: atenuados, no cuentan para el veredicto (en uno chico casi todo parece típico) |
| 3c · qué corpus gana cada bloque | Azul: radif, 7 victorias. Naranja: rock, 8 victorias. Gris: sin vecino, 9 casos |

## Diapositiva 16 · El algoritmo completo (diagrama por bloques)

**Pie descriptivo.** En amarillo, el núcleo propio del trabajo. «diap. n»: dónde se explicó cada paso. El pseudocódigo
está en la sub-diapositiva de abajo.

Para el escrito: «En amarillo, el núcleo propio del trabajo: la transcripción en 24-EDO guiada por el looper. Cada bloque
indica la sección donde se explica.»

## Diapositiva 18 · ¿La herramienta acierta?

**Pie descriptivo (versión final).** Contra las referencias corregidas de oído (corridas congeladas). En promedio, la
fundamental del acorde acierta el 85 % en los compases confiables y la melodía el 49 %.

Versión anterior, reemplazada: «Contra las referencias corregidas de oído (corridas congeladas). Yor Zarad: prueba a
ciegas, melodía 37 % y fundamental 88 %.» Se cambió para mostrar la media de las cuatro canciones.

## Diapositiva 19 · Armonía

### Vista conjunta (diapositiva eliminada)

- **1a, matriz con rock y pop (hallazgo).** Frente a rock y pop, los estilos más cercanos, el máximo es **17.7** (50 = pieza
  típica). En rock real, «sin vecino» sale el 5.2 % de las veces; en la banda, el 37.5 %.
- **1b, mapa de fundamentales (hallazgo).** Mata Zyklek y Utzp (pedales) quedan en el borde del rock; Sarniezz y Fabienk,
  donde no hay piezas de ningún corpus, por el peso de ♭VII y ♭III.
- **Nota del orador.** Calibración: en 388 piezas reales de rock, el método da «sin vecino» solo el 5.2 % de las veces.

### 1a · Matriz de verosimilitud

**Pie descriptivo.** Cada casilla es un percentil: el % de piezas del estilo que están igual o más lejos de su centro que
la canción (50 = pieza típica; 0 = más rara que todas). «¼ %»: tiempo con la fundamental en cuarto de tono, llevada al
grado de abajo porque ningún corpus tiene cuartos de tono. Corpus: RS 200, Kostka-Payne, iRealPro y 9 álbumes de
Hooktheory.

### 1b · Mapa de fundamentales

**Pie descriptivo.** Cada punto del fondo es una pieza de un corpus; los símbolos son las canciones comparadas. La
cercanía resume el parecido entre sus repartos de fundamentales. Cada eje es una componente principal; entre paréntesis,
los tres grados que más pesan en ella (+ y − indican el sentido).

## Diapositiva 20 · Melodía

### Vista conjunta (diapositiva eliminada)

- **2a (hallazgo).** Entre el **48 y el 82 %** de los cuartos de tono caen en **dos grados fijos** que vuelven en cada vuelta
  del loop. Angor (5 %) queda bajo el piso de ruido.
- **2b (hallazgo).** Dos familias de escala: **♭2+ y ♭6+** sobre frigio (Mata Zyklek, Yor Zarad, Utzp), y **7+, 6+ y ♭3+**
  sobre dórico (Sarniezz, Fabienk). Precisión para el escrito: la familia frigia es la más común en el radif persa y en
  King Gizzard; la dórica no la tiene ningún corpus medido (ver [`verosimilitud_por_bloques.md`](verosimilitud_por_bloques.md)).
  La versión de la diapositiva decía «cercana al maqam», que no está medido.

### 2a · Uso de los cuartos de tono

**Pie descriptivo.** Porcentaje del tiempo de la melodía en cuartos de tono: como grado sostenido (oscuro) o como adorno
de paso (claro). La franja gris es el piso de ruido medido en Primus, que no usa cuartos de tono. A la derecha, qué parte
de los cuartos de tono cae en los dos grados más usados.

### 2b · Círculo de 24-EDO

**Pie descriptivo.** La quinta de 24-EDO mide 14 pasos y mcd(14, 24) = 2: el ciclo se parte en dos campos, los grados
regulares (anillo exterior, amarillo) y los de cuarto de tono (interior, azul); cada grado «+» queda junto a su vecino
regular. El área del punto es el tiempo melódico; las líneas, los pasos melódicos más frecuentes. El panel grande
resume el álbum.

### Círculo en movimiento (se conserva en la diapositiva)

Notas del notebook sincronizadas con el audio; en «quintas», los dos campos de la 2b. Con tónica Sol, las voces giran
sobre Sol y Sol#+ (♭2+), el cuarto de tono del riff. Frente a la partitura corregida de oído: mismo grado el **87 %** del
tiempo en la voz aguda y el **94 %** en la grave; si falla, lee Sol#+ como Sol.

## Diapositiva 21 · Síntesis

### Vista conjunta (diapositiva eliminada)

- **3a (hallazgo).** Picos en **20 y 28 corcheas**: dos compases de 5 y de 7, los tiempos que la banda menciona (hipótesis).
  Sarniezz y Utzp, en cambio, van en 4.
- **3b (hallazgo).** Rock gana 8 de 24 bloques, radif 7 y en **9 no hay vecino**. El vecino más cercano es **King Gizzard**:
  en armonía, Angor es idéntica a «Flying Microtonal Banana».

### 3a · Ciclos métricos

**Pie descriptivo.** Cada barra mide cuánto se repiten las alturas y los ataques al comparar la música consigo misma ℓ
corcheas después (0 a 1). Un pico alto y aislado es un ciclo largo y estable; las cifras sobre las barras son los mejores
periodos.

### 3b · Clasificación por corpus

**Pie descriptivo.** Percentil medio de tipicidad de cada canción frente a cada corpus (azul oscuro = más parecido;
50 = pieza típica). «bl.» = bloques de rasgos con datos para esa canción y ese corpus. La fila «Álbum» es la media.
Atenuados (*): corpus con menos de 100 piezas, que no cuentan para el veredicto; por eso el 83 de Mata Zyklek en clásica
no es un parecido real.

### 3c · Qué corpus gana cada bloque

**Pie descriptivo.** En cuántas canciones del disco gana cada corpus en cada bloque de rasgos. «Sin vecino»: ningún
corpus pasa el percentil 5. Rock gana 8 de 24, radif 7 y en 9 no hay vecino.

## Otras notas retiradas de las diapositivas

- **Diapositiva 11 (Piston).** «Piston deja fuera las escalas microtonales: los grados en cuarto de tono quedan con
  función «neutra».» Se quitó de la diapositiva; la idea sigue en la tabla del estado del arte (diap. 6) y en
  [`armonia.md`](armonia.md).
