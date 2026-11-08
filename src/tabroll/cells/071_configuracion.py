"""Celda 137 del notebook original. Descripcion asociada: Configuracion preliminar:.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

VIEW_SECONDS = None
BEATS_PER_PAGE = 21
PX_PER_BEAT = 64
OUTPUT_DIR = BASE_DIR / 'harmony_outputs' / audio_path.stem; OUTPUT_DIR.mkdir(parents=True, exist_ok=True)   # una carpeta por canción
for old in OUTPUT_DIR.glob('*.png'): old.unlink()                                                           # las imágenes de la vez anterior se reemplazan

view_scale = fine_scale(scale, tonic_midi) if FINE_ROWS else scale
view_chords = [replace(c, numeral=c.numeral or label_chord(c, scale)[0], name=c.name or label_chord(c, scale)[1]) for c in chords]
ROW_H = 11 if FINE_ROWS else 18

_n = view_scale.n
_row_of = lambda nt: view_scale.locate(nt.cents)[0]

_median_oct = int(np.floor(np.median([_row_of(nt) for nt in song.notes]) / _n))
_mmss = lambda s: f'{int(s // 60)}:{int(s % 60):02d}'
_bar_no = {id(m): k + 1 for k, m in enumerate(song.measures)}
