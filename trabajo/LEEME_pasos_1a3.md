# Pasos 1 a 3 (16-nov)

Los tres van en `scripts/`. Probados solo en mi copia de trabajo; no toqué el repo.

1. `comparar_repertorio.py`: quita corridas repetidas (si dos globs traen la misma canción, se queda la última). Así desaparece el 0.00 falso entre temas de King Gizzard.
2. `campos_haba.py` (nuevo): desplazamiento de campos de Hába y uso de los cuartos de tono, con modelos nulos por permutación.
3. `ciclos_metricos.py` v2: añade «bucle contra compás» (fase del riff en cada compás; polímetro o rotación).

## Qué correr (en la raíz del repo)

```
python scripts/comparar_repertorio.py outputs/*angine_de_poitrine* --repertorio outputs/*king_gizzard* --control outputs/*primus* --salida outputs/comparar_kg
python scripts/campos_haba.py outputs/*angine_de_poitrine* --control outputs/*primus* --comparar outputs/*king_gizzard* --salida outputs/campos_haba
python scripts/ciclos_metricos.py outputs/*angine_de_poitrine* outputs/*king_gizzard* --salida outputs/ciclos_metricos
```
Mándame la salida de consola de los tres y `outputs/campos_haba.md`, `outputs/ciclos_metricos.md`.

`resultados_prueba/` tiene lo que me dio a mí con las corridas que tengo (Vol. II completo, 3 de Primus, 5 de King Gizzard). Tus corridas tienen los 9 temas de KG: valen las tuyas.
