"""Celda 128 del notebook original. Descripcion asociada: 5) Evidencia por pulso (qué clases de altura suenan): bajo y melodía..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def _norm(H):
    s = H.sum(axis=1)
    return H / (np.percentile(s[s > 0], 90) if (s > 0).any() else 1.0)

Hb = _norm(beat_histograms(bass - off, np.clip(Sbass / thr_b, 0, 3), pos, sr, HOP_P, nb))
Hm = _norm(beat_histograms(midi - off, np.clip(Smax / thr, 0, 3), pos, sr, HOP_P, nb))
