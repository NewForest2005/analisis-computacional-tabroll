# Paso 3c: King Crimson y Gentle Giant como repertorios comparados

Reemplaza en `scripts/` estos cuatro archivos. El único cambio: los nombres de las canciones salen sin el nombre del grupo delante (King Gizzard, King Crimson, Gentle Giant, Primus). Las cifras no cambian.

## 1. Audio
- Nombra cada archivo «King Crimson - <tema>.mp3» o «Gentle Giant - <tema>.mp3». Así las carpetas de salida llevan `king_crimson_` o `gentle_giant_` y los globs las encuentran.
- Que el nombre NO contenga «Angine de Poitrine», «Primus» ni «King Gizzard»: si no, el tema entraría en el grupo equivocado.
- Córrelos uno por uno con la ruta completa, sin `--set` ni `--preset` (los mismos ajustes que King Gizzard, para que sean comparables):
  `python scripts/run_song.py "Angine de Poitrine Audios/King Crimson - Discipline.mp3"`
- Comprueba que cada carpeta nueva tenga `armonia.json` y `line_diagnostics.json`.

## 2. No pisar lo que usa el artículo
Todo lo nuevo va en `outputs/prog/`. No cambies `--salida` a ninguno de estos: `outputs/bloques_v8.*`, `outputs/campos_haba.*`, `outputs/ciclos_metricos*`, `outputs/comparar_kg*`, `outputs/figuras_album_*`, `outputs/equivalencias_edo.*`.
```
mkdir -p outputs/prog
```

## 3. Comandos (un repertorio por vez; cambia king_crimson por gentle_giant y kc por gg)
```
python scripts/comparar_repertorio.py outputs/*angine_de_poitrine* outputs/*fabienk_official_audio_repro --repertorio outputs/*king_crimson* --control outputs/*primus* --nombre "King Crimson" --salida outputs/prog/comparar_kc
python scripts/campos_haba.py outputs/*angine_de_poitrine* outputs/*fabienk_official_audio_repro --control outputs/*primus* --comparar outputs/*king_crimson* --salida outputs/prog/campos_kc
python scripts/ciclos_metricos.py outputs/*angine_de_poitrine* outputs/*fabienk_official_audio_repro outputs/*king_crimson* --salida outputs/prog/ciclos_kc
```
Test por bloques: repite EXACTAMENTE los argumentos de tu corrida de `bloques_v8` (corpus, `--control` con Primus, umbral), y cambia solo dos cosas: `--comparar outputs/*king_crimson*` y `--salida outputs/prog/bloques_kc`. King Crimson y Gentle Giant van siempre en `--comparar`, nunca en `--control`: el control mide el error de medición con Primus y cambiarlo movería todas las cifras del artículo.

Si Angor no entra con `*angine_de_poitrine*`, agrega su carpeta a mano, como antes.

## 4. Qué mandarme
La consola de los cuatro comandos de cada grupo y `outputs/prog/*.md`.
