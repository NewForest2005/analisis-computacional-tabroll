# Armonía en 24-EDO, paso 1: fundamental por compás con confianza

Las celdas del final del cuaderno («Armonía en 24-EDO (paso 1)») calculan, para cada compás, la fundamental, la
calidad, el grado, la nota del bajo y una confianza. `run_song.py` lo guarda en `armonia.json` en cualquier canción.
Si la canción tiene partitura corregida (Mata Zyklek, Sarniezz o Fabienk), además lo mide contra ella.

## Cómo se calcula

1. **Compases.** Salen de los pulsos reales (`beat_times`) y de la longitud de cada compás (`lens`).
2. **Entradas.**
   - El bajo (`raw_bass`).
   - El contenido de la voz aguda (`raw_high`) en 24 clases de cuarto de tono. Sin contar las notas de menos de un
     cuarto de pulso, que suelen ser notas de paso o adornos.
3. **Suma sobre las vueltas.**
   - El perfil de cada compás se suma sobre todas las vueltas del ciclo que lo contiene, tomando el mismo punto del
     ciclo en cada vuelta.
   - El bajo usa los ciclos de la voz grave y la voz aguda usa los suyos, porque pueden tener periodos distintos.
4. **Acorde (`chord24`).**
   - Se compara con las calidades de Piston extendidas a 24-EDO: 5, m, n (tercera neutra), M, dism, aum, sus2 y sus4.
   - Cuenta lo que cae dentro del acorde, resta lo que cae fuera y premia que el bajo esté en la fundamental.
   - Pesos: bajo 1 y voz aguda 0.6, como en la celda de acordes que ya tenía el cuaderno.
5. **Confianza (0 a 1).** Es el producto de tres factores:
   - `fundamental`: probabilidad de la fundamental elegida frente a las otras 23.
   - `acuerdo_vueltas`: cuánto se parecen entre sí las vueltas del ciclo en ese compás.
   - `cobertura`: qué parte del compás tiene notas.

   La claridad del bajo, es decir cuánto se concentra en una sola nota, se guarda como dato, pero no entra en el producto.

## `armonia.json`

- **`compases`**: una fila por compás. Campos:
  - Tiempo: `inicio_s`, `fin_s`.
  - Acorde: `fundamental` (por ejemplo `D`, `D+`), `fundamental_pc24`, `calidad`, `grado` (respecto de la tónica;
    «+» sube un cuarto de tono).
  - Bajo: `bajo`, `bajo_pc24`.
  - Confianza: `confianza` y `componentes`.
  - Ciclos: `ciclo_bajo`, `ciclo_aguda`, y las vueltas sumadas en cada voz.
  - Perfiles: `perfil_bajo` y `perfil_aguda`, en segundos por vuelta en cada una de las 24 clases, empezando en Do.
- **`resumen`**: lo que usará el círculo armónico.
  - `fundamentales_por_grado` y `bajo_por_grado`: ponderados por duración y confianza, en 24 grados contados desde
    la tónica.
  - `tiempo_confiable`: el porcentaje del tiempo con confianza ≥ 0.5.

## Evaluación (`evaluacion_armonia.json` y `_por_compas.csv`)

Para cada compás del cuaderno se analiza la partitura con la misma función, en el mismo tramo de audio: los bajos de
la partitura como bajo y todas sus guitarras como voz aguda. Así se compara lo que sale de las notas detectadas con lo
que saldría de las notas verdaderas.

- **`fundamental`**: misma fundamental en 24-EDO, ponderada por la duración del compás.
- **`fundamental_y_calidad`**: además, la misma calidad. Es exigente, porque el cuaderno transcribe dos voces y la
  partitura tiene todas.
- **`bajo`**: la nota que más suena en el bajo.
- **`tiempo_confiable`**, **`fundamental_confiables`** y **`fundamental_resto`**: si la confianza sirve, la fundamental
  acierta mucho más en los compases confiables que en el resto.

## Paso 2: centro, modo y capas del círculo

- **Centro (`center24_by_layer`).** Usa la medida de tres partes de Piston para la música sin dominante. En cada capa
  (bajo y voz aguda) suma, con el mismo peso:
  - **Tiempo:** la nota que más tiempo suena.
  - **Bordes de vuelta:** la que más aparece al principio y al final de cada vuelta.
  - **Regresos:** la que más vuelve después de alejarse.

  El centro de la canción combina las dos capas, con el bajo al doble de peso. `margen` (0 a 1) dice cuánto le gana a
  la segunda candidata: por debajo de 0.1, el centro es dudoso.
- **Qué centro se usa.** Por defecto (`CENTRO = 'cuaderno'`), la tónica de la celda de tonalidad. Coincide con la
  tónica de oído del autor en las cinco canciones (Mata Zyklek Sol, Sarniezz Mi, Fabienk Mi, Uztp Mi, Yor Zarad Sol).
  La medida de 24-EDO por capa queda como dato y como centro de cada capa. `CENTRO = 'auto'` usa esa medida, y una
  nota (`'E'`, `'D+'`) fija el centro a mano. Los grados se cuentan desde el centro elegido, y `run_song.py` compara
  ese centro con la tónica de oído.
- **Modo (`mode24`).** Los grados 2, 3, 6 y 7, cada uno en su versión menor, neutra o mayor (por ejemplo «♭2+, 3,
  ♭6+, ♭7»). No se fuerza un nombre de 12 tonos.
- **Capas (`harmony_layers`).** Se calculan con los compases confiables.
  - Sin depender del centro: `movimientos`, `cambios_por_compas` y `calidades`. Los movimientos son fuerte (4.ª/5.ª),
    débil (3.ª/6.ª), color (2.ª, 7.ª, tritono), deslizamiento (¼ de tono) e intermedio (intervalos neutros, incluida
    la 3.ª neutra).
  - Desde el centro: `transiciones` entre grados.
- **Ciclos.** `armonia.json` guarda en `resumen.ciclos` los ciclos que usó la armonía, para que la evaluación mida
  con los mismos.
- **`chord24`.** Los empates exactos (por ejemplo, Re sus2 y La sus4 tienen las mismas notas) se resuelven igual en
  cualquier máquina.

La evaluación agrega:
- `centro_partitura`: la misma medida de centro, aplicada al bajo y a la melodía principal de la partitura.
- Movimientos y calidades del cuaderno frente a los de la partitura, con su distancia de Jensen-Shannon (0 = iguales).

## Paso 3: el círculo armónico

Las celdas del paso 3 calculan el círculo de la canción y dibujan `circulo_armonico.png` en `harmony_outputs`.
`run_song.py` guarda además `circulo.json`. El círculo tiene 24 posiciones contadas desde la tónica, perfiles del
bajo, voz aguda y fundamentales, fundamentales por ciclo, transiciones, movimientos, calidades y ritmo armónico.
`scripts/comparar_circulos.py` calcula distancias entre círculos de 0 a 1 y valida audio frente a partitura, mitades
de una canción y canciones cercanas.

**Ajuste 1 (`scripts/ajustar_circulo.py`).** En `fundamentales_por_ciclo` cada ciclo distinto del bajo cuenta una
vez, y los compases sin ciclo cuentan juntos como un ciclo más. Antes cada compás suelto contaba como un ciclo entero, y
en Mata Zyklek 30 compases sueltos pesaban más que sus tres ciclos. El círculo guarda también `tiempo_sin_ciclo`.
Pesar cada ciclo por sus vueltas se probó y quedó descartado: acerca la capa a `fundamentales` y empeora Mata Zyklek.

**Ajuste 1b.** `draw_harmony_circle` arma la figura con `matplotlib.figure.Figure`, sin pyplot, así que no depende de
la celda que fija el backend ni abre ventanas. `python scripts/comparar_circulos.py outputs/<carpetas> --actualizar`
reescribe `circulo.json` y la figura de corridas ya hechas sin correr el cuaderno. La comparación se guarda por defecto
en `outputs/comparacion_circulos.json`.

**Ajuste 2 (`src/tabroll/evaluation/circulo.py`).** En la distancia combinada, transiciones y movimientos pesan según
los cambios de fundamental del círculo que tiene menos: nada con menos de 5, n/20 entre 5 y 20, y completo desde 20
(`peso_cambios` en cada distancia). Con pocos cambios esas capas son sobre todo ruido de muestreo:
`scripts/ruido_cambios.py` saca dos muestras de n cambios de una misma canción y mide cuánto difieren.

| Cambios | Transiciones | Movimientos |
|---:|---:|---:|
| 6 | 0.28 | 0.12 |
| 10 | 0.19 | 0.07 |
| 20 | 0.11 | 0.03 |
| 40 | 0.06 | 0.02 |

Con 6 cambios, como en Uztp y Yor Zarad, el ruido supera la distancia entre un audio y su partitura (alrededor de 0.1).
Llegar al peso completo en 20, en 40 para transiciones y 13 para movimientos, o pesar n/(n+10) da casi lo mismo.

## Paso 4: grados, funciones y progresiones

Celdas `chord_roles`, `roles_summary` y `chord_progressions` (scripts `agregar_funciones.py` y
`funciones_y_progresiones.py`). Las columnas nuevas van en `armonia_por_compas.csv` y los resúmenes en `armonia.json`
(`funciones` y `progresiones`).

- **Cifrado y grado.** Números romanos sobre el centro: mayúscula para mayor, minúscula para menor, «+» sube un cuarto
  de tono, «aum» aumentado, «n» tercera neutra, «5» sin tercera, «°» disminuido, más sus2 y sus4. Cada grado lleva su
  nombre (tónica, supertónica, mediante, subdominante, dominante, superdominante, subtónica o sensible, con «rebajada»
  o «elevada» cuando hace falta) y su clase según Piston (cap. 5): tonales I, IV y V; casi tonal II; modales III y VI;
  el VII se absorbe en el V. Los grados de cuarto de tono se nombran como neutros: supertónica neutra (♭2+), mediante
  neutra (♭3+), superdominante neutra (♭6+), séptimo grado neutro (♭7+); los demás, «alta» o «baja».
- **Función.** Familias de Riemann y Piston, escritas con la calidad del acorde: «subdominante menor», «dominante
  menor (modal, sin sensible)». Criterios del proyecto:
  - ♭III, III y VI son **tónica relativa**, como en Riemann. Piston los trata como grados modales sin función propia;
    en canciones con mucho ♭III, como Sarniezz (42 % del tiempo), esto sube la parte de tónica. Si más adelante
    conviene, se pasan a «modal, sin función» en la tabla `GRADOS`.
  - ♭VII es **dominante modal** (subtónica, sin sensible): la dominante de los modos que evitan la sensible.
  - II mayor es dominante de la dominante (V/V). El V menor o sin tercera es dominante modal, sin sensible.
  - ♭II es la napolitana, ♭VI la mixtura y ♯IV el tritono, que queda sin función.
  - Los grados de cuarto de tono tienen función **neutra**: Piston deja fuera las escalas microtonales (p. 474).
- **Inversión.** Dónde cae el bajo respecto del acorde: fundamental, 1.ª inversión (6), 2.ª inversión (6/4), séptima en
  el bajo (4/2) o bajo fuera del acorde. Un bajo a un cuarto de tono de una nota del acorde cuenta como esa nota y se
  marca «(bajo a 1/4 de tono)»: en Sarniezz, el bajo detectado en D#+ es el Mi de la partitura.
- **Voz aguda.** La nota que más suena en el compás, qué es dentro del acorde y qué parte de su tiempo cae en notas del
  acorde.
- **Progresión.** En cada cambio de fundamental entre compases confiables: la progresión («♭III → ♭VII»), el movimiento
  de la fundamental según Piston (pp. 22-24: quinta abajo, quinta arriba, tercera abajo, tercera arriba, segunda,
  tritono o microtonal) y qué tan usual es según su tabla de progresiones (pp. 21-22), leída por número de grado (♭VII
  como VII). Si el modo tiene ♭3 se agregan los añadidos del menor (p. 45). Un cambio con un grado de cuarto de tono
  queda como «microtonal» y «fuera de la tabla».

El resumen de progresiones sale dos veces, uno al lado del otro: con los compases confiables y con todos los compases.
Cada uno da qué parte de los cambios va por quintas, las progresiones más frecuentes, las progresiones con nombre y los
vaivenes entre dos acordes; las columnas de cada compás salen de los confiables. Hacen falta los dos: en Mata Zyklek el
vaivén ♭II+5 ↔ ♭VII de los primeros compases, que la partitura confirma, tiene confianza entre 0.14 y 0.44 y solo aparece
con todos los compases; en Sarniezz, en cambio, los compases poco confiables agregan cambios microtonales que la partitura
no tiene. Las progresiones con nombre salen de la lista de progresiones de Wikipedia y se reconocen por las fundamentales,
sin mirar la calidad. Las cuartas están incluidas: subir una cuarta es bajar una quinta («quinta abajo») y bajar una
cuarta es subir una quinta («quinta arriba»). Una canción que casi no se mueve por quintas, o que se mueve por grados de
cuarto de tono, se aparta del círculo de quintas: es un indicio de lo que la banda hace distinto.

**Contra la partitura** (`evaluacion_armonia.json`): la función de cada compás en el cuaderno y en la partitura, con el
mismo centro, y las progresiones de los dos en todos los compases medidos. Medido sobre las corridas `funciones2`:

| Canción | Misma función | En los confiables | Distancia de funciones | Por quintas: partitura / cuaderno |
|---|---:|---:|---:|---:|
| Sarniezz | 66.0 % | 90.4 % | 0.039 | 67 / 72 % |
| Mata Zyklek | 98.1 % | 98.8 % | 0.001 | 25 / 33 % |
| Fabienk | 82.9 % | 83.5 % | 0.015 | 45 / 55 % |

La función coincide casi lo mismo que la fundamental: los errores vienen de la fundamental de `chord24`, no del
etiquetado.

## Paso 4b: ejes de Lendvai

Lendvai, en su análisis de Bartók, agrupa las 12 clases por terceras menores en tres ejes. Medido en semitonos sobre el
centro, el eje es el grado módulo 3. Cada eje tiene una rama principal (polo y contrapolo, a un tritono) y una
secundaria; un polo puede reemplazar a su contrapolo sin cambiar de función.

| Eje | Rama principal (polo, contrapolo) | Rama secundaria |
|---|---|---|
| Tónica | I, ♯IV | VI, ♭III |
| Subdominante | IV, VII | II, ♭VI |
| Dominante | V, ♭II | III, ♭VII |

**Extensión a 24-EDO (propuesta del proyecto, no de Lendvai).** Un grado de cuarto de tono cae entre dos ejes vecinos.
Como la tercera menor tiene 6 cuartos de tono, esos grados forman tres ejes neutros: T–D (1+, ♭3+, ♯4+, 6+), D–S (♭2+,
3+, 5+, ♭7+) y S–T (2+, 4+, ♭6+, 7+).

El eje y la función de Riemann y Piston solo difieren en cuatro grados: III y ♭II son D para Lendvai, VII es S y ♯IV es
T. En el tabroll24 el eje se escribe solo cuando no coincide con la función («D sens. · eje S»).

Cada cambio de fundamental se clasifica como adelante (T→S→D→T, como V-I, I-IV o IV-V), atrás (como I-V o IV-I),
dentro del mismo eje (sustitución por tercera menor o tritono), en el mismo eje neutro o microtonal.

Lo que ya muestra: en Sarniezz, el 24 % de los cambios de la partitura queda dentro del eje de tónica (I ↔ ♭III, Mi ↔
Sol), una sustitución y no un movimiento por quintas; el cuaderno no lo ve porque lee ese Mi mayor como VII. Las
canciones con cuartos de tono se mueven entre un eje de Lendvai y uno neutro (Mata Zyklek D ↔ D–S, Yor Zarad T ↔ D–S).

## Paso 5: tabroll con la armonía en 24-EDO

`tabroll24_pNN.png` y `tabroll24_completo.png`, en la misma carpeta de imágenes que el tabroll (celdas `harmony_labels`
y la última del cuaderno). Es el mismo tabroll, con la franja de acordes de `armonia` en lugar de la de 12 clases:

- **Cifrado.** Números romanos sobre el centro, con la convención del tabroll: sus2, sus4 y 5 abajo; n, ° y aum arriba;
  «+» sube un cuarto de tono.
- **Inversión.** Bajo cifrado: ⁶ primera inversión, ⁶₄ segunda, ⁴₂ séptima en el bajo. Si la calidad ya ocupa un índice,
  la cifra va arriba (6/4).
- **Nombre.** Debajo del compás, con las notas en 24-EDO y barra para el bajo cuando no es la fundamental: G/D, Dsus2/D♯+.
- **Función.** Debajo del cifrado, en su color: T tónica (dorado), S subdominante (azul), D dominante (rojo), N neutra
  (lila); en minúscula si el acorde es menor, con su matiz corto (rel., modal, sens., V/V, nap., mixt., tt).
- **Confianza.** Los compases de baja confianza van entre paréntesis, como los acordes deducidos del tabroll de 12 clases.
- Las barras de la franja tienen el color del grado de la fundamental, como las filas.

Si `CENTRO` no es 'cuaderno', los romanos cuentan desde el centro y los colores desde la tónica del tabroll.

## Paso 6: notas columna

Celdas `melodic_columns` y `columns_summary`, y la celda que las aplica, antes del tabroll24. En cada compás (un cuadro
del tabroll):

- **Columnas de pulso.** En cada pulso, la nota de la voz aguda con más peso y el bajo que suena en ese momento («1 D3/D2
  · 2 E3/E2 …»). El peso combina cuatro reglas de preferencia, a la manera de la reducción de Lerdahl y Jackendoff: dónde
  cae el ataque, si es nota del acorde del compás, cuánto dura y si es un punto alto o bajo del contorno. Los pesos
  (`PESOS`) son fijos y no se ajustan con la partitura.
- **Columna principal.** La de más peso del compás: nota aguda, bajo, intervalo entre los dos, qué es la nota en el
  acorde y en qué pulso cae.
- **Arco.** La forma de la voz aguda en el compás: arco (sube y baja), valle, asciende, desciende o plano, con su cumbre
  y su ámbito.
- **Resumen.** En los compases confiables: qué es la columna en el acorde, intervalo con el bajo, arcos, pulsos y, en cada
  ciclo de la voz aguda, su columna y su arco más frecuentes.

Que la columna caiga dentro del acorde (99-100 %) dice poco, porque el acorde sale de las mismas notas. La evaluación
aplica la misma regla a la melodía principal y al bajo de la partitura:

| Canción | Misma nota principal | Entre las columnas de pulso | Mismo bajo | Misma nota del acorde | Mismo arco |
|---|---:|---:|---:|---:|---:|
| Sarniezz | 31 % | 57 % | 33 % | 32 % | 59 % |
| Mata Zyklek | 63 % | 83 % | 81 % | 64 % | 53 % |
| Fabienk | 37 % | 68 % | 29 % | 36 % | 35 % |

La nota de la partitura suele estar entre las columnas de pulso del cuaderno aunque no sea la principal: la regla elige
otra, sobre todo cuando la fundamental o el ritmo del cuaderno difieren. La partitura mide qué tan estable es la regla
frente a los errores de transcripción, no si elige bien musicalmente. Lo que sí confirma: la guitarra dobla al bajo en
unísono u octava buena parte del tiempo (38-73 % de las columnas de la partitura), y el resto se apoya en quintas y
terceras.

En el tabroll24, la columna principal de cada compás va marcada con anillos dorados en la nota aguda y en el bajo,
unidos por una línea; las columnas de los demás pulsos, con un anillo blanco fino. En Sarniezz se ve que la guitarra y
el bajo tocan la misma línea a una octava; en el ciclo E de Yor Zarad la columna es G♯+ sobre G♯+, un grado de cuarto
de tono que sostiene el arco.

## Lo que todavía no hace

Lo que sigue pertenece a los pasos siguientes de la estrategia: las notas extrañas, el inicio de cada ciclo por su
  cadencia más fuerte, las séptimas, y la figura y las distancias del círculo.
