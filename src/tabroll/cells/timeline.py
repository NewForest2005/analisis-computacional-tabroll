"""**`Timeline`**: Convierte pulsos en píxeles, con un pequeño espacio entre compases.
"""

class Timeline:
    def __init__(self, measures: Sequence[Measure], ppb: float, gap: float):

        self.m, self.ppb = list(measures), ppb
        self.starts = [m.start for m in self.m]
        self.x0, x = [], 0.0

        for m in self.m:
            self.x0.append(x)
            x += m.beats * ppb + gap

    def x(self, beat: float, side: str = "start") -> float:
        eps = 1e-9

        if side == "start":
            i = bisect_right(self.starts, beat + eps) - 1

        else:
            i = bisect_left(self.starts, beat - eps) - 1

        i = min(max(i, 0), len(self.m) - 1)

        return self.x0[i] + (beat - self.m[i].start) * self.ppb
