"""**`harmony_layers`**: Capas del círculo armónico calculadas con los compases confiables.
"""

import numpy as np

def harmony_layers(bars, center_pc24, min_conf=0.5):
    names = ['1', '1+', '♭2', '♭2+', '2', '2+', '♭3', '♭3+', '3', '3+', '4', '4+',
             '♯4', '♯4+', '5', '5+', '♭6', '♭6+', '6', '6+', '♭7', '♭7+', '7', '7+']
    kinds = {10: 'fuerte', 6: 'débil', 8: 'débil', 2: 'color', 4: 'color', 12: 'color', 1: 'deslizamiento'}   # neutros: intermedio
    ok = {b['compas']: b for b in bars if b.get('fundamental_pc24') is not None and b.get('confianza', 0) >= min_conf}
    mov = dict.fromkeys(['fuerte', 'débil', 'color', 'deslizamiento', 'intermedio'], 0.0)
    trans = {}
    pares = cambios = 0
    for k, b in ok.items():
        a = ok.get(k - 1)
        if a is None:
            continue
        pares += 1
        r0, r1 = (a['fundamental_pc24'] - center_pc24) % 24, (b['fundamental_pc24'] - center_pc24) % 24
        if r0 == r1:
            continue
        cambios += 1
        i = min((r1 - r0) % 24, (r0 - r1) % 24)
        mov[kinds.get(i, 'intermedio')] += 1
        trans[(names[r0], names[r1])] = trans.get((names[r0], names[r1]), 0) + 1
    calidades = {}
    for b in ok.values():
        calidades[b['calidad']] = calidades.get(b['calidad'], 0.0) + b['fin_s'] - b['inicio_s']
    tc = sum(calidades.values()) or 1.0
    return dict(compases_confiables=len(ok),
                movimientos={k: round(v / max(cambios, 1), 3) for k, v in mov.items()},
                cambios_por_compas=round(cambios / max(pares, 1), 3),
                calidades={k: round(v / tc, 3) for k, v in sorted(calidades.items(), key=lambda kv: -kv[1])},
                transiciones=[dict(de=a, a=b, veces=n) for (a, b), n in sorted(trans.items(), key=lambda kv: -kv[1])])
