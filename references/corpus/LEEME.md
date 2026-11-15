# Corpus de referencia (pop, progresiones, jazz)

Datos sacados de los materiales del usuario (`Lo_que_sigue.zip`, gráficos de Hooktheory) el 14-nov-2026. Sirven solo para
comparar: no entran al análisis del cuaderno. Los scripts que los generan están en `trabajo/` (`doc23/albumes.py` y
`doc23/construir_corpus.py`).

| Archivo | Qué tiene |
|---|---|
| `albumes_progresiones.csv` | 121 temas de 9 álbumes (Adele, Reneé Rapp, Luke Combs, Billie Eilish, Taylor Swift, Lil Nas X, Lorde, Ed Sheeran, Tate McRae): la progresión que muestra Hooktheory por tema, en cifrado romano, el grado del bajo (color del círculo) y conteos de séptimas, inversiones, prestados, aplicados y sus/add |
| `albumes_frecuencia_acordes.csv` | % de cada acorde (M: = tema en mayor, m: = en menor) por álbum y en total (682 acordes) |
| `albumes_transiciones.csv` | Cambios de acorde (el último vuelve al primero, como bucle), total y por álbum |
| `albumes_progresiones_compartidas.csv` | Bucles de 2 a 5 acordes que aparecen en dos o más temas, normalizados por rotación |
| `albumes_parecido_js.csv` | Distancia de Jensen-Shannon entre las distribuciones de acordes de los álbumes (0 = iguales) |
| `progresiones_catalogo.csv` | 21 progresiones con nombre (de 20 MIDI): código, acordes en Do, romanos, funciones, raíces en cuartos de tono, canciones de ejemplo y alturas MIDI |
| `linea_base_pop.json` | Tónicas más usadas por modo, acordes más usados en Do mayor, raíces, bajos, funciones y categorías |
| `metricas_hooktheory.csv` | Las cinco métricas (0-100, 50 = canción media) de 32 obras |
| `jazz_ejemplos_theorytab.csv` | Acordes de 4 ejemplos de jazz en formato TheoryTab: «Autumn Leaves», blues de 12 compases, «So What» y «Giant Steps» |

Avisos:
- En los PDF, la fuente del cifrado tiene codificación propia; se decodificó por el número de glifo y se comprobó a la vista
  en cuatro álbumes (incluido el «vii°»). Los superíndices 6 y 7 pegados al número son la inversión ⁶ y la séptima ⁷.
- En temas en mayor, «VII» en mayúscula se escribió ♭VII: en varios PDF el bemol no está en el texto.
- En 3 temas el número de círculos no coincide con el de acordes (círculos rayados): allí `bajo_grados` queda vacío.
- Las métricas de «Stick Season» y de los temas vault de «Speak Now» se midieron de las barras (±1).
- Es una muestra pequeña de pop de 2021-2023: sirve de línea base, no de corpus de un estilo. Los corpus grandes por estilo
  están listados en `24_estilos_y_corpus.md`.
