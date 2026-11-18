"""¿Cómo usa la banda los cuartos de tono en la melodía: como adorno o como grado de su escala?

Uso:
    python scripts/microtonal.py outputs/<corrida> [...] --salida outputs/microtonal

Lee line_diagnostics.json (la voz aguda) y armonia.json (tónica, compases y ciclos) de cada corrida. Escribe
<salida>.json, <salida>.csv, <salida>_uso.png (adorno frente a grado, por canción) y <salida>_escalas.png (la «escala»
de 24 notas de cada canción como un círculo: cuánto tiempo suena cada grado; los cuartos de tono en color).

Cada nota en cuarto de tono (fuera de los 12 semitonos) se clasifica:
- Inflexión (adorno): dura menos que la nota mediana de la canción y llega o sale por un paso de ¼ de tono hacia una nota
  de los 12 semitonos (un bend, un slide, una nota de paso).
- Grado (estructural): todo lo demás: dura lo que una nota normal, o se llega y se sale por saltos.
Concentración: % del tiempo en cuartos de tono que cae en los dos grados más usados. Si es alta, los cuartos de tono son
grados elegidos de la escala de la canción; si están repartidos por igual entre muchos grados, son desafinación o adorno.
Además, para cada grado en cuarto de tono, qué tanto se repite: % de las vueltas del ciclo principal de la voz aguda en
que aparece (si un grado vuelve en casi todas las vueltas, es parte fija del motivo, no un accidente).

Piso de ruido: en canciones sin cuartos de tono (Primus) el cuaderno marca 9-13 % del tiempo en cuartos de tono, casi
todo como inflexión (bends, vibrato, slides). Lo que sube por encima de eso, sobre todo como grado, es de la banda.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

GRADOS24 = ["1", "1+", "♭2", "♭2+", "2", "2+", "♭3", "♭3+", "3", "3+", "4", "4+", "♯4", "♯4+", "5", "5+", "♭6", "♭6+", "6", "6+",
            "♭7", "♭7+", "7", "7+"]


def nombre(corrida: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", corrida)
    n = re.sub(r"(angine_de_poitrine_|primus_|_audio_off\w*|_official_audio|_repro|_cache|_\d{4}_\w+$)", "", n)
    return n.replace("_", " ").strip().capitalize()


def medir(run: Path) -> dict:
    J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
    H = json.loads((run / "armonia.json").read_text(encoding="utf-8"))
    ton = H.get("tonica_pc24") or 0
    notas = sorted(((n["start_s"], n["end_s"], round(n["midi"] * 2)) for n in J["raw_high"]), key=lambda x: x[0])
    if not notas:
        return dict(corrida=run.name, cancion=nombre(run.name), notas=0)
    durs = sorted(e - a for a, e, q in notas)
    mediana = durs[len(durs) // 2]
    total = sum(durs) or 1.0
    tiempo = Counter()
    infl = grado = 0.0
    n_infl = n_grado = 0
    for i, (a, e, q) in enumerate(notas):
        g = (q - ton) % 24
        tiempo[g] += e - a
        if q % 2 == 0:
            continue
        cerca = lambda j: 0 <= j < len(notas) and abs(notas[j][2] - q) == 1 and notas[j][2] % 2 == 0 and \
            (abs(notas[j][0] - e) < 0.12 if j > i else abs(a - notas[j][1]) < 0.12)
        if (e - a) < mediana and (cerca(i - 1) or cerca(i + 1)):
            infl += e - a
            n_infl += 1
        else:
            grado += e - a
            n_grado += 1

    # repetición en el ciclo principal de la voz aguda (o de la grave si la aguda no tiene)
    pat = (H.get("resumen") or {}).get("patrones") or {}
    principal = None
    for voz in ("Voz aguda", "Voz grave"):
        for x in (pat.get(voz) or {}).values():
            if x.get("segmentos") and (principal is None or x.get("vueltas", 0) > principal.get("vueltas", 0)):
                principal = x
        if principal:
            break
    persist = {}
    if principal:
        vueltas = []
        for s in principal["segmentos"]:
            a0, a1, per = s[0], s[1], (s[2] if len(s) > 2 else principal["periodo_s"])
            t = a0
            while t + per <= a1 + 0.05:
                vueltas.append((t, t + per))
                t += per
        presencia = defaultdict(int)
        for t0, t1 in vueltas:
            for g in {(q - ton) % 24 for a, e, q in notas if t0 <= a < t1 and q % 2}:
                presencia[g] += 1
        if vueltas:
            persist = {GRADOS24[g]: round(100 * v / len(vueltas), 1) for g, v in sorted(presencia.items(), key=lambda kv: -kv[1])[:5]}
    micro = infl + grado
    top = sorted((tiempo[g] for g in tiempo if g % 2), reverse=True)
    conc = 100 * sum(top[:2]) / micro if micro else 0.0
    return dict(corrida=run.name, cancion=nombre(run.name), notas=len(notas), centro=(H.get("resumen") or {}).get("centro"),
                cuartos_de_tono=round(100 * micro / total, 1), como_inflexion=round(100 * infl / total, 1), como_grado=round(100 * grado / total, 1),
                notas_inflexion=n_infl, notas_grado=n_grado, concentracion_dos_grados=round(conc, 1),
                grados_en_cuarto=[{"grado": GRADOS24[g], "tiempo": round(100 * tiempo[g] / total, 1)}
                                  for g in sorted((g for g in tiempo if g % 2), key=lambda g: -tiempo[g])[:5]],
                repeticion_en_el_ciclo=persist, vueltas_del_ciclo=len(vueltas) if principal else 0,
                escala24={GRADOS24[g]: round(100 * tiempo[g] / total, 2) for g in range(24)})


def dibujar(filas: list[dict], salida: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    tinta, gris, fondo, rejilla = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"
    azul, naranja = "#2a78d6", "#eb6834"
    # 1) uso: barras apiladas horizontales (inflexión / grado), con la franja del piso de ruido
    fig, ax = plt.subplots(figsize=(10, 1.6 + 0.6 * len(filas)), facecolor=fondo)
    y = list(range(len(filas)))[::-1]
    ax.axvspan(9, 13, color=rejilla, zorder=0)
    ax.text(11, len(filas) - 0.35, "piso de ruido\n(9-13 %)", ha="center", va="bottom", fontsize=8, color=gris)
    ax.barh(y, [f["como_grado"] for f in filas], color=naranja, height=0.6, label="como grado (estructural)")
    ax.barh(y, [f["como_inflexion"] for f in filas], left=[f["como_grado"] for f in filas], color="#f5b48f", height=0.6,
            label="como inflexión (adorno)")
    for yi, f in zip(y, filas):
        g2 = " y ".join(x["grado"] for x in f["grados_en_cuarto"][:2])
        ax.text(f["cuartos_de_tono"] + 0.5, yi, f"{f['cuartos_de_tono']:g} %  ·  {f['concentracion_dos_grados']:g} % en {g2}", va="center", fontsize=9,
                color=tinta)
    ax.set_yticks(y, [f["cancion"] for f in filas], fontsize=10)
    ax.set_xlabel("% del tiempo de la melodía en cuartos de tono", color=gris, fontsize=9)
    ax.set_xlim(0, max(f["cuartos_de_tono"] for f in filas) * 1.75)
    ax.set_title("Uso estructural de los cuartos de tono en la melodía", loc="left", fontsize=12, color=tinta)
    ax.legend(frameon=False, fontsize=9, loc="lower right")
    ax.set_facecolor(fondo)
    ax.tick_params(colors=gris, length=0)
    ax.grid(axis="x", color=rejilla, lw=0.8)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    fig.savefig(salida + "_uso.png", dpi=200, facecolor=fondo)
    plt.close(fig)

    # 2) escalas de 24 notas: un círculo por canción
    n = len(filas)
    cols = min(n, 4)
    filas_g = (n + cols - 1) // cols
    fig = plt.figure(figsize=(4.2 * cols, 4.6 * filas_g + 0.6), facecolor=fondo)
    ang = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    for k, f in enumerate(filas):
        ax = fig.add_subplot(filas_g, cols, k + 1, polar=True)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        v = np.array([f["escala24"][g] for g in GRADOS24])
        ax.bar(ang, np.sqrt(v), width=2 * np.pi / 24 * 0.85, color=[naranja if i % 2 else azul for i in range(24)], alpha=0.9)
        ax.set_xticks(ang, [g if i % 2 == 0 else "" for i, g in enumerate(GRADOS24)], fontsize=8, color=tinta)
        ax.set_yticks([])
        ax.set_facecolor(fondo)
        ax.spines["polar"].set_color(rejilla)
        ax.grid(color=rejilla, lw=0.6)
        ax.set_title(f"{f['cancion']} · centro {f.get('centro') or '—'}", fontsize=11, color=tinta, pad=14)
    fig.suptitle("Escalas melódicas en 24-EDO: distribución temporal por grado", x=0.02, ha="left", fontsize=12, color=tinta)
    fig.text(0.02, 0.01, "Radio = raíz del porcentaje de tiempo en cada grado; azul = grado regular y naranja = cuarto de tono.", fontsize=8, color=gris)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(salida + "_escalas.png", dpi=200, facecolor=fondo)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--salida", default="outputs/microtonal")
    a = ap.parse_args()
    filas = []
    for run in a.corridas:
        if not (run / "line_diagnostics.json").exists() or not (run / "armonia.json").exists():
            print(f"faltan archivos: {run.name}")
            continue
        f = medir(run)
        filas.append(f)
        print(json.dumps({k: v for k, v in f.items() if k not in ("escala24", "corrida")}, ensure_ascii=False))
    Path(a.salida + ".json").write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(a.salida + ".csv", "w", newline="", encoding="utf-8") as fh:
        campos = ["cancion", "centro", "cuartos_de_tono", "concentracion_dos_grados", "como_grado", "como_inflexion", "notas_grado", "notas_inflexion", "vueltas_del_ciclo"]
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(filas)
    dibujar(filas, a.salida)


if __name__ == "__main__":
    main()
