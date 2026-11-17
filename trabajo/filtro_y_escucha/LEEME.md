# Filtro de cuartos de tono con mínimo de tiempo, y escucha de Red (16-nov)

## 1. scripts/verosimilitud_por_bloques.py (reemplaza el del repo)
- Nuevo: la concentración solo cuenta si la melodía tiene al menos 10 s en cuarto de tono (`--min-segundos-cuartos`, por defecto 10).
- La consola muestra los segundos: «¼ tono 25.3 % (48.4 s), concentración …».
- La banda no cambia (Angor, la que menos tiene: 13.5 s). Quedan fuera Discipline (0.3 s), G-Spot Tornado (6.8 s), The Black Page #1 (4.4 s), Peaches en Regalia (2.1 s) y Frame by Frame (8.3 s).
- Para que las cifras del artículo salgan con el filtro nuevo, vuelve a correr bloques_v8 con los mismos argumentos, y también las corridas de Zappa y King Crimson (salidas en outputs/prog/).

## 2. escucha_red/ (5 momentos de Red, 4 s cada uno, pista de guitarra y mezcla)
El cuaderno marca en Red un 25 % del tiempo en cuarto de tono, sobre todo La#+ (un cuarto de tono por encima de La#) y Mi+, con centro en Mi. La nota marcada está a 1.5 s del inicio de cada clip.
En cada clip, di cuál de estas oyes:
- A: un bend o un slide que pasa por esa altura (la nota no se queda ahí).
- B: una nota fija que suena desafinada (más alta que La# o que Mi).
- C: no oigo nada raro: suena La# / Mi normales.
- D: no se distingue (distorsión).
Clips: 0:14.9, 0:32.3, 1:05.3, 1:47.3, 4:45.8.
