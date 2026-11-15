"""Radar de la estructura rítmica de una canción: rasgos rítmicos de 0 a 100 (no parecido medido con un estilo).

Uso:
    python scripts/radar_ritmico.py outputs/<corrida> [...] [--titulo "Fabienk"]

Lee armonia.json (compases y ciclos) y line_diagnostics.json (tempo y notas de la voz aguda). Escribe radar_ritmico.png
y radar_ritmico.json en la carpeta de la corrida. Con varias corridas, además dibuja todas superpuestas en
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


def dibujar(filas: list[dict], salida: Path, titulo: str, sub: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    tinta, gris, rejilla, fondo = "#0b0b0b", "#52514e", "#d9d8d2", "#fcfcfb"
    nombres = list(filas[0]["rasgos"])
    ang = np.linspace(0, 2 * np.pi, len(nombres), endpoint=False)
    fig = plt.figure(figsize=(9.5, 9.5), facecolor=fondo)
    ax = fig.add_axes([0.2, 0.14, 0.6, 0.6], polar=True)
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
    una = len(filas) == 1
    for i, f in enumerate(filas):
        vals = list(f["rasgos"].values())
        c = COLORES[i % len(COLORES)]
        ax.fill(cierre, vals + vals[:1], color=c, alpha=0.22 if una else 0.07)
        ax.plot(cierre, vals + vals[:1], color=c, lw=2, label=nombre(f["corrida"]))
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
        ax.legend(loc="upper left", bbox_to_anchor=(-0.32, 1.2), frameon=False, fontsize=9.5)
    fig.text(0.05, 0.955, titulo, fontsize=17, fontweight="bold", color=tinta)
    fig.text(0.05, 0.92, sub, fontsize=10, color=gris)
    fig.text(0.05, 0.025, "Rasgos rítmicos de 0 a 100 (ver el script). Entre paréntesis, el estilo al que se asocia cada rasgo: no hay cifras publicadas\n"
             "para medir el parecido. Compases detectados por el cuaderno, sin validar contra la partitura.", fontsize=8, color=gris)
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
        dibujar(filas, sal, a.titulo or "Estructura rítmica", f"{len(filas)} canciones superpuestas")
        print(f"comparado: {sal}")


if __name__ == "__main__":
    main()
