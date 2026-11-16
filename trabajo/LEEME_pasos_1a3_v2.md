# Arreglo de pasos 2 y 3

Los dos scripts ahora usan una sola corrida por canción (la más reciente) y saltan las carpetas sin armonia.json (_ejes).
Reemplaza `scripts/campos_haba.py` y `scripts/ciclos_metricos.py`.

Fabienk y Angor no entraron porque sus carpetas no llevan «angine_de_poitrine» en el nombre. Agrégalas al glob:

```
python scripts/campos_haba.py outputs/*angine_de_poitrine* outputs/*fabienk* outputs/*angor* --control outputs/*primus* --comparar outputs/*king_gizzard* --salida outputs/campos_haba
python scripts/ciclos_metricos.py outputs/*angine_de_poitrine* outputs/*fabienk* outputs/*angor* outputs/*king_gizzard* --salida outputs/ciclos_metricos
python scripts/comparar_repertorio.py outputs/*angine_de_poitrine* outputs/*fabienk* outputs/*angor* --repertorio outputs/*king_gizzard* --control outputs/*primus* --salida outputs/comparar_kg
```
(Si Angor tiene otro nombre de carpeta, usa ese.)
