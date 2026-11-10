"""**`chord24`**: Fundamental y calidad del acorde de un compás en 24-EDO, a partir del perfil del bajo y del de la voz aguda. Compara con las calidades de Piston extendidas a 24-EDO: 5, m, n (tercera neutra), M, dism, aum, sus2 y sus4. Suma lo que cae dentro del acorde, resta lo que cae fuera y premia que el bajo esté en la fundamental. `p_fundamental` es la probabilidad de esa fundamental frente a las otras 23.
"""

import numpy as np

CHORDS24 = {'5': (0, 14), 'm': (0, 6, 14), 'n': (0, 7, 14), 'M': (0, 8, 14), 'dism': (0, 6, 12),
            'aum': (0, 8, 16), 'sus2': (0, 4, 14), 'sus4': (0, 10, 14)}         # pasos de cuarto de tono sobre la fundamental

def chord24(Pb, Pm, wm=0.6, lam=0.5, beta=0.5, gamma=0.02, tau=0.05):
    tb, tm = float(np.sum(Pb)), float(np.sum(Pm))
    if tb + tm <= 0:
        return None
    b = np.asarray(Pb, float) / tb if tb > 0 else np.zeros(24)
    m = np.asarray(Pm, float) / tm if tm > 0 else np.zeros(24)
    C = b + wm * m
    C = C / C.sum()
    S = np.empty((24, len(CHORDS24)))
    for j, iv in enumerate(CHORDS24.values()):
        for r in range(24):
            fit = C[[(r + i) % 24 for i in iv]].sum()
            S[r, j] = (1 + lam) * fit - lam + beta * b[r] - gamma * (len(iv) - 2)
    S = np.round(S, 9)                                                         # empates exactos iguales en cualquier máquina
    best = S.max(axis=1)
    r0 = int(best.argmax())
    p = np.exp((best - best.max()) / tau)
    p = p / p.sum()
    return dict(fundamental=r0, calidad=list(CHORDS24)[int(S[r0].argmax())], p_fundamental=float(p[r0]),
                alternativa=int(np.argsort(-best)[1]), bajo=int(np.round(b, 9).argmax()) if tb > 0 else None,
                claridad_bajo=float(b.max()) if tb > 0 else 0.0)
