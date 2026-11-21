# Regla combinada de «grado fijo» en cuarto de tono

Reemplaza scripts/comparacion/verosimilitud_por_bloques.py (usa campos_haba.py, que va también por si acaso).

Una canción cuenta como microtonal (bloque «Cuartos de tono») si cumple las tres:
1. concentración en dos grados con z ≥ 2 frente a Primus;
2. al menos 10 s de melodía en cuarto de tono (`--min-segundos-cuartos 10`);
3. separación de campos de Hába: bajo y voz aguda evitan sonar en campos distintos al menos un 30 % más que el azar (`--efecto-campos 30`) con p < 0.01 (`--alfa-campos 0.01`).

Se pide el tamaño del efecto y no solo p: con muchos compases, Level Five evita apenas un 7 % y ya da p = 0.002.
Para volver a la regla anterior (solo 1 y 2): `--alfa-campos 1`.

Tarda más: corre la prueba de campos (500 permutaciones) en cada canción que pasa 1 y 2.

Qué correr: bloques_v8 y las corridas de Zappa, King Crimson y King Gizzard con los mismos argumentos de siempre y `--salida outputs/prog/bloques_regla`. Mándame la consola.
