# Inventario de celdas extraidas

| Celda original | Archivo | Elementos principales | Descripcion |
|---:|---|---|---|
| 1 | [`001_configuracion`](../src/tabroll/cells/001_configuracion.py) | `configuracion / ejecucion` | Tabroll para cualquier cancion de Angine de Poitrine |
| 2 | [`002_0_librerias`](../src/tabroll/cells/002_0_librerias.py) | `configuracion / ejecucion` | Sin descripcion en markdown |
| 3 | [`003_1_subir_el_audio`](../src/tabroll/cells/003_1_subir_el_audio.py) | `configuracion / ejecucion` | Sin descripcion en markdown |
| 4 | [`004_1b_separar_guitarra_y_bajo_con_demucs`](../src/tabroll/cells/004_1b_separar_guitarra_y_bajo_con_demucs.py) | `configuracion / ejecucion` | Sin descripcion en markdown |
| 6 | [`005_find_stem`](../src/tabroll/cells/005_find_stem.py) | `find_stem` | find_stem: busca, entre los audios subidos, la pista de un instrumento que corresponde a la canción elegida (por ejemplo Canción_guitar.mp3 para Canción.mp3). Si no la encuentra, devuelve None. |
| 8 | [`006_separate_stems`](../src/tabroll/cells/006_separate_stems.py) | `separate_stems` | separate_stems: separa la canción con la red neuronal Demucs (modelo htdemucs_6s, el que tiene pista de guitarra) y guarda la guitarra y el bajo como Canción_guitar.mp3 y Canción_bass.mp3 junto a la canción. La primera vez instala demucs-infer y descarga el modelo. |
| 10 | [`007_configuracion`](../src/tabroll/cells/007_configuracion.py) | `configuracion / ejecucion` | Separar guitarra y bajo: si junto con la canción no subiste sus pistas _guitar y _bass, Demucs las saca del mismo audio y las descarga para que la próxima vez las subas con la canción y no haya que separar de nuevo. Con SEPARATE = False el análisis usa solo la mezcla. |
| 13 | [`008_mix_and_helpers`](../src/tabroll/cells/008_mix_and_helpers.py) | `mix, lighten, palette` | **`mix`**, **`lighten`** y **`palette`**: Mezclan dos colores, aclaran un color y generan una paleta de `n` colores a partir de la de Hooktheory. |
| 15 | [`009_accidental`](../src/tabroll/cells/009_accidental.py) | `accidental` | **`accidental`**: Alteración de `k` pasos. Usa ♯ y ♭ cuando un paso equivale a un semitono (12-TET); en otra afinación usa flechas ↑ y ↓, y cada flecha equivale a un paso. |
| 17 | [`010_scale`](../src/tabroll/cells/010_scale.py) | `Scale` | **`Scale`**: Escala musical en cents. |
| 19 | [`011_parse_scl`](../src/tabroll/cells/011_parse_scl.py) | `parse_scl` | **`parse_scl`**: Lee un archivo Scala `.scl` y devuelve `(alturas en cents desde 0.0, periodo en cents)`. |
| 21 | [`012_note_and_helpers`](../src/tabroll/cells/012_note_and_helpers.py) | `Note, Chord, Measure` | Modelo de la canción |
| 23 | [`013_song`](../src/tabroll/cells/013_song.py) | `Song` | **`Song`**: Reúne la escala, las notas, los acordes y los compases de una canción. |
| 25 | [`014_measures_from_lengths`](../src/tabroll/cells/014_measures_from_lengths.py) | `measures_from_lengths` | **`measures_from_lengths`**: Crea compases consecutivos a partir de sus duraciones; por ejemplo, `[4, 4, 2, 4]`. Admite cambios de métrica. |
| 27 | [`015_pieces`](../src/tabroll/cells/015_pieces.py) | `pieces` | **`pieces`**: Divide un evento en las barras de compás y devuelve `[(inicio, fin), ...]`, un tramo por cada compás que toca. |
| 29 | [`016_closest_and_helpers`](../src/tabroll/cells/016_closest_and_helpers.py) | `_closest, label_chord, _plain_len, _mathtext` | Etiquetado de acordes |
| 31 | [`017_implied_chords`](../src/tabroll/cells/017_implied_chords.py) | `implied_chords` | **`implied_chords`**: Completa los tramos sin acorde medido con la raíz de `chord_roots` y la calidad de las notas que suenan. Los acordes deducidos se muestran entre paréntesis. |
| 34 | [`018_style`](../src/tabroll/cells/018_style.py) | `Style` | **`Style`**: Estilo del gráfico, con medidas en píxeles. |
| 36 | [`019_timeline`](../src/tabroll/cells/019_timeline.py) | `Timeline` | **`Timeline`**: Convierte pulsos en píxeles, con un pequeño espacio entre compases. |
| 38 | [`020_fill`](../src/tabroll/cells/020_fill.py) | `_fill` | **`_fill`**: Dibuja un rectángulo del color del grado o, entre dos grados, rayas diagonales de los dos colores vecinos. El ancho de las rayas es proporcional a la posición de la altura entre ambos grados. |
| 40 | [`021_render`](../src/tabroll/cells/021_render.py) | `render` | **`render`**: Dibuja la canción y devuelve la figura. |
| 41 | [`022_2a_funciones_de_analisis_pulso_melodia_tonalidad_compases_y_acordes`](../src/tabroll/cells/022_2a_funciones_de_analisis_pulso_melodia_tonalidad_compases_y_acordes.py) | `configuracion / ejecucion` | Sin descripcion en markdown |
| 43 | [`023_stft_mag`](../src/tabroll/cells/023_stft_mag.py) | `stft_mag` | Espectros |
| 45 | [`024_mel_bank`](../src/tabroll/cells/024_mel_bank.py) | `mel_bank` | **`mel_bank`**: Crea un banco de `n` filtros triangulares en escala mel y devuelve `(filtros, frecuencias centrales)`. |
| 47 | [`025_onset_envelopes`](../src/tabroll/cells/025_onset_envelopes.py) | `onset_envelopes` | Pulso (beat tracking) |
| 49 | [`026_estimate_tempo`](../src/tabroll/cells/026_estimate_tempo.py) | `estimate_tempo` | **`estimate_tempo`**: Tempo (BPM) por autocorrelación de la envolvente de ataques, con un prior suave hacia ~120 BPM. |
| 51 | [`027_track_beats`](../src/tabroll/cells/027_track_beats.py) | `track_beats` | **`track_beats`**: Seguimiento de pulso por programación dinámica (Ellis, 2007). Devuelve los tiempos de pulso en segundos. |
| 53 | [`028_make_beat_map`](../src/tabroll/cells/028_make_beat_map.py) | `make_beat_map` | **`make_beat_map`**: Convierte segundos en posición en pulsos (0 = primer pulso), con extrapolación antes y después. |
| 55 | [`029_note_grid`](../src/tabroll/cells/029_note_grid.py) | `note_grid` | note_grid: mira en qué parte del pulso caen los ataques. Si caen en tercios, el pulso se divide en tres corcheas, como en el 12/8 de Sarniezz, y la cuantización pasa a 1/6 de pulso para que cada corchea quede en su sitio. Si no, deja GRID como está. |
| 57 | [`030_pitch_salience`](../src/tabroll/cells/030_pitch_salience.py) | `pitch_salience` | Altura (línea dominante) |
| 59 | [`031_harmonic_part`](../src/tabroll/cells/031_harmonic_part.py) | `harmonic_part` | **`harmonic_part`**: atenúa los golpes de batería en el espectrograma y conserva lo que se sostiene en el tiempo. |
| 61 | [`032_stereo_salience`](../src/tabroll/cells/032_stereo_salience.py) | `stereo_salience` | **`stereo_salience`**: calcula la saliencia de la voz aguda con el canal central y el lateral, para sacar el bajo sin perder la octava de la guitarra. Si el audio es mono, devuelve la saliencia normal. |
| 63 | [`033_add_guitar_stem`](../src/tabroll/cells/033_add_guitar_stem.py) | `add_guitar_stem` | **`add_guitar_stem`**: mezcla la saliencia de la voz aguda con la pista `guitar` de Demucs. Si no hay pista, deja la saliencia igual. |
| 65 | [`034_load_stem`](../src/tabroll/cells/034_load_stem.py) | `load_stem` | Sin descripcion en markdown |
| 67 | [`035_guitar_gate`](../src/tabroll/cells/035_guitar_gate.py) | `guitar_gate` | Sin descripcion en markdown |
| 69 | [`036_viterbi_pitch`](../src/tabroll/cells/036_viterbi_pitch.py) | `viterbi_pitch` | **`viterbi_pitch`**: Contorno de altura por Viterbi. Los estados son las alturas candidatas más un estado sin altura (`NaN`). |
| 71 | [`037_detect_onsets`](../src/tabroll/cells/037_detect_onsets.py) | `detect_onsets` | Notas |
| 73 | [`038_tuning_offset`](../src/tabroll/cells/038_tuning_offset.py) | `tuning_offset` | **`tuning_offset`**: Mide la desafinación global (en semitonos) en los parciales de las notas estables, con media circular sobre el grid de `step` cents. Usa el grid de semitonos para distinguir un desfase real de un cuarto de tono, y devuelve 0 si no hay evidencia clara. |
| 75 | [`039_extract_notes`](../src/tabroll/cells/039_extract_notes.py) | `extract_notes` | **`extract_notes`**: Segmenta el contorno en notas: corta en cada ataque y en cada cambio de altura. Devuelve `[(t_inicio_s, t_fin_s, altura MIDI)]`, con la altura cuantizada a la rejilla de `step` cents. |
| 77 | [`040_place_notes`](../src/tabroll/cells/040_place_notes.py) | `place_notes` | **`place_notes`**: coloca las notas de una voz en la rejilla del compás y resuelve las que se solapan. |
| 79 | [`041_configuracion`](../src/tabroll/cells/041_configuracion.py) | `configuracion / ejecucion` | Tonalidad y escala |
| 81 | [`042_chroma_profile`](../src/tabroll/cells/042_chroma_profile.py) | `chroma_profile` | **`chroma_profile`**: Perfil de 12 clases de altura de todo el espectro (acordes, bajo y melodía), sobre el espectro blanqueado y corregido con `offset`. |
| 83 | [`043_pc_histogram`](../src/tabroll/cells/043_pc_histogram.py) | `pc_histogram` | **`pc_histogram`**: Histograma de 12 clases de altura; una nota de cuarto de tono se reparte entre sus dos vecinas. |
| 85 | [`044_detect_key`](../src/tabroll/cells/044_detect_key.py) | `detect_key` | **`detect_key`**: Devuelve `(tónica_pc, modo)`: el conjunto de 7 notas que mejor cubre el histograma, con la clase más tónica como tónica. |
| 87 | [`045_key_alternatives`](../src/tabroll/cells/045_key_alternatives.py) | `key_alternatives` | Sin descripcion en markdown |
| 89 | [`046_parse_key`](../src/tabroll/cells/046_parse_key.py) | `parse_key` | **`parse_key`**: Convierte una tonalidad en `(pc, modo)`; por ejemplo, `('E', 'dorian')`, `('F#', 'minor')` o `('Bb', 'major')`. |
| 91 | [`047_spell_scale`](../src/tabroll/cells/047_spell_scale.py) | `spell_scale` | **`spell_scale`**: Nombres de las 7 notas con letras consecutivas (E dórico → E F♯ G A B C♯ D). |
| 93 | [`048_make_scale`](../src/tabroll/cells/048_make_scale.py) | `make_scale` | **`make_scale`**: `Scale` de tabroll con los 7 grados del modo; lo que cae entre grados se dibuja rayado (microtonal o cromático). |
| 95 | [`049_fine_scale`](../src/tabroll/cells/049_fine_scale.py) | `fine_scale` | **`fine_scale`**: Crea una escala de dibujo con 24 filas por octava para que cada cuarto de tono tenga su propia casilla. `D_{1/4}` es un cuarto de tono por encima de D. Los acordes se siguen nombrando con la escala normal. |
| 97 | [`050_zs`](../src/tabroll/cells/050_zs.py) | `_zs` | Compases (longitud variable) |
| 99 | [`051_beat_evidence`](../src/tabroll/cells/051_beat_evidence.py) | `beat_evidence` | **`beat_evidence`**: Evidencia de inicio de compás en cada pulso: golpe grave, golpe general y cambio de bajo. |
| 101 | [`052_meter_cue`](../src/tabroll/cells/052_meter_cue.py) | `meter_cue` | meter_cue: mide, pulso a pulso, cuánto se parecen los ataques (sobre todo de la batería) a los de L pulsos después. Donde la canción va en 7/8 se parecen cada 7 corcheas, y donde va en 2/4, cada 4. Así segment_bars sabe qué compás elegir en cada región de una canción que cambia de métrica. |
| 103 | [`053_segment_bars`](../src/tabroll/cells/053_segment_bars.py) | `segment_bars` | **`segment_bars`**: Puede recibir la pista de meter_cue. A cada compás posible de L pulsos le suma gamma · L · r, donde r es cuánto se repiten los golpes cada L pulsos en ese punto. Si no recibe la pista, funciona igual que antes. |
| 105 | [`054_beat_histograms`](../src/tabroll/cells/054_beat_histograms.py) | `beat_histograms` | Acordes |
| 107 | [`055_chord_roots`](../src/tabroll/cells/055_chord_roots.py) | `chord_roots` | **`chord_roots`**: Raíz del acorde en cada pulso, por Viterbi sobre 12 clases de altura, con inercia al cambio y una penalización suave a las raíces fuera de la escala. |
| 109 | [`056_mask_line`](../src/tabroll/cells/056_mask_line.py) | `mask_line` | **`mask_line`**: Borra de `M` los armónicos de una línea de altura, para dejar a la vista las demás notas que suenan a la vez. |
| 111 | [`057_chord_lines`](../src/tabroll/cells/057_chord_lines.py) | `chord_lines` | **`chord_lines`**: Busca hasta `n_lines` líneas simultáneas, borrando en cada paso los armónicos de la línea anterior. Compensa los armónicos compartidos entre notas, como en las quintas, y descarta las que suenan más de `min_db` dB por debajo de la línea principal. Devuelve una lista de contornos; el primero es `main`. |
| 113 | [`058_drop_echoes`](../src/tabroll/cells/058_drop_echoes.py) | `drop_echoes` | **`drop_echoes`**: Limpia las líneas adicionales; quita las notas que ya aparecen en las líneas anteriores dentro de ±`near` fotogramas, porque suelen ser restos de la ventana de análisis, y las que duran menos de `min_frames` fotogramas. |
| 115 | [`059_sonorities`](../src/tabroll/cells/059_sonorities.py) | `sonorities` | **`sonorities`**: Sigue cada nota por separado y crea un `Chord` cuando dos o más notas distintas se sostienen a la vez durante al menos `min_beats` pulsos, aunque otra línea se mueva debajo. Une huecos de hasta `bridge` pulsos y ordena las notas de grave a agudo, así que la más grave queda como raíz. Si solo suena una línea o una octava, no crea acorde. |
| 116 | [`060_2_analizar_el_audio_y_preparar_el_modelo_harmony`](../src/tabroll/cells/060_2_analizar_el_audio_y_preparar_el_modelo_harmony.py) | `configuracion / ejecucion` | Sin descripcion en markdown |
| 118 | [`061_configuracion`](../src/tabroll/cells/061_configuracion.py) | `configuracion / ejecucion` | Ajustes de inicializacion: |
| 120 | [`062_configuracion`](../src/tabroll/cells/062_configuracion.py) | `configuracion / ejecucion` | 1)  Pulso real de la grabación: los compases se miden en pulsos reales, no en una rejilla fija desde t=0. |
| 122 | [`063_configuracion`](../src/tabroll/cells/063_configuracion.py) | `configuracion / ejecucion` | 2) Altura: línea dominante, bajo y voz aguda. La voz aguda usa el canal lateral y, si existe, la pista `guitar` de Demucs. |
| 124 | [`064_configuracion`](../src/tabroll/cells/064_configuracion.py) | `configuracion / ejecucion` | 3) Notas: cada ataque o cambio de altura inicia una nota; alturas cuantizadas a pasos de MICRO_STEP cents. |
| 126 | [`065_configuracion`](../src/tabroll/cells/065_configuracion.py) | `configuracion / ejecucion` | 4) Tonalidad y modo detectados en cada canción -> escala de 7 grados como en Hooktheory. |
| 128 | [`066_norm`](../src/tabroll/cells/066_norm.py) | `_norm` | 5) Evidencia por pulso (qué clases de altura suenan): bajo y melodía. |
| 130 | [`067_configuracion`](../src/tabroll/cells/067_configuracion.py) | `configuracion / ejecucion` | 6) Compases de longitud variable (2, 3, 4, 7... pulsos), estimados con los acentos graves y los cambios de bajo. |
| 132 | [`068_configuracion`](../src/tabroll/cells/068_configuracion.py) | `configuracion / ejecucion` | 7) Acordes: raíz por pulso (bajo + melodía) y calidad según las notas que suenan. |
| 134 | [`069_configuracion`](../src/tabroll/cells/069_configuracion.py) | `configuracion / ejecucion` | 8) Notas de la voz grave y la voz aguda en pulsos (cuantizadas a GRID) y modelo final. |
| 135 | [`070_3_mostrar_el_grafico_de_armonia_toda_la_cancion_por_paginas`](../src/tabroll/cells/070_3_mostrar_el_grafico_de_armonia_toda_la_cancion_por_paginas.py) | `configuracion / ejecucion` | Sin descripcion en markdown |
| 137 | [`071_configuracion`](../src/tabroll/cells/071_configuracion.py) | `configuracion / ejecucion` | Configuracion preliminar: |
| 139 | [`072_sec_at`](../src/tabroll/cells/072_sec_at.py) | `sec_at` | **`sec_at`**: Convierte una posición en pulsos a segundos. |
| 141 | [`073_pages`](../src/tabroll/cells/073_pages.py) | `_pages` | **`_pages`**: Agrupa compases completos en páginas de hasta `BEATS_PER_PAGE` pulsos. |
| 143 | [`074_rows`](../src/tabroll/cells/074_rows.py) | `_rows` | **`_rows`**: Ventana vertical de la página: octavas completas que contienen sus notas, mínimo 3 como en Hooktheory. |
| 145 | [`075_stack`](../src/tabroll/cells/075_stack.py) | `_stack` | **`_stack`**: Une las páginas, una debajo de otra, en una imagen única; si pasa de `max_h` píxeles, la parte en varias. |
| 147 | [`076_render_song_graphic`](../src/tabroll/cells/076_render_song_graphic.py) | `render_song_graphic` | **`render_song_graphic`**: Dibuja la canción o un tramo (`start_s`, `duration_s`) por páginas, las guarda en `OUTPUT_DIR` y devuelve sus rutas. |
| 149 | [`077_cycle`](../src/tabroll/cells/077_cycle.py) | `Cycle` | **`Cycle`**: Patrón de notas que se repite en una voz durante un tramo de la canción. |
| 151 | [`078_find_cycles`](../src/tabroll/cells/078_find_cycles.py) | `find_cycles` | **`find_cycles`**: Busca qué periodos se repiten en una voz y en qué tramos de la canción. |
| 153 | [`079_note_changes`](../src/tabroll/cells/079_note_changes.py) | `note_changes` | **`note_changes`**: Encuentra en qué puntos del ciclo cambia la nota. |
| 155 | [`080_cycle_subdivision`](../src/tabroll/cells/080_cycle_subdivision.py) | `cycle_subdivision` | **`cycle_subdivision`**: Elige en cuántas casillas se divide el pulso de la canción. |
| 157 | [`081_smooth_path`](../src/tabroll/cells/081_smooth_path.py) | `smooth_path` | smooth_path |
| 159 | [`082_fold_cycle`](../src/tabroll/cells/082_fold_cycle.py) | `fold_cycle` | **`fold_cycle`**: Superpone las vueltas del ciclo y elige la nota de cada casilla, de la voz grave o de la aguda. |
| 161 | [`083_name_cycles`](../src/tabroll/cells/083_name_cycles.py) | `name_cycles` | **`name_cycles`**: Da la misma letra a los ciclos con las mismas notas y los hace empezar en el mismo punto. |
| 163 | [`084_cycle_anchor`](../src/tabroll/cells/084_cycle_anchor.py) | `cycle_anchor` | **`cycle_anchor`**: Busca el ciclo vecino con el que este debe compartir su inicio. |
| 165 | [`085_has_motion`](../src/tabroll/cells/085_has_motion.py) | `has_motion` | **`has_motion`**: Descarta los tramos que son una sola nota sostenida; un ritmo sobre una nota sí cuenta como ciclo. |
| 167 | [`086_stem_active`](../src/tabroll/cells/086_stem_active.py) | `stem_active` | Sin descripcion en markdown |
| 169 | [`087_cycle_song`](../src/tabroll/cells/087_cycle_song.py) | `cycle_song` | **`cycle_song`**: Convierte un ciclo en una canción de una sola vuelta para dibujarla. |
| 171 | [`088_cycle_bar`](../src/tabroll/cells/088_cycle_bar.py) | `cycle_bar` | cycle_bar: devuelve el compás que domina dentro de un ciclo, es decir, el más frecuente entre los compases que empiezan en él. Así cada ciclo se cuenta y se dibuja con su propio compás y no con el más común de toda la canción. |
| 173 | [`089_render_cycles`](../src/tabroll/cells/089_render_cycles.py) | `render_cycles` | **`render_cycles`**: El parámetro bar puede ser un número fijo o una función que devuelva el compás de cada ciclo. |
| 175 | [`090_loop_period`](../src/tabroll/cells/090_loop_period.py) | `loop_period` | loop_period: |
| 177 | [`091_layer_changes`](../src/tabroll/cells/091_layer_changes.py) | `layer_changes` | layer_changes: |
| 179 | [`092_plot_cycle_map`](../src/tabroll/cells/092_plot_cycle_map.py) | `plot_cycle_map` | **`plot_cycle_map`**: Dibuja en qué tramos de la canción aparece cada ciclo, por voz. |
| 181 | [`093_configuracion`](../src/tabroll/cells/093_configuracion.py) | `configuracion / ejecucion` | Y asi, el tabroll resultante de nuestro analisis es |
| 183 | [`094_configuracion`](../src/tabroll/cells/094_configuracion.py) | `configuracion / ejecucion` | Ahora, pasemos a visualizar los ciclos melodicos que tiene la cancion: |
