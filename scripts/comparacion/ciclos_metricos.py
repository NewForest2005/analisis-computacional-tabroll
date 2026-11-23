"""Tramos de compás y ciclos métricos largos de una corrida, para saber dónde escuchar y si hay ciclos de más de 8 tiempos.

Uso:
    python scripts/comparacion/ciclos_metricos.py outputs/<corrida> [...] [--max 40] [--ventana 30] [--salida outputs/ciclos_metricos]

El cuaderno parte la canción en compases de 2 a 8 pulsos (BAR_LENGTHS). Un ciclo más largo, por ejemplo uno de 19
corcheas o de 19 pulsos, sale partido en trozos (4 + 4 + 4 + 7, 7 + 7 + 5…). Este script:

1. Lista los tramos seguidos de compases con el mismo número de pulsos, con su minuto de inicio y fin: es la guía para
   escuchar («de 1:05 a 2:07 hay 18 compases de 7»).
2. Busca en la secuencia de compases un patrón que se repite (por ejemplo 4-4-4-7 tres veces o más) y da su suma en
   pulsos: un ciclo largo escondido detrás de un compás «cambiante».
3. Mide, en una rejilla de corcheas, cuánto se repite la música a cada distancia ℓ (de 2 a --max corcheas): la misma
   clase de cuarto de tono en la voz aguda y los mismos ataques ℓ corcheas después. Es la diagonal de una matriz de
   autosimilitud por desfase, como en la búsqueda de ciclos del cuaderno, pero en tiempo musical y con ciclos largos.
   Lo hace en toda la canción y en ventanas de --ventana segundos, para ver dónde cambia el ciclo.
Un ciclo de L corcheas que sea el verdadero da un pico en L y en sus múltiplos, y no en los periodos de los trozos.

4. (v2) Bucle contra compás. Toma el ciclo del riff L* (el mejor periodo de toda la canción), arma la plantilla del
   bucle (la clase de cuarto de tono más frecuente en cada una de sus L* posiciones) y, en cada compás, busca en qué
   punto del bucle cae su primer tiempo (la rotación que mejor encaja con lo que suena). Si el compás mide lo mismo que
   el bucle, la fase queda fija; si la fase avanza siempre lo mismo compás a compás, el compás y el bucle tienen largos
   distintos (polímetro, como propone Mathemusique, o compás mal leído); un salto aislado de fase tras un silencio es una
   rotación del bucle (el riff vuelve a entrar por otro punto).

Escribe <salida>.md (las tablas), <salida>_fases.csv (fase de cada compás) y <salida>.png (perfil de repetición).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estilo_figuras  # noqa: E402


def nombre(run: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", run)
    n = re.sub(r"(angine_de_poitrine_|king_gizzard(_and_the_lizard_wizard)?_|king_crimson_|gentle_giant_|primus_|_audio_off\w*|_official_audio|_repro|_cache)", "", n)
    return n.replace("_", " ").strip().capitalize()


def artista(run: str) -> str:
    return estilo_figuras.artista(run)


def mmss(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:04.1f}"


def compases(run: Path) -> tuple[list[dict], float]:
    H = json.loads((run / "armonia.json").read_text(encoding="utf-8"))
    J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
    bpm = float(J.get("tempo_bpm") or 120.0)
    pulso = 60.0 / bpm
    out = []
    for b in H["compases"]:
        d = b["fin_s"] - b["inicio_s"]
        out.append(dict(n=b.get("compas"), t0=b["inicio_s"], t1=b["fin_s"], L=max(1, int(round(d / pulso)))))
    return out, bpm


def tramos(cs: list[dict], minimo: int) -> list[dict]:
    res, i = [], 0
    while i < len(cs):
        j = i
        while j + 1 < len(cs) and cs[j + 1]["L"] == cs[i]["L"]:
            j += 1
        if j - i + 1 >= minimo:
            res.append(dict(L=cs[i]["L"], n=j - i + 1, desde=cs[i]["n"], hasta=cs[j]["n"], t0=cs[i]["t0"], t1=cs[j]["t1"]))
        i = j + 1
    return res


def patrones(cs: list[dict], max_p: int = 6, min_vueltas: int = 3) -> list[dict]:
    """Patrones de longitudes de compás de 2 a max_p compases que se repiten seguidos al menos min_vueltas veces
    (y que no son un solo compás repetido)."""
    L = [c["L"] for c in cs]
    res, i = [], 0
    while i < len(L):
        mejor = None
        for p in range(2, max_p + 1):
            pat = L[i:i + p]
            if len(pat) < p or len(set(pat)) == 1:
                continue
            k = 1
            while L[i + k * p:i + (k + 1) * p] == pat:
                k += 1
            if k >= min_vueltas and (mejor is None or k * p > mejor[1] * mejor[0]):
                mejor = (p, k, pat)
        if mejor:
            p, k, pat = mejor
            res.append(dict(patron=pat, suma=sum(pat), vueltas=k, t0=cs[i]["t0"], t1=cs[i + k * p - 1]["t1"]))
            i += k * p
        else:
            i += 1
    return res


def rejilla(run: Path, cs: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Rejilla de corcheas: tiempo de cada corchea, ataque (0/1) y clase de cuarto de tono de la voz aguda (−1 = nada)."""
    J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
    ts = []
    for c in cs:
        k = 2 * c["L"]
        ts += list(c["t0"] + (c["t1"] - c["t0"]) * np.arange(k) / k)
    ts = np.array(ts)
    paso = np.median(np.diff(ts)) if len(ts) > 1 else 0.25
    on = np.zeros(len(ts))
    for t in (J.get("onsets_h_s") or []) + (J.get("onsets_b_s") or []):
        i = int(np.argmin(np.abs(ts - t)))
        if abs(ts[i] - t) <= paso / 2:
            on[i] = 1
    pc = np.full(len(ts), -1)
    notas = J.get("raw_high") or J.get("raw_bass") or []
    for n in notas:
        sel = (ts >= n["start_s"]) & (ts < n["end_s"])
        pc[sel] = int(round(n["midi"] * 2)) % 24
    return ts, on, pc


def repeticion(on: np.ndarray, pc: np.ndarray, lags: np.ndarray) -> np.ndarray:
    """R(ℓ) = media de: misma clase de cuarto de tono ℓ corcheas después (donde suenan las dos) y mismo ataque."""
    R = np.zeros(len(lags))
    for k, l in enumerate(lags):
        if l >= len(pc):
            continue
        a, b = pc[:-l], pc[l:]
        v = (a >= 0) & (b >= 0)
        r_pc = (a[v] == b[v]).mean() if v.sum() > 8 else 0.0
        x, y = on[:-l], on[l:]
        r_on = 1 - np.abs(x - y).mean() if len(x) > 8 else 0.0
        R[k] = 0.7 * r_pc + 0.3 * r_on
    return R


def picos(R: np.ndarray, lags: np.ndarray, n: int = 3) -> list[tuple[int, float]]:
    """Mejores periodos: máximos locales, quitando los que son múltiplos de uno mejor ya elegido."""
    cand = [(R[i], int(lags[i])) for i in range(1, len(R) - 1) if R[i] >= R[i - 1] and R[i] >= R[i + 1]]
    cand.sort(reverse=True)
    out = []
    for r, l in cand:
        if any(l % m == 0 for m, _ in out):
            continue
        out.append((l, round(float(r), 3)))
        if len(out) == n:
            break
    return out


def fases(ts: np.ndarray, pc: np.ndarray, cs: list[dict], L: int, minimo: float = 0.5) -> list[dict]:
    """Fase del bucle de L corcheas en el primer tiempo de cada compás (None si suena poco o encaja mal)."""
    idx = np.arange(len(pc))
    plantilla = np.full(L, -1)
    for f in range(L):
        v = pc[f::L]
        v = v[v >= 0]
        if len(v):
            plantilla[f] = np.bincount(v).argmax()
    out = []
    for c in cs:
        i = int(np.searchsorted(ts, c["t0"] - 1e-6))
        seg = pc[i:i + L]
        if len(seg) < L or (seg >= 0).sum() < L / 3:
            out.append(dict(compas=c["n"], t0=c["t0"], L=c["L"], fase=None, ajuste=None))
            continue
        puntos = np.array([((seg == np.roll(plantilla, -s)) & (seg >= 0)).sum() for s in range(L)])
        mejor = int(puntos.argmax())
        aj = puntos[mejor] / (seg >= 0).sum()
        # fase ambigua: otra rotación encaja casi igual (riff de una sola nota, plantilla casi constante)
        unica = (np.sort(puntos)[-2] if L > 1 else 0) < puntos[mejor] - max(1, 0.1 * puntos[mejor])
        out.append(dict(compas=c["n"], t0=c["t0"], L=c["L"], fase=mejor if aj >= minimo and unica else None, ajuste=round(float(aj), 2)))
    return out


def lectura_fases(fs: list[dict], L: int) -> dict:
    """Saltos de fase entre compases seguidos, quitando lo que explica el largo del compás (2·pulsos corcheas)."""
    esperados, otros, cuenta = 0, [], 0
    for a, b in zip(fs, fs[1:]):
        if a["fase"] is None or b["fase"] is None:
            continue
        cuenta += 1
        salto = (b["fase"] - a["fase"]) % L
        if salto == (2 * a["L"]) % L:
            esperados += 1
        else:
            otros.append((b["compas"], b["t0"], salto))
    deriva = sum(1 for a in fs if a["fase"] is not None and L % (2 * a["L"]) != 0 and (2 * a["L"]) % L != 0)
    validos = sum(1 for a in fs if a["fase"] is not None)
    return dict(pares=cuenta, coherentes=esperados, rotaciones=otros,
                polimetro=round(deriva / validos, 2) if validos else None)


def dibujar(curvas: list[tuple[str, np.ndarray, str]], lags: np.ndarray, columnas: int = 4, diapositiva: bool = False):
    """Una curva de repetición por canción, en una cuadrícula de `columnas` con ejes compartidos."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch
    from estilo_figuras import FONDO, GRIS, PALETA_ARTISTA, REJILLA, TINTA

    orden = list(PALETA_ARTISTA)
    curvas = sorted(curvas, key=lambda c: orden.index(c[2]) if c[2] in orden else len(orden))
    columnas = max(1, min(columnas, len(curvas)))
    filas = -(-len(curvas) // columnas)
    alto_fila = 2.0 if diapositiva else 1.05
    fig, cuerpo = estilo_figuras.figura(
        12 if diapositiva else 16, alto_fila * filas + 0.9, "Repetición musical según la distancia temporal",
        subtitulo="" if diapositiva else "Cada barra muestra cuánto se repiten ataques y alturas al separar la música ℓ "
                  "corcheas. Un pico estable ayuda a identificar ciclos métricos largos del repertorio.",
        nota="" if diapositiva else "Eje x: distancia en corcheas ℓ. Eje y: repetición en la canción completa (0 a 1). "
             "Las cifras sobre las barras son los mejores periodos detectados.")
    ejes = cuerpo.subplots(filas, columnas, sharex=True, sharey=True, squeeze=False)
    ticks = np.arange(0, min(40, int(lags[-1])) + 1, 10)
    for k, ax in enumerate(ejes.flat):
        if k >= len(curvas):
            ax.set_visible(False)
            continue
        n, R, grupo = curvas[k]
        ax.bar(lags, R, color=PALETA_ARTISTA[grupo], width=0.75)
        for l, r in picos(R, lags):
            ax.text(l, r + 0.03, str(l), ha="center", va="bottom", fontsize=6.5, color=TINTA)
        ax.set_title(n, loc="left", fontsize=8.5, color=TINTA, pad=2)
        ax.set_ylim(0, 1.25)
        ax.set_yticks([0, 0.5, 1])
        ax.set_xlim(0, lags[-1] + 0.5)
        ax.set_xticks(ticks)
        ax.set_facecolor(FONDO)
        ax.grid(axis="y", color=REJILLA, lw=0.6)
        ax.set_axisbelow(True)
        for s_ in ("top", "right"):
            ax.spines[s_].set_visible(False)
        for s_ in ("left", "bottom"):
            ax.spines[s_].set_color(REJILLA)
        ax.tick_params(labelsize=7.5, colors=GRIS, length=0)
        if diapositiva or k >= len(curvas) - columnas:          # en la diapositiva, todas; si no, la última fila
            ax.xaxis.set_tick_params(labelbottom=True)
            ax.set_xlabel("Distancia ℓ entre repeticiones (corcheas)" if diapositiva else "ℓ (corcheas)", fontsize=8.5, color=GRIS)
    presentes = [g for g in PALETA_ARTISTA if any(c[2] == g for c in curvas)]
    if not diapositiva:          # en la diapositiva, sin leyenda
        cuerpo.legend(handles=[Patch(facecolor=PALETA_ARTISTA[g], label=g) for g in presentes], loc="outside upper center",
                      ncol=len(presentes), frameon=False, fontsize=9.5)
    return fig


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--max", type=int, default=40, help="periodo máximo en corcheas")
    ap.add_argument("--ventana", type=float, default=30.0, help="segundos por ventana")
    ap.add_argument("--min-tramo", type=int, default=4, help="compases seguidos para listar un tramo")
    ap.add_argument("--salida", default="outputs/ciclos_metricos")
    ap.add_argument("--diapositiva", action="store_true", help="3 columnas, marcas y rótulo del eje x en cada panel")
    a = ap.parse_args()

    por = {}
    for r in sorted(a.corridas, key=lambda r: r.name):
        if (r / "armonia.json").exists():
            por[nombre(r.name)] = r          # una corrida por canción: la más reciente
    a.corridas = list(por.values())
    lags = np.arange(2, a.max + 1)
    md, curvas, todas_fases = ["# Tramos de compás y ciclos métricos", ""], [], []
    for run in a.corridas:
        if not (run / "armonia.json").exists():
            print(f"falta armonia.json: {run}")
            continue
        cs, bpm = compases(run)
        ts, on, pc = rejilla(run, cs)
        R = repeticion(on, pc, lags)
        curvas.append((nombre(run.name), R, artista(run.name)))
        md += [f"## {nombre(run.name)} ({bpm:.0f} BPM, {len(cs)} compases)", "",
               "| Pulsos por compás | Compases | Desde (compás, minuto) | Hasta (compás, minuto) |", "|---|---|---|---|"]
        md += [f"| {t['L']} | {t['n']} | {t['desde']} · {mmss(t['t0'])} | {t['hasta']} · {mmss(t['t1'])} |" for t in tramos(cs, a.min_tramo)]
        ps = patrones(cs)
        md += ["", "Patrones de compases que se repiten (posible ciclo largo):"]
        md += [f"- {'+'.join(map(str, p['patron']))} = {p['suma']} pulsos, {p['vueltas']} vueltas, {mmss(p['t0'])}-{mmss(p['t1'])}" for p in ps] or ["- ninguno"]
        md += ["", f"Repetición por corcheas en toda la canción (mejores periodos): " +
               ", ".join(f"{l} corcheas ({l / 2:g} pulsos) R={r}" for l, r in picos(R, lags)), "",
               "| Ventana | Mejor periodo (corcheas) | R |", "|---|---|---|"]
        t_fin = ts[-1] if len(ts) else 0
        t = 0.0
        while t < t_fin:
            sel = (ts >= t) & (ts < t + a.ventana)
            if sel.sum() > 2 * a.max:
                Rw = repeticion(on[sel], pc[sel], lags)
                pw = picos(Rw, lags, 1)
                if pw:
                    md.append(f"| {mmss(t)}-{mmss(min(t + a.ventana, t_fin))} | {pw[0][0]} ({pw[0][0] / 2:g} pulsos) | {pw[0][1]} |")
            t += a.ventana
        if picos(R, lags):
            Lb = picos(R, lags, 1)[0][0]
            fs = fases(ts, pc, cs, Lb)
            lf = lectura_fases(fs, Lb)
            todas_fases.append((nombre(run.name), Lb, fs))
            md += ["", f"Bucle contra compás (bucle de {Lb} corcheas): {lf['coherentes']} de {lf['pares']} pasos de compás a compás "
                   f"mueven la fase lo que mide el compás; fracción de compases que no dividen al bucle ni son múltiplo de él (polímetro o compás mal leído): {lf['polimetro']}. "
                   f"Saltos de fase no explicados (posible rotación o error de compás): {len(lf['rotaciones'])}"]
            md += [f"- compás {n} ({mmss(t)}): salto de {sl} corcheas" for n, t, sl in lf["rotaciones"][:15]]
            print(f"   bucle {Lb}: coherentes {lf['coherentes']}/{lf['pares']}, compás≠bucle {lf['polimetro']}, saltos {len(lf['rotaciones'])}")
        md.append("")
        print(f"{nombre(run.name)}: tramos {[(t['L'], t['n']) for t in tramos(cs, a.min_tramo)]} · patrones "
              f"{[('+'.join(map(str, p['patron'])), p['suma'], p['vueltas']) for p in ps]} · periodos {picos(R, lags)}")
    Path(a.salida + ".md").write_text("\n".join(md), encoding="utf-8")
    with open(a.salida + "_fases.csv", "w", encoding="utf-8") as fh:
        fh.write("cancion,bucle_corcheas,compas,inicio_s,pulsos,fase,ajuste\n")
        for n, Lb, fs in todas_fases:
            for f in fs:
                fh.write(f"{n},{Lb},{f['compas']},{f['t0']:.2f},{f['L']},{'' if f['fase'] is None else f['fase']},{'' if f['ajuste'] is None else f['ajuste']}\n")

    estilo_figuras.preparar()
    estilo_figuras.guardar(dibujar(curvas, lags, columnas=3 if a.diapositiva else 4, diapositiva=a.diapositiva),
                           a.salida + ".png", dpi=170)
    print(f"→ {a.salida}.md, {a.salida}.png")


if __name__ == "__main__":
    main()
