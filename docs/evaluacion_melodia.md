# Evaluación de la melodía y el bajo

La evaluación mide las notas que da el cuaderno (`raw_high` y `raw_bass` de `line_diagnostics.json`) contra las
partituras corregidas de Mata Zyklek, Sarniezz y Fabienk. No interviene en el análisis: el cuaderno nunca lee las
partituras, ni el `.gp`, ni este módulo.

## Cómo correrla

`run_song.py` la corre sola al final de cada corrida de esas tres canciones y guarda, en la carpeta de la corrida:

- `evaluacion_melodia.json`: las medidas globales y por sección.
- `evaluacion_melodia_por_seccion.csv`: la tabla por sección.
- Un resumen en `resumen.md` y en `resumen.json` (`evaluacion_melodia`).

Para medir corridas que ya existen:

```bash
python scripts/evaluar_melodia.py outputs/<carpeta> [outputs/<otra> ...] [--secciones]
```

## Qué se mide

Cada nota de la referencia cuenta como acierto si el cuaderno da una nota con el ataque a ±75 ms y la misma altura
(±25 cents, es decir, la misma casilla de 24-EDO). Con eso se calcula la F (media armónica de precisión y
exhaustividad). Las versiones «sin octava» aceptan la misma clase de altura en cualquier octava.

| Medida | Referencia |
|---|---|
| `principal` (medida primaria) | La melodía principal de cada sección: la guitarra que lleva la melodía según el autor (tabla `MELODIA_PRINCIPAL` en `src/tabroll/evaluation/melodia.py`). Donde esa guitarra calla, cuenta la nota más aguda de las demás. Las secciones sin asignar usan la nota más aguda. |
| `mas_aguda` (secundaria) | La nota más aguda de todas las guitarras en cada instante. Es más dura: castiga seguir la melodía cuando otra guitarra suena un momento más arriba. |
| `bajo` | La nota más grave de los bajos. |

Cuando dos instrumentos tocan la misma nota a la vez, cuenta una sola vez, porque el cuaderno da una sola nota.

La melodía principal se eligió por criterio musical, la voz que uno cantaría, y nunca mirando qué guitarra sigue el
cuaderno.

## Alineación y tramos que no se miden

`references/alineaciones/*.json` guarda el camino DTW entre la partitura y el audio oficial. La evaluación lo ajusta a
una recta por sección, porque la banda graba con looper y el tempo no cambia dentro de una sección. Si la sección
entera no es compatible con un tempo constante, se parte en ventanas de 4 s y solo se miden las que sí lo son. Las que
no lo son tienen pendiente lejos de 1, se desvían más de 60 ms o tienen más de un 15 % de partitura que el audio no
tiene.

Este criterio usa solo la alineación, nunca la salida del cuaderno. Se conserva este tiempo medible:

| Canción | Tiempo medible |
|---|---|
| Mata Zyklek | 83 % |
| Sarniezz | 83 % |
| Fabienk | 72 % |

Lo que queda fuera:

- **Fabienk, la introducción.** La grabación de estudio no sigue el reparto de vueltas de la transcripción: el bajo
  entra en 0:12 y la guitarra calla de 0:16 a 0:25.
- **Sarniezz, c. 58–63.** En 3:23 suena una línea de la guitarra 1 que la partitura no tiene y cuyo ritmo no quedó
  fijado.
- **Lo que las partituras ya marcaban como no medible.** El «go go» de Sarniezz y los acordes sueltos de Fabienk.

## Correcciones de las partituras

Las de Sarniezz y Fabienk se hicieron de oído el 9-nov-2026. Cada una se verificó con clips: la pista de guitarra real
en un canal y la partitura sintetizada en el otro. Están anotadas en la cabecera de `references/sarniezz_partitura.py`
y de `references/fabienk_partitura.py`. Mata Zyklek usa `references/mata_zyklek_loops.py` sin cambios.

## Advertencia sobre las pistas separadas

El resultado depende de las pistas de guitarra y bajo. El mismo código dio 57.2 en Mata Zyklek con unas pistas de
Demucs y 61.6 con otras. Para comparar versiones del cuaderno hay que usar siempre las mismas pistas, y en la tesis
conviene indicar qué separación se usó.

## Notas sueltas (`drop_loose_notes`)

Por cada nota de la melodía principal, en las corridas del paso 3, el cuaderno detectaba 1.3 a 1.5 notas. Entre 43 y
64 % de las notas detectadas no estaban en la melodía principal: unas eran de otras capas del looper y la mayoría eran
pedazos cortos que deja `extract_notes`, que corta una nota nueva en cada ataque y en cada cambio de altura.

`drop_loose_notes` quita las notas de hasta 3 cuadros (menos de 80 ms) que no reaparecen a la misma altura una vuelta
antes y una vuelta después del ciclo que las contiene. Se eligió así porque en las tres canciones, entre esas notas,
solo 6 a 24 % eran aciertos; las notas cortas que sí vuelven en las dos vueltas vecinas aciertan mucho más y se quedan.
Se aplica a las dos voces (`scripts/limpiar_notas.py`).

| | Melodía principal | Bajo |
|---|---|---|
| Mata Zyklek | 63.7 → 66.8 | 78.7 → 82.9 |
| Sarniezz | 43.4 → 46.2 | 75.3 → 78.7 |
| Fabienk | 44.0 → 45.4 | 63.8 → 69.3 |

Se probaron otras reglas y se descartaron. Unir notas seguidas de la misma altura borra re-ataques reales del riff. La
saliencia no distingue un re-ataque de un corte. Las notas de otra capa no se distinguen por cuántas vueltas llevan
sonando. Quitarlas pide separar la capa en el audio, que es un paso aparte.
