"""Aplica al cuaderno los dos cambios del 9-nov-2026.

1. Melodía (celda «2) Altura»): la línea `melody_n` se atrae suavemente al registro típico de la melodía de la canción.
2. Armonía en 24-EDO, paso 1: celdas nuevas al final del cuaderno (funciones y una celda de ejecución).

Uso, desde la raíz del repo:
    python scripts/agregar_armonia.py
    make extract
    make test

Se puede correr más de una vez: si un cambio ya está, lo deja como está.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
MARKER = "## Armonía en 24-EDO (paso 1)"

OLD_MELODY = "melody_n = melody_n_baseline                     # la selección extra no mejora de forma estable"
NEW_MELODY = """registro_n = (float(np.nanmedian(melody_n_baseline)) if np.isfinite(melody_n_baseline).any()
              else float(np.median(cand[ishigh])))                         # registro típico de la melodía en esta canción
atraccion_n = 0.7 + 0.3 * np.exp(-0.5 * ((cand[ishigh] - registro_n) / 12.0) ** 2)   # atracción suave a ese registro, no a lo más agudo
melody_n = viterbi_pitch(consenso_n * atraccion_n[:, None], cand[ishigh], np.percentile(Snote, 55))"""

CELLS = [
    ("markdown", MARKER + """: fundamental por compás, con confianza

La armonía se calcula por compás con dos entradas: el bajo y el contenido de clases de altura en 24-EDO (cuartos de
tono). Cada entrada se suma sobre todas las vueltas del ciclo que contiene el compás, así que un error en una vuelta
pesa poco.

- **Notas que no cuentan.** En la voz aguda no cuentan las notas más cortas que un cuarto de pulso: suelen ser notas
  de paso o adornos, que es donde la transcripción falla más. La armonía nunca se decide con una nota suelta.
- **Confianza.** Cada compás lleva una confianza entre 0 y 1. El círculo armónico usará los compases confiables, o
  les dará más peso.
- **Independencia de la melodía.** La elección de la línea melódica puede seguir mejorándose sin tocar estas celdas."""),
    ("markdown", "**`bar_spans`**: Inicio y fin en segundos de cada compás, a partir de los pulsos reales y de la longitud de cada compás en pulsos."),
    ("code", """import numpy as np

def bar_spans(beat_times, lens):
    bt = np.asarray(beat_times, float)
    spb = float(np.median(np.diff(bt)))
    idx = np.concatenate([[0.0], np.cumsum(lens)]).astype(float)
    t = np.interp(idx, np.arange(len(bt)), bt)
    over = idx > len(bt) - 1
    t[over] = bt[-1] + (idx[over] - (len(bt) - 1)) * spb                     # el último compás termina un pulso después
    return [(float(a), float(b)) for a, b in zip(t[:-1], t[1:]) if b > a]"""),
    ("markdown", "**`NoteTable`**: Notas (inicio, fin, altura) listas para sumar cuánto tiempo suena cada una de las 24 clases de altura en cualquier tramo."),
    ("code", """import numpy as np

class NoteTable:
    def __init__(self, notes):
        a = np.array([tuple(n)[:3] for n in notes], float).reshape(-1, 3)
        self.a, self.b = a[:, 0], a[:, 1]
        self.pc = np.round(a[:, 2] * 2).astype(int) % 24                     # 0 = Do, 1 = Do+, 2 = Do#, ...
        self.d = self.b - self.a

    def profile(self, t0, t1, min_dur=0.0):
        \"\"\"Segundos que suena cada clase entre t0 y t1; las notas más cortas que min_dur no cuentan.\"\"\"
        m = (self.a < t1) & (self.b > t0) & (self.d >= min_dur)
        h = np.zeros(24)
        np.add.at(h, self.pc[m], np.minimum(self.b[m], t1) - np.maximum(self.a[m], t0))
        return h"""),
    ("markdown", "**`fold_bar_profiles`**: Suma el perfil de cada compás sobre todas las vueltas del ciclo que lo contiene, en el mismo punto del ciclo. Devuelve también cuántas vueltas sumó y cuánto se parecen entre sí (acuerdo, de 0 a 1). Un compás que no está dentro de ningún ciclo usa solo su propio perfil."),
    ("code", """import numpy as np

def fold_bar_profiles(spans, table, cycles, min_dur=0.0):
    get = lambda c, k: c[k] if isinstance(c, dict) else getattr(c, k)
    cos = lambda x, y: float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y))) if x.any() and y.any() else 0.0
    prof, info = [], []
    for t0, t1 in spans:
        mid = 0.5 * (t0 + t1)
        c = next((c for c in cycles if get(c, 'start') <= mid < get(c, 'end')), None)
        if c is None:
            prof.append(table.profile(t0, t1, min_dur))
            info.append(dict(ciclo=None, vueltas=1, acuerdo=None))
            continue
        P, cs, ce = get(c, 'period'), get(c, 'start'), get(c, 'end')
        turns = [table.profile(t0 + k * P, t1 + k * P, min_dur)
                 for k in range(-int((t0 - cs) / P) - 1, int((ce - t1) / P) + 2)
                 if t0 + k * P >= cs - 0.05 and t1 + k * P <= ce + 0.05]
        H = np.sum(turns, axis=0) if turns else table.profile(t0, t1, min_dur)
        full = [h for h in turns if h.any()]
        prof.append(H)
        info.append(dict(ciclo=get(c, 'label') or None, vueltas=max(len(turns), 1),
                         acuerdo=float(np.mean([cos(h, H) for h in full])) if len(full) >= 2 else None))
    return np.array(prof).reshape(-1, 24), info"""),
    ("markdown", "**`chord24`**: Fundamental y calidad del acorde de un compás en 24-EDO, a partir del perfil del bajo y del de la voz aguda. Compara con las calidades de Piston extendidas a 24-EDO: 5, m, n (tercera neutra), M, dism, aum, sus2 y sus4. Suma lo que cae dentro del acorde, resta lo que cae fuera y premia que el bajo esté en la fundamental. `p_fundamental` es la probabilidad de esa fundamental frente a las otras 23."),
    ("code", """import numpy as np

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
    best = S.max(axis=1)
    r0 = int(best.argmax())
    p = np.exp((best - best.max()) / tau)
    p = p / p.sum()
    return dict(fundamental=r0, calidad=list(CHORDS24)[int(S[r0].argmax())], p_fundamental=float(p[r0]),
                alternativa=int(np.argsort(-best)[1]), bajo=int(b.argmax()) if tb > 0 else None,
                claridad_bajo=float(b.max()) if tb > 0 else 0.0)"""),
    ("markdown", "**`harmony_by_bar`**: Armonía de cada compás: fundamental, calidad, grado respecto de la tónica (como en el tabroll, «+» sube un cuarto de tono), nota del bajo y confianza. La confianza multiplica tres cosas: lo segura que es la fundamental frente a las demás, cuánto coinciden entre sí las vueltas del ciclo y qué parte del compás tiene notas."),
    ("code", """import numpy as np

PC24_NAMES = ['C', 'C+', 'C#', 'C#+', 'D', 'D+', 'D#', 'D#+', 'E', 'E+', 'F', 'F+',
              'F#', 'F#+', 'G', 'G+', 'G#', 'G#+', 'A', 'A+', 'A#', 'A#+', 'B', 'B+']
DEG24_NAMES = ['1', '1+', '♭2', '♭2+', '2', '2+', '♭3', '♭3+', '3', '3+', '4', '4+',
               '♯4', '♯4+', '5', '5+', '♭6', '♭6+', '6', '6+', '♭7', '♭7+', '7', '7+']

def harmony_by_bar(raw_bass, raw_high, beat_times, lens, cycles, tonic_pc24, min_melody_beats=0.25):
    spans = bar_spans(beat_times, lens)
    spb = float(np.median(np.diff(beat_times)))
    Pb, ib = fold_bar_profiles(spans, NoteTable(raw_bass), cycles.get('Voz grave', []))
    Pm, im = fold_bar_profiles(spans, NoteTable(raw_high), cycles.get('Voz aguda', []), min_dur=min_melody_beats * spb)
    out = []
    for k, ((t0, t1), pb, pm, xb, xm) in enumerate(zip(spans, Pb, Pm, ib, im)):
        row = dict(compas=k + 1, inicio_s=round(t0, 3), fin_s=round(t1, 3),
                   ciclo_bajo=xb['ciclo'], vueltas_bajo=xb['vueltas'], ciclo_aguda=xm['ciclo'], vueltas_aguda=xm['vueltas'],
                   perfil_bajo=np.round(pb / xb['vueltas'], 4).tolist(), perfil_aguda=np.round(pm / xm['vueltas'], 4).tolist())
        ch = chord24(pb, pm)
        if ch is None:
            row.update(fundamental=None, fundamental_pc24=None, calidad=None, grado=None, bajo=None, bajo_pc24=None,
                       confianza=0.0, componentes=None)
            out.append(row)
            continue
        agree = [a for a in (xb['acuerdo'], xm['acuerdo']) if a is not None]
        acuerdo = float(np.mean(agree)) if agree else 0.6                    # sin ciclo no hay vueltas que comparar
        cover = min(1.0, (pb.sum() / xb['vueltas'] + 0.5 * pm.sum() / xm['vueltas']) / (t1 - t0))
        row.update(fundamental=PC24_NAMES[ch['fundamental']], fundamental_pc24=ch['fundamental'], calidad=ch['calidad'],
                   grado=DEG24_NAMES[(ch['fundamental'] - tonic_pc24) % 24],
                   bajo=PC24_NAMES[ch['bajo']] if ch['bajo'] is not None else None, bajo_pc24=ch['bajo'],
                   confianza=round(ch['p_fundamental'] * acuerdo * cover, 3),
                   componentes=dict(fundamental=round(ch['p_fundamental'], 3), acuerdo_vueltas=round(acuerdo, 3),
                                    cobertura=round(cover, 3), claridad_bajo=round(ch['claridad_bajo'], 3)))
        out.append(row)
    return out"""),
    ("markdown", "**`harmony_summary`**: Resumen de la canción para el círculo armónico: tiempo de cada grado como fundamental y perfil del bajo por grado, ambos ponderados por la confianza, y qué parte de la canción es confiable."),
    ("code", """import numpy as np

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
                bajo_por_grado=dict(zip(DEG24_NAMES, np.round(bass / max(bass.sum(), 1e-9), 4).tolist())))"""),
    ("markdown", "Armonía de la canción: una fila por compás (`armonia`) y el resumen para el círculo (`armonia_resumen`). `run_song.py` los guarda en `armonia.json`."),
    ("code", """tonic_pc24 = (2 * tonic_pc) % 24                                               # la tónica del cuaderno (12 clases) en la rejilla de 24
armonia = harmony_by_bar(raw_bass, raw_high, beat_times, lens, cycles, tonic_pc24)
armonia_resumen = harmony_summary(armonia, tonic_pc24)

grados = sorted(armonia_resumen['fundamentales_por_grado'].items(), key=lambda kv: -kv[1])[:5]
print(f"Armonía: {len(armonia)} compases | confiable el {armonia_resumen['tiempo_confiable']:.0f}% del tiempo | "
      "fundamentales más usadas: " + ', '.join(f'{g} {100 * v:.0f}%' for g, v in grados if v > 0))"""),
]


def _cell(kind: str, text: str) -> dict:
    source = text.splitlines(keepends=True)
    cell = {"id": uuid.uuid4().hex[:12], "cell_type": kind, "metadata": {}, "source": source}
    if kind == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]
    done = []
    melody = [c for c in cells if c["cell_type"] == "code" and OLD_MELODY in "".join(c["source"])]
    if melody:
        text = "".join(melody[0]["source"]).replace(OLD_MELODY, NEW_MELODY)
        melody[0]["source"] = text.splitlines(keepends=True)
        done.append("melodía: atracción al registro agregada en la celda «2) Altura»")
    elif any("atraccion_n" in "".join(c["source"]) for c in cells):
        done.append("melodía: el cambio ya estaba")
    else:
        done.append("melodía: NO encontré la línea `melody_n = melody_n_baseline ...`; revisa la celda «2) Altura» a mano")
    if any(MARKER in "".join(c["source"]) for c in cells if c["cell_type"] == "markdown"):
        done.append("armonía: las celdas ya estaban")
    else:
        cells.extend(_cell(kind, text) for kind, text in CELLS)
        done.append(f"armonía: {sum(1 for k, _ in CELLS if k == 'code')} celdas de código agregadas al final")
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("\n".join(done))
    print("Ahora: make extract && make test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
