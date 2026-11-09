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
