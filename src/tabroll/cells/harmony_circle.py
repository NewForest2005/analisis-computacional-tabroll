"""**`harmony_circle`**: Calcula las capas del círculo armónico a partir de la armonía por compás y del centro. Todo queda normalizado: cada perfil suma 1, y las transiciones también.
"""

import numpy as np

def harmony_circle(bars, center_pc24, min_conf=0.5):
    names = ['1', '1+', '♭2', '♭2+', '2', '2+', '♭3', '♭3+', '3', '3+', '4', '4+',
             '♯4', '♯4+', '5', '5+', '♭6', '♭6+', '6', '6+', '♭7', '♭7+', '7', '7+']
    kinds = {10: 'fuerte', 6: 'débil', 8: 'débil', 2: 'color', 4: 'color', 12: 'color', 1: 'deslizamiento'}   # neutros: intermedio
    rel = lambda v: np.roll(np.asarray(v, float), -center_pc24)
    norm = lambda v: (v / v.sum()).round(4).tolist() if v.sum() > 0 else [0.0] * 24
    dur = lambda b: b['fin_s'] - b['inicio_s']
    ok = [b for b in bars if b.get('fundamental_pc24') is not None and b.get('confianza', 0) >= min_conf]
    bajo, aguda, fund = np.zeros(24), np.zeros(24), np.zeros(24)
    for b in bars:
        bajo += rel(b['perfil_bajo']) * b.get('confianza', 0)
        aguda += rel(b['perfil_aguda']) * b.get('confianza', 0)
    grupos = {}
    for b in ok:
        r = (b['fundamental_pc24'] - center_pc24) % 24
        fund[r] += dur(b) * b['confianza']
        grupos.setdefault(b.get('ciclo_bajo') or f"compás {b['compas']}", np.zeros(24))[r] += dur(b)
    por_ciclo = sum((g / g.sum() for g in grupos.values()), np.zeros(24))
    trans = np.zeros((24, 24))
    mov = dict.fromkeys(['fuerte', 'débil', 'color', 'deslizamiento', 'intermedio'], 0.0)
    by = {b['compas']: b for b in ok}
    pares = cambios = 0
    for k, b in by.items():
        a = by.get(k - 1)
        if a is None:
            continue
        pares += 1
        r0, r1 = (a['fundamental_pc24'] - center_pc24) % 24, (b['fundamental_pc24'] - center_pc24) % 24
        if r0 != r1:
            cambios += 1
            trans[r0, r1] += 1
            mov[kinds.get(min((r1 - r0) % 24, (r0 - r1) % 24), 'intermedio')] += 1
    cal = {}
    for b in ok:
        cal[b['calidad']] = cal.get(b['calidad'], 0.0) + dur(b)
    total = sum(dur(b) for b in bars) or 1.0
    return dict(formato='tabroll-circulo-24edo-v1', centro_pc24=int(center_pc24), posiciones=names,
                perfil_bajo=norm(bajo), perfil_aguda=norm(aguda), fundamentales=norm(fund), fundamentales_por_ciclo=norm(por_ciclo),
                transiciones=(trans / max(trans.sum(), 1)).round(4).tolist(),
                movimientos={k: round(v / max(cambios, 1), 3) for k, v in mov.items()},
                calidades={k: round(v / (sum(cal.values()) or 1), 3) for k, v in sorted(cal.items(), key=lambda kv: -kv[1])},
                cambios_por_compas=round(cambios / max(pares, 1), 3), cambios=cambios, ciclos_distintos=len(grupos),
                tiempo_confiable=round(100 * sum(dur(b) for b in ok) / total, 1))
