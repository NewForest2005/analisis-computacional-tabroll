# Paso 4: figuras del álbum

Van en `scripts/`:
- `figuras_album.py` (nuevo): seis figuras del Vol. II.
- `ciclos_metricos.py` (arreglo): cuando dos rotaciones del riff encajan casi igual (riff de una sola nota), la fase queda en blanco en vez de forzarla a 0. Eso cambia los conteos de «coherentes»: hay que volver a correrlo.

`ejemplo_graficas/` son mis pruebas: con un bloques.json viejo (sin Radif ni KG), 5 temas de KG y 3 de Primus. Las tuyas salen con los datos finales.

## Qué correr (en la raíz del repo, en este orden)

```
python scripts/ciclos_metricos.py outputs/*angine_de_poitrine* outputs/*fabienk_official_audio_repro outputs/*king_gizzard* --salida outputs/ciclos_metricos
python scripts/figuras_album.py outputs/*angine_de_poitrine* outputs/*fabienk_official_audio_repro --control outputs/*primus* --comparar outputs/*king_gizzard* --bloques outputs/<json de tu última corrida de verosimilitud_por_bloques v8> --campos outputs/campos_haba --fases outputs/ciclos_metricos_fases.csv --salida outputs/figuras_album
```
(Si Angor no entra con `*angine_de_poitrine*`, agrégala con su carpeta.)

Mándame: la consola del primer comando y las seis `outputs/figuras_album_*.png`.

## Las figuras
- `_a_clasificacion`: percentil medio por canción y corpus, fila «Álbum», estilo predominante y secundario; abajo, qué corpus gana cada bloque.
- `_b_perfil`: medidas tipo Hooktheory (complejidad de acordes y melódica, tensión, novedad, % de ¼) frente a KG y Primus.
- `_c_circulo_haba`: círculo de quintas de 24 notas en sus dos campos (dorado regular, azul ¼), álbum y cada canción.
- `_d_campos_tiempo`: compás por compás, % de ¼ y mezcla vertical.
- `_e_campos_resumen`: las tres pruebas de campos por grupo (relleno = p < 0.003).
- `_f_bucle_compas`: fase del riff en cada compás.
