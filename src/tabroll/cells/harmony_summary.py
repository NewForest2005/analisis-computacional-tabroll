"""**`harmony_summary`**: Resumen de la canción para el círculo armónico: tiempo de cada grado como fundamental y perfil del bajo por grado, ambos ponderados por la confianza, y qué parte de la canción es confiable.
"""

import numpy as np

def harmony_summary(bars, tonic_pc24, min_conf=0.5):
    dur = np.array([b['fin_s'] - b['inicio_s'] for b in bars])
    conf = np.array([b['confianza'] for b in bars])
    roots, bass = np.zeros(24), np.zeros(24)
    for b, d, c in zip(bars, dur, conf):
        if b['fundamental_pc24'] is not None:
            roots[(b['fundamental_pc24'] - tonic_pc24) % 24] += d * c
        bass += np.roll(np.asarray(b['perfil_bajo'], float), -tonic_pc24) * c
    return dict(tonica_pc24=int(tonic_pc24), compases=len(bars), umbral_confianza=min_conf,
                tiempo_confiable=round(100 * dur[conf >= min_conf].sum() / max(dur.sum(), 1e-9), 1),
                fundamentales_por_grado=dict(zip(DEG24_NAMES, np.round(roots / max(roots.sum(), 1e-9), 4).tolist())),
                bajo_por_grado=dict(zip(DEG24_NAMES, np.round(bass / max(bass.sum(), 1e-9), 4).tolist())))
