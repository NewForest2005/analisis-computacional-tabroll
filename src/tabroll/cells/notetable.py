"""**`NoteTable`**: Notas (inicio, fin, altura) listas para sumar cuánto tiempo suena cada una de las 24 clases de altura en cualquier tramo.
"""

import numpy as np

class NoteTable:
    def __init__(self, notes):
        a = np.array([tuple(n)[:3] for n in notes], float).reshape(-1, 3)
        self.a, self.b = a[:, 0], a[:, 1]
        self.pc = np.round(a[:, 2] * 2).astype(int) % 24                     # 0 = Do, 1 = Do+, 2 = Do#, ...
        self.d = self.b - self.a

    def profile(self, t0, t1, min_dur=0.0):
        """Segundos que suena cada clase entre t0 y t1; las notas más cortas que min_dur no cuentan."""
        m = (self.a < t1) & (self.b > t0) & (self.d >= min_dur)
        h = np.zeros(24)
        np.add.at(h, self.pc[m], np.minimum(self.b[m], t1) - np.maximum(self.a[m], t0))
        return h
