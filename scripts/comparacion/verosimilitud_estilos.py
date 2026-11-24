"""Matriz de verosimilitud: ¿qué tan probable es la armonía de cada canción bajo el modelo de cada estilo?

Uso:
    python scripts/comparacion/corpus_estilos.py                       # una vez: arma references/corpus/estilos_por_pieza.json
    python scripts/comparacion/verosimilitud_estilos.py outputs/<corrida> [...] --salida outputs/verosimilitud

Cada estilo (rock, práctica común, jazz, pop) se resume por el «centro» de su corpus en dos cosas:
- qué fundamentales suenan y cuánto tiempo (12 grados respecto de la tónica), y
- cómo se cambia de fundamental (intervalo del cambio y grado de llegada, 12 × 12).
Verosimilitud de una canción en un estilo = el % de piezas del corpus que quedan igual o más lejos del centro de su estilo
que la canción (distancia de Jensen-Shannon; cada pieza se mide contra el centro de las demás). 50 = tan típica como la
pieza mediana del estilo; 0 = más rara que cualquier pieza del corpus. Es la media de las dos partes; con menos de 3
cambios de acorde, solo cuenta la de las fundamentales. Así los cuatro estilos quedan en la misma escala.

Canción: fundamentales de los compases confiables del cuaderno (armonia.json). Las que caen en cuarto de tono se llevan
al grado de abajo para poder comparar, y su peso se informa aparte: ningún corpus tiene cuartos de tono.

Escribe <salida>.json, <salida>.csv, <salida>_matriz.png (canciones × estilos) y <salida>_mapa.png (todas las piezas de
los corpus y las canciones en un plano, según sus fundamentales).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estilo_figuras  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
CORPUS = RAIZ / "references" / "corpus" / "estilos_por_pieza.json"
ESTILOS = {"rock": "Rock (RS 200)", "clasica": "Práctica común (Kostka-Payne)", "jazz": "Jazz (iRealPro)", "pop": "Pop (Hooktheory)"}
CITA = {"rock": "RS 200 (de Clercq y Temperley)", "clasica": "Kostka-Payne (Temperley 2009)", "jazz": "iRealPro (Shanahan y Broze)",
        "pop": "9 álbumes de Hooktheory"}
COLOR = {"rock": "#1f5fa8", "clasica": "#c6532a", "jazz": "#16825d", "pop": "#bd7900"}
GRADOS = ["I", "♭II", "II", "♭III", "III", "IV", "♯IV", "V", "♭VI", "VI", "♭VII", "VII"]
ALFA = 0.5                                                              # suavizado de Laplace


def js(p, q) -> float:
    d = 0.0
    for a, b in zip(p, q):
        m = (a + b) / 2
        d += (0.5 * a * math.log2(a / m) if a > 0 else 0) + (0.5 * b * math.log2(b / m) if b > 0 else 0)
    return d


def cambios_dist(cs: list) -> list[float] | None:
    """Reparto de los cambios por intervalo de la fundamental y grado de llegada (12 × 12), o None si hay menos de 3."""
    if len(cs) < 3:
        return None
    v = [0.0] * 144
    for a, b in cs:
        v[((b - a) % 12) * 12 + b] += 1.0 / len(cs)
    return v


def centro(piezas: list[dict], clave: str, excluir: dict | None = None) -> list[float]:
    vs = [p[clave] for p in piezas if p is not excluir and p.get(clave)]
    n = len(vs[0])
    c = [sum(v[k] for v in vs) / len(vs) for k in range(n)]
    return [(x + 1e-4) / (1 + n * 1e-4) for x in c]


def preparar(C: dict) -> dict:
    """Para cada estilo: sus centros y la distancia de cada pieza al centro de las demás (para los percentiles)."""
    out = {}
    for e, ps in C.items():
        for p in ps:
            p["cambios_v"] = cambios_dist([tuple(x) for x in p["cambios"]])
        cu, cc = centro(ps, "fundamentales"), centro(ps, "cambios_v")
        du = sorted(js(p["fundamentales"], centro(ps, "fundamentales", p)) for p in ps)
        dc = sorted(js(p["cambios_v"], centro(ps, "cambios_v", p)) for p in ps if p["cambios_v"])
        out[e] = dict(cu=cu, cc=cc, du=du, dc=dc)
    return out


def percentil(d: float, ref: list[float]) -> float:
    """% de piezas del estilo que quedan igual o más lejos de su centro que la canción."""
    return 100 * sum(1 for x in ref if x >= d) / len(ref)


def cancion(run: Path, min_conf: float = 0.5) -> dict:
    H = json.loads((run / "armonia.json").read_text(encoding="utf-8"))
    ton = H.get("tonica_pc24") or 0
    ok = [b for b in H["compases"] if b.get("fundamental_pc24") is not None and (b.get("confianza") or 0) >= min_conf]
    dist = [0.0] * 12
    cuarto = 0.0
    cambios = []
    prev = None
    for b in ok:
        r24 = (b["fundamental_pc24"] - ton) % 24
        r = r24 // 2
        d = b["fin_s"] - b["inicio_s"]
        dist[r] += d
        cuarto += d * (r24 % 2)
        if prev is not None and prev[0] != r and abs(b["inicio_s"] - prev[1]) < 0.05:
            cambios.append((prev[0], r))
        prev = (r, b["fin_s"])
    s = sum(dist) or 1.0
    return dict(fundamentales=[x / s for x in dist], cambios=cambios, cambios_v=cambios_dist(cambios), cuarto_de_tono=round(100 * cuarto / s, 1))


def nombre(corrida: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", corrida)
    n = re.sub(r"(angine_de_poitrine_|primus_|_audio_off\w*|_official_audio|_repro|_cache|_\d{4}_\w+$)", "", n)
    return n.replace("_", " ").strip().capitalize()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--salida", default="outputs/verosimilitud")
    ap.add_argument("--diapositiva", action="store_true",
                    help="sin subtítulo ni nota (van en la diapositiva); en el mapa, leyenda grande, estrellas grandes y rombos pequeños")
    ap.add_argument("--estilos", help="columnas de la matriz, separadas por comas (por ejemplo rock,pop); los percentiles no cambian")
    a = ap.parse_args()
    if not CORPUS.exists():
        raise SystemExit("Falta references/corpus/estilos_por_pieza.json: corre antes scripts/comparacion/corpus_estilos.py")
    C = {k: list(v.values()) for k, v in json.loads(CORPUS.read_text(encoding="utf-8")).items() if v}

    R = preparar(C)

    filas = []
    for run in a.corridas:
        if not (run / "armonia.json").exists():
            print(f"sin armonia.json: {run.name}")
            continue
        c = cancion(run)
        f = dict(corrida=run.name, cancion=nombre(run.name), cambios=len(c["cambios"]), fundamentales_cuarto_de_tono=c["cuarto_de_tono"],
                 fundamentales={GRADOS[k]: round(100 * x, 1) for k, x in enumerate(c["fundamentales"]) if x > 0.004})
        for e in C:
            du = js(c["fundamentales"], R[e]["cu"])
            pu = percentil(du, R[e]["du"])
            f[f"percentil_fundamentales_{e}"] = round(pu, 1)
            if c["cambios_v"]:
                pc = percentil(js(c["cambios_v"], R[e]["cc"]), R[e]["dc"])
                f[f"percentil_cambios_{e}"] = round(pc, 1)
                f[f"percentil_{e}"] = round((pu + pc) / 2, 1)
            else:
                f[f"percentil_cambios_{e}"] = None
                f[f"percentil_{e}"] = round(pu, 1)
        mejor = max(C, key=lambda e: f[f"percentil_{e}"])
        f["estilo_mas_verosimil"] = ESTILOS[mejor]
        filas.append(f)
        print(f"{f['cancion']}: " + " · ".join(f"{ESTILOS[e].split(' (')[0]} {f[f'percentil_{e}']:g}" for e in C) + f"  → {ESTILOS[mejor]}")

    Path(a.salida + ".json").write_text(json.dumps(dict(canciones=filas, piezas_por_estilo={e: len(p) for e, p in C.items()}), ensure_ascii=False, indent=1),
                                        encoding="utf-8")
    with open(a.salida + ".csv", "w", newline="", encoding="utf-8") as fh:
        campos = ["cancion", "cambios", "fundamentales_cuarto_de_tono", "estilo_mas_verosimil"] + [f"percentil_{e}" for e in C] + \
            [f"percentil_fundamentales_{e}" for e in C] + [f"percentil_cambios_{e}" for e in C]
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    estilos = [e.strip() for e in a.estilos.split(",")] if a.estilos else None
    if estilos and (desconocidos := [e for e in estilos if e not in C]):
        raise SystemExit(f"estilos desconocidos: {', '.join(desconocidos)} (hay: {', '.join(C)})")
    dibujar(filas, C, a.salida, a.diapositiva, estilos)


def dibujar(filas: list[dict], C: dict, salida: str, diapositiva: bool = False, estilos: list[str] | None = None) -> None:
    estilo_figuras.preparar()
    estilo_figuras.guardar(figura_matriz(filas, estilos or list(C), textos=not diapositiva), salida + "_matriz.png")
    estilo_figuras.guardar(figura_mapa(filas, C, diapositiva), salida + "_mapa.png")


def figura_matriz(filas: list[dict], est: list[str], textos: bool = True):
    """Canciones × estilos (percentil). Secuencial de un tono: más oscuro = más verosímil.

    Con textos=False no lleva subtítulo ni nota (en la diapositiva van como leyenda debajo de la imagen)."""
    import numpy as np
    from matplotlib.colors import LinearSegmentedColormap
    from estilo_figuras import GRIS, TINTA

    M = np.array([[f[f"percentil_{e}"] for e in est] for f in filas])
    fig, cuerpo = estilo_figuras.figura(
        max(9.0, 3.6 + 1.9 * len(est)) if len(est) > 2 else 6.6, 0.42 * len(filas) + 1.2, "Verosimilitud de la armonía por canción y estilo",
        subtitulo="Escala: % de piezas del estilo igual o más alejadas que la canción; 50 = pieza típica y 0 = más rara que todas."
        if textos else "",
        nota="Corpus: " + ", ".join(CITA[e] for e in est) + ".\n«¼ %»: tiempo con la fundamental en cuarto de tono, que "
             "se llevó al grado de abajo porque ningún corpus tiene cuartos de tono." if textos else "", texto_pt=8.5)
    ax = cuerpo.subplots()
    cmap = LinearSegmentedColormap.from_list("azul", ["#f1f0ea", "#a9c8ef", "#2a78d6", "#0d3c78"])
    ax.imshow(M, cmap=cmap, vmin=0, vmax=60, aspect="auto")
    for i in range(len(filas)):
        for j in range(len(est)):
            v = M[i, j]
            ax.text(j, i, f"{v:g}", ha="center", va="center", fontsize=10, fontweight="bold", color="#ffffff" if v >= 30 else TINTA)
    ax.set_xticks(range(len(est)), [ESTILOS[e].replace(" (", "\n(") for e in est], fontsize=9, color=TINTA)
    ax.set_yticks(range(len(filas)), [f"{f['cancion']}" + (f"  · ¼ {f['fundamentales_cuarto_de_tono']:g} %" if f["fundamentales_cuarto_de_tono"] else "")
                                      for f in filas], fontsize=9, color=TINTA)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.tick_params(length=0)
    for s_ in ax.spines.values():
        s_.set_visible(False)
    ax.set_xlabel("Estilo del corpus", color=GRIS, labelpad=12)   # arriba de los encabezados, con aire
    ax.set_ylabel("Canción", color=GRIS, labelpad=12)
    ax.yaxis.label.set_y(0.68)        # más arriba: a la altura de los nombres cortos, lejos de «Yor zarad · ¼ …»
    return fig


def figura_mapa(filas: list[dict], C: dict, diapositiva: bool = False):
    """Análisis de componentes principales de los repartos de fundamentales (raíz cuadrada, como en Hellinger)."""
    import numpy as np
    from matplotlib.lines import Line2D
    from estilo_figuras import FONDO, GRIS, REJILLA, TINTA

    est = list(C)
    X, lab = [], []
    for e, ps in C.items():
        for p in ps:
            X.append(np.sqrt(p["fundamentales"]))
            lab.append(e)
    X = np.array(X)
    mu = X.mean(0)
    _, _, Vt = np.linalg.svd(X - mu, full_matrices=False)
    P = (X - mu) @ Vt[:2].T
    fig, cuerpo = estilo_figuras.figura(
        12, 5.4 if diapositiva else 7.2, "Posición de las canciones según sus fundamentales armónicas",
        subtitulo="" if diapositiva else "Cada punto del fondo es una pieza de un corpus; los símbolos son las canciones "
                  "comparadas. La cercanía resume el parecido entre sus repartos de fundamentales.",
        nota="" if diapositiva else "Cada eje es una componente principal; entre paréntesis, los tres grados que más pesan "
             "en ella (+ y − indican el sentido).")
    ax = cuerpo.subplots()
    for e in est:
        k = [i for i, l in enumerate(lab) if l == e]
        ax.scatter(P[k, 0], P[k, 1], s=14, color=COLOR[e], alpha=0.58, label=f"{ESTILOS[e]} · {len(k)} piezas", edgecolors="none")
    from estilo_figuras import PALETA_ARTISTA, SIMBOLO_ARTISTA, artista
    presentes = []
    for f in filas:
        q = (np.sqrt([f["fundamentales"].get(g, 0) / 100 for g in GRADOS]) - mu) @ Vt[:2].T
        quien = artista(f["corrida"])
        presentes.append(quien)
        marca, color, _ = SIMBOLO_ARTISTA[quien]
        banda = quien == "Angine de Poitrine"
        # La estrella llena menos área que los otros símbolos: se agranda para que la banda se vea igual o más.
        # En la diapositiva (banda y Primus) la estrella es aún mayor y el rombo, pequeño.
        tam = (260 if banda else 50) if diapositiva else (200 if banda else 60)
        ax.scatter(*q, s=tam, marker=marca, color=color, zorder=6 if banda else 5,
                   edgecolors=FONDO if banda else TINTA, linewidths=1 if banda else 0.5)
    eje = lambda v: ", ".join(f"{GRADOS[k]}{'+' if v[k] > 0 else '−'}" for k in np.argsort(-np.abs(v))[:3])
    letra_eje = {"fontsize": 13, "labelpad": 12} if diapositiva else {}   # en la diapositiva, rótulo separado de las marcas
    ax.set_xlabel(f"Componente 1 ({eje(Vt[0])})", color=GRIS, **letra_eje)
    ax.set_ylabel(f"Componente 2 ({eje(Vt[1])})", color=GRIS, **letra_eje)
    handles, _ = ax.get_legend_handles_labels()
    for h in handles:
        h.set_alpha(1)
    for quien in [a for a in PALETA_ARTISTA if a in presentes]:
        marca, color, tam_leyenda = SIMBOLO_ARTISTA[quien]
        handles.append(Line2D([0], [0], marker=marca, color="none", markerfacecolor=color, markeredgecolor=color,
                              markersize=tam_leyenda, label=quien))
    leyenda = cuerpo.legend(handles=handles, loc="outside right upper", frameon=False, fontsize=12 if diapositiva else 9,
                            title="Corpus y bandas", title_fontsize=13 if diapositiva else 10, labelspacing=1.0,
                            markerscale=1.6 if diapositiva else 1.4)
    leyenda.get_title().set_fontweight("bold")
    leyenda._legend_box.align = "left"
    ax.set_facecolor(FONDO)
    ax.tick_params(colors=GRIS, length=0, labelsize=12 if diapositiva else None)
    ax.grid(color=REJILLA, lw=0.7)
    for s_ in ax.spines.values():
        s_.set_visible(False)
    return fig


if __name__ == "__main__":
    main()
