"""Tabroll con la armonía en 24-EDO: `tabroll24_pNN.png` por página y `tabroll24_completo.png` en la carpeta de imágenes. Las notas columna van marcadas: la principal de cada compás con anillos dorados en la nota aguda y en el bajo, unidos por una línea; las de los demás pulsos, con un anillo blanco fino. `MOSTRAR_TABROLL24 = True` muestra aquí cada página.
"""

MOSTRAR_TABROLL24 = False                                              # las imágenes se guardan siempre

acordes24 = [Chord(song.measures[e['compas'] - 1].start, song.measures[e['compas'] - 1].beats, e['tones'],
                   numeral=e['numeral'], name=e['name'], annot=e['annot'], annot_color=e['annot_color'])
             for e in harmony_labels(armonia, tonic_midi) if e['compas'] <= len(song.measures)]
columnas24 = [dict(onset=round(float(pos(c['t'])) / GRID) * GRID, cents=(c['midi'] - tonic_midi) * 100.0,
                   bajo=None if c['bajo_midi'] is None else (c['bajo_midi'] - tonic_midi) * 100.0,
                   principal=c['pulso'] == r['columna_pulso'])
              for r in armonia for c in r.get('columnas_pulso') or []]
tabroll24 = render_song_graphic(filename='tabroll24', show=MOSTRAR_TABROLL24, chords=acordes24, columns=columnas24)
