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

## Lo que todavía no hace

Lo que sigue pertenece a los pasos siguientes de la estrategia: la tónica en 24-EDO (hoy se toma la del cuaderno, de 12
clases), las séptimas, las notas extrañas, las cadencias y el círculo.
