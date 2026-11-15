"""Pruebas de estilo: ¿a qué estilo existente se parece cada canción? Compara la armonía y la melodía medidas por el
cuaderno con reglas medibles de cada estilo y con cifras publicadas de rock, práctica común y jazz.

Uso:
    python scripts/pruebas_de_estilo.py outputs/<corrida> [...] --salida outputs/pruebas_de_estilo

Lee armonia.json y line_diagnostics.json de cada corrida. Escribe <salida>.json, <salida>.csv, <salida>_veredictos.png
(canciones × estilos) y <salida>_distancias.png (distancia a rock, práctica común y pop). Solo usa compases confiables.

Cifras publicadas (no se descarga nada):
- Rock: de Clercq y Temperley (2011), «A corpus analysis of rock harmony», Popular Music 30(1): 100 canciones (RS 5×20).
- Práctica común: Temperley (2009), «A Statistical Analysis of Tonal Harmony» (corpus Kostka-Payne, 919 acordes). Sus
  fundamentales publicadas suman 91,5 %; el resto se reparte entre los grados que faltan (aproximación).
- Jazz: Broze y Shanahan (2013), «Diachronic Changes in Jazz Harmony», Music Perception 31(1): la cuarta ascendente es el
  55,8 % de los cambios.
- Pop: los 9 álbumes de references/corpus (si está el archivo).

Los umbrales de «encaja» son PROPUESTAS de este trabajo, puestas a partir de esas cifras; no son umbrales publicados.
Las fundamentales en cuarto de tono se llevan al grado de 12 más cercano por abajo para comparar, y su peso se informa.
El cuaderno no etiqueta séptimas, así que el jazz solo se prueba por el movimiento de las fundamentales.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

try:
    from corpus_adapters import load_references, transition_share
except ImportError:                                                       # permite importar el módulo desde otro directorio
    load_references = lambda: {}
    transition_share = lambda *_: None

GRADOS = ["I", "♭II", "II", "♭III", "III", "IV", "♯IV", "V", "♭VI", "VI", "♭VII", "VII"]
ROCK = dict(zip(GRADOS, [32.8, 0.5, 3.6, 2.6, 1.9, 22.6, 0.3, 16.3, 4.0, 7.2, 8.1, 0.4]))
_kp = {"I": 34.6, "V": 23.3, "II": 11.3, "IV": 7.6, "VI": 5.4, "VII": 3.8, "♭VI": 3.7, "♭VII": 0.7, "♭III": 1.1}
CLASICA = {g: _kp.get(g, (100 - sum(_kp.values())) / (12 - len(_kp))) for g in GRADOS}
# movimiento de la fundamental, % de los cambios: quinta descendente, quinta ascendente, segundas, terceras, tritono
MOV = {"rock": [24.8, 24.3, 33.3, 17.5, 0.2], "práctica común": [39.1, 21.2, 24.4, 12.2, 3.2]}
MOV_NOMBRES = ["5ª desc.", "5ª asc.", "segundas", "terceras", "tritono"]
ANTES_DE_I = {"rock": {"IV": 39.6, "V": 26.9, "♭VII": 13.2}, "práctica común": {"V": 62.1, "IV": 11.9, "♭VII": 0.0}}
PENTA_MENOR, PENTA_MAYOR = {0, 3, 5, 7, 10}, {0, 2, 4, 7, 9}
ESTILOS = ["Rock modal-pentatónico", "Práctica común", "Jazz", "Pentatónica", "Tonos enteros", "Dodecafonismo", "Minimalismo", "Microtonal"]
CORPUS = Path(__file__).resolve().parent.parent / "references" / "corpus" / "albumes_progresiones.csv"
_REFERENCIAS = load_references()
JAZZ_CUARTA_ASCENDENTE = 100 * (transition_share(_REFERENCIAS.get("jazz"), 5) or 0.558)


def js(p: dict, q: dict) -> float:
    """Distancia de Jensen-Shannon (bits; 0 = iguales, 1 = sin nada en común)."""
    sp, sq = sum(p.values()) or 1.0, sum(q.values()) or 1.0
    d = 0.0
    for k in set(p) | set(q):
        a, b = p.get(k, 0) / sp, q.get(k, 0) / sq
        m = (a + b) / 2
        d += (0.5 * a * math.log2(a / m) if a else 0) + (0.5 * b * math.log2(b / m) if b else 0)
    return d


def pop() -> dict | None:
    if not CORPUS.exists():
        return None
    rom = {"I": 0, "II": 2, "III": 4, "IV": 5, "V": 7, "VI": 9, "VII": 11}
    c = Counter()
    with open(CORPUS, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            menor = r["modo"] == "menor"
            for b in r["acordes_base"].split():
                m = re.match(r"([♭♯]*)([ivIV]+)", b.split("/")[0])
                if not m or m.group(2).upper() not in rom:
                    continue
                k = rom[m.group(2).upper()] + sum(-1 if x == "♭" else 1 for x in m.group(1))
                if menor and not m.group(1) and m.group(2).upper() in ("III", "VI", "VII"):
                    k -= 1
                c[GRADOS[k % 12]] += 1
    return dict(c)


def medir(run: Path, min_conf: float = 0.5) -> dict:
    H = json.loads((run / "armonia.json").read_text(encoding="utf-8"))
    J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
    ton = H.get("tonica_pc24") or 0
    bars = H["compases"]
    ok = [b for b in bars if b.get("fundamental_pc24") is not None and (b.get("confianza") or 0) >= min_conf]
    dur = lambda b: b["fin_s"] - b["inicio_s"]
    total = sum(dur(b) for b in ok) or 1.0

    # fundamentales en 12 grados (las de cuarto de tono, al grado de abajo) y su peso en cuartos de tono
    fund = Counter()
    cuarto = 0.0
    for b in ok:
        r = (b["fundamental_pc24"] - ton) % 24
        fund[GRADOS[r // 2]] += dur(b)
        cuarto += dur(b) * (r % 2)
    p12 = {g: fund.get(g, 0) / total for g in GRADOS}
    masa = lambda conj: sum(p12[GRADOS[k]] for k in conj)

    # cambios de fundamental entre compases confiables seguidos
    mov = Counter()
    antes = Counter()
    cambios = distintos = 0
    vistos = set()
    for x, y in zip(ok, ok[1:]):
        if abs(y["inicio_s"] - x["fin_s"]) > 0.05:
            continue
        a, b = ((x["fundamental_pc24"] - ton) % 24) // 2, ((y["fundamental_pc24"] - ton) % 24) // 2
        if a == b:
            continue
        cambios += 1
        vistos.add((a, b))
        d = (b - a) % 12
        mov[{5: 0, 7: 1, 1: 2, 2: 2, 10: 2, 11: 2, 3: 3, 4: 3, 8: 3, 9: 3, 6: 4}[d]] += 1
        if b == 0:
            antes[GRADOS[a]] += 1
    distintos = len(vistos)
    pm = [100 * mov[k] / cambios if cambios else 0.0 for k in range(5)]
    asim = (mov[0] - mov[1]) / (mov[0] + mov[1]) if mov[0] + mov[1] else None
    n_antes = sum(antes.values())

    # melodía
    notas = [(n["start_s"], n["end_s"], n["midi"]) for n in J["raw_high"]]
    tm = sum(b - a for a, b, m in notas) or 1.0
    pc12, pc24 = Counter(), Counter()
    for a, b, m in notas:
        q = round(m * 2)
        pc24[(q - ton) % 24] += b - a
        pc12[((q - ton) % 24) // 2] += b - a
    ent12 = -sum(v / tm * math.log2(v / tm) for v in pc12.values() if v)
    wt = max(sum(pc12[k] for k in (0, 2, 4, 6, 8, 10)), sum(pc12[k] for k in (1, 3, 5, 7, 9, 11))) / tm
    micro = sum(v for k, v in pc24.items() if k % 2) / tm
    pasos = Counter()
    for (a0, b0, m0), (a1, b1, m1) in zip(notas, notas[1:]):
        if a1 - b0 < 0.25:
            pasos[abs(round(m1 * 2) - round(m0 * 2))] += 1
    np_ = sum(v for k, v in pasos.items() if k) or 1
    # melodía: cuánto cabe en una pentatónica sobre el centro y cuánto en el modo de la canción
    mel_penta = max(sum(pc12[k] for k in PENTA_MENOR), sum(pc12[k] for k in PENTA_MAYOR)) / tm
    pasos_g = {"1": 0, "2": 4, "3": 8, "4": 10, "5": 14, "6": 18, "7": 22}
    en_modo = {0, 10, 14}
    for g in (((H.get("resumen") or {}).get("modo") or {}).get("grados") or {}).values():
        m_ = re.fullmatch(r"([♭b♯#]*)([1-7])([+d-]?)", (g or "").strip())
        if m_:
            en_modo.add((pasos_g[m_.group(2)] + sum(-2 if c in "♭b" else 2 for c in m_.group(1)) + {"+": 1, "d": -1, "-": -1, "": 0}[m_.group(3)]) % 24)
    mel_modo = sum(v for k, v in pc24.items() if k in en_modo) / tm
    segs_a = [s_ for x in (((H.get("resumen") or {}).get("patrones") or {}).get("Voz aguda") or {}).values() for s_ in (x.get("segmentos") or [])]
    grado_micro = max(((v / tm, k) for k, v in pc24.items() if k % 2), default=(0.0, None))

    # repetición: tiempo dentro de los patrones de ciclo de la voz grave (o de la aguda si la grave no tiene)
    pat = (H.get("resumen") or {}).get("patrones") or {}
    en_ciclo = 0.0
    for v in ("Voz grave", "Voz aguda"):
        segs = [s for x in (pat.get(v) or {}).values() for s in (x.get("segmentos") or [])]
        if segs:
            en_ciclo = sum(s[1] - s[0] for s in segs)
            break
    largo = max(b["fin_s"] for b in bars) - min(b["inicio_s"] for b in bars)
    acordes = len({(b["fundamental_pc24"], b.get("calidad")) for b in ok})

    rock_ref = _REFERENCIAS.get("rock", {}).get("roots") or ROCK
    clasica_ref = _REFERENCIAS.get("classical", {}).get("roots") or CLASICA
    jazz_ref = _REFERENCIAS.get("jazz", {}).get("roots")
    r = dict(corrida=run.name, centro=(H.get("resumen") or {}).get("centro"), modo=((H.get("resumen") or {}).get("modo") or {}).get("nombre"),
             fundamentales={g: round(100 * p12[g], 1) for g in GRADOS if p12[g] > 0.004},
             fundamentales_cuarto_de_tono=round(100 * cuarto / total, 1),
             distancia_rock=round(js(p12, rock_ref), 3), distancia_practica_comun=round(js(p12, clasica_ref), 3),
             distancia_jazz=None if jazz_ref is None else round(js(p12, jazz_ref), 3),
             pentatonica_menor=round(100 * masa(PENTA_MENOR), 1), pentatonica_mayor=round(100 * masa(PENTA_MAYOR), 1),
             cambios=cambios, cambios_distintos=distintos, movimiento={n: round(v, 1) for n, v in zip(MOV_NOMBRES, pm)},
             asimetria_quintas=None if asim is None else round(asim, 2),
             distancia_movimiento_rock=round(js(dict(enumerate(pm)), dict(enumerate(MOV["rock"]))), 3) if cambios else None,
             distancia_movimiento_practica_comun=round(js(dict(enumerate(pm)), dict(enumerate(MOV["práctica común"]))), 3) if cambios else None,
             antes_de_la_tonica={g: round(100 * v / n_antes, 1) for g, v in antes.most_common(4)} if n_antes else {},
             llegadas_a_la_tonica=n_antes, cuarta_ascendente=round(pm[0], 1),
             tonos_enteros=round(100 * wt, 1), entropia_melodia_bits=round(ent12, 2),
             acordes_distintos=acordes, tiempo_en_ciclos=round(100 * min(1.0, en_ciclo / largo), 1) if largo else 0.0,
             cambios_por_compas=round(cambios / max(len(ok) - 1, 1), 2),
             melodia_pentatonica=round(100 * mel_penta, 1), melodia_en_el_modo=round(100 * mel_modo, 1),
             melodia_en_ciclos=round(100 * min(1.0, sum(x_[1] - x_[0] for x_ in segs_a) / largo), 1) if largo else 0.0,
             cuartos_de_tono_melodia=round(100 * micro, 1), paso_de_cuarto_de_tono=round(100 * pasos[1] / np_, 1),
             paso_de_tres_cuartos=round(100 * pasos[3] / np_, 1),
             grado_en_cuarto_mas_usado=None if grado_micro[1] is None else f"{GRADOS[grado_micro[1] // 2]}+ ({100 * grado_micro[0]:.1f} %)")
    P = pop()
    if P:
        r["distancia_pop"] = round(js(p12, P), 3)
    r["veredictos"] = veredictos(r)
    return r


def veredictos(r: dict) -> dict:
    """«encaja», «en parte», «no encaja» o «sin datos» (menos de 8 cambios de acorde), con la cifra que lo decide. Umbrales propuestos por este trabajo."""
    v = {}
    pen = max(r["pentatonica_menor"], r["pentatonica_mayor"])
    a = r["asimetria_quintas"]
    vi = r["antes_de_la_tonica"].get("V", 0.0)
    pocos = r["cambios"] < 8
    # rock modal-pentatónico: fundamentales cerca del rock, sin preferencia por la quinta descendente, sin V→I dominante
    cerca = r["distancia_rock"] < r["distancia_practica_comun"]
    sin = ("sin datos", f"solo {r['cambios']} cambios de acorde · no alcanza para medir")
    if pocos:
        v[ESTILOS[0]] = sin
    else:
        sim = a is None or abs(a) < 0.15
        v[ESTILOS[0]] = ("encaja" if cerca and sim and vi < 30 else "en parte" if cerca or sim else "no encaja",
                         f"JS rock {r['distancia_rock']:.2f} · asimetría {('—' if a is None else f'{a:+.2f}')} · V→I {vi:.0f} %")
    # práctica común: quinta descendente preferida y V→I como llegada principal
    tonal = a is not None and a >= 0.2 and vi >= 50
    v[ESTILOS[1]] = sin if pocos else ("encaja" if tonal and not cerca else "en parte" if tonal or (a is not None and a >= 0.2) else "no encaja",
                                       f"JS {r['distancia_practica_comun']:.2f} · V→I {vi:.0f} % (clásica 62 %)")
    # jazz: la cuarta ascendente domina los cambios (55,8 % en el corpus de estándares)
    q = r["cuarta_ascendente"]
    v[ESTILOS[2]] = sin if pocos else ("encaja" if q >= 0.84 * JAZZ_CUARTA_ASCENDENTE and vi >= 30 else
                                       "en parte" if q >= 0.72 * JAZZ_CUARTA_ASCENDENTE else "no encaja",
                                       f"cuarta ascendente {q:.0f} % (jazz {JAZZ_CUARTA_ASCENDENTE:.0f} %) · V→I {vi:.0f} %")
    # pentatónica: las fundamentales caben en una pentatónica sobre el centro (rock 82 %, clásica 67 %)
    v[ESTILOS[3]] = ("encaja" if pen >= 90 else "en parte" if pen >= 75 else "no encaja", f"{pen:.0f} % de las fundamentales (rock 82 %)")
    # tonos enteros: la melodía cabe en una de las dos escalas (al azar: 50 %)
    w = r["tonos_enteros"]
    v[ESTILOS[4]] = ("encaja" if w >= 85 else "en parte" if w >= 70 else "no encaja", f"{w:.0f} % de la melodía (azar 50 %)")
    # dodecafonismo: las doce clases por igual (máximo 3,58 bits) y sin centro
    e = r["entropia_melodia_bits"]
    v[ESTILOS[5]] = ("encaja" if e >= 3.5 else "en parte" if e >= 3.4 else "no encaja", f"entropía {e:.2f} de 3,58 bits")
    # minimalismo: casi todo el tiempo dentro de ciclos repetidos y pocos acordes
    c, n = r["tiempo_en_ciclos"], r["acordes_distintos"]
    v[ESTILOS[6]] = ("encaja" if c >= 70 and r["cambios_distintos"] <= 10 else "en parte" if c >= 40 else "no encaja",
                     f"{c:.0f} % del tiempo en ciclos · {r['cambios_distintos']} cambios distintos")
    # microtonal: cuartos de tono por encima del piso de ruido medido en música sin cuartos de tono (9-13 %)
    m = r["cuartos_de_tono_melodia"]
    v[ESTILOS[7]] = ("encaja" if m >= 20 else "en parte" if m >= 14 else "no encaja", f"{m:.0f} % de la melodía (piso 9-13 %)")
    return {k: dict(veredicto=a_, dato=b_) for k, (a_, b_) in v.items()}


def nombre(corrida: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", corrida)
    n = re.sub(r"(angine_de_poitrine_|primus_|_audio_off\w*|_official_audio|_repro|_\d{4}_\w+$)", "", n)
    return n.replace("_", " ").strip().capitalize()


def dibujar(filas: list[dict], salida: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tinta, gris, fondo = "#0b0b0b", "#52514e", "#fcfcfb"
    tono = {"encaja": "#2a78d6", "en parte": "#a9c8ef", "no encaja": "#eeede8", "sin datos": fondo}
    letra = {"encaja": "#ffffff", "en parte": tinta, "no encaja": gris, "sin datos": gris}
    nf, nc = len(filas), len(ESTILOS)
    fig, ax = plt.subplots(figsize=(2.6 + 2.15 * nc, 1.5 + 0.95 * nf), facecolor=fondo)
    ax.set_xlim(0, nc)
    ax.set_ylim(0, nf)
    ax.axis("off")
    for i, r in enumerate(filas):
        y = nf - 1 - i
        ax.text(-0.08, y + 0.5, nombre(r["corrida"]), ha="right", va="center", fontsize=11, fontweight="bold", color=tinta)
        for j, e in enumerate(ESTILOS):
            v = r["veredictos"][e]
            ax.add_patch(plt.Rectangle((j + 0.03, y + 0.05), 0.94, 0.9, fc=tono[v["veredicto"]], ec="#d9d8d2" if v["veredicto"] == "sin datos" else "none", ls="--", lw=1))
            ax.text(j + 0.5, y + 0.64, v["veredicto"], ha="center", va="center", fontsize=10.5, fontweight="bold", color=letra[v["veredicto"]])
            dato = v["dato"].replace(" · ", "\n")
            ax.text(j + 0.5, y + 0.3, dato, ha="center", va="center", fontsize=6.6, color=letra[v["veredicto"]], linespacing=1.15)
    for j, e in enumerate(ESTILOS):
        ax.text(j + 0.5, nf + 0.12, e.replace(" ", "\n", 1) if len(e) > 14 else e, ha="center", va="bottom", fontsize=10, color=tinta)
    fig.text(0.01, 0.01, "Umbrales propuestos por este trabajo a partir de cifras publicadas (de Clercq y Temperley 2011; Temperley 2009; Broze y Shanahan 2013). "
             "Solo compases confiables.", fontsize=7.5, color=gris)
    fig.subplots_adjust(left=0.13, right=0.995, top=0.86, bottom=0.07)
    fig.savefig(salida + "_veredictos.png", dpi=200, facecolor=fondo)
    plt.close(fig)

    # distancias de las fundamentales a cada referencia
    refs = [("distancia_rock", "Rock (100 canciones)", "#2a78d6"), ("distancia_practica_comun", "Práctica común", "#eb6834")]
    if all("distancia_pop" in r for r in filas):
        refs.append(("distancia_pop", "Pop (9 álbumes)", "#1baf7a"))
    fig, ax = plt.subplots(figsize=(9.5, 1.3 + 0.7 * nf), facecolor=fondo)
    alto = 0.8 / len(refs)
    for k, (campo, etiqueta, color) in enumerate(refs):
        ys = [nf - 1 - i + 0.4 - alto * (k + 0.5) for i in range(nf)]
        ax.barh(ys, [r[campo] for r in filas], height=alto * 0.86, color=color, label=etiqueta)
        for y, r in zip(ys, filas):
            ax.text(r[campo] + 0.008, y, f"{r[campo]:.2f}", va="center", fontsize=8.5, color=tinta)
    ax.set_yticks(range(nf), [nombre(r["corrida"]) for r in filas][::-1], fontsize=10)
    ax.set_xlim(0, max(max(r[c] for r in filas) for c, _, _ in refs) * 1.18)
    ax.set_xlabel("Distancia de Jensen-Shannon entre las fundamentales de la canción y las del estilo (0 = iguales)", fontsize=9, color=gris)
    ax.set_title("¿De qué estilo están más cerca las fundamentales de cada canción?", loc="left", fontsize=12, color=tinta)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_facecolor(fondo)
    ax.tick_params(colors=gris, length=0)
    ax.grid(axis="x", color="#e4e3df", lw=0.8)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    fig.savefig(salida + "_distancias.png", dpi=200, facecolor=fondo)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--salida", default="outputs/pruebas_de_estilo")
    a = ap.parse_args()
    filas = []
    for run in a.corridas:
        if not (run / "armonia.json").exists():
            print(f"sin armonia.json: {run.name}")
            continue
        filas.append(medir(run))
    Path(a.salida + ".json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
    planos = [k for k, v in filas[0].items() if not isinstance(v, dict)]
    with open(a.salida + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(planos + ESTILOS)
        for r in filas:
            w.writerow([r.get(k) for k in planos] + [r["veredictos"][e]["veredicto"] for e in ESTILOS])
    dibujar(filas, a.salida)
    for r in filas:
        print(json.dumps({k: v for k, v in r.items() if k != "veredictos"}, ensure_ascii=False))
        print("   " + " | ".join(f"{e}: {r['veredictos'][e]['veredicto']}" for e in ESTILOS))


if __name__ == "__main__":
    main()
