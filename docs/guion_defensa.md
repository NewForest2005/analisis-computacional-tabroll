# Guion de la defensa

Lo que se dice en cada diapositiva de `presentacion/index.html`, con la numeración actual (25 diapositivas; la 6 es
«Estado del arte»). Cada diapositiva lleva un recuadro de **Términos**: cada término se explica la primera vez que
aparece. Los que ya se explicaron antes (24-EDO, MIDI, cents, pYIN, piano roll, compás, Riemann, Piston, Basic Pitch)
están en [`glosario.md`](glosario.md). Las fuentes citadas están en [`referencias_compiladas.md`](referencias_compiladas.md).

Por ahora cubre de la diapositiva 12 a la 23 (Trabajo futuro).

---

## 12 · Mejorar la melodía: hipótesis que se prueban

«Para mejorar la melodía probamos varias ideas. Cada una se midió y, según el resultado, se adoptó o se descartó.

- **Adoptadas:**
  - el consenso entre vueltas del looper, que hace todo más rápido y estable;
  - la atracción al registro de la melodía, con la que Mata Zyklek pasó de 57 a 64;
  - quitar las notas sueltas, que suma 3 puntos en las tres canciones.
- **Descartadas:**
  - guiarse por la partitura, porque la herramienta debe servir sin ella;
  - REPET, que deja solo entre el 1 y el 18 % de la melodía;
  - Basic Pitch, que da menos melodía y no tiene cuartos de tono;
  - unir notas iguales seguidas, porque borra re-ataques reales.

Todo se mide con la medida F de notas: el ataque tiene que caer a ±75 ms y la altura en la misma casilla de 24-EDO.
Donde el notebook y la partitura no coincidían, escuchamos los clips a ciegas, y la partitura tenía razón solo la mitad
de las veces. Por último, dos separaciones de la misma canción daban 57 y 62. Por eso un hallazgo solo cuenta si se
mantiene en las dos.»

> **Términos**
> - **Consenso entre vueltas:** como el loop se repite, en cada punto se combina lo que suena en las distintas vueltas y gana lo que más se repite.
> - **Registro:** la zona de alturas (grave, media o aguda) donde suele ir la melodía.
> - **Medida F:** combina cuántas de las notas detectadas son correctas (*precisión*) y cuántas de las notas reales se encontraron (*exhaustividad*), con la media armónica \(2PR/(P+R)\). Va de 0 a 100. Viene de la evaluación de buscadores (van Rijsbergen, 1979); la «F» no es una sigla. Detalle y ejemplo en el glosario.
> - **Ataque:** el instante en que empieza una nota.
> - **Arbitraje a ciegas:** escuchar los dos clips en orden al azar, sin saber cuál es de la partitura y cuál del notebook.
> - **REPET:** algoritmo que separa lo que se repite de lo que no (Rafii y Pardo, 2013).
> - **Re-ataque:** volver a tocar la misma nota.
> - **Semilla fija:** fijar el azar del programa para que cada corrida dé lo mismo (en la diapositiva: «el azar queda fijo y cada corrida da lo mismo»).
> - **Huella SHA-256:** la huella digital de un archivo: un código de 64 caracteres que cambia por completo si el archivo cambia en lo más mínimo (NIST, 2015). Sirve para saber que dos corridas usaron exactamente el mismo audio. Detalle en el glosario.

---

## 13 · Separar instrumentos: Demucs y BS-RoFormer

«BS-RoFormer separa la guitarra mucho mejor que Demucs: 9.05 dB frente a 5.22. Aun así, la melodía de Sarniezz quedó
igual con los dos, en 44.9, y el bajo hasta bajó un poco, de 78.6 a 76.5. Además, BS-RoFormer tardó una hora en separar
una sola canción.

¿Por qué no mejoró? El separador limpia la guitarra de los demás instrumentos, pero el problema está dentro de la
guitarra: el looper superpone varias capas del mismo instrumento, y ningún separador las distingue.

Este resultado negativo no invalida el trabajo. Muestra que la medida no depende del separador y ubica el cuello de
botella. Por eso Demucs sigue por defecto y BS-RoFormer queda como opción.»

> **Términos**
> - **Separación de fuentes:** sacar de una mezcla cada instrumento por aparte.
> - **Demucs / BS-RoFormer:** dos redes neuronales que separan instrumentos (Rouard et al., 2023; Lu et al., 2024); BS-RoFormer es más reciente y más precisa.
> - **SDR (dB):** *signal-to-distortion ratio*, mide qué tan limpia sale la pista separada. Más alto es mejor.
> - **CPU:** el procesador común del computador, más lento que una tarjeta gráfica para este cálculo.
> - **Resultado negativo:** un experimento en el que la mejora esperada no apareció. También es información.
> - **Cuello de botella:** el paso que limita todo el resultado.

---

## 14 · Background matemático: comparar con estilos

«Para comparar con estilos usamos cuatro fórmulas. Las ilustramos con Primus para no adelantar los resultados de la
banda.

- **La distancia de Jensen-Shannon** mide qué tan distintos son dos repartos de fundamentales. «My Name Is Mud» está a
  0.15 del centro del rock.
- **El percentil de tipicidad** dice qué parte del corpus está igual o más lejos de su centro que la canción. «My Name Is
  Mud» da 37, casi típica (la típica sería 50). «Jerry Was a Race Car Driver» da 2.2: es rara.
- **La repetición a distancia ℓ** encuentra el ciclo de la música. Pesa 70 % que se repita la misma nota y 30 % que se
  repita el ataque. Jerry se repite cada 8 corcheas, o sea un compás de 4/4.
- **Los dos campos de quintas:** en 24-EDO la quinta mide 14 pasos, y como mcd(14, 24) = 2, el ciclo de quintas se parte
  en dos. Un campo tiene los grados regulares y el otro los grados en cuarto de tono.»

> **Términos**
> - **Fundamental:** la nota base de un acorde, la que le da nombre.
> - **Reparto de fundamentales:** qué porcentaje del tiempo pasa la canción sobre cada grado (I, IV, V…).
> - **Divergencia de Kullback-Leibler (D_KL):** la pieza básica de Jensen-Shannon; mide cuánto se aleja un reparto de otro.
> - **Centro del estilo:** el reparto promedio de todas las piezas de un corpus.
> - **Percentil de tipicidad:** el porcentaje de piezas del corpus que están igual o más lejos del centro que la canción. 50 es típica y 0 es más rara que todas.
> - **Corchea:** la mitad de una negra; es la unidad con la que se mide la repetición.
> - **R(ℓ):** cuánto se parece la música a sí misma ℓ corcheas después. Un pico indica un ciclo.
> - **mcd:** máximo común divisor. Que dé 2 significa que el ciclo de quintas recorre solo 12 de las 24 notas y deja las otras 12 aparte.
> - **Campo:** cada uno de esos dos grupos de 12 notas.

---

## 15 · Datos para comparar estilos e influencias

«Medimos 36 canciones con el mismo notebook: las 6 del álbum, las influencias que cita la banda (King Gizzard, Zappa,
King Crimson y Gentle Giant) y Primus, que es la comparación propia. Además usamos seis corpus de estilos: rock
(Rolling Stone 200, 200 canciones con dos analistas), práctica común (Kostka-Payne, 46 piezas), jazz (iRealPro, 1 186),
pop (Hooktheory, 121), radif persa (229) y música indostánica (50). El makam turco y el folk irlandés están descargados,
pero no entraron en la comparación, y el maqam árabe no tiene un corpus simbólico abierto.»

> **Términos**
> - **Rolling Stone 200:** las 200 mejores canciones de rock según la revista Rolling Stone, con su armonía analizada por dos analistas (400 análisis).
> - **Práctica común (Kostka-Payne):** música clásica tonal, de Bach a Brahms, tomada de un libro de texto de armonía; solo trae armonía.
> - **iRealPro:** una aplicación con los acordes de los estándares de jazz.
> - **Radif:** el repertorio clásico de la música persa, organizado en modos.
> - **Indostánica:** música clásica del norte de la India; el corpus trae alturas en 22 *shrutis*, llevadas a los 24 grados.
> - **Makam / maqam:** sistemas de modos de la música turca y árabe, que usan intervalos menores que el semitono.
> - **Corpus simbólico:** piezas guardadas como notas (partitura) y no como audio.

---

## 16 · El algoritmo completo

«Este es el mapa de todo el método, del audio al veredicto de estilo, en tres etapas.

**Primera, la señal:** el audio oficial se separa con Demucs en guitarra y bajo. Luego se calcula la saliencia armónica,
que da evidencia de cada altura posible cada 25 cents.

**Segunda, el núcleo, en amarillo, que es la parte propia del trabajo.** Como la banda repite cada riff con el looper,
primero se busca el ciclo del looper. Después se promedia la altura entre vueltas, se atrae la melodía a su registro
típico, Viterbi traza el contorno y las notas caen en la rejilla de cuartos de tono. Al final se quitan las notas
sueltas. Por eso el método funciona con cuartos de tono.

**Tercera, estructura y estilo:** se detectan pulsos y compases, se elige un acorde por compás con su confianza, se
dibuja el tabroll y se comparan cuatro bloques de rasgos con los corpus.

Cada caja dice en qué diapositiva se explicó ese paso. Abajo está el pseudocódigo con los parámetros reales del código.»

*(Sub-diapositiva del pseudocódigo: no hace falta leerla. Si preguntan, las líneas 3 a 8 son el núcleo del looper.)*

> **Términos**
> - **Saliencia armónica:** evidencia de cada altura en cada instante, sumando la energía de sus armónicos. A diferencia de pYIN, mira todas las alturas a la vez.
> - **Autocorrelación:** comparar la señal consigo misma desplazada en el tiempo; un pico indica cada cuánto se repite.
> - **Viterbi:** algoritmo que elige la secuencia de notas más probable sin saltos innecesarios (Viterbi, 1967).
> - **Programación dinámica:** resolver un problema grande combinando las mejores soluciones de sus partes; aquí, la mejor división en compases (Ellis, 2007).
> - **Confianza κ:** qué tan segura está la herramienta del acorde de un compás.
> - **Pseudocódigo:** el algoritmo escrito paso a paso en lenguaje matemático, sin un lenguaje de programación concreto.

---

## 17 · El repositorio en GitHub

«Todo el trabajo es reproducible y está en un repositorio público.

**El notebook es la fuente de verdad:** todos los cambios se hacen ahí. `make extract` lo parte en un archivo por celda
y guarda la huella de cada uno. `run_song.py` corre todas las celdas sobre una canción, de punta a punta, y las salidas
quedan en `outputs/`: el tabroll, la armonía, los ciclos y un resumen.

Si alguien edita un módulo a mano, su huella deja de coincidir y la extracción se detiene en vez de borrar el cambio. El
notebook siempre manda.

Además están las referencias (partituras y corpus), la documentación, esta misma presentación y 107 pruebas
automáticas.»

> **Términos**
> - **Repositorio (GitHub):** la carpeta del proyecto con todo su historial de cambios, publicada en línea.
> - **Reproducible:** otra persona puede correrlo y obtener los mismos resultados.
> - **Notebook:** documento que mezcla código, texto y gráficas, y se ejecuta celda por celda (aquí, Jupyter/Colab).
> - **Celda:** cada bloque de código del notebook.
> - **Fuente de verdad:** el único lugar donde se edita; todo lo demás se genera desde ahí.
> - **Módulo:** un archivo de código; aquí, una celda del notebook convertida en archivo.
> - **Script:** un programa corto que se corre desde la consola, como `run_song.py`.
> - **make:** herramienta que ejecuta tareas con un solo comando (`make extract`, `make presentacion`…).
> - **Huella:** la huella SHA-256 de cada módulo (ver diapositiva 12): si el archivo cambia, la huella cambia.
> - **Pruebas automáticas:** pequeños programas que verifican que el código sigue dando lo que debe (`pytest`).

---

## 18 · ¿La herramienta acierta?

«Comparamos lo que da la herramienta con las partituras corregidas de oído, en corridas congeladas. La melodía queda en
valores medios: 49 % en promedio. La fundamental del acorde, en cambio, acierta el **85 %** de las veces en los compases
confiables, como marca la línea punteada.

¿Por qué la armonía es fiable aunque la melodía no lo sea tanto? Por cuatro razones:

1. **El bajo manda:** para decidir la fundamental, el bajo pesa 1 y la voz aguda 0.6, y el bajo es lo mejor transcrito.
2. **Se suma sobre las vueltas del loop:** un error en una vuelta queda en minoría frente a las demás.
3. **La octava no importa:** una nota una octava arriba cuenta como la misma clase de altura.
4. **Se mide por compás y no por nota:** la melodía exige acertar el ataque a ±75 ms; el acorde solo exige saber qué notas
   suenan en el compás.

Lo comprobamos en un experimento aparte: cambiamos solo el peso de la melodía. La melodía de Fabienk varió de 41 a 44 % y
la de Sarniezz de 46 a 48 %, y su fundamental quedó idéntica en las tres corridas. La armonía no depende de lo que le
pase a la melodía.»

> **Términos**
> - **Referencia corregida de oído:** la partitura revisada escuchando la grabación; es la respuesta correcta con la que se compara.
> - **Corrida congelada:** una ejecución guardada que no se vuelve a tocar, para que los números citados no cambien.
> - **Acierto de la melodía:** la medida F de notas (diapositiva 12): ataque a ±75 ms y misma casilla de 24-EDO.
> - **Acierto de la fundamental:** el porcentaje de compases en que la fundamental del acorde coincide con la de la partitura.
> - **Compás confiable:** un compás en el que la herramienta tiene suficiente evidencia para decidir el acorde (su confianza κ supera el umbral).
> - **Media (4 canciones):** el promedio simple de Mata Zyklek, Fabienk, Sarniezz y Yor Zarad.
> - **Prueba a ciegas:** medir una canción que no se usó para ajustar la herramienta; en la gráfica es Yor Zarad.
> - **Peso de la melodía:** cuánto cuenta la voz aguda frente al bajo, aquí 1 frente a 0.6.
> - **Clase de altura:** la nota sin importar la octava; todos los Do son la misma clase.

**Si preguntan por Sarniezz:** es la canción más baja en armonía (58 %; 67 % en los 76 compases confiables). En la
versión del cuaderno del 10-nov daba 72 % (ver [`armonia.md`](armonia.md)): es la más sensible a los cambios de código.
El ♭III **no** es la causa: se acierta en el 87.5 % de sus compases. Los 25 errores vienen de dos sitios
(`evaluacion_armonia_por_compas.csv` de la corrida `_repro`):

- **♭VIIsus2** (Re sus2: Re, Mi, La), el acorde más frecuente (45 % de los compases), acierta solo el 62 %: se confunde
  con ♭III (Sol, 7 compases) o con i (Mi menor, 6), con los que comparte notas. Los sus2 son ambiguos por naturaleza
  (Re sus2 y La sus4 tienen las mismas notas).
- **I** (Mi mayor, 8 compases) acierta el 12.5 %: casi siempre sale como un acorde sobre VII (Re♯), medio tono abajo.
  Encaja con lo que documenta [`armonia.md`](armonia.md): el bajo detectado en Re♯+ es el Mi de la partitura, un bajo
  a un cuarto de tono que la fundamental redondea hacia abajo.

> «En Sarniezz la armonía baja porque su acorde más usado es un sus2, que comparte notas con sus vecinos, y porque el
> bajo de Mi suena un cuarto de tono bajo y la herramienta lo lee como Re♯.»

Datos: corridas congeladas `_repro` del 13-nov-2026 (`evaluacion_melodia.json` y `evaluacion_armonia.json`); gráfica de
`scripts/comparacion/figuras_presentacion.py`.

---

## 19 · Armonía: fuera de todos los corpus

«Frente a rock y pop, que son los estilos más cercanos, ninguna canción pasa de 17.7, cuando una pieza típica daría 50.
Primero calibramos: con 388 piezas reales de rock, el método dice "sin vecino" solo el 5.2 % de las veces. En la banda
lo dice el 37.5 %. En el mapa, Mata Zyklek y Utzp, que se apoyan en pedales, quedan en el borde del rock. Sarniezz y
Fabienk caen donde no hay piezas de ningún corpus, por el peso de ♭VII y ♭III.»

- **19·1, la matriz:** cada casilla es el percentil de la canción frente a un estilo. La columna «¼ %» es el tiempo con
  la fundamental en cuarto de tono; para comparar, esa fundamental se lleva al grado de abajo, porque ningún corpus tiene
  cuartos de tono.
- **19·2, el mapa:** cada punto del fondo es una pieza de un corpus. Cada eje es una componente principal del reparto de
  fundamentales.

> **Términos**
> - **Matriz de verosimilitud:** una tabla de canciones por estilos; cada casilla dice qué tan típica es la canción en ese estilo.
> - **Sin vecino:** ningún corpus llega al percentil 5; la canción es más rara que el 95 % de las piezas de todos los estilos.
> - **Calibrar:** probar el método con piezas cuya respuesta ya se conoce, para saber cuánto se equivoca.
> - **Pedal:** una nota que se sostiene o se repite mientras la armonía se mueve encima.
> - **♭VII / ♭III:** acordes sobre el séptimo y el tercer grado bajados un semitono; son típicos del rock modal.
> - **Componente principal (PCA):** técnica que resume muchos números en dos ejes para poder dibujarlos, conservando las diferencias más grandes.

---

## 20 · Melodía: cuartos de tono como grados fijos

«Lo nuevo está en la melodía. Entre el 48 y el 82 % de los cuartos de tono de cada canción caen en solo dos grados, que
vuelven en cada vuelta del loop. Son grados de la escala, no adornos. Angor, con 5 %, queda bajo el piso de ruido que
medimos con Primus. Aparecen dos familias de escala: ♭2+ y ♭6+ sobre frigio, cercana al maqam (Mata Zyklek, Yor Zarad y
Utzp), y 7+, 6+ y ♭3+ sobre dórico (Sarniezz y Fabienk). La frigia es el par más común del radif persa y aparece en seis
de las nueve canciones de King Gizzard; la dórica no aparece en ningún corpus.»

- **20·1:** qué parte del tiempo de la melodía está en cuartos de tono, como grado sostenido o como adorno de paso. La
  franja gris es el piso de ruido.
- **20·2:** el círculo de dos campos por canción. El área de cada punto es el tiempo en ese grado y las líneas son los
  pasos melódicos más frecuentes.
- **20·3, el círculo en movimiento:** Mata Zyklek de 0:42 a 1:12, con tónica Sol. Las voces giran sobre Sol y Sol♯+
  (♭2+), el cuarto de tono del riff. Frente a la partitura corregida, el círculo da el mismo grado el 87 % del tiempo en
  la voz aguda y el 94 % en la grave. Cuando falla, lee Sol♯+ como Sol.

> **Términos**
> - **Grado fijo:** una nota que pertenece a la escala y vuelve siempre en el mismo lugar.
> - **Adorno / nota de paso:** una nota breve que solo conecta otras dos.
> - **Piso de ruido:** lo que la herramienta marca como cuarto de tono en música que no los tiene (Primus). Por debajo de ese nivel, no cuenta.
> - **Frigio:** modo menor con el segundo grado bajado (♭2); suena «oriental» o «flamenco».
> - **♭2+:** el segundo grado bajado un semitono y luego subido un cuarto de tono.
> - **Voz aguda / voz grave:** la línea más alta (guitarra) y la más baja (bajo).

---

## 21 · Síntesis: ritmo, forma y estilo

«La repetición muestra picos en 20 y 28 corcheas: ciclos de dos compases de 5 y de 7, justo los tiempos que menciona la
banda y que planteamos en la hipótesis. Sarniezz y Utzp, en cambio, van en 4. En la clasificación por bloques, el rock
gana 8 de 24, el radif 7 y en 9 no hay vecino. El vecino más cercano es King Gizzard: en armonía, Angor es idéntica a
"Flying Microtonal Banana".»

- **21·1, ciclos métricos:** cuánto se repiten alturas y ataques ℓ corcheas después. Un pico alto y aislado es un ciclo
  largo y estable.
- **21·2, clasificación por corpus:** el percentil medio de cada canción frente a cada corpus; la fila «Álbum» es la
  media.
- **Si preguntan por el 83 de Mata Zyklek en clásica:** no es un parecido real. Kostka-Payne tiene solo 46 piezas y
  solo armonía; en un corpus chico y disperso casi todo parece típico, por eso el test no cuenta los corpus de menos de
  100 piezas (clásica, pop e indostánica salen atenuados con *). Además, la armonía de Mata Zyklek es un pedal: 89 % del
  tiempo sobre I y 6 % sobre V, un reparto tónica-dominante que cualquier corpus tonal tiene (en Kostka-Payne, I y V
  suman el 63 % del tiempo). Por eso también sale alta en rock (80) y jazz (73).
- **21·3, qué corpus gana cada bloque:** en cuántas canciones gana cada corpus en cada bloque (rock 8 de 24, radif 7,
  sin vecino 9).

> **Términos**
> - **Ciclo métrico:** cada cuántas corcheas se repite el patrón; 20 corcheas son dos compases de 5.
> - **Bloque de rasgos:** un grupo de medidas de una misma dimensión: armonía, escala, cuartos de tono o metro.
> - **Ganar un bloque:** que un corpus sea el más parecido a la canción en esa dimensión.
> - **Vecino más cercano:** la pieza o banda que más se parece según todas las medidas juntas.
> - **«Flying Microtonal Banana»:** álbum de King Gizzard tocado con guitarras de cuartos de tono.

---

## 22 · Conclusiones

«Un híbrido con un elemento nuevo. Tres conclusiones:

1. **La armonía no encaja en ningún estilo.** El 37.5 % de los casos queda sin vecino, frente al 5.2 % en rock real.
   Ninguna canción pasa de 17.7 sobre 50, y el método no exagera: con rock real casi siempre encuentra vecino.
2. **La melodía es lo nuevo.** Dos grados en cuarto de tono concentran entre el 48 y el 82 % de los cuartos de tono. Son
   grados de la escala, en dos familias. La frigia (♭2+, ♭6+) es la más común en el radif persa y en King Gizzard; la
   dórica (7+, 6+, ♭3+) no la tiene ningún corpus medido.
3. **El conjunto es un híbrido.** Tiene compases de 5 y 7 tiempos, como dice la banda; armonía de rock modal; cuartos de
   tono repartidos como en el radif, y King Gizzard como vecino más próximo. Sarniezz y Fabienk no tienen vecino ni
   siquiera ahí. (El parecido con el radif viene del bloque de cuartos de tono, no del de escala en 12 notas, que no
   discrimina; y es de escala, no de influencia: ver `verosimilitud_por_bloques.md`.)

La respuesta a la pregunta es que no es un estilo existente: es una recombinación nueva de lenguajes que ya existen, con
un elemento propio, los cuartos de tono como grados fijos.»

> **Términos**
> - **Híbrido:** algo que combina rasgos de varios estilos.
> - **Rock modal:** rock que usa modos (dórico, frigio, mixolidio) en lugar de la escala mayor o menor clásica.

---

## 23 · Trabajo futuro

«El siguiente paso es un tabroll que mejore solo, para cualquier canción. El ciclo tendría cuatro pasos:

1. sintetizar partituras de Guitar Pro con cuartos de tono;
2. entrenar con ellas un transcriptor en 24-EDO;
3. transcribir canciones nuevas;
4. validar con referencias de oído.

Así habría datos sin límite y sin transcribir a mano. Además:

- **Melodía:** tratar las vueltas del looper como varias tomas de la misma frase, para separar las capas.
- **Armonía:** elegir el centro tonal de forma robusta en cualquier canción; hoy falla en «Tommy the Cat».
- **Datos y producto:** un corpus de maqam árabe, un tabroll web interactivo, otros músicos microtonales como King
  Gizzard y Sevish, y el uso en la enseñanza.»

> **Términos**
> - **Sintetizar:** generar con el computador el audio de una partitura.
> - **Entrenar:** enseñar a un modelo con ejemplos cuya respuesta ya se conoce.
> - **Toma:** cada grabación de una misma frase. Varias tomas permiten promediar y limpiar.
> - **Robusto:** que funcione bien también en casos difíciles o distintos.
> - **Sevish:** compositor de música electrónica microtonal.
