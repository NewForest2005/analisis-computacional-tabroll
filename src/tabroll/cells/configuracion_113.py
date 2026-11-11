"""Tabroll con la armonía en 24-EDO: `tabroll24_pNN.png` por página y `tabroll24_completo.png` en la carpeta de imágenes. `MOSTRAR_TABROLL24 = True` muestra aquí cada página.
"""

MOSTRAR_TABROLL24 = False                                              # las imágenes se guardan siempre

acordes24 = [Chord(song.measures[e['compas'] - 1].start, song.measures[e['compas'] - 1].beats, e['tones'],
                   numeral=e['numeral'], name=e['name'], annot=e['annot'], annot_color=e['annot_color'])
             for e in harmony_labels(armonia, tonic_midi) if e['compas'] <= len(song.measures)]
tabroll24 = render_song_graphic(filename='tabroll24', show=MOSTRAR_TABROLL24, chords=acordes24)
