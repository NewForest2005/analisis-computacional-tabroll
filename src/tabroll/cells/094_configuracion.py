"""Celda 183 del notebook original. Descripcion asociada: Ahora, pasemos a visualizar los ciclos melodicos que tiene la cancion:.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

beat = (beat_times[-1] - beat_times[0]) / (len(beat_times) - 1)

lines_v = {'Voz grave': bass, 'Voz aguda': melody}
cycles = {voice: find_cycles(line, off, sr, HOP_P, min_turns=2 if line is bass else 3) for voice, line in lines_v.items()}
main = 'Voz grave' if cycles['Voz grave'] else 'Voz aguda'

sub = BEAT_DIV if BEAT_DIV > 1 else cycle_subdivision(lines_v[main], off, cycles[main], sr, HOP_P, beat)
bar = max(set(lens), key=lens.count)
bar_of = lambda c: cycle_bar(c, lens, beat_times, bar)

for voice, line in lines_v.items():
    prev, others = None, [] if voice == main else cycles[main]

    for c in cycles[voice]:
        fold_cycle(Sb if line is bass else Sh, cand, line, off, c, sr, HOP_P, beat, sub, 'grave' if line is bass else 'aguda', cycle_anchor(c, prev, others), stereo=Sh is not S, weak=0.0 if Sh is not S else 0.8)
        prev = c

    cycles[voice] = [c for c in cycles[voice] if has_motion(c) and (line is bass or stem is None or stem_active(stem, c, sr) >= 0.2)]
    name_cycles(cycles[voice])
    print(voice)

    for c in cycles[voice]:
        print(f'  {c.label}  {_mmss(c.start)} – {_mmss(c.end)}  |  {c.period:.3f} s  |  {c.slots / sub / bar_of(c):g} compases  |  '
              f'{(c.end - c.start) / c.period:.0f} vueltas  |  se repite {c.score:.0%}' + ('  |  dobla al bajo' if c.doubled >= 0.8 else ''))

layers = None

if stem is not None:                                                               # con la pista guitar se ven las capas del looper
    loop = loop_period(cycles)
    layer_events, level = layer_changes(stem, loop, sr, HOP_P, NFFT_P)
    layers = (layer_events, level, HOP_P / sr)

    print(f'Capas de guitarra (loop de {loop:.3f} s): ' + '  '.join(f'{k} {_mmss(t)}' for t, k in layer_events))

plot_cycle_map(cycles, len(y) / sr, layers=layers)

for voice, group in cycles.items():
    render_cycles([c for c in group if c.doubled < 0.8 or Sh is not S], view_scale, tonic_midi, bar_of, filename=f'ciclo_{voice.split()[1]}')
