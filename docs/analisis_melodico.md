# Análisis melódico

## Paso M1: figuras melódicas

Celda `melodic_figures` y la celda que la aplica, antes del tabroll24. La voz aguda se corta en frases (notas separadas
por menos de un pulso) y en cada frase se mide:

- **Intervalos** entre notas seguidas, por clase: unísono, cuarto de tono, semitono, tres cuartos de tono, tono, tercera,
  cuarta o quinta, sexta o más. Grado conjunto es de un cuarto de tono a un tono; microtonal, todo intervalo que no es un
  número entero de semitonos (también las terceras neutras).
- **Giros**: la figura de cada nota con la anterior y la siguiente (repetición, repite y sigue, paso, bordadura, vuelta
  por grado, salto y paso, salto y vuelta, paso y salto, arpegio, zigzag), con «(¼)» si hay un intervalo microtonal. El
  giro principal de cada compás y de cada ciclo de la voz aguda.
- **Espectro**: el tiempo que suena cada grado de 24-EDO sobre el centro, y qué parte cae en grados de cuarto de tono.
- **Notas extrañas** al acorde del compás, en los compases confiables: inflexión de ¼ de tono (una nota del acorde
  desplazada un cuarto de tono), retardo, anticipación, nota de paso, bordadura, vuelta, apoyatura, salto a nota extraña,
  escapada o libre.

| Canción | Grado conjunto | Saltos | Repetidas | Intervalos microtonales | Espectro en ¼ de tono | Notas extrañas |
|---|---:|---:|---:|---:|---:|---:|
| Sarniezz | 46 % | 33 % | 21 % | 48 % | 25 % | 52 % |
| Mata Zyklek | 56 % | 14 % | 30 % | 45 % | 24 % | 43 % |
| Fabienk | 43 % | 33 % | 24 % | 23 % | 14 % | 39 % |
| Utzp | 42 % | 24 % | 34 % | 25 % | 12 % | 37 % |
| Yor Zarad | 48 % | 27 % | 25 % | 29 % | 17 % | 50 % |

**Contra la partitura** (`evaluacion_armonia.json`), con la melodía principal de la partitura en los mismos compases:

| Canción | Intervalos microtonales (cuaderno / partitura) | Notas extrañas | Distancia de intervalos | De giros | De espectro | De tipos de extrañas |
|---|---:|---:|---:|---:|---:|---:|
| Sarniezz | 50 / 51 % | 59 / 60 % | 0.042 | 0.069 | 0.106 | 0.020 |
| Mata Zyklek | 48 / 51 % | 49 / 48 % | 0.018 | 0.034 | 0.025 | 0.045 |
| Fabienk | 20 / 22 % | 40 / 38 % | 0.063 | 0.108 | 0.032 | 0.110 |

Aunque las notas sueltas coinciden solo en 46-67 %, los repartos coinciden con la partitura. Los cuartos de tono son
parte del lenguaje melódico: la partitura también tiene la mitad de los intervalos microtonales en Sarniezz y Mata
Zyklek. La nota extraña más común es la inflexión de ¼ de tono de una nota del acorde; en Mata Zyklek y Utzp, la
bordadura. El cuaderno cuenta de más las notas repetidas (21 contra 9 % en Sarniezz) porque a veces parte una nota larga
en dos.

## Paso M2: patrones de ciclo

Celda `cycle_patterns` y la celda que la aplica, antes del tabroll24. Para cada ciclo (letra) de cada voz:

- **Patrón.** Las vueltas de la letra se ponen una sobre otra en una rejilla de semicorcheas; el patrón es la nota que
  aparece en cada casilla en al menos la mitad de las vueltas. Si una letra aparece con un periodo que es múltiplo de
  otro, se parte en vueltas del más corto.
- **Qué es cada nota del patrón.** Su posición (pulso.subdivisión), su grado sobre el centro y qué es en el acorde del
  momento: fundamental, 2.ª, 3.ª, 4.ª, 5.ª, inflexión de ¼ de tono o disonante, con la nota a la que resuelve si la
  siguiente está a un grado y es del acorde («4 (disonante → ♭3)»). El resumen dice qué parte de las disonantes resuelve
  por grado y si el patrón termina en reposo (1 o 5) o queda abierto.
- **Cada vuelta** se compara con el patrón: qué parte de sus notas coincide (se acoge) y, si no es igual, por qué:
  inflexión de ¼ de tono, cambio de octava, otras notas, notas omitidas, notas agregadas, transportada, cambios menores o
  cambia el acorde. Un motivo de notas cuenta si toca al menos el 10 % del patrón. Por compás: `acoge_aguda`,
  `motivo_aguda`, `acoge_bajo` y `motivo_bajo`.
- **Dónde varía**: las notas del patrón que más cambian entre vueltas y a qué nota.

Lo que muestra: en el bajo de Mata Zyklek (ciclo B) lo que más varía es G♯+1 ↔ G1, la fundamental y su vecina un cuarto
de tono arriba; en el de Fabienk (ciclo B), la octava y un cuarto de tono bajo la fundamental; en el de Yor Zarad sobre
♭II+5 (ciclo B), el G resuelve hacia arriba a G♯+: el grado de cuarto de tono es la meta.

**Contra la partitura**, con las mismas vueltas (solo las que caen enteras en compases medidos):

| Canción | Parecido de los patrones (medida F) | Se acogen: cuaderno | Se acogen: partitura |
|---|---:|---:|---:|
| Sarniezz | 52 % | 57 % | 62 % |
| Mata Zyklek | 86 % | 56 % | 60 % |
| Fabienk | 78 % | 72 % | 67 % |

En la partitura las vueltas tampoco se repiten iguales: la variación entre vueltas es real, no solo error de
transcripción. «Cambia el acorde» sale mucho, pero en parte es ruido de la detección de acordes.
