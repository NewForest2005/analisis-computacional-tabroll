"""Radar de la estructura rítmica de una canción: rasgos rítmicos de 0 a 100 (no parecido medido con un estilo).

Uso:
    python scripts/radar_ritmico.py outputs/<corrida> [...] [--titulo "Fabienk"]

Lee armonia.json (compases y ciclos) y line_diagnostics.json (tempo y notas de la voz aguda). Escribe radar_ritmico.png
y radar_ritmico.json en la carpeta de la corrida. Con varias corridas, además dibuja un perfil mediano por banda en
outputs/radar_ritmico_comparado.png (o en --salida).

No hay cifras publicadas de ritmo para math rock, minimalismo ni techno: cada punta es un rasgo, y el estilo asociado
va entre paréntesis solo como guía. Los compases son los que detecta el cuaderno, sin validar contra la partitura.

Puntas:
- Compás irregular (math rock, prog): % del tiempo en compases de 5 o 7 pulsos (o 9, 11, 13).
- Compás cambiante (math rock): % de compases cuya cantidad de pulsos es distinta a la del anterior.
- Compás de 4 (rock, pop): % del tiempo en compases de 4 pulsos.
- Ostinato (loops, techno): % del tiempo dentro de ciclos repetidos (voz grave o aguda, la que tenga más).
- Ciclos de largo desigual (fase, polirritmia): cuántos largos de ciclo distintos (más de 5 % de diferencia) suenan a la
  vez en algún momento, 1 → 0, 3 o más → 100.
- Capas (minimalismo aditivo, techno): entradas de patrones de ciclo por minuto; 4 por minuto → 100.
- Síncopa (funk, jazz): % de ataques de la voz aguda en posición débil (contratiempo o semicorchea) que se sostienen sobre la
  siguiente posición más fuerte sin que haya un ataque ahí (Longuet-Higgins y Lee 1984, simplificado), con el retraso
  medio de los ataques corregido.
- Pulso constante (minimalismo, techno): 100 − 10 × el coeficiente de variación (%) de la duración del pulso.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path


def recorta(x: float) -> float:
    return round(max(0.0, min(100.0, x)), 1)


def medir(run: Path) -> dict:
    H = json.loads((run / "armonia.json").read_text(encoding="utf-8"))
    J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
    bpm = J.get("tempo_bpm") or 120.0
    pulso = 60.0 / bpm
    bars = sorted(H["compases"], key=lambda b: b["inicio_s"])
    dur = [b["fin_s"] - b["inicio_s"] for b in bars]
    pulsos = [max(1, round(d / pulso)) for d in dur]
    total = sum(dur) or 1.0

    irregular = sum(d for d, n in zip(dur, pulsos) if n in (5, 7, 9, 11, 13)) / total
    cuatro = sum(d for d, n in zip(dur, pulsos) if n == 4) / total
    cambia = sum(1 for a, b in zip(pulsos, pulsos[1:]) if a != b) / max(len(pulsos) - 1, 1)
    # pulso constante: duración de un pulso en cada compás
    por_pulso = [d / n for d, n in zip(dur, pulsos)]
    m = sum(por_pulso) / len(por_pulso)
    cv = 100 * math.sqrt(sum((x - m) ** 2 for x in por_pulso) / len(por_pulso)) / m if m else 0.0

    # ciclos
    pat = (H.get("resumen") or {}).get("patrones") or {}
    largo = max(b["fin_s"] for b in bars) - min(b["inicio_s"] for b in bars)
    segs = []                                                            # (inicio, fin, periodo, voz)
    for voz, d in pat.items():
        for x in d.values():
            for s in x.get("segmentos") or []:
                segs.append((s[0], s[1], s[2] if len(s) > 2 else x.get("periodo_s"), voz))
    en_ciclo = 0.0
    for voz in pat:
        en_ciclo = max(en_ciclo, sum(e - a for a, e, p, v in segs if v == voz))
    distintos = 1
    for t in [a + 0.01 for a, e, p, v in segs]:
        ps = sorted(p for a, e, p, v in segs if a <= t < e and p)
        grupos = []
        for p in ps:
            if not grupos or p > grupos[-1] * 1.05:
                grupos.append(p)
        distintos = max(distintos, len(grupos))
    entradas_min = len(segs) / (largo / 60) if largo else 0.0

    # síncopa (Longuet-Higgins y Lee 1984, simplificada): cada ataque va a la semicorchea más cercana de su compás, con
    # el retraso medio de la canción corregido. Peso métrico: tiempo 0, corchea a contratiempo −1, semicorchea −2. Hay
    # síncopa cuando un ataque en posición débil no tiene ataque en la siguiente posición más fuerte (la nota «se
    # sostiene» sobre ella); vale la diferencia de pesos. Se informa el % de ataques sincopados.
    fases = []
    k = 0
    for nota in J["raw_high"]:
        t = nota["start_s"]
        while k + 1 < len(bars) and bars[k]["fin_s"] <= t:
            k += 1
        b = bars[k]
        if b["inicio_s"] <= t < b["fin_s"]:
            fases.append((k, (t - b["inicio_s"]) / ((b["fin_s"] - b["inicio_s"]) / pulsos[k])))
    retraso = 0.0
    if fases:
        ang = [2 * math.pi * 4 * (x % 1) for _, x in fases]
        retraso = math.atan2(sum(math.sin(v) for v in ang), sum(math.cos(v) for v in ang)) / (2 * math.pi * 4)
    pos = set()
    for k_, x in fases:
        pos.add((k_, round((x - retraso) * 4)))                          # (compás, semicorchea)
    peso = lambda s16: 0 if s16 % 4 == 0 else -1 if s16 % 2 == 0 else -2
    sinc = n = 0
    for k_, s16 in pos:
        n += 1
        siguiente = s16 + 1 if peso(s16) == -2 else s16 + 2 if peso(s16) == -1 else None
        if siguiente is None:
            continue
        kk, ss = (k_, siguiente) if siguiente < 4 * pulsos[k_] else (k_ + 1, 0)
        if (kk, ss) not in pos and (k_, s16 + 1) not in pos:
            sinc += 1
    cuenta = Counter(pulsos)
    r = dict(corrida=run.name, tempo_bpm=round(bpm, 1), compases=len(bars),
             pulsos_por_compas={str(k_): round(100 * v / len(pulsos), 1) for k_, v in cuenta.most_common(5)},
             ciclos=len(segs), largos_de_ciclo_a_la_vez=distintos, variacion_del_pulso_pct=round(cv, 1))
    r["rasgos"] = {"Compás irregular\n(math rock, prog)": recorta(100 * irregular),
                   "Compás cambiante\n(math rock)": recorta(100 * cambia),
                   "Compás de 4\n(rock, pop)": recorta(100 * cuatro),
                   "Ostinato\n(loops, techno)": recorta(100 * en_ciclo / largo) if largo else 0.0,
                   "Ciclos de largo desigual\n(fase, polirritmia)": recorta(50 * (distintos - 1)),
                   "Capas\n(minimalismo aditivo)": recorta(25 * entradas_min),
                   "Síncopa\n(funk, jazz)": recorta(100 * sinc / n) if n else 0.0,
                   "Pulso constante\n(minimalismo, techno)": recorta(100 - 10 * cv)}
    return r


COLORES = ["#1baf7a", "#2a78d6", "#eb6834", "#eda100", "#e87ba4", "#6250d6", "#008300", "#e34948"]


def nombre(corrida: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", corrida)
    n = re.sub(r"(angine_de_poitrine_|primus_|_audio_off\w*|_official_audio|_repro|_\d{4}_\w+$)", "", n)
    return n.replace("_", " ").strip().capitalize()


def artista(corrida: str) -> str:
    """Agrupa cada corrida por la banda que la originó para las comparaciones."""
    n = corrida.lower()
    if "angine_de_poitrine" in n or "sarniezz" in n or "angor" in n:
        return "Angine de Poitrine"
    if "primus" in n:
        return "Primus"
    if "king_gizzard" in n or "kinggizzard" in n:
        return "King Gizzard"
    if "king_crimson" in n or "kingcrimson" in n:
        return "King Crimson"
    if "gentle_giant" in n or "gentlegiant" in n:
        return "Gentle Giant"
    if "zappa" in n or "g_spot" in n or "inca_roads" in n or "peaches" in n or "black_page" in n or "zomby" in n:
        return "Frank Zappa"
    if "fabienk" in n:
        return "Fabienk"
    if "mata_zyklek" in n or "matazyklek" in n:
        return "Mata Zyklek"
    if "yor_zarad" in n or "yorzarad" in n:
        return "Yor Zarad"
    if "utzp" in n:
        return "Utzp"
    return nombre(corrida)


def agrupar_por_artista(filas: list[dict]) -> list[dict]:
    """Devuelve un perfil mediano por artista, evitando superponer cada canción."""
    grupos = {}
    for f in filas:
        grupos.setdefault(artista(f["corrida"]), []).append(f)
    perfiles = []
    for banda, canciones in grupos.items():
        rasgos = {
            rasgo: round(sorted(f["rasgos"][rasgo] for f in canciones)[len(canciones) // 2], 1)
            for rasgo in canciones[0]["rasgos"]
        }
        perfiles.append({"corrida": banda, "rasgos": rasgos, "canciones": len(canciones)})
    return perfiles


def dibujar(filas: list[dict], salida: Path, titulo: str, sub: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    tinta, gris, rejilla, fondo = "#0b0b0b", "#52514e", "#d9d8d2", "#fcfcfb"
    nombres = list(filas[0]["rasgos"])
    ang = np.linspace(0, 2 * np.pi, len(nombres), endpoint=False)
    fig = plt.figure(figsize=(9.5, 9.5), facecolor=fondo)
    ax = fig.add_axes([0.2, 0.13, 0.6, 0.55], polar=True)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_facecolor(fondo)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100], ["25", "50", "75", "100"], fontsize=7.5, color=gris)
    ax.set_rlabel_position(180 / len(nombres))
    ax.set_xticks(ang, [""] * len(nombres))
    ax.grid(color=rejilla, lw=0.9)
    ax.spines["polar"].set_color(rejilla)
    cierre = np.append(ang, ang[0])
    comparada = len(filas) > 1
    perfiles = agrupar_por_artista(filas) if comparada else filas
    una = len(perfiles) == 1
    for i, f in enumerate(perfiles):
        vals = list(f["rasgos"].values())
        c = COLORES[i % len(COLORES)]
        ax.fill(cierre, vals + vals[:1], color=c, alpha=0.22 if una else 0.07)
        etiqueta = f["corrida"] if not comparada else f'{f["corrida"]} ({f["canciones"]} canciones)'
        ax.plot(cierre, vals + vals[:1], color=c, lw=2, label=etiqueta)
        ax.scatter(ang, vals, s=36 if una else 18, color=c, zorder=3, edgecolors=fondo, linewidths=1.2)
        if una:
            for a, v in zip(ang, vals):
                ax.text(a, v + 10 if v < 80 else v - 13, f"{v:g}", ha="center", va="center", fontsize=9.5, color=c, fontweight="bold",
                        bbox=dict(fc=fondo, ec="none", pad=1.2))
    for a, n in zip(ang, nombres):
        ha = "center" if abs(math.sin(a)) < 0.2 else "left" if math.sin(a) > 0 else "right"
        va = "bottom" if math.cos(a) > 0.5 else "top" if math.cos(a) < -0.5 else "center"
        ax.text(a, 108, n, ha=ha, va=va, fontsize=10, color=tinta, fontweight="bold", linespacing=1.1)
    if not una:
        fig.legend(*ax.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.04, 0.84),
                   frameon=False, fontsize=9.5, title="Color por banda", title_fontsize=10)
    fig.text(0.5, 0.955, f"{titulo}: perfil de estructura rítmica", ha="center", fontsize=19,
             fontweight="bold", color=tinta)
    fig.text(0.5, 0.91, "Cada color representa una banda; en la comparación se muestra la mediana de sus canciones.\n"
             "Los valores indican cuánto presenta cada canción o banda de cada rasgo rítmico.",
             ha="center", fontsize=10.5, color=gris, linespacing=1.35)
    fig.text(0.5, 0.018, "Escala radial: 0–100; cada punto marca el valor de un rasgo rítmico.\n"
             "La distancia al centro indica su intensidad; los compases son los detectados en el audio.",
             fontsize=9.5, color=gris, ha="center", linespacing=1.25)
    fig.savefig(salida, dpi=200, facecolor=fondo)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--titulo")
    ap.add_argument("--salida", type=Path, help="imagen comparada (por defecto outputs/radar_ritmico_comparado.png)")
    a = ap.parse_args()
    filas = []
    for run in a.corridas:
        if not (run / "armonia.json").exists():
            print(f"sin armonia.json: {run.name}")
            continue
        r = medir(run)
        filas.append(r)
        limpio = {k.replace("\n", " "): v for k, v in r["rasgos"].items()}
        (run / "radar_ritmico.json").write_text(json.dumps({**r, "rasgos": limpio}, ensure_ascii=False, indent=1), encoding="utf-8")
        titulo = a.titulo if a.titulo and len(a.corridas) == 1 else nombre(run.name)
        dibujar([r], run / "radar_ritmico.png", titulo, f"Estructura rítmica · {r['tempo_bpm']:g} BPM · {r['compases']} compases")
        print(run.name + ": " + json.dumps(limpio, ensure_ascii=False))
    if len(filas) > 1:
        sal = a.salida or (a.corridas[0].parent / "radar_ritmico_comparado.png")
        dibujar(filas, sal, a.titulo or "Estructura rítmica comparada", "Comparación de perfiles rítmicos por banda")
        print(f"comparado: {sal}")


if __name__ == "__main__":
    main()
