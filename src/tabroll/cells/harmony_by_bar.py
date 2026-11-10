"""**`harmony_by_bar`**: Armonía de cada compás: fundamental, calidad, grado respecto de la tónica (como en el tabroll, «+» sube un cuarto de tono), nota del bajo y confianza. La confianza multiplica tres cosas: lo segura que es la fundamental frente a las demás, cuánto coinciden entre sí las vueltas del ciclo y qué parte del compás tiene notas.
"""

import numpy as np

PC24_NAMES = ['C', 'C+', 'C#', 'C#+', 'D', 'D+', 'D#', 'D#+', 'E', 'E+', 'F', 'F+',
              'F#', 'F#+', 'G', 'G+', 'G#', 'G#+', 'A', 'A+', 'A#', 'A#+', 'B', 'B+']
DEG24_NAMES = ['1', '1+', '♭2', '♭2+', '2', '2+', '♭3', '♭3+', '3', '3+', '4', '4+',
               '♯4', '♯4+', '5', '5+', '♭6', '♭6+', '6', '6+', '♭7', '♭7+', '7', '7+']

def harmony_by_bar(raw_bass, raw_high, beat_times, lens, cycles, tonic_pc24, min_melody_beats=0.25):
    spans = bar_spans(beat_times, lens)
    spb = float(np.median(np.diff(beat_times)))
    Pb, ib = fold_bar_profiles(spans, NoteTable(raw_bass), cycles.get('Voz grave', []))
    Pm, im = fold_bar_profiles(spans, NoteTable(raw_high), cycles.get('Voz aguda', []), min_dur=min_melody_beats * spb)
    out = []
    for k, ((t0, t1), pb, pm, xb, xm) in enumerate(zip(spans, Pb, Pm, ib, im)):
        row = dict(compas=k + 1, inicio_s=round(t0, 3), fin_s=round(t1, 3),
                   ciclo_bajo=xb['ciclo'], vueltas_bajo=xb['vueltas'], ciclo_aguda=xm['ciclo'], vueltas_aguda=xm['vueltas'],
                   perfil_bajo=np.round(pb / xb['vueltas'], 4).tolist(), perfil_aguda=np.round(pm / xm['vueltas'], 4).tolist())
        ch = chord24(pb, pm)
        if ch is None:
            row.update(fundamental=None, fundamental_pc24=None, calidad=None, grado=None, bajo=None, bajo_pc24=None,
                       confianza=0.0, componentes=None)
            out.append(row)
            continue
        agree = [a for a in (xb['acuerdo'], xm['acuerdo']) if a is not None]
        acuerdo = float(np.mean(agree)) if agree else 0.6                    # sin ciclo no hay vueltas que comparar
        cover = min(1.0, (pb.sum() / xb['vueltas'] + 0.5 * pm.sum() / xm['vueltas']) / (t1 - t0))
        row.update(fundamental=PC24_NAMES[ch['fundamental']], fundamental_pc24=ch['fundamental'], calidad=ch['calidad'],
                   grado=DEG24_NAMES[(ch['fundamental'] - tonic_pc24) % 24],
                   bajo=PC24_NAMES[ch['bajo']] if ch['bajo'] is not None else None, bajo_pc24=ch['bajo'],
                   confianza=round(ch['p_fundamental'] * acuerdo * cover, 3),
                   componentes=dict(fundamental=round(ch['p_fundamental'], 3), acuerdo_vueltas=round(acuerdo, 3),
                                    cobertura=round(cover, 3), claridad_bajo=round(ch['claridad_bajo'], 3)))
        out.append(row)
    return out
