# Referencias de evaluación

`mata_zyklek_loops.py` contiene la transcripción de referencia de los loops de Mata Zyklek. Las alturas están escritas como en la partitura, con cuartos de tono; las guitarras y los bajos del audio suenan una octava abajo.

Para comparar con alturas detectadas del audio, usar:

```python
audio_pitch = written_pitch - 12
```

La referencia conserva las excepciones conocidas del audio oficial: la figura rápida ausente aproximadamente en los compases 194–201 y los desplazamientos de un pulso en los compases 57, 98 y 129.

`sarniezz_corrections.py` registra una corrección verificada en la partitura de
Sarniezz: la última nota del primer compás del riff es Re#+. El archivo
MusicXML la escribe como Mi medio bemol, su equivalente enarmónico en cuartos
de tono.

Los JSON generados desde Guitar Pro (`*_gp.json`) conservan dos conceptos:
`pitch.name` es el nombre visual de la partitura y `pitch.midi_with_bend` es
el `ConcertPitch` que Guitar Pro guarda como altura sonora MIDI. Para alinear
con el audio se debe usar `midi_with_bend` directamente; no hay que restar otra
octava a ese campo.

## Partituras corregidas para la evaluación

`sarniezz_partitura.py` y `fabienk_partitura.py` son las transcripciones de Andrew Kahler desplegadas nota a nota,
con las correcciones hechas de oído y comprobadas contra la grabación oficial (9-nov-2026; la lista está en la
cabecera de cada archivo). Junto con `mata_zyklek_loops.py` son las referencias que usa
`src/tabroll/evaluation/melodia.py`. Las alturas están ESCRITAS: guitarras y bajos suenan una octava abajo
(`TRANSPOSE`).

`alineaciones/*.json` guarda, para cada canción, el camino DTW entre la partitura y el audio oficial. Está calculado
sobre ese audio, así que con otra versión de la grabación hay que recalcularlo. Ver `docs/evaluacion_melodia.md`.
