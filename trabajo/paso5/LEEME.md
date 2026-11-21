# Paso 5: equivalencias en 19, 31 y 53-EDO

Van en `scripts/`:
- `equivalencias_edo.py` (nuevo). Importa funciones de `figuras_album.py`.
- `figuras_album.py` (arreglo de la figura a): el estilo predominante y el secundario ahora salen de cuántos bloques gana cada corpus, no del percentil medio. En tu figura el percentil medio daba un empate (hindustani 32, rock 31, jazz 31) que no decía nada. Si las dos primeras medias quedan a menos de 3 puntos, el título lo dice.

## Qué correr (en la raíz del repo)

1. Angor no está en `bloques_v8.json` (salen 5 canciones). Vuelve a correr verosimilitud_por_bloques v8 con Angor, con los mismos argumentos de tu última corrida y la carpeta de Angor añadida.
2. Después:
```
python scripts/equivalencias_edo.py outputs/*angine_de_poitrine* outputs/*fabienk_official_audio_repro --salida outputs/equivalencias_edo
python scripts/figuras_album.py outputs/*angine_de_poitrine* outputs/*fabienk_official_audio_repro --control outputs/*primus* --comparar outputs/*king_gizzard* --bloques outputs/bloques_v8.json --campos outputs/campos_haba --fases outputs/ciclos_metricos_fases.csv --salida outputs/figuras_album
```
Mándame la consola de los dos, `outputs/equivalencias_edo.md` y `figuras_album_a_clasificacion.png`.

`ejemplo/` es lo que me dio a mí con mis corridas (deberían coincidir con las tuyas: son las mismas canciones).
