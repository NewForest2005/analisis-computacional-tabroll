"""Evaluación de la voz aguda y la voz grave del tabroll contra las partituras corregidas.

Solo sirve para medir: el cuaderno no usa nada de este módulo ni de las partituras.

Medidas (nota a nota; acierto = ataque a ±75 ms y misma altura a ±25 cents; «sin octava» = misma clase de altura):
- principal: la melodía principal de cada sección, es decir, la guitarra que el autor eligió por criterio musical
  (MELODIA_PRINCIPAL). Donde esa guitarra calla cuenta la nota más aguda de las demás. Las secciones sin asignar usan
  la nota más aguda.
- mas_aguda: la nota más aguda de todas las guitarras en cada instante.
- bajo: la nota más grave de los bajos.
Los unísonos entre instrumentos cuentan una vez (el cuaderno da una sola nota).

Alineación: el camino DTW guardado en references/alineaciones (croma del audio oficial frente a la partitura) se
ajusta a una recta por sección, porque el looper mantiene el tempo dentro de cada sección. Si la sección entera no es
compatible con un tempo constante, se parte en ventanas de 4 s y solo se miden las ventanas que sí lo son. Esta
decisión usa solo la alineación, nunca la salida del cuaderno.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
if not (ROOT / "references" / "alineaciones").is_dir():          # instalación no editable: buscar desde la carpeta actual
    ROOT = next((p for p in [Path.cwd(), *Path.cwd().parents] if (p / "references" / "alineaciones").is_dir()), ROOT)
REFS = ROOT / "references"
TOL = 0.075                                       # tolerancia de ataque (s)
SLOPE_TOL, MAD_MAX, DEL_MAX, WIN = 0.05, 0.06, 0.15, 4.0

CANCIONES = {"mata_zyklek": "mata zyklek", "sarniezz": "sarniezz", "fabienk": "fabienk"}

# Guitarra que lleva la melodía en cada sección (prefijo del nombre de la sección), elegida por el autor el 9-nov-2026.
MELODIA_PRINCIPAL = {
    "mata_zyklek": [("Entra el riff en la guitarra 3", "G3"), ("Riff en guitarra 4", "G4"), ("Melodía 1", "G3"),
                    ("Melodía 2", "G3"), ("Corte", "G3"), ("Riff sin melodía", "G4"), ("Figura rápida", "G1"),
                    ("Guitarra 1 sola", "G1"), ("Final", "G2")],
    "sarniezz": [("Riff en bajo y guitarra 2", "G2"), ("Riff + acorde", "G2"), ("Frase 1", "G1"),
                 ("Todo corrido 3 corcheas", "G1"), ("Patrón del bajo en guitarra 1", "G1")],
    "fabienk": [("Melodía «Fabien»", "G1"), ("Guitarra 1 dobla al bajo", "G1"), ("La guitarra 2 toca la línea del bajo", "G2"),
                ("Entra la guitarra 2", "G1"), ("Corrido otra vez", "G2"), ("Las dos guitarras", "G2"),
                ("Segunda voz sobre la línea", "G2")],
}


def song_key(name: str) -> str | None:
    """Clave de la canción a partir del nombre del audio o de la carpeta de la corrida."""
    low = name.lower().replace("_", " ")
    return next((k for k, v in CANCIONES.items() if v in low), None)


def _module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def reference(song: str) -> dict:
    """Notas (inicio, duración, altura sonora, parte) y secciones (t0, t1, nombre, medible) en segundos de partitura."""
    if song == "mata_zyklek":
        R = _module(REFS / "mata_zyklek_loops.py")
        q = 60 / 186
        notes = [(t * q, d * q, p - 12, part) for b, t, d, p, part, pat in R.notes(R.GUITARS + R.BASSES)]
        secs = [((a - 1) * 5 * q, b * 5 * q, nm, True) for a, b, nm in R.SECTIONS]
    elif song == "sarniezz":
        R = _module(REFS / "sarniezz_partitura.py")
        tl = R.timeline()
        starts = np.cumsum([0.0] + [n * e for t0, n, e, known, name in tl])
        notes = [(starts[k] + (t - tl[k][0]) * tl[k][2], d * tl[k][2], p + R.TRANSPOSE[part], part)
                 for k, t, d, p, part in R.notes(R.GUITARS + R.BASSES)]
        secs = [(starts[k], starts[k] + n * e, name, known) for k, (t0, n, e, known, name) in enumerate(tl)]
    elif song == "fabienk":
        R = _module(REFS / "fabienk_partitura.py")
        six = R.SIX
        notes = [(t * six, d * six, p + R.TRANSPOSE[part], part) for k, t, d, p, part in R.notes(R.GUITARS + R.BASSES)]
        secs = [(t * six, (t + n) * six, name, known) for t, n, known, name in R.timeline()]
    else:
        raise ValueError(f"Canción sin partitura de evaluación: {song}")
    return dict(notes=notes, sections=secs, guitars=tuple(R.GUITARS), basses=tuple(R.BASSES))


class Alignment:
    """Mapa partitura → audio: recta por sección, o por ventanas de 4 s donde la sección entera no encaja."""

    def __init__(self, song: str, ref: dict | None = None):
        J = json.loads((REFS / "alineaciones" / f"{song}.json").read_text(encoding="utf-8"))
        self.dt = float(J["dt"])
        s, a = np.asarray(J["partitura_s"], float), np.asarray(J["audio_s"], float)
        self.deleted = np.array([c == "1" for c in J["borrado"]], bool)
        self._s, self._a = s, a
        base = ref or reference(song)
        pieces = []
        for t0, t1, nm, kn in base["sections"]:
            c, ok = self._fit(t0, t1)
            if ok:
                pieces.append((t0, t1, nm, kn, c))
                continue
            edges = np.linspace(t0, t1, max(1, int(round((t1 - t0) / WIN))) + 1)
            for w0, w1 in zip(edges[:-1], edges[1:]):
                cw, okw = self._fit(w0, w1, margin=0.5)
                pieces.append((w0, w1, nm, kn and okw, cw if okw else None))
        self._pieces = pieces
        self.ref = dict(base, sections=[(t0, t1, nm, kn) for t0, t1, nm, kn, c in pieces])
        total = sum(t1 - t0 for t0, t1, nm, kn in base["sections"] if kn)
        self.kept = sum(t1 - t0 for t0, t1, nm, kn, c in pieces if kn) / max(total, 1e-9)

    def _fit(self, t0, t1, margin=0.0):
        s, a = self._s, self._a
        m = (s >= t0 - margin) & (s < t1 + margin)
        if m.sum() < 12:
            return None, False
        c = np.polyfit(s[m], a[m], 1)
        for _ in range(3):                                   # quita los puntos sueltos del camino del DTW
            r = a[m] - np.polyval(c, s[m])
            keep = np.abs(r) < 4 * (np.median(np.abs(r)) + 1e-9) + 0.03
            if keep.sum() < 8:
                break
            c = np.polyfit(s[m][keep], a[m][keep], 1)
        mad = float(np.median(np.abs(a[m] - np.polyval(c, s[m]))))
        i0, i1 = int(t0 / self.dt), max(int(t1 / self.dt), int(t0 / self.dt) + 1)
        dl = float(np.mean(self.deleted[i0:i1])) if i0 < len(self.deleted) else 1.0
        return c, abs(c[0] - 1) <= SLOPE_TOL and mad <= MAD_MAX and dl <= DEL_MAX

    def t(self, ts):
        ts = np.asarray(ts, float)
        out = np.interp(ts, self._s, self._a).reshape(-1)
        flat = ts.reshape(-1)
        for t0, t1, nm, kn, c in self._pieces:
            if c is not None:
                m = (flat >= t0) & (flat < t1 + 1e-9)
                out[m] = np.polyval(c, flat[m])
        return out.reshape(ts.shape) if ts.ndim else float(out[0])


def exact(a, b):
    return abs(a - b) < 0.26


def pclass(a, b):
    return abs((a - b + 6) % 12 - 6) < 0.26


def mapped(al: Alignment, parts, known_only=True) -> list[dict]:
    secs = al.ref["sections"]
    out = []
    for t, d, p, part in al.ref["notes"]:
        if part not in parts:
            continue
        k = next((i for i, (t0, t1, nm, kn) in enumerate(secs) if t0 <= t < t1), None)
        if k is None or (known_only and not secs[k][3]):
            continue
        if al.deleted[min(int(t / al.dt), len(al.deleted) - 1)]:
            continue
        out.append(dict(t=float(al.t(t)), te=float(al.t(t + d)), p=p, part=part, sec=k))
    return sorted(out, key=lambda n: n["t"])


def top_line(ns: list[dict], low=False) -> list[dict]:
    """Nota más aguda (o más grave) en cada ataque; los unísonos entre instrumentos cuentan una vez."""
    s = -1 if low else 1
    ts = np.array([n["t"] for n in ns])
    te = np.array([n["te"] for n in ns])
    ps = s * np.array([n["p"] for n in ns])
    out = []
    for n in ns:
        on = (ts <= n["t"] + 0.02) & (te > n["t"] + 0.02)
        if not on.any() or ps[on].max() <= s * n["p"] + 1e-9:
            if out and any(abs(m["t"] - n["t"]) < 0.03 and abs(m["p"] - n["p"]) < 0.1 for m in out[-4:]):
                continue
            out.append(n)
    return out


def match(ref, det, ok):
    det_t = np.array([d[0] for d in det])
    used = np.zeros(len(det), bool)
    hit = []
    for k, n in enumerate(ref):
        lo, hi = np.searchsorted(det_t, n["t"] - TOL), np.searchsorted(det_t, n["t"] + TOL)
        c = [j for j in range(lo, hi) if not used[j] and ok(det[j][2], n["p"])]
        if c:
            j = min(c, key=lambda j: abs(det_t[j] - n["t"]))
            used[j] = True
            hit.append((k, j))
    return hit


def f_measure(h, nr, nd) -> float:
    P, R = len(h) / max(nd, 1), len(h) / max(nr, 1)
    return 200 * P * R / max(P + R, 1e-9)


def calib(ref, det) -> float:
    """Desfase constante entre la partitura alineada y las notas detectadas (mediana, solo aciertos de altura)."""
    dt_ = np.array([d[0] for d in det])
    diffs = []
    for n in ref:
        j = np.searchsorted(dt_, n["t"])
        for jj in (j - 1, j):
            if 0 <= jj < len(dt_) and abs(dt_[jj] - n["t"]) < 0.12 and exact(det[jj][2], n["p"]):
                diffs.append(dt_[jj] - n["t"])
    return float(np.median(diffs)) if diffs else 0.0


def in_known(det, al: Alignment):
    spans = [(al.t(t0), al.t(t1)) for t0, t1, nm, kn in al.ref["sections"] if kn]
    return [d for d in det if any(a - 0.04 <= d[0] < b - 0.04 for a, b in spans)]


def lead_line(al: Alignment, song: str) -> list[dict]:
    gu = mapped(al, al.ref["guitars"])
    out = []
    for k, (t0, t1, nm, kn) in enumerate(al.ref["sections"]):
        ns = [n for n in gu if n["sec"] == k]
        if not kn or not ns:
            continue
        part = next((p for pre, p in MELODIA_PRINCIPAL.get(song, []) if nm.startswith(pre)), None)
        if part is None:
            out += top_line(ns)
            continue
        lead = top_line([n for n in ns if n["part"] == part])
        rest = top_line([n for n in ns if n["part"] != part])
        out += lead + [n for n in rest if not any(l["t"] - 0.03 <= n["t"] < l["te"] for l in lead)]
    return sorted(out, key=lambda n: n["t"])


def _notes(rows):
    """Acepta dicts de line_diagnostics.json ({start_s, end_s, midi}) o tuplas (inicio, fin, altura)."""
    out = [(float(r["start_s"]), float(r["end_s"]), float(r["midi"])) if isinstance(r, dict) else tuple(map(float, r[:3]))
           for r in rows]
    return sorted(out)


def evaluate(song: str, raw_high, raw_bass) -> dict:
    al = Alignment(song)
    gu, ba = mapped(al, al.ref["guitars"]), mapped(al, al.ref["basses"])
    top, low, lead = top_line(gu), top_line(ba, low=True), lead_line(al, song)
    hi, lo = _notes(raw_high), _notes(raw_bass)
    sh, sb = calib(top, hi), calib(low, lo)
    hi = in_known([(a - sh, b - sh, p) for a, b, p in hi], al)
    lo = in_known([(a - sb, b - sb, p) for a, b, p in lo], al)
    r = dict(cancion=song,
             principal=f_measure(match(lead, hi, exact), len(lead), len(hi)),
             principal_sin_octava=f_measure(match(lead, hi, pclass), len(lead), len(hi)),
             mas_aguda=f_measure(match(top, hi, exact), len(top), len(hi)),
             mas_aguda_sin_octava=f_measure(match(top, hi, pclass), len(top), len(hi)),
             bajo=f_measure(match(low, lo, exact), len(low), len(lo)),
             bajo_sin_octava=f_measure(match(low, lo, pclass), len(low), len(lo)),
             notas_principal=len(lead), notas_mas_aguda=len(top), notas_bajo=len(low), notas_detectadas=len(hi),
             tiempo_medible=100 * al.kept, desfase_s=sh)
    agg = {}
    for k, (t0, t1, nm, kn) in enumerate(al.ref["sections"]):
        if not kn:
            continue
        a0, a1 = al.t(t0), al.t(t1)
        A = agg.setdefault(nm, [[], [], [], [], []])
        A[0] += [n for n in lead if n["sec"] == k]
        A[1] += [n for n in top if n["sec"] == k]
        A[2] += [x for x in hi if a0 - 0.04 <= x[0] < a1 - 0.04]
        A[3] += [n for n in low if n["sec"] == k]
        A[4] += [x for x in lo if a0 - 0.04 <= x[0] < a1 - 0.04]
    r["secciones"] = [dict(seccion=nm, notas=len(L),
                           principal=round(f_measure(match(L, D, exact), len(L), len(D)), 1) if L else None,
                           mas_aguda=round(f_measure(match(T, D, exact), len(T), len(D)), 1) if T else None,
                           bajo=round(f_measure(match(B, E, exact), len(B), len(E)), 1) if B else None)
                      for nm, (L, T, D, B, E) in agg.items()]
    return r


def evaluate_run(run_dir: Path, song: str | None = None, write=True) -> dict | None:
    """Evalúa una carpeta de corrida (con line_diagnostics.json) y guarda evaluacion_melodia.json y .csv."""
    run_dir = Path(run_dir)
    song = song or song_key(run_dir.name)
    diag = run_dir / "line_diagnostics.json"
    if song is None or not diag.exists():
        return None
    J = json.loads(diag.read_text(encoding="utf-8"))
    r = evaluate(song, J["raw_high"], J["raw_bass"])
    if write:
        (run_dir / "evaluacion_melodia.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        with open(run_dir / "evaluacion_melodia_por_seccion.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["seccion", "notas", "principal", "mas_aguda", "bajo"])
            w.writeheader()
            w.writerows(r["secciones"])
    return r
