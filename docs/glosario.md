# Glosario de la presentación

Términos que aparecen en la presentación de la defensa (`presentacion/`), explicados en lenguaje sencillo, con lo que
significan en este trabajo y la diapositiva donde aparecen. Cada entrada termina con una frase corta para el guion. Las
fuentes están en [`referencias_compiladas.md`](referencias_compiladas.md), en el bloque «Glosario: conceptos y teoría».

## Altura y afinación

### Octava
Distancia entre una nota y la misma nota con el doble de frecuencia, por ejemplo de un La a 220 Hz al La siguiente a
440 Hz.

### Semitono y cent
El **semitono** es el paso más pequeño del piano: 12 por octava. El **cent** es la centésima parte de un semitono, así
que una octava tiene 1200 cents y un cuarto de tono, 50.

### 24-EDO
Siglas de *24 Equal Divisions of the Octave*: **24 divisiones iguales de la octava**.

- **12-EDO** es el sistema de siempre: piano y guitarra común, 12 semitonos iguales de 100 cents.
- **24-EDO** parte cada semitono por la mitad: 24 pasos iguales de 50 cents, es decir, **cuartos de tono**.
- «Iguales» quiere decir que cada paso multiplica la frecuencia por el mismo número, \(2^{1/24} \approx 1.0293\)
  (fórmula α de la diapositiva 8). Tras 24 pasos la frecuencia se duplica.
- Conserva las 12 notas de siempre (Do, Do♯, Re…) y añade 12 nuevas entre ellas (Do+, Do♯+…). Por eso la guitarra de
  Khn tiene el doble de trastes por octava (diapositiva 3).
- En la presentación, las 12 notas de siempre van en amarillo y los 12 cuartos de tono en azul, marcados con «+».

> **Guion:** la octava dividida en 24 pasos iguales de 50 cents (cuartos de tono), en lugar de los 12 semitonos del piano.

### MIDI
Siglas de *Musical Instrument Digital Interface*, estándar de 1983 para que instrumentos electrónicos, computadores y
programas se comuniquen.

- **No es sonido:** guarda instrucciones, como una partitura para máquinas: qué nota (0 a 127), cuándo empieza y
  termina, con qué fuerza (*velocity*) y con qué instrumento. Un sintetizador produce luego el sonido.
- **Números de nota:** cada tecla del piano es un entero. Do central = 60, La 440 Hz = 69; cada semitono suma 1 y cada
  octava 12. Mi2 = 40, Mi3 = 52.
- **Límite:** al ser enteros no hay cuartos de tono; para escribir uno hace falta un truco aparte como el *pitch bend*.
- **En este trabajo:** el primer notebook leía la partitura de Sarniezz como MIDI y la dibujaba como piano roll
  (diapositiva 7); la herramienta actual usa la misma numeración con decimales (MIDI fraccionario).

> **Guion:** estándar digital que guarda notas como instrucciones (qué nota, cuándo y cuánto dura), no como sonido;
> numera las teclas del piano con enteros: Do central = 60, La 440 = 69.

### MIDI fraccionario
\[
M_{\text{frac}} = 69 + 12\,\log_2\!\left(\frac{f}{440}\right)
\]
Convierte una frecuencia en hercios en un número de nota. Se lee de adentro hacia afuera:

1. \(f/440\): cuántas veces más aguda o grave es la nota que el La de referencia.
2. \(\log_2\): cuántas octavas de distancia (cada octava duplica la frecuencia).
3. \(\times 12\) y \(+69\): pasa a semitonos y a la numeración MIDI.

Lo «fraccionario» son los decimales: `.0` es una tecla del piano, `.5` es un cuarto de tono y cada 0.01 es 1 cent.

**Ejemplo:** 169.6 Hz → \(169.6/440 = 0.3855\) → \(\log_2 = -1.375\) → \(\times 12 = -16.5\) → \(69 - 16.5 = 52.5\).
Queda a mitad de camino entre Mi (52) y Fa (53): es **Mi+**.

**Casilla de 24-EDO:** \(q = \operatorname{round}(2M)\), así que cada casilla mide 50 cents y la tolerancia es de ±25
cents. 52.5 → 105 (Mi+); 52.2, un Mi alto por 20 cents → 104 (Mi).

> **Guion:** numera las notas como las teclas del piano, La 440 = 69, pero con decimales: 52 es Mi, 53 es Fa, y 52.5 es
> el cuarto de tono que hay entre ellos.

### Perfil de 24 clases (\(v\) y \(v_k\))
\[
v \in \mathbb{R}^{24},\qquad v_k = \frac{\text{tiempo en la clase } k}{\text{tiempo total}}
\]

- **\(v\)** es una lista de 24 números, uno por clase de altura de 24-EDO: dice cuánto suena cada nota.
- **\(k\)** va de 0 a 23 en el orden de la regla: 0 = Do, 1 = Do+, 2 = Do♯, … 23 = Si+.
- **\(v_k\)** es la fracción del tiempo en que suena la clase \(k\). Está entre 0 y 1 y las 24 suman 1.
- **Clase de altura:** la octava no importa; un Sol grave y uno agudo cuentan en la misma casilla.
- Las casillas impares son los cuartos de tono; su suma da qué parte del tiempo suena en cuartos de tono.
- Se calcula por compás y por canción. Con estos perfiles se compara la banda con los corpus mediante la distancia de
  Jensen-Shannon (diapositiva 14) y se ve en qué grados se concentran los cuartos de tono (diapositiva 20).

> **Guion:** el perfil de una canción o de un compás: 24 números, uno por cada nota de 24-EDO sin importar la octava, y
> cada uno dice qué fracción del tiempo suena esa nota.

### Distancia de Jensen-Shannon
Medida de cuánto se diferencian dos perfiles de probabilidad, como dos \(v\). Vale 0 si son iguales y crece cuanto más
distintos son; a diferencia de la divergencia de Kullback-Leibler, es simétrica (Lin, 1991).

## Del audio a las notas

### MFCC
*Mel-Frequency Cepstral Coefficients*, coeficientes cepstrales en la escala Mel. Se calculan en cinco pasos:

1. Cortar el audio en ventanas de 20 a 50 ms.
2. Transformada de Fourier de cada ventana: cuánta energía hay en cada frecuencia.
3. Escala Mel: agrupar la energía en bandas como las del oído, estrechas en los graves y anchas en los agudos.
4. Logaritmo, porque el oído percibe el volumen de forma logarítmica.
5. Transformada del coseno (DCT): resumir las bandas en unos pocos números; se guardan los primeros 13.

Describen la **forma del espectro**, es decir el **timbre**, no qué nota suena. Nacieron en el reconocimiento de voz
(Davis y Mermelstein, 1980).

**En este trabajo:** el primer notebook sacaba 13 MFCC con librosa por fragmento de 10 s del bajo de Sarniezz y pasaba
su media y desviación (26 números) a una red MLP de dos capas (64 y 32 neuronas). Entrenó con 21 fragmentos y acertó 3
de 7 de prueba (diapositiva 9; detalle en [`graficas.md`](graficas.md), sección 11). No bastó porque las secciones de
Angine de Poitrine se distinguen por qué notas y capas del looper suenan, no por el timbre.

> **Guion:** salen del espectro del sonido: se agrupa la energía en bandas como las del oído, se pasa a logaritmo y se
> resume en unos 13 números que describen el timbre, no la nota.

### pYIN
Algoritmo que estima la **frecuencia fundamental** (\(f_0\)), qué tan aguda es la nota, instante a instante (Mauch y
Dixon, 2014). Es la versión probabilística de YIN (de Cheveigné y Kawahara, 2002).

- **YIN:** compara un trozo de audio con copias de sí mismo desplazadas en el tiempo y busca el desplazamiento en que
  más se parecen. Ese es el periodo \(T\), y \(f_0 = 1/T\).
- **pYIN añade:** varios candidatos por instante con su probabilidad; un camino suave en el tiempo elegido con un modelo
  oculto de Markov y Viterbi; y la decisión de si hay nota o no (*voiced / unvoiced*).
- **En este trabajo:** el primer notebook lo aplicó con librosa al bajo de Sarniezz, entre Do2 y Do7, con ventanas de
  2048 muestras (contorno de la diapositiva 9).
- **Límite:** da una sola altura por instante. Con varias capas del looper sonando a la vez salta entre ellas. Por eso
  la herramienta actual usa la saliencia armónica.

> **Guion:** estima, instante a instante, la frecuencia fundamental buscando cada cuánto se repite la onda; elige entre
> varios candidatos el camino más probable, pero da una sola nota por instante.

### Desviación en cents
\[
\text{desviación} = 1200\,\log_2\!\left(\frac{f}{f_{\text{tecla más cercana}}}\right)
\]
Cuántos cents se aleja una nota de la tecla de piano (12-EDO) más cercana. El primer notebook la usaba sobre la salida
de pYIN para buscar cuartos de tono: las notas normales darían cerca de 0 y los cuartos de tono cerca de ±50, y así se
ubicaría la zona del mástil con \(\mathbb{Z}_{24}\) (diapositiva 7).

**Por qué no funcionó (diapositiva 9):** al redondear a la tecla más cercana nada pasa de ±50, así que un cuarto de
tono cae justo en el borde y no se distingue de una nota muy desafinada. La herramienta actual redondea en 24-EDO, donde
el cuarto de tono queda en el centro de su casilla, y confirma la nota viendo si vuelve igual en cada vuelta del looper.

> **Guion:** medía cuánto se alejaba cada nota de la tecla de piano más cercana; un cuarto de tono debía dar ±50, pero
> eso es justo el borde de la medida, así que no se distinguía de una nota desafinada.

### Saliencia armónica
Evidencia de cada altura posible en cada instante, sumando la energía de sus armónicos. A diferencia de pYIN, da
evidencia para todas las alturas a la vez; la herramienta la promedia entre vueltas del looper y luego aplica Viterbi.

### Viterbi
Algoritmo que, entre muchas secuencias posibles, encuentra la más probable paso a paso (Viterbi, 1967). Aquí elige la
secuencia de notas que mejor explica la evidencia sin saltos innecesarios.

## Separación de fuentes y redes neuronales

### Perceptrón multicapa (MLP)
La red neuronal más básica: capas de «neuronas» conectadas todas con todas. El primer notebook usó una, con capas de
64 y 32 neuronas, para reconocer la sección a partir de 26 números de MFCC (ver «MFCC» y [`graficas.md`](graficas.md),
sección 11).

### Demucs y BS-RoFormer
Dos **redes neuronales profundas** que separan una mezcla en una pista por instrumento (guitarra, bajo, batería, voz…).
No son perceptrones simples: usan piezas especializadas en audio y tienen millones de parámetros. Aprendieron con miles
de canciones de las que se tenía cada instrumento grabado por aparte (*aprendizaje supervisado*).

- **Demucs** (Meta; Rouard et al., 2023, versión *Hybrid Transformer*): combina una red **convolucional** tipo U-Net
  (filtros que buscan patrones locales, como un ataque o un armónico, y comprimen y reconstruyen la señal) con un
  **Transformer** en el centro (la *atención* deja que cada instante mire a todos los demás). Es **híbrida** porque
  trabaja a la vez con la onda y con el espectrograma. El proyecto usa `htdemucs_6s`, de 6 pistas, con semilla 0.
- **BS-RoFormer** (ByteDance; Lu et al., 2024): un **Transformer** sobre el espectrograma. *Band-split*: lo parte en
  bandas de frecuencia, más finas en los graves. *RoFormer*: codifica la posición con RoPE (*rotary position
  embedding*). Alterna la atención entre instantes y entre bandas y produce una **máscara** que dice qué parte de cada
  punto del espectrograma es de la guitarra. Detalle del modelo usado en [`separacion_roformer.md`](separacion_roformer.md).

| | MLP del primer notebook | Demucs | BS-RoFormer |
|---|---|---|---|
| Tipo | perceptrón multicapa | convolucional + Transformer | Transformer |
| Entrada | 26 números (MFCC) | onda y espectrograma | espectrograma por bandas |
| Salida | una sección (verso, riff…) | pistas separadas | pistas separadas (por máscara) |
| Tamaño | miles de parámetros | millones | ~200 millones |

Descripción general a partir de los artículos de cada modelo; los detalles de arquitectura están por verificar en ellos.

> **Guion:** Demucs y BS-RoFormer son redes neuronales profundas entrenadas con miles de canciones multipista: Demucs
> combina convoluciones y un Transformer sobre la onda y el espectrograma; BS-RoFormer es un Transformer que trabaja por
> bandas de frecuencia.

### SDR
*Signal-to-distortion ratio*, relación señal a distorsión: qué tan limpia sale una pista separada frente a la misma
pista grabada por aparte.
\[
\text{SDR} = 10\,\log_{10}\frac{\text{energía de la pista verdadera}}{\text{energía del error}}
\]
Está en decibeles y más alto es mejor; cada 10 dB más, el error es 10 veces menor en energía. Las cifras de la
diapositiva 13 (guitarra: Demucs 5.22, BS-RoFormer 9.05) son públicas, de la tabla de MVSEP sobre mezclas comerciales:
de Angine de Poitrine no hay guitarra aislada para medirlo. Un SDR más alto no mejoró la transcripción (melodía de
Sarniezz 44.9 con los dos), porque el problema son las capas del looper dentro de la misma guitarra.

> **Guion:** el SDR mide, en decibeles, qué tan limpia sale la guitarra separada frente a la grabada por aparte;
> BS-RoFormer saca 9 dB y Demucs 5, pero en esta música separar mejor no mejoró la transcripción.

## Evaluación

### Medida F
Un solo número de 0 a 100 que dice qué tan bien coincide la melodía de la herramienta con la partitura corregida de
oído (diapositiva 12). Se calcula en tres pasos (código: `src/tabroll/evaluation/melodia.py`):

1. **Aciertos.** Una nota de la herramienta acierta si empieza a **±75 ms** de una nota de la partitura y tiene la misma
   altura a **±25 cents** (la misma casilla de 24-EDO). Cada nota de la partitura se empareja con una sola nota; la
   duración no cuenta.
2. **Precisión (P):** de las notas que dio la herramienta, cuántas aciertan (castiga las notas inventadas).
   **Exhaustividad (R):** de las notas de la partitura, cuántas se encontraron (castiga las que faltan).
3. **Media armónica:**
\[
F = 100 \cdot \frac{2PR}{P+R}
\]
   A diferencia del promedio común, solo es alta si P y R lo son a la vez: dar muy pocas notas o dar notas por todas
   partes la hunde.

**Ejemplo:** partitura con 100 notas; la herramienta da 80 y 60 aciertan. P = 75 %, R = 60 %, F ≈ 66.7. En la
diapositiva 12, «Mata Zyklek: 57 → 64» es la F de la melodía antes y después de la atracción al registro.

**Forma general:** \(F_\beta = (1+\beta^2)\,PR/(\beta^2 P + R)\). Con β > 1 pesa más encontrarlo todo; con β < 1, no
inventar. Este trabajo usa β = 1, la **F1**.

**De dónde viene.** De la evaluación de buscadores de documentos, no de la música: van Rijsbergen (1979) propuso la
medida de efectividad **E**, y la medida F es su complemento, F = 1 − E. La letra F no es una sigla; se cree que el
nombre se fijó en la conferencia MUC-4 (1992), tomado de otra función F del mismo libro (Christen, Hand y Kirielle,
2024, repasan su historia). La comunidad de MIR la adoptó para transcripción, ataques y pulsos, y mir_eval (Raffel et
al., 2014) la estandarizó con la tolerancia de ataque. El código de este trabajo la calcula por su cuenta, con esa
misma regla.

> **Guion:** la medida F combina cuántas de las notas que da la herramienta son correctas y cuántas de las notas reales
> encuentra; una nota es correcta si empieza a ±75 ms y cae en la misma casilla de 24-EDO. Viene de la evaluación de
> buscadores (van Rijsbergen, 1979) y la «F» no es una sigla.

### Acierto de la herramienta (diapositiva 18)
Se mide contra las **referencias corregidas de oído**, en **corridas congeladas** (ejecuciones guardadas que no se
vuelven a tocar, para que los números citados no cambien; las `_repro` del 13-nov-2026).

- **Acierto de la melodía y del bajo:** la medida F de notas (ver arriba).
- **Acierto de la fundamental:** el porcentaje de compases en que la fundamental del acorde coincide con la de la
  partitura.
- **Compás confiable:** un compás donde la confianza κ del acorde supera el umbral; ahí la herramienta tiene evidencia
  suficiente para decidir.
- **Prueba a ciegas:** una canción que no se usó para ajustar la herramienta (Yor Zarad).

| | Melodía | Bajo | Fundamental | Fundamental en compases confiables |
|---|---:|---:|---:|---:|
| Mata Zyklek | 66 | 83 | 95 | 100 |
| Fabienk | 46 | 69 | 82 | 82 |
| Sarniezz | 45 | 79 | 58 | 67 |
| Yor Zarad (a ciegas) | 37 | 69 | 88 | 90 |
| **Media (4 canciones)** | **49** | **75** | **81** | **85** |

La armonía acierta más que la melodía porque el bajo pesa más (1 frente a 0.6 de la voz aguda), se suma sobre las vueltas
del loop, la octava no importa y se decide por compás, no por nota. Y no depende de la melodía: al cambiar solo su peso,
la fundamental quedó idéntica (ver [`armonia.md`](armonia.md)).

> **Guion:** la melodía acierta el 49 % en promedio, pero la fundamental del acorde acierta el 85 % en los compases
> confiables.

## Reproducibilidad

### Semilla fija
Los programas que usan azar (por ejemplo, Demucs) parten de un número inicial, la semilla. Si se fija, el azar sale
igual en cada corrida y los resultados se pueden repetir (diapositiva 12; Demucs usa semilla 0).

### Huella SHA-256
La **huella digital de un archivo**: una fórmula (el estándar SHA-256 del NIST, FIPS 180-4) lee todos sus bytes y
devuelve siempre un código de **64 caracteres**, sin importar el tamaño del archivo.

1. **Siempre da lo mismo:** el mismo archivo da el mismo código en cualquier computador.
2. **Cualquier cambio lo cambia todo:** basta un carácter distinto para que el código salga irreconocible.
   «La melodía de **S**arniezz» → `4223e9e01c94397d…`; «La melodía de **s**arniezz» → `8a367595a06b1c12…`.
3. **No se puede ir hacia atrás:** el código no permite reconstruir el archivo, y en la práctica dos archivos distintos
   nunca dan el mismo código.

Sirve para comprobar que dos archivos son idénticos sin compararlos byte por byte. En este trabajo:

- **Qué audio se midió:** cada corrida guarda en `resumen.json` (`pistas.sha256`) la huella de la mezcla y de las dos
  pistas separadas. Dos separaciones de la misma canción daban 57 y 62; las huellas muestran que el audio era distinto,
  por eso un hallazgo solo cuenta si se mantiene en ambas (diapositiva 12).
- **Proteger el notebook:** `make extract` guarda la huella de cada módulo en `src/tabroll/cells/.extraccion.json`; si
  un módulo se editó a mano, la huella ya no coincide y la extracción se detiene en vez de borrar el cambio.
- **Identificar el modelo de BS-RoFormer:** sus pesos no tienen autor ni versión oficial, así que se citan por su huella
  (`24e7d35e…`; ver [`separacion_roformer.md`](separacion_roformer.md)).

> **Guion:** la huella SHA-256 es como la huella digital de un archivo: un código de 64 caracteres que cambia por
> completo si el archivo cambia en lo más mínimo; así sabemos que dos corridas usaron exactamente el mismo audio.

## Representación

### Piano roll
Gráfico con el **tiempo** en el eje horizontal y la **altura** en el vertical; cada nota es una barra que empieza
cuando empieza la nota y dura lo que dura. El nombre viene de los rollos de papel perforado de las pianolas. Un piano
roll normal tiene 12 filas por octava; el tabroll tiene 24. Aparece en las diapositivas 7 y 10.

> **Guion:** gráfico con el tiempo en el eje horizontal y la altura en el vertical, donde cada nota es una barra; el
> nombre viene de los rollos perforados de las pianolas.

### Hooktheory
Sitio web con transcripciones de canciones populares que muestra la melodía y los acordes juntos (páginas *TheoryTab*).
Su formato inspiró el tabroll (diapositiva 10).

### Tabroll
El piano roll de este trabajo en 24-EDO, con los acordes debajo y todo sacado del audio. El nombre viene de
*tablatura* + *piano roll*. Es una representación del repositorio, no un corpus externo.

### Corregida de oído
La partitura revisada escuchando la grabación; sirve de referencia para medir el acierto.

## Ritmo

### Pulso
Cada golpe regular que se siente al llevar el ritmo con el pie o la cabeza.

### Compás
Grupo de pulsos que se repite, con el primero más acentuado. Se escribe como fracción: 4/4 son cuatro pulsos de negra
(rock y pop), 3/4 tres (el vals). Los compases impares, de 5 o 7 pulsos, suenan «cojos» porque el oído espera grupos de
2 o 4.

- El notebook no supone el compás: lo mide en el audio, por eso el tabroll muestra cuántos pulsos tiene cada uno.
- El acorde se decide por compás (diapositiva 18) y los perfiles de 24 clases se calculan por compás (diapositiva 8).
- **Compás no es ciclo del looper:** un riff puede durar varios compases.

> **Guion:** grupo de pulsos que se repite, con el primero más acentuado; 4/4 son cuatro pulsos de negra por compás.

### Métrica
Cómo se agrupan los pulsos en compases.

## Armonía

### Walter Piston, *Harmony*
Libro clásico de armonía tonal (Piston, 1987, 5.ª ed. revisada por M. DeVoto). El trabajo toma de él las calidades de
acorde, la clasificación de grados en tonales y modales y una medida del centro para música sin dominante, y las
extiende a 24-EDO (diapositiva 11; detalle en [`armonia.md`](armonia.md), pasos 1, 2 y 4).

### Calidad de acorde
El tipo de acorde según los intervalos que hay sobre su fundamental: mayor, menor, disminuido, suspendido… La
herramienta asigna una calidad a cada compás. En 24-EDO se cuentan los intervalos en cuartos de tono:

| Calidad | Tercera | Pasos de ¼ |
|---|---|---|
| 5 (quinta sola) | sin tercera | — |
| m (menor) | 3.ª menor · 300 cents | 6 |
| n (neutra) | 350 cents | 7 |
| M (mayor) | 3.ª mayor · 400 cents | 8 |
| dism · aum | 3.ª menor · 3.ª mayor | 6 · 8 |
| sus2 · sus4 | 2.ª · 4.ª | 4 · 10 |

- **Quinta sola (5):** fundamental y quinta (700 cents, 14 pasos) sin tercera, el *power chord* del rock. Como no hay
  tercera, no es mayor, menor ni neutra; por eso las columnas de la tercera van vacías. Es la calidad más frecuente en
  Mata Zyklek (53 % de los compases) y la segunda en Yor Zarad (29 %).
- **dism · aum:** disminuido (dos terceras menores apiladas) y aumentado (dos mayores).
- **sus2 · sus4:** la tercera se cambia por la segunda o por la cuarta; suenan abiertos.

> **Guion:** la calidad es el tipo de acorde, y la decide sobre todo el tamaño de su tercera.

### Tercera neutra
Tercera de 350 cents (7 cuartos de tono), a mitad de camino entre la menor (300) y la mayor (400). Solo existe con
cuartos de tono: es la calidad que 24-EDO añade a las de Piston. La herramienta puede detectarla, pero en las corridas
actuales de Sarniezz, Mata Zyklek, Fabienk y Yor Zarad no aparece en ningún compás.

> **Guion:** una tercera justo entre la menor y la mayor, que no es ni triste ni alegre y solo existe con cuartos de tono.

### Centro en tres partes
Forma de hallar la tónica en música **sin dominante**, donde no hay cadencias que la anuncien. En cada capa (bajo y voz
aguda) suma, con el mismo peso:

- **Tiempo:** la nota que más tiempo suena.
- **Bordes de vuelta:** la que más aparece al principio y al final de cada vuelta del looper.
- **Regresos:** la que más vuelve después de alejarse.

El bajo pesa el doble que la voz aguda. El `margen` dice cuánto gana la primera candidata a la segunda; por debajo de
0.1 el centro es dudoso.

> **Guion:** la tónica es la nota que más suena, la que abre y cierra cada vuelta y a la que la música regresa.

### Centro tonal o tónica
La nota de reposo de la pieza, la que se siente como casa.

### Dominante
El acorde sobre el quinto grado. En la música clásica crea la tensión que empuja a volver a la tónica; esta banda casi
no lo usa, por eso hace falta otra forma de hallar el centro.

### Grados tonales y modales
Clasificación de Piston (cap. 5): los grados **tonales** (I, IV, V) definen la tonalidad; el II es casi tonal; los
**modales** (III, VI) definen el modo, es decir, si suena mayor, menor, dórico… En este trabajo, ♭III, III y VI se leen
además como tónica relativa, siguiendo a Riemann.

### Función neutra
La función que se asigna a un acorde cuya fundamental cae en un grado en cuarto de tono. Piston deja fuera las escalas
microtonales (p. 474) y Riemann pensaba en 12 notas, así que esos acordes no caben en tónica, subdominante ni dominante.
Con los ejes de Lendvai extendidos a 24-EDO, esos grados forman tres **ejes neutros** entre los ejes vecinos (T–D,
D–S y S–T).

> **Guion:** un acorde sobre un cuarto de tono no es ni tónica, ni subdominante, ni dominante: queda como neutro.


### Modo y dórico
Un **modo** es un tipo de escala. El **dórico** es menor pero con la sexta mayor. Mi dórico: Mi, Fa♯, Sol, La, Si,
Do♯, Re.

### Grado
Posición de una nota en la escala: 1 es la tónica (Mi en Mi dórico), 5 la quinta (Si)…

### Cifrado romano
El acorde escrito según el grado sobre el que se construye. ♭VII es el acorde sobre el séptimo grado bajado (Re en Mi);
♭III, sobre el tercero bajado (Sol).

### sus2
Acorde suspendido que cambia la tercera por la segunda; suena abierto, ni mayor ni menor.

### Función armónica (H. Riemann)
**Hugo Riemann** (1849–1919), teórico musical alemán; **no** es Bernhard Riemann, el matemático. Aquí no se cita una
función ni un teorema, sino su **teoría funcional de la armonía** (*Funktionstheorie*, década de 1890): en una
tonalidad cada acorde cumple uno de tres papeles.

| Función | Símbolo | Papel | En Do mayor |
|---|---|---|---|
| Tónica | T | reposo, «estar en casa» | Do (I) |
| Subdominante | S | alejarse de casa | Fa (IV) |
| Dominante | D | tensión que pide volver | Sol (V) |

Los demás acordes se agrupan en esas familias como **sustitutos**, porque comparten dos de sus tres notas con el acorde
principal:

- **Relativo** (*Parallelklang*; Tp, Sp, Dp): el acorde una tercera menor abajo.
- **Contraacorde** (*Leittonwechselklang* o *Gegenklang*): el acorde una tercera mayor arriba.

| Función | Principal | Relativo | Contraacorde |
|---|---|---|---|
| T | Do (I) | La m (vi) | Mi m (iii) |
| S | Fa (IV) | Re m (ii) | La m (vi) |
| D | Sol (V) | Mi m (iii) | (Si°) |

Los principales y los relativos son el núcleo de la teoría; la columna de contraacordes está por verificar en la fuente.
«Función» es una metáfora: se parece a asignar a cada acorde un valor de {T, S, D}, pero es una clasificación, no una
fórmula.

**Criterios del proyecto:** ♭III, III y VI son tónica relativa; ♭VII es dominante modal (sin sensible); II mayor es
dominante de la dominante (V/V); ♭II es la napolitana, ♭VI la mixtura y ♯IV queda sin función; los grados en cuarto de
tono, neutros.

- **Modal:** la tensión viene del modo y no de una nota sensible (por ejemplo ♭VII como dominante modal).
- **Rel.:** relativo de la tónica (por ejemplo ♭III, que el tabroll escribe «Tónica relativa»).
- **Neutra:** ver «Función neutra» más abajo.

Detalle del cálculo en [`armonia.md`](armonia.md), paso 4.

> **Guion:** Hugo Riemann, teórico musical alemán, no el matemático; su teoría funcional clasifica cada acorde como
> tónica (reposo), subdominante (alejamiento) o dominante (tensión).

### Ejes de Lendvai
**Ernő Lendvai** (1925–1993), musicólogo húngaro que estudió la música de Bartók. Extendió la idea de Riemann con su
**sistema de ejes**: en el círculo de quintas, toma las notas de tres en tres posiciones, es decir, por terceras
menores. Salen tres ejes de cuatro notas, y cada eje es una función.

| Eje | Rama principal (polo ↔ contrapolo, a un tritono) | Rama secundaria | En Do |
|---|---|---|---|
| Tónica | I ↔ ♯IV | VI ↔ ♭III | Do, Fa♯ · La, Mi♭ |
| Subdominante | IV ↔ VII | II ↔ ♭VI | Fa, Si · Re, La♭ |
| Dominante | V ↔ ♭II | III ↔ ♭VII | Sol, Re♭ · Mi, Si♭ |

- Un acorde puede reemplazar a otro de su eje sin cambiar de función. El reemplazo más fuerte es el contrapolo, a un
  tritono: Re♭ puede hacer de dominante en lugar de Sol.
- Frente a Riemann solo cambian cuatro grados: III y ♭II son dominante, VII es subdominante y ♯IV es tónica.

**Extensión a 24-EDO (propuesta del proyecto, no de Lendvai).** Un grado en cuarto de tono cae entre dos ejes vecinos.
Como la tercera menor mide 6 cuartos de tono, esos grados forman tres **ejes neutros**:

| Eje neutro | Grados |
|---|---|
| T–D | 1+, ♭3+, ♯4+, 6+ |
| D–S | ♭2+, 3+, 5+, ♭7+ |
| S–T | 2+, 4+, ♭6+, 7+ |

**Lo que mostró:** en Sarniezz, el 24 % de los cambios de acorde de la partitura queda dentro del eje de tónica (Mi ↔
Sol, I ↔ ♭III), una sustitución y no un movimiento por quintas. Las canciones con cuartos de tono se mueven entre un eje
de Lendvai y uno neutro: Mata Zyklek D ↔ D–S, Yor Zarad T ↔ D–S. Detalle en [`armonia.md`](armonia.md), paso 4b.

> **Guion:** Riemann agrupa los acordes en tónica, subdominante y dominante según a cuál se parecen; Lendvai los agrupa
> en tres ejes de cuatro notas a una tercera menor de distancia, y nosotros extendimos esos ejes a los cuartos de tono.
