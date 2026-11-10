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

## Lo que todavía no hace

Lo que sigue pertenece a los pasos siguientes de la estrategia: las notas extrañas, el inicio de cada ciclo por su
  cadencia más fuerte, el tipo de cadencia, las séptimas, y la figura y las distancias del círculo.
