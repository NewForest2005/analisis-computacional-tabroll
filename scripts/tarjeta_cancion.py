"""Tarjeta resumen de una corrida (o de un tramo), al estilo de «Song Stats» de Hooktheory, adaptada a 24-EDO.

Uso:
    python scripts/tarjeta_cancion.py outputs/<corrida>
    python scripts/tarjeta_cancion.py outputs/<corrida> --desde 177 --hasta 205 --seccion "Riff de 2:57" \\
        --hooktheory "CC=50,MC=81,CMT=11,CPN=71"

Lee armonia.json y line_diagnostics.json (y, si están, evaluacion_melodia.json y evaluacion_armonia.json). Escribe
tarjeta[_<sección>].json y tarjeta[_<sección>].png en la carpeta de la corrida. No corre el cuaderno.

Las métricas son valores CRUDOS de 0 a 100 (porcentaje del tiempo), no percentiles: no se comparan directamente con los
números de Hooktheory, que son percentiles contra su base. Con --hooktheory se muestran al lado, como contexto.
- Complejidad de acordes: acordes que no son M ni m (1 punto), grado fuera del modo (1) e inversión (0.5), sobre 2.5,
  ponderado por duración y confianza.
- Complejidad melódica: tiempo de la melodía en notas fuera del modo. Todavía no incluye la síncopa.
- Tensión acorde-melodía: tiempo de la melodía fuera del acorde del compás (a un cuarto de tono de una nota del acorde
  cuenta la mitad). El acorde del cuaderno ya usa la voz aguda, así que este valor sale bajo.
- Si en el tramo casi no hay voz aguda (menos del 10 % del tiempo), la melodía se toma del bajo y la tarjeta lo dice.
- Novedad de la progresión: sorpresa media, en bits, de los cambios de fundamental frente a los 9 álbumes de pop de
  references/corpus/albumes_transiciones.csv (al lado va la del propio pop, como punto de comparación). Cada cambio
  distinto cuenta una vez. Si falta ese archivo, sale «sin corpus».
- Cuartos de tono: tiempo de la melodía en cuartos de tono, y compases con fundamental en cuarto de tono o tercera neutra.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

NOMBRES = ["Do", "Do#", "Re", "Re#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]
CHORDS24 = {"5": (0, 14), "m": (0, 6, 14), "n": (0, 7, 14), "M": (0, 8, 14), "dism": (0, 6, 12),
            "aum": (0, 8, 16), "sus2": (0, 4, 14), "sus4": (0, 10, 14)}
PASOS = {"1": 0, "2": 4, "3": 8, "4": 10, "5": 14, "6": 18, "7": 22}
MODOS = {("2", "3", "6", "7"): "jónico (mayor)", ("2", "♭3", "6", "♭7"): "dórico", ("♭2", "♭3", "♭6", "♭7"): "frigio",
         ("2", "3", "6", "♭7"): "mixolidio", ("2", "♭3", "♭6", "♭7"): "eólico (menor)", ("♭2", "3", "♭6", "♭7"): "frigio dominante",
         ("2", "♭3", "♭6", "7"): "menor armónico", ("2", "♭3", "6", "7"): "menor melódico"}


ROMANOS = {"I": 0, "II": 2, "III": 4, "IV": 5, "V": 7, "VI": 9, "VII": 11}
CORPUS = Path(__file__).resolve().parent.parent / "references" / "corpus" / "albumes_transiciones.csv"


def _raiz12(acorde: str, menor: bool) -> int | None:
    """Fundamental (0-11 sobre la tónica) de un cifrado romano del corpus; «V/vi» es el V del vi."""
    if "/" in acorde:
        a, b = acorde.split("/", 1)
        ra, rb = _raiz12(a, False), _raiz12(b, menor)
        return None if ra is None or rb is None else (ra + rb) % 12
    m = re.match(r"([♭♯]*)([ivIV]+)", acorde)
    if not m or m.group(2).upper() not in ROMANOS:
        return None
    r = ROMANOS[m.group(2).upper()] + sum(-1 if c == "♭" else 1 for c in m.group(1))
    if menor and not m.group(1) and m.group(2).upper() in ("III", "VI", "VII"):      # en menor son los grados rebajados
        r -= 1
    return r % 12


def modelo_pop():
    """P(fundamental siguiente | fundamental) en los 9 álbumes de pop del corpus, con suavizado; None si no está el archivo."""
    if not CORPUS.exists():
        return None
    import csv
    n = [[1.0] * 12 for _ in range(12)]                                 # suavizado: una cuenta por casilla
    pares = []
    with open(CORPUS, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            modo, _, tr = r["transicion"].partition(":")
            a, _, b = tr.partition("→")
            ra, rb = _raiz12(a, modo == "m"), _raiz12(b, modo == "m")
            if ra is None or rb is None or ra == rb:
                continue
            n[ra][rb] += float(r["total"])
            pares.append((ra, rb, float(r["total"])))
    import math
    P = [[n[a][b] / (sum(n[a]) - n[a][a]) for b in range(12)] for a in range(12)]
    base = sum(w * -math.log2(P[a][b]) for a, b, w in pares) / sum(w for _, _, w in pares)
    return P, base


def novedad(ok: list[dict], tonica: int):
    """Sorpresa media (bits) de los cambios de fundamental frente al pop. Cada cambio distinto cuenta una vez, para que
    las vueltas del looper no inflen la cuenta. Una fundamental en cuarto de tono va a la de 12 más cercana y suma 1 bit."""
    import math
    M = modelo_pop()
    if M is None:
        return None, None, 0
    P, base = M
    cambios = set()
    for x, y in zip(ok, ok[1:]):
        if abs(y["inicio_s"] - x["fin_s"]) < 0.05 and x["fundamental_pc24"] != y["fundamental_pc24"]:
            cambios.add(((x["fundamental_pc24"] - tonica) % 24, (y["fundamental_pc24"] - tonica) % 24))
    bits = []
    for a, b in cambios:
        ra, rb = (a // 2) % 12, (b // 2) % 12
        extra = float(a % 2 or b % 2)
        bits.append((-math.log2(P[ra][rb]) if ra != rb else 0.0) + extra)
    return (round(sum(bits) / len(bits), 2) if bits else None), round(base, 2), len(cambios)


def pasos_grado(g: str | None) -> int | None:
    """Cuartos de tono sobre el centro de un grado escrito como «♭3», «7+» o «♯4»."""
    m = re.fullmatch(r"([♭b♯#]*)([1-7])([+d-]?)", (g or "").strip())
    if not m:
        return None
    alt = sum(-2 if c in "♭b" else 2 for c in m.group(1))
    return (PASOS[m.group(2)] + alt + {"+": 1, "d": -1, "-": -1, "": 0}[m.group(3)]) % 24


def nombre_nota(midi: float) -> str:
    q = round(midi * 2)
    return f"{NOMBRES[(q // 2) % 12]}{'+' if q % 2 else ''}{q // 2 // 12 - 1}"


def tarjeta(run: Path, desde: float | None = None, hasta: float | None = None, min_conf: float = 0.5) -> dict:
    H = json.loads((run / "armonia.json").read_text(encoding="utf-8"))
    J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
    res = H.get("resumen") or {}
    t0 = desde if desde is not None else 0.0
    t1 = hasta if hasta is not None else max(b["fin_s"] for b in H["compases"])
    bars = [b for b in H["compases"] if b["fin_s"] > t0 and b["inicio_s"] < t1]
    recorte = lambda linea: [(max(n["start_s"], t0), min(n["end_s"], t1), n["midi"]) for n in linea if n["end_s"] > t0 and n["start_s"] < t1]
    notas, voz = recorte(J["raw_high"]), "voz aguda"
    if sum(b - a for a, b, m in notas) < 0.1 * (t1 - t0) and J.get("raw_bass"):      # sin guitarra: la melodía la lleva el bajo
        notas, voz = recorte(J["raw_bass"]), "bajo"
    dur = lambda b: min(b["fin_s"], t1) - max(b["inicio_s"], t0)
    ok = [b for b in bars if b.get("fundamental_pc24") is not None and (b.get("confianza") or 0) >= min_conf]
    tonica = H.get("tonica_pc24")

    # centro y modo
    grados = (res.get("modo") or {}).get("grados") or {}
    clave = tuple(grados.get(k) for k in ("2", "3", "6", "7"))
    modo = MODOS.get(clave) or (res.get("modo") or {}).get("nombre") or "sin modo claro"
    en_modo = {0, 10, 14} | {p for p in (pasos_grado(g) for g in grados.values()) if p is not None}

    # compás: pulsos por compás según el tempo del cuaderno
    bpm = J.get("tempo_bpm")
    pulsos = Counter(round((b["fin_s"] - b["inicio_s"]) * bpm / 60) for b in bars) if bpm else Counter()
    total = sum(pulsos.values()) or 1
    compas = ", ".join(f"{k} pulsos ({100 * v / total:.0f} %)" for k, v in pulsos.most_common(3))

    # ámbito de la melodía (del 2 % al 98 % del tiempo, para no contar notas sueltas)
    orden = sorted((m, b - a) for a, b, m in notas)
    tm = sum(d for _, d in orden) or 1.0

    def cuantil(q):
        acc = 0.0
        for m, d in orden:
            acc += d
            if acc >= q * tm:
                return m
        return orden[-1][0]

    ambito = f"{nombre_nota(cuantil(0.02))} – {nombre_nota(cuantil(0.98))}" if orden else "—"

    # acorde más usado (por tiempo, compases confiables)
    uso = Counter()
    for b in ok:
        uso[b.get("cifrado") or b["fundamental"]] += dur(b)
    t_ok = sum(dur(b) for b in ok) or 1.0
    mas_usado = uso.most_common(1)[0] if uso else ("—", 0.0)

    # complejidad de acordes
    num = den = 0.0
    for b in ok:
        w = dur(b) * b["confianza"]
        p = pasos_grado(b.get("grado"))
        s = (b.get("calidad") not in ("M", "m")) + (p is None or p not in en_modo) + 0.5 * (b.get("inversion") not in (None, "fundamental"))
        num += w * s / 2.5
        den += w
    cc = 100 * num / den if den else None

    # complejidad melódica y cuartos de tono de la melodía
    fuera = micro = 0.0
    for a, b_, m in notas:
        pc = (round(m * 2) - (tonica or 0)) % 24
        fuera += (b_ - a) * (pc not in en_modo)
        micro += (b_ - a) * (round(m * 2) % 2)
    mc = 100 * fuera / tm if notas and tonica is not None else None

    # tensión acorde-melodía
    num = den = 0.0
    for b in ok:
        if b.get("calidad") not in CHORDS24:
            continue
        acorde = {(b["fundamental_pc24"] + k) % 24 for k in CHORDS24[b["calidad"]]}
        for a, b_, m in notas:
            d = min(b_, b["fin_s"]) - max(a, b["inicio_s"])
            if d <= 0:
                continue
            pc = round(m * 2) % 24
            num += d * (0.0 if pc in acorde else 0.5 if ((pc + 1) % 24 in acorde or (pc - 1) % 24 in acorde) else 1.0)
            den += d
    cmt = 100 * num / den if den else None

    cpn, cpn_pop, n_cambios = novedad(ok, tonica) if tonica is not None else (None, None, 0)
    acordes_micro = sum(dur(b) for b in ok if b["fundamental_pc24"] % 2 or b.get("calidad") == "n")
    r = dict(corrida=run.name, desde_s=round(t0, 2), hasta_s=round(t1, 2), centro=res.get("centro"), modo=modo,
             grados_modo=(res.get("modo") or {}).get("nombre"), tempo_bpm=round(bpm, 1) if bpm else None, compas=compas or "—",
             ambito_melodia=ambito, voz_melodia=voz, acorde_mas_usado=mas_usado[0], acorde_mas_usado_pct=round(100 * mas_usado[1] / t_ok, 1),
             complejidad_acordes=None if cc is None else round(cc, 1), complejidad_melodica=None if mc is None else round(mc, 1),
             tension_acorde_melodia=None if cmt is None else round(cmt, 1), novedad_progresion=cpn, novedad_progresion_pop=cpn_pop,
             cambios_distintos=n_cambios,
             cuartos_de_tono_melodia=round(100 * micro / tm, 1) if notas else None,
             cuartos_de_tono_acordes=round(100 * acordes_micro / t_ok, 1) if ok else None,
             compases=len(bars), tiempo_confiable=round(100 * sum(dur(b) for b in ok) / (sum(dur(b) for b in bars) or 1.0), 1))
    if desde is None and hasta is None:                                # la precisión solo existe para la canción entera
        for nombre, campo, llave in (("evaluacion_melodia.json", "principal", "precision_melodia"),
                                     ("evaluacion_armonia.json", "fundamental", "precision_fundamental")):
            f = run / nombre
            if f.exists():
                v = json.loads(f.read_text(encoding="utf-8")).get(campo)
                r[llave] = None if v is None else round(v, 1)
    return r


def dibujar(r: dict, salida: Path, titulo: str, seccion: str | None, hook: dict | None = None) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    tinta, gris, linea, fondo, panel = "#0b0b0b", "#52514e", "#d9d8d2", "#fcfcfb", "#f1f0ea"
    fmt = lambda v, s="": "—" if v is None else f"{v:g}{s}"
    arriba = [("Centro y modo", f"{r['centro']} {r['modo']}"), ("Grados del modo", r.get("grados_modo") or "—"),
              ("Tempo", fmt(r["tempo_bpm"], " BPM")), ("Compás", r["compas"]), ("Ámbito de la melodía" + (" (bajo)" if r.get("voz_melodia") == "bajo" else ""), r["ambito_melodia"]),
              ("Acorde más usado", f"{r['acorde_mas_usado']} ({r['acorde_mas_usado_pct']:g} % del tiempo)")]
    abajo = [("Complejidad de acordes", r["complejidad_acordes"], "CC"), ("Complejidad melódica", r["complejidad_melodica"], "MC"),
             ("Tensión acorde-melodía", r["tension_acorde_melodia"], "CMT"), ("Novedad de la progresión", r["novedad_progresion"], "CPN"),
             ("Cuartos de tono: melodía", r["cuartos_de_tono_melodia"], None), ("Cuartos de tono: acordes", r["cuartos_de_tono_acordes"], None)]
    pie = f"Compases confiables: {r['tiempo_confiable']:g} % del tiempo"
    if r.get("precision_melodia") is not None:
        pie += f" · melodía contra la referencia: F {r['precision_melodia']:g}"
    if r.get("precision_fundamental") is not None:
        pie += f" · fundamental: {r['precision_fundamental']:g} %"
    filas = len(arriba) + len(abajo)
    alto = 1.55 + 0.36 * filas + 0.75
    fig = plt.figure(figsize=(6.4, alto), facecolor=fondo)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, alto)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.04, 0.12), 0.92, alto - 0.24, boxstyle="round,pad=0,rounding_size=0.04", fc=panel, ec=linea, lw=1))
    y = alto - 0.62
    ax.text(0.09, y, "DATOS DE LA CANCIÓN", fontsize=11.5, fontweight="bold", color=tinta, va="center")
    ax.text(0.91, y, titulo + (f" · {seccion}" if seccion else ""), fontsize=10.5, color=gris, va="center", ha="right")
    y -= 0.3
    ax.plot([0.09, 0.91], [y, y], color=linea, lw=1)
    for nombre, valor in arriba:
        y -= 0.36
        ax.text(0.09, y, nombre, fontsize=10.5, color=gris, va="center")
        ax.text(0.91, y, valor, fontsize=10.5, fontweight="bold", color=tinta, va="center", ha="right")
    y -= 0.26
    ax.plot([0.09, 0.91], [y, y], color=linea, lw=1)
    x_h = 0.91 if not hook else 0.74
    if hook:
        ax.text(0.74, y - 0.14, "cuaderno", fontsize=8, color=gris, ha="right", va="center")
        ax.text(0.91, y - 0.14, "Hooktheory", fontsize=8, color=gris, ha="right", va="center")
        y -= 0.12
    for nombre, valor, sigla in abajo:
        y -= 0.36
        ax.text(0.09, y, nombre, fontsize=10.5, color=gris, va="center")
        if sigla == "CPN":
            texto = "sin corpus" if r.get("novedad_progresion_pop") is None else "sin cambios" if valor is None else f"{valor:g} bits (pop {r['novedad_progresion_pop']:g})"
        else:
            texto = fmt(valor)
        ax.text(x_h, y, texto, fontsize=10.5, fontweight="bold", color=tinta,
                va="center", ha="right")
        if hook and sigla:
            ax.text(0.91, y, fmt(hook.get(sigla)), fontsize=10.5, color=gris, va="center", ha="right")
    y -= 0.34
    ax.text(0.09, y, pie, fontsize=8.5, color=gris, va="center")
    ax.text(0.09, y - 0.2, "Valores crudos de 0 a 100 (% del tiempo), no percentiles." + (" Hooktheory: percentiles suyos." if hook else ""),
            fontsize=8.5, color=gris, va="center")
    fig.savefig(salida, dpi=200, facecolor=fondo)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--desde", type=float, help="segundo inicial del tramo")
    ap.add_argument("--hasta", type=float, help="segundo final del tramo")
    ap.add_argument("--seccion", help="nombre del tramo, para el título y el nombre del archivo")
    ap.add_argument("--titulo", help="título de la canción (si no, sale del nombre de la carpeta)")
    ap.add_argument("--hooktheory", help='valores de Hooktheory para mostrar al lado, p. ej. "CC=50,MC=81,CMT=11,CPN=71"')
    a = ap.parse_args()
    hook = {k.strip().upper(): float(v) for k, v in (p.split("=") for p in a.hooktheory.split(","))} if a.hooktheory else None
    for run in a.corridas:
        r = tarjeta(run, a.desde, a.hasta)
        if hook:
            r["hooktheory"] = hook
        titulo = a.titulo or re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", run.name).replace("_", " ")[:40]
        sufijo = "_" + re.sub(r"\W+", "_", a.seccion.lower()).strip("_") if a.seccion else ""
        (run / f"tarjeta{sufijo}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        dibujar(r, run / f"tarjeta{sufijo}.png", titulo, a.seccion, hook)
        print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
