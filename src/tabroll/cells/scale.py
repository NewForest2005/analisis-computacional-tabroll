"""**`Scale`**: Escala musical en cents.
"""

@dataclass
class Scale:
    steps: list[float]
    period: float = 1200.0
    names: Optional[list[str]] = None
    tonic_name: str = "C"
    tonic_octave: int = 4
    accidental_unit: float = 100.0
    colors: Optional[list[str]] = None
    tol: float = 12.0
    tuning: Optional[list[float]] = None
    degrees: Optional[list[str]] = None

    def __post_init__(self):
        assert abs(self.steps[0]) < 1e-9 and sorted(self.steps) == list(self.steps)
        assert self.steps[-1] < self.period
        if self.colors is None:
            self.colors = palette(self.n)

    @property
    def n(self) -> int:
        return len(self.steps)

    # helpers para constructor
    @classmethod
    def from_tuning(cls, tuning: Sequence[float], period: float, degrees: Sequence[int], **kw) -> "Scale":
        kw.setdefault("accidental_unit", period / len(tuning))
        return cls([tuning[i] for i in degrees], period=period, tuning=list(tuning), **kw)

    def pitch(self, degree: int, octave: int = 0, shift: float = 0.0) -> float:
        return self.steps[degree - 1] + octave * self.period + shift

    # mapa central
    def deg_cents(self, k: int) -> float:
        return (k // self.n) * self.period + self.steps[k % self.n]

    def row(self, cents: float) -> float:
        p, r = divmod(cents, self.period)
        i = bisect_right(self.steps, r + 1e-9) - 1
        lo = self.steps[i]
        hi = self.steps[i + 1] if i + 1 < self.n else self.period
        return p * self.n + i + (r - lo) / (hi - lo)

    def locate(self, cents: float) -> tuple[float, bool]:
        r = self.row(cents)
        k = round(r)
        if abs(cents - self.deg_cents(k)) <= self.tol:
            return float(k), True
        return r, False

    def colors_for(self, cents: float) -> tuple[str, str, float]:
        r, diat = self.locate(cents)
        if diat:
            c = self.colors[int(r) % self.n]
            return c, c, 0.0
        lo = math.floor(r)
        return self.colors[lo % self.n], self.colors[(lo + 1) % self.n], r - lo

    # naming
    def spell(self, cents: float) -> tuple[int, str]:
        r, diat = self.locate(cents)
        if diat:
            return int(r), ""
        lo = math.floor(r)
        d_lo, d_hi = cents - self.deg_cents(lo), cents - self.deg_cents(lo + 1)
        base, d = (lo, d_lo) if abs(d_lo) <= abs(d_hi) + 1e-6 else (lo + 1, d_hi)
        return base, accidental(int(round(d / self.accidental_unit)), self.accidental_unit)

    def degree_name(self, idx: int) -> str:
        return self.names[idx % self.n] if self.names else str(idx % self.n + 1)

    def note_name(self, cents: float) -> str:
        base, acc = self.spell(cents)
        return self.degree_name(base) + acc
