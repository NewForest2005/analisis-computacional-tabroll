"""Figuras del álbum Vol. II para el artículo: el disco entero frente a los corpus y a los repertorios comparados.

Uso (en la raíz del repo, después de verosimilitud_por_bloques.py, campos_haba.py y ciclos_metricos.py):
    python scripts/figuras_album.py outputs/*angine_de_poitrine* outputs/*fabienk_official_audio_repro \
        --control outputs/*primus* --comparar outputs/*king_gizzard* \
        --bloques outputs/bloques.json --campos outputs/campos_haba --fases outputs/ciclos_metricos_fases.csv \
        --salida outputs/figuras_album

Cada figura se hace solo si está su entrada. Una corrida por canción (la más reciente). Seis PNG:
  _a_clasificacion  De qué corpus viene el disco: percentil medio por canción y corpus (fila «Álbum» = media), estilo
                    predominante y secundario del álbum, y qué corpus gana cada bloque en cuántas canciones.
  _b_perfil         Perfil de medidas al estilo de Hooktheory (complejidad de acordes y melódica, tensión acorde-melodía,
                    novedad de la progresión, % de cuartos de tono) de cada canción, frente a King Gizzard y Primus
                    medidos con el mismo cuaderno.
  _c_circulo_haba   El círculo de quintas de 24 notas partido en sus dos campos (mcd(14, 24) = 2): anillo exterior los 12
                    grados regulares, anillo interior los 12 en cuarto de tono, en el orden de quintas y con cada grado
                    «+» junto a su vecino regular. Área = tiempo de la melodía en ese grado; líneas = pasos melódicos más
                    frecuentes (azul los que cambian de campo). Álbum entero y cada canción.
  _d_campos_tiempo  Línea de tiempo por compás: % de cuartos de tono (color) y mezcla vertical de campos (marcas).
  _e_campos_resumen Las tres pruebas de campos por grupo: mezcla vertical evitada, paso de ¼ y cuartos en el pulso.
  _f_bucle_compas   Fase del riff en el primer tiempo de cada compás (0 a 1 vuelta del bucle) y largo del compás.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

ORDEN = ["fabienk", "mata zyklek", "sarniezz", "utzp", "yor zarad", "angor"]          # Vol. II, orden del disco
GRADOS = ["1", "♭2", "2", "♭3", "3", "4", "♯4", "5", "♭6", "6", "♭7", "7"]
TINTA, GRIS, MUTED, FONDO, REJILLA = "#0b0b0b", "#52514e", "#8a8984", "#fcfcfb", "#e4e3de"
GRUPO_COLOR = {"banda": "#2a78d6", "comparar": "#eb6834", "control": "#1baf7a"}
CAMPO_REG, CAMPO_Q = "#eda100", "#2a78d6"
SEQ = ["#f1f0ea", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def nombre(run: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", run)
    n = re.sub(r"(angine_de_poitrine_|king_gizzard(_and_the_lizard_wizard)?_|king_crimson_|gentle_giant_|primus_|_audio_off\w*|_official_audio\w*|_repro|_cache|_\d{4}_\w+$)", "", n)
    return n.replace("_", " ").strip().capitalize()


def unicas(lista: list[Path]) -> list[Path]:
    por = {}
    for r in sorted(lista, key=lambda r: r.name):
        if (r / "armonia.json").exists():
            por[nombre(r.name)] = r
    return list(por.values())


def orden_banda(n: str) -> int:
    n = n.lower()
    return next((i for i, o in enumerate(ORDEN) if n.startswith(o)), len(ORDEN))


def grado24(d: int) -> str:
    return GRADOS[d // 2] + ("+" if d % 2 else "")


def estilo(ax, grid_x: bool = False, grid_y: bool = False) -> None:
    ax.set_facecolor(FONDO)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(REJILLA)
    ax.tick_params(colors=GRIS, labelsize=8.5, length=0)
    if grid_x:
        ax.grid(axis="x", color=REJILLA, lw=0.8)
    if grid_y:
        ax.grid(axis="y", color=REJILLA, lw=0.8)
    ax.set_axisbelow(True)


def guardar(fig, ruta: str) -> None:
    fig.savefig(ruta, dpi=200, facecolor=FONDO)
    import matplotlib.pyplot as plt
    plt.close(fig)
    print(f"→ {ruta}")


# ---------------------------------------------------------------- (a) clasificación por corpus
def fig_clasificacion(bloques: dict, salida: str) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    u = bloques.get("umbral", 5)
    filas = sorted([f for f in bloques["canciones"] if f.get("grupo", "banda") == "banda" and not f.get("control")], key=lambda f: orden_banda(f["cancion"]))
    vistos, tmp = set(), []
    for f in filas:
        if f["cancion"] not in vistos:
            vistos.add(f["cancion"])
            tmp.append(f)
    filas = tmp
    corpora = sorted({c for f in filas for c in f["percentiles"]})
    M = np.full((len(filas) + 1, len(corpora)), np.nan)
    nb = np.zeros((len(filas), len(corpora)), dtype=int)
    for i, f in enumerate(filas):
        for j, c in enumerate(corpora):
            v = [x for x in f["percentiles"].get(c, {}).values() if x is not None]
            if v:
                M[i, j], nb[i, j] = float(np.mean(v)), len(v)
    M[-1] = np.nanmean(M[:-1], axis=0)
    orden_c = np.argsort(-np.nan_to_num(M[-1], nan=-1))
    M, nb, corpora = M[:, orden_c], nb[:, orden_c], [corpora[j] for j in orden_c]
    medias = [(corpora[j], M[-1, j]) for j in range(len(corpora)) if not np.isnan(M[-1, j])]
    empate = len(medias) > 1 and medias[0][1] - medias[1][1] < 3

    bl = sorted({b for f in filas for b in f["mejor_por_bloque"]})
    titulo_b = {"armonia": "Armonía", "escala": "Escala (12)", "microtono": "Cuartos de tono", "metro": "Metro"}
    cuenta = {b: Counter() for b in bl}
    for f in filas:
        for b, m in f["mejor_por_bloque"].items():
            cuenta[b][m["corpus"] if m["percentil"] >= u else "sin vecino"] += 1
    victorias = Counter(c for b in bl for c, n in cuenta[b].items() for _ in range(n) if c != "sin vecino")
    pred = [c for c, _ in victorias.most_common(2)]
    sin_v = sum(cuenta[b]["sin vecino"] for b in bl)
    total = sum(sum(cuenta[b].values()) for b in bl)

    fig = plt.figure(figsize=(12.5, 3.6 + 0.48 * len(filas) + 3.4), facecolor=FONDO)
    gs = fig.add_gridspec(2, 1, height_ratios=[len(filas) + 1, 2.4], hspace=1.35)
    ax = fig.add_subplot(gs[0])
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    imagen = ax.imshow(np.nan_to_num(M, nan=0), cmap=cmap, vmin=0, vmax=60, aspect="auto")
    barra = fig.colorbar(imagen, ax=ax, orientation="horizontal", fraction=0.045, pad=0.28,
                         ticks=[0, 15, 30, 45, 60], aspect=40)
    barra.set_label("Percentil medio de tipicidad: blanco = menor · azul oscuro = mayor", fontsize=8.5, color=GRIS, labelpad=5)
    barra.ax.tick_params(labelsize=8, colors=GRIS)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if np.isnan(M[i, j]):
                ax.text(j, i, "—", ha="center", va="center", fontsize=8, color=MUTED)
                continue
            txt = f"{M[i, j]:.0f}" + (f"\n{nb[i, j]} bl." if i < len(filas) else "")
            ax.text(j, i, txt, ha="center", va="center", fontsize=8 if i < len(filas) else 9, color="#ffffff" if M[i, j] > 30 else TINTA,
                    fontweight="bold" if i == len(filas) and corpora[j] in pred else "normal")
    ax.axhline(len(filas) - 0.5, color=FONDO, lw=4)
    ax.set_yticks(range(M.shape[0]), [f["cancion"] for f in filas] + ["Álbum (media)"], fontsize=9.5, color=TINTA)
    ax.set_xticks(range(len(corpora)), corpora, fontsize=9, color=TINTA, rotation=0)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.suptitle("Clasificación del álbum por corpus", x=0.56, y=0.98, ha="center", fontsize=16, fontweight="bold", color=TINTA)
    fig.text(0.56, 0.925, "El color resume el percentil medio de tipicidad de la banda frente a cada corpus.\n"
             "Azul más oscuro = mayor parecido estadístico; blanco = menor parecido.", ha="center", va="top", fontsize=9.5, color=GRIS, linespacing=1.25)
    fig.text(0.56, 0.455, "bl. = cantidad de bloques de rasgos con datos válidos para esa canción y ese corpus.",
             ha="center", va="top", fontsize=9, color=GRIS)
    if empate:
        fig.text(0.56, 0.885, f"Empate entre {medias[0][0]} y {medias[1][0]}: diferencia menor de 3 puntos.", ha="center", va="top", fontsize=8.5, color=GRIS)

    ax2 = fig.add_subplot(gs[1])
    estilo(ax2, grid_x=True)
    todos = sorted({c for b in bl for c in cuenta[b]}, key=lambda c: (c == "sin vecino", c))
    paleta = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
    color = {c: (REJILLA if c == "sin vecino" else paleta[k % len(paleta)]) for k, c in enumerate([c for c in todos if c != "sin vecino"])}
    color["sin vecino"] = "#c9c8c2"
    for i, b in enumerate(bl):
        x = 0
        for c in todos:
            n = cuenta[b][c]
            if not n:
                continue
            ax2.barh(i, n, left=x, color=color[c], height=0.6, edgecolor=FONDO, linewidth=2)
            x += n
    ax2.set_yticks(range(len(bl)), [titulo_b.get(b, b) for b in bl], fontsize=9, color=TINTA)
    ax2.set_xlim(0, len(filas))
    ax2.set_xlabel("Canciones del disco", fontsize=9.5, color=GRIS, labelpad=12)
    ax2.invert_yaxis()
    if len(pred) > 1 and victorias[pred[0]] == victorias[pred[1]]:
        resumen = f"empate entre {pred[0]} y {pred[1]} ({victorias[pred[0]]} de {total} cada uno)"
    else:
        resumen = (f"predominante: {pred[0] if pred else '—'} ({victorias[pred[0]] if pred else 0} de {total}); "
                   f"secundario: {pred[1] if len(pred) > 1 else '—'} ({victorias[pred[1]] if len(pred) > 1 else 0})")
    ax2.set_title(f"Qué corpus gana cada bloque", loc="center", fontsize=12.5, fontweight="bold", color=TINTA, pad=20)
    fig.text(0.56, 0.415, f"Percentil ≥ {u:g}: {resumen}; sin vecino: {sin_v}", ha="center", va="center", fontsize=8.5, color=GRIS)
    victorias_totales = {c: sum(cuenta[b][c] for b in bl) for c in todos}
    handles = [plt.Line2D([0], [0], color=color[c], lw=8, label=f"{c} — {victorias_totales[c]} victorias") for c in todos]
    handles.append(plt.Line2D([0], [0], color=color["sin vecino"], lw=8, label=f"Sin vecino — {victorias_totales['sin vecino']} casos"))
    # La paleta queda debajo del gráfico inferior; el texto metodológico ocupa
    # una franja independiente, más cercana al gráfico y sin cruzar la leyenda.
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.68, 0.185), ncol=3, frameon=False, fontsize=7.8)
    fig.text(0.07, 0.045, "Número = canciones del álbum en que ese corpus gana un bloque.\n"
             "«Sin vecino» = ningún corpus supera el umbral.",
             fontsize=8.5, color=GRIS, ha="left", va="bottom", linespacing=1.15)
    fig.subplots_adjust(top=0.84, bottom=0.25, left=0.14, right=0.98)
    guardar(fig, salida + "_a_clasificacion.png")


# ---------------------------------------------------------------- (b) perfil al estilo Hooktheory
def fig_perfil(runs: dict, salida: str) -> None:
    import matplotlib.pyplot as plt
    from tarjeta_cancion import tarjeta

    medidas = [("complejidad_acordes", "Complejidad de acordes", "%"), ("complejidad_melodica", "Complejidad melódica (notas fuera del modo)", "%"),
               ("tension_acorde_melodia", "Tensión acorde-melodía", "%"), ("novedad_progresion", "Novedad de la progresión (sorpresa frente a pop)", "bits"),
               ("cuartos_de_tono_melodia", "Cuartos de tono en la melodía", "% del tiempo")]
    datos = defaultdict(list)
    for grupo, lista in runs.items():
        for r in lista:
            try:
                t = tarjeta(r)
            except Exception as e:                                       # noqa: BLE001
                print(f"  sin tarjeta {r.name}: {e}")
                continue
            datos[grupo].append((nombre(r.name), t))
    if not datos.get("banda"):
        return
    fig, ejes = plt.subplots(len(medidas), 1, figsize=(11, 3.0 * len(medidas) + 3.2), facecolor=FONDO)
    etiqueta = {"banda": "Angine de Poitrine", "comparar": "King Gizzard", "control": "Primus (control)"}
    filas_y = {"control": 0, "comparar": 1, "banda": 2}
    for ax, (k, titulo, unidad) in zip(ejes, medidas):
        estilo(ax, grid_x=True)
        for g, lista in datos.items():
            xs = [t[k] for _, t in lista if t.get(k) is not None]
            if not xs:
                continue
            y = filas_y[g]
            ax.scatter(xs, [y] * len(xs), s=46, color=GRUPO_COLOR[g], edgecolor=FONDO, linewidth=1.5, zorder=3, label=etiqueta[g])
            ax.plot([np.median(xs)] * 2, [y - 0.35, y + 0.35], color=GRUPO_COLOR[g], lw=2, zorder=2)
        ax.set_yticks([0, 1, 2], ["Primus", "King Gizzard", "Angine de Poitrine"], fontsize=8.5, color=TINTA)
        ax.set_ylim(-0.6, 2.9)
        ax.set_title(f"{titulo} ({unidad})", loc="center", fontsize=12, fontweight="bold", color=TINTA, pad=14)
        ax.set_xlabel(f"Eje horizontal: valor de {titulo.lower()} en {unidad}; cada punto = una canción; raya = mediana del grupo.",
                      fontsize=9, color=GRIS, labelpad=13)
    fig.suptitle("Perfil estructural del álbum frente a Primus y King Gizzard", x=0.5, y=0.98, ha="center",
                 fontsize=16, fontweight="bold", color=TINTA)
    fig.text(0.5, 0.925, "Compara cinco medidas directas de las canciones de Angine de Poitrine con Primus y King Gizzard.\n"
             "Los puntos muestran canciones individuales y las rayas verticales resumen la mediana de cada grupo.",
             ha="center", va="top", fontsize=9.5, color=GRIS, linespacing=1.25)
    handles = [plt.Line2D([0], [0], marker="o", color="none", markerfacecolor=GRUPO_COLOR[g], markeredgecolor=FONDO,
                          markersize=8, label=etiqueta[g]) for g in ("banda", "control", "comparar") if datos.get(g)]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.105), ncol=3, fontsize=9.5, frameon=False,
               title="Paleta de grupos", title_fontsize=10)
    fig.text(0.03, 0.035, "Angine de Poitrine = repertorio de referencia.  Primus = control de medición.  King Gizzard = repertorio comparado.\n"
             "La posición horizontal permite ver qué medidas son mayores o menores en la banda respecto a cada grupo.",
             ha="left", va="bottom", fontsize=9, color=GRIS, linespacing=1.25)
    fig.subplots_adjust(left=0.18, right=0.98, top=0.82, bottom=0.22, hspace=1.0)
    guardar(fig, salida + "_b_perfil.png")
    with open(salida + "_b_perfil.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["grupo", "cancion"] + [k for k, _, _ in medidas])
        for g, lista in datos.items():
            for n, t in lista:
                w.writerow([g, n] + [t.get(k) for k, _, _ in medidas])


# ---------------------------------------------------------------- (c) círculo de dos campos (Hába)
def reparto(run: Path) -> tuple[np.ndarray, np.ndarray]:
    H = json.loads((run / "armonia.json").read_text(encoding="utf-8"))
    J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
    ton = H.get("tonica_pc24") or 0
    notas = sorted(J.get("raw_high") or J.get("raw_bass") or [], key=lambda n: n["start_s"])
    alt, tr = np.zeros(24), np.zeros((24, 24))
    prev = None
    for n in notas:
        d = (round(n["midi"] * 2) - ton) % 24
        alt[d] += max(0.0, n["end_s"] - n["start_s"])
        if prev is not None and n["start_s"] - prev[1] < 0.5 and prev[0] != d:
            tr[prev[0], d] += 1
        prev = (d, n["end_s"])
    return alt, tr


def angulo(d: int) -> float:
    k = next(k for k in range(12) if (14 * k) % 24 == d - d % 2)       # posición en el ciclo de quintas de su campo
    return np.pi / 2 - 2 * np.pi * k / 12


def dibujar_circulo(ax, alt: np.ndarray, tr: np.ndarray, titulo: str, grande: bool) -> None:
    from matplotlib.patches import Circle
    ax.set_aspect("equal")
    ax.axis("off")
    R = {0: 1.0, 1: 0.68}
    for r, c in ((1.0, CAMPO_REG), (0.68, CAMPO_Q)):
        ax.add_patch(Circle((0, 0), r, fill=False, color=c, lw=1.2, alpha=0.45))
    p = alt / alt.sum() if alt.sum() else alt
    pos = {d: (R[d % 2] * np.cos(angulo(d)), R[d % 2] * np.sin(angulo(d))) for d in range(24)}
    if tr.sum():
        top = np.argsort(tr, axis=None)[::-1][:14 if grande else 8]
        mx = tr.max()
        for idx in top:
            a, b = divmod(int(idx), 24)
            if tr[a, b] <= 0:
                continue
            cruza = (a % 2) != (b % 2)
            (x0, y0), (x1, y1) = pos[a], pos[b]
            ax.plot([x0, x1], [y0, y1], color=CAMPO_Q if cruza else MUTED, lw=0.6 + 3 * tr[a, b] / mx, alpha=0.55, zorder=1)
    esc = 2600 if grande else 1440
    for d in range(24):
        x, y = pos[d]
        ax.scatter([x], [y], s=12 + esc * p[d], color=CAMPO_Q if d % 2 else CAMPO_REG, edgecolor=FONDO, linewidth=1.2, zorder=3,
                   alpha=0.95 if p[d] > 0.005 else 0.25)
        f = 1.17 if d % 2 == 0 else 0.80
        ax.text(x * f, y * f, grado24(d), ha="center", va="center", fontsize=8.5 if grande else 7.2,
                color=TINTA if p[d] >= 0.02 else MUTED, fontweight="bold" if p[d] >= 0.08 else "normal")
    cuartos = 100 * p[1::2].sum()
    ax.set_title(f"{titulo}\n¼ de tono {cuartos:.0f} %", fontsize=10.5 if grande else 8.5, color=TINTA, pad=4)
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)


def fig_circulo(runs: list[Path], salida: str) -> None:
    import matplotlib.pyplot as plt
    rs = sorted(runs, key=lambda r: orden_banda(nombre(r.name)))
    datos = [(nombre(r.name), *reparto(r)) for r in rs]
    alt_tot = sum(a / a.sum() for _, a, _ in datos if a.sum())
    tr_tot = sum(t for _, _, t in datos)
    fig = plt.figure(figsize=(16, 8.8), facecolor=FONDO)
    gs = fig.add_gridspec(2, 5, width_ratios=[3.2, 3.2, 2, 2, 2], wspace=0.34, hspace=0.55)
    dibujar_circulo(fig.add_subplot(gs[:, :2]), alt_tot, tr_tot, "Vol. II completo (media de las canciones)", True)
    for i, (n, a, t) in enumerate(datos[:6]):
        dibujar_circulo(fig.add_subplot(gs[i // 3, 2 + i % 3]), a, t, n, False)
    fig.suptitle("Círculo de quintas en 24-EDO: campos regulares y de cuarto de tono",
                 x=0.5, y=0.98, ha="center", fontsize=16, fontweight="bold", color=TINTA)
    fig.text(0.5, 0.925, "El círculo muestra cómo se reparte la melodía de Angine de Poitrine entre los dos campos de quintas de 24-EDO.\n"
             "El panel grande resume el álbum y los paneles pequeños muestran cada canción.",
             ha="center", va="top", fontsize=9.5, color=GRIS, linespacing=1.25)
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    leyenda = [
        Patch(facecolor=CAMPO_REG, edgecolor="none", label="Círculo/anillo amarillo: grados regulares"),
        Patch(facecolor=CAMPO_Q, edgecolor="none", label="Círculo/anillo azul: grados en cuarto de tono"),
        Line2D([0], [0], color=MUTED, lw=2, label="Línea gris: transición dentro de un campo"),
        Line2D([0], [0], color=CAMPO_Q, lw=2, label="Línea azul: transición entre campos"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=CAMPO_REG, markersize=10, label="Punto grande: mayor tiempo melódico en el grado"),
        Line2D([0], [0], marker="o", color="none", markerfacecolor=CAMPO_REG, alpha=0.3, markersize=5, label="Punto pequeño o tenue: menor uso del grado"),
    ]
    fig.legend(handles=leyenda, loc="lower center", bbox_to_anchor=(0.5, 0.12), ncol=2,
               frameon=False, fontsize=8.5, title="Paleta y marcas de los círculos", title_fontsize=9.5)
    fig.text(0.02, 0.035, "En 24-EDO la quinta mide 14 pasos y divide el ciclo en dos campos. Cada grado «+» está junto a su vecino regular.\n"
             "El área del punto indica tiempo melódico; las líneas muestran los pasos melódicos más frecuentes. En 19, 31 y 53-EDO hay un solo campo.",
             ha="left", va="bottom", fontsize=8.8, color=GRIS, linespacing=1.25)
    fig.subplots_adjust(left=0.03, right=0.98, top=0.82, bottom=0.30)
    guardar(fig, salida + "_c_circulo_haba.png")


# ---------------------------------------------------------------- (d) campos en el tiempo
def leer_csv(ruta: str) -> list[dict]:
    with open(ruta, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fig_campos_tiempo(compases: list[dict], salida: str) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.cm import ScalarMappable
    por = defaultdict(list)
    for c in compases:
        if c["grupo"] == "banda":
            por[c["cancion"]].append(c)
    canciones = sorted(por, key=orden_banda)
    if not canciones:
        return
    cmap = LinearSegmentedColormap.from_list("seq", SEQ)
    fig, ejes = plt.subplots(len(canciones), 1, figsize=(12, 0.95 * len(canciones) + 1.3), sharex=True, facecolor=FONDO, squeeze=False)
    for ax, n in zip(ejes[:, 0], canciones):
        estilo(ax)
        for c in por[n]:
            t0, t1 = float(c["inicio_s"]) / 60, float(c["fin_s"]) / 60
            q = float(c["cuartos"] or 0)
            ax.add_patch(plt.Rectangle((t0, 0), t1 - t0, 0.6, color=cmap(min(q / 0.6, 1)), lw=0))
            if c["mezcla"] not in ("", None):
                m = float(c["mezcla"])
                ax.add_patch(plt.Rectangle((t0, 0.68), t1 - t0, 0.32 * min(m / 0.5, 1), color=TINTA, lw=0, alpha=0.75))
        ax.set_ylim(0, 1.02)
        ax.set_yticks([])
        ax.set_ylabel(n, rotation=0, ha="right", va="center", fontsize=9, color=TINTA)
        ax.spines["left"].set_visible(False)
    ejes[-1, 0].set_xlabel("minuto", fontsize=9, color=GRIS)
    ejes[-1, 0].set_xlim(0, max(float(c["fin_s"]) for v in por.values() for c in v) / 60)
    sm = ScalarMappable(cmap=cmap)
    sm.set_clim(0, 60)
    cb = fig.colorbar(sm, ax=ejes[:, 0], orientation="horizontal", fraction=0.025, pad=0.12, aspect=50)
    cb.set_label("% del compás con cuarto de tono (franja de color); barra negra = mezcla vertical de campos (alto = 50 % o más)", fontsize=8, color=GRIS)
    cb.ax.tick_params(labelsize=7.5, colors=GRIS)
    fig.suptitle("Uso temporal de cuartos de tono y mezcla de campos", x=0.01, ha="left", fontsize=11, color=TINTA)
    guardar(fig, salida + "_d_campos_tiempo.png")


# ---------------------------------------------------------------- (e) resumen de las pruebas de campos
def fig_campos_resumen(filas: list[dict], salida: str, alfa: float) -> None:
    import matplotlib.pyplot as plt
    num = lambda x: None if x in ("", None) else float(x)
    for f in filas:
        v, z = num(f["mezcla_vertical"]), num(f["mezcla_nula"])
        f["reduccion"] = None if not z else 100 * (z - v) / z
        cp, rp = num(f.get("cuartos_en_pulso")), num(f.get("regulares_en_pulso"))
        f["dif"] = None if cp is None or rp is None else cp - rp
    paneles = [("reduccion", "Mezcla vertical evitada frente al azar (%)", "p_mezcla"),
               ("paso_cuarto", "Pasos de ¼ de tono entre los que tocan un ¼ (%)", None),
               ("dif", "¼ en el pulso − regulares en el pulso (puntos)", "p_pulso")]
    grupos = [("banda", "Vol. II"), ("comparar", "King Gizzard"), ("control", "Primus")]
    fig, ejes = plt.subplots(1, 3, figsize=(13, 4.6), facecolor=FONDO)
    for ax, (k, titulo, pk) in zip(ejes, paneles):
        estilo(ax, grid_x=True)
        piso = [num(f[k]) if k in ("paso_cuarto",) else f[k] for f in filas if f["grupo"] == "control"]
        piso = [x for x in piso if x is not None]
        if piso:
            ax.axvspan(min(piso), max(piso), color=GRUPO_COLOR["control"], alpha=0.10, lw=0)
        y = 0
        ticks = []
        for g, et in grupos:
            fs = sorted([f for f in filas if f["grupo"] == g], key=lambda f: orden_banda(f["cancion"]) if g == "banda" else f["cancion"])
            for f in fs:
                x = num(f[k]) if k == "paso_cuarto" else f[k]
                if x is None:
                    continue
                p = num(f.get(pk)) if pk else None
                lleno = pk is None or (p is not None and p < alfa)
                ax.scatter([x], [y], s=42, color=GRUPO_COLOR[g] if lleno else FONDO, edgecolor=GRUPO_COLOR[g], linewidth=1.6, zorder=3)
                ticks.append((y, f["cancion"][:18]))
                y += 1
            y += 0.8
        ax.set_yticks([t for t, _ in ticks], [n for _, n in ticks], fontsize=7.5, color=TINTA)
        ax.invert_yaxis()
        ax.set_title(titulo, loc="left", fontsize=9.5, color=TINTA)
        if k == "dif":
            ax.axvline(0, color=MUTED, lw=1)
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=GRUPO_COLOR[g], label=et) for g, et in grupos] + \
        [Line2D([], [], marker="o", ls="", markerfacecolor=FONDO, markeredgecolor=GRIS, label=f"no significativo (p ≥ {alfa:g})")]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(0.01, 0.94), ncol=4, fontsize=8, frameon=False)
    fig.suptitle("Separación de los campos de Hába: tres pruebas frente al control", x=0.01, ha="left",
                 fontsize=11, color=TINTA)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    guardar(fig, salida + "_e_campos_resumen.png")


# ---------------------------------------------------------------- (f) bucle contra compás
def fig_bucle(fases: list[dict], salida: str, extra: list[str]) -> None:
    import matplotlib.pyplot as plt
    por = defaultdict(list)
    for f in fases:
        por[f["cancion"]].append(f)
    canciones = sorted([n for n in por if orden_banda(n) < len(ORDEN)], key=orden_banda) + \
        [n for n in por if any(n.lower().startswith(e.lower()) for e in extra)]
    if not canciones:
        return
    col_pulsos = {3: "#1baf7a", 4: "#2a78d6", 5: "#e87ba4", 6: "#eda100", 7: "#eb6834", 8: "#6250d6"}
    nc = 2
    nr = (len(canciones) + 1) // 2
    fig, ejes = plt.subplots(nr, nc, figsize=(13.5, 3.6 * nr + 3.0), facecolor=FONDO, squeeze=False)
    for ax, n in zip(ejes.flat, canciones):
        estilo(ax, grid_y=True)
        L = int(por[n][0]["bucle_corcheas"])
        for f in por[n]:
            if f["fase"] == "":
                continue
            p = int(f["pulsos"])
            ax.scatter(float(f["inicio_s"]) / 60, int(f["fase"]) / L, s=14, color=col_pulsos.get(p, MUTED), lw=0)
        ax.set_ylim(-0.05, 1.05)
        ax.set_yticks([0, 0.5, 1], ["0", "½", "1"], fontsize=7.5)
        ax.set_title(f"{n} · bucle de {L} corcheas ({L / 2:g} pulsos)", loc="center", fontsize=10.5, fontweight="bold", color=TINTA, pad=12)
        ax.set_ylabel("Fase del riff / longitud del bucle", fontsize=8.5, color=GRIS, labelpad=12)
        ax.set_xlabel("Tiempo desde el inicio de la canción (min)", fontsize=8.5, color=GRIS, labelpad=12)
    for ax in list(ejes.flat)[len(canciones):]:
        ax.axis("off")
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=c, label=f"compás de {p}") for p, c in col_pulsos.items()]
    fig.suptitle("Fase del riff al inicio de cada compás", x=0.5, y=0.98, ha="center",
                 fontsize=16, fontweight="bold", color=TINTA)
    fig.text(0.5, 0.945, "La fase indica en qué punto del bucle comienza cada compás de la banda.\n"
             "Una fase fija o escalonada ayuda a distinguir sincronía, polimetría y cambios de entrada del riff.",
             ha="center", va="top", fontsize=9.5, color=GRIS, linespacing=1.25)
    fig.text(0.02, 0.095, "Fase fija = el compás mide lo mismo que el bucle o lo divide.\n\n"
             "Fase en escalera = compás y bucle tienen longitudes distintas.\n\n"
             "Salto aislado = el riff vuelve a entrar por otro punto tras un silencio.\n\n"
             "Sin punto = fase ambigua o poco sonido.", fontsize=8.8, color=GRIS, linespacing=1.2, va="bottom")
    fig.legend(handles=h, loc="lower right", bbox_to_anchor=(0.98, 0.075), ncol=3, fontsize=8.5, frameon=False,
               title="Color = pulsos del compás", title_fontsize=9.5)
    fig.subplots_adjust(left=0.13, right=0.98, top=0.84, bottom=0.25, wspace=0.45, hspace=0.95)
    guardar(fig, salida + "_f_bucle_compas.png")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--control", nargs="*", type=Path, default=[])
    ap.add_argument("--comparar", nargs="*", type=Path, default=[])
    ap.add_argument("--bloques", help="json de verosimilitud_por_bloques.py")
    ap.add_argument("--campos", help="prefijo de salida de campos_haba.py (sin extensión)")
    ap.add_argument("--fases", help="<salida>_fases.csv de ciclos_metricos.py")
    ap.add_argument("--extra-bucle", nargs="*", default=["Flying microtonal banana", "Doom city"], help="temas comparados a incluir en (f)")
    ap.add_argument("--alfa", type=float, default=0.003, help="umbral de p (≈ Bonferroni para ~18 canciones)")
    ap.add_argument("--salida", default="outputs/figuras_album")
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.family"] = "DejaVu Sans"

    runs = {"banda": sorted(unicas(a.corridas), key=lambda r: orden_banda(nombre(r.name))), "comparar": unicas(a.comparar), "control": unicas(a.control)}
    print("Vol. II:", ", ".join(nombre(r.name) for r in runs["banda"]))
    if a.bloques and Path(a.bloques).exists():
        fig_clasificacion(json.loads(Path(a.bloques).read_text(encoding="utf-8")), a.salida)
    fig_perfil(runs, a.salida)
    fig_circulo(runs["banda"], a.salida)
    if a.campos and Path(a.campos + "_compases.csv").exists():
        fig_campos_tiempo(leer_csv(a.campos + "_compases.csv"), a.salida)
    if a.campos and Path(a.campos + ".csv").exists():
        fig_campos_resumen(leer_csv(a.campos + ".csv"), a.salida, a.alfa)
    if a.fases and Path(a.fases).exists():
        fig_bucle(leer_csv(a.fases), a.salida, a.extra_bucle)


if __name__ == "__main__":
    main()
