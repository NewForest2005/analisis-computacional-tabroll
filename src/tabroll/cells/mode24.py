"""**`mode24`**: Modo descrito por los grados 2, 3, 6 y 7, cada uno en su versión menor, neutra o mayor. Por ejemplo, «♭2+, ♭3, 6, ♭7». En 24-EDO no se fuerza un nombre de 12 tonos. Usa los perfiles de los compases confiables, con el bajo a peso 1 y la voz aguda a 0.6.
"""

import numpy as np

def mode24(bars, center_pc24, min_conf=0.5, wm=0.6):
    names = ['1', '1+', '♭2', '♭2+', '2', '2+', '♭3', '♭3+', '3', '3+', '4', '4+',
             '♯4', '♯4+', '5', '5+', '♭6', '♭6+', '6', '6+', '♭7', '♭7+', '7', '7+']
    use = [b for b in bars if b.get('confianza', 0) >= min_conf] or bars
    prof = sum((np.asarray(b['perfil_bajo'], float) + wm * np.asarray(b['perfil_aguda'], float) for b in use), np.zeros(24))
    rel = np.roll(prof, -center_pc24)
    grados = {}
    for grado, opciones in (('2', (2, 3, 4)), ('3', (6, 7, 8)), ('6', (16, 17, 18)), ('7', (20, 21, 22))):
        v = rel[list(opciones)]
        grados[grado] = names[opciones[int(v.argmax())]] if v.max() > 0 else None
    return dict(grados=grados, nombre=', '.join(g for g in grados.values() if g))
