"""Lista tramos de compás y busca ciclos métricos largos en una o más corridas."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np


def nombre(run: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", run)
    n = re.sub(r"(angine_de_poitrine_|king_gizzard_|primus_|_audio_off\w*|_official_audio|_repro|_cache)", "", n)
    return n.replace("_", " ").strip().capitalize()


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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--max", type=int, default=40, help="periodo máximo en corcheas")
    ap.add_argument("--ventana", type=float, default=30.0, help="segundos por ventana")
    ap.add_argument("--min-tramo", type=int, default=4, help="compases seguidos para listar un tramo")
    ap.add_argument("--salida", default="outputs/ciclos_metricos")
    a = ap.parse_args()

    lags = np.arange(2, a.max + 1)
    md, curvas = ["# Tramos de compás y ciclos métricos", ""], []
    for run in a.corridas:
        if not (run / "armonia.json").exists():
            print(f"falta armonia.json: {run}")
            continue
        cs, bpm = compases(run)
        ts, on, pc = rejilla(run, cs)
        R = repeticion(on, pc, lags)
        curvas.append((nombre(run.name), R))
        md += [f"## {nombre(run.name)} ({bpm:.0f} BPM, {len(cs)} compases)", "",
               "| Pulsos por compás | Compases | Desde (compás, minuto) | Hasta (compás, minuto) |", "|---|---|---|---|"]
        md += [f"| {t['L']} | {t['n']} | {t['desde']} · {mmss(t['t0'])} | {t['hasta']} · {mmss(t['t1'])} |" for t in tramos(cs, a.min_tramo)]
        ps = patrones(cs)
        md += ["", "Patrones de compases que se repiten (posible ciclo largo):"]
        md += [f"- {'+'.join(map(str, p['patron']))} = {p['suma']} pulsos, {p['vueltas']} vueltas, {mmss(p['t0'])}-{mmss(p['t1'])}" for p in ps] or ["- ninguno"]
        md += ["", "Repetición por corcheas en toda la canción (mejores periodos): " +
               ", ".join(f"{l} corcheas ({l / 2:g} pulsos) R={r}" for l, r in picos(R, lags)), "",
               "| Ventana | Mejor periodo (corcheas) | R |", "|---|---|---|"]
        t_fin, t = ts[-1] if len(ts) else 0, 0.0
        while t < t_fin:
            sel = (ts >= t) & (ts < t + a.ventana)
            if sel.sum() > 2 * a.max:
                pw = picos(repeticion(on[sel], pc[sel], lags), lags, 1)
                if pw:
                    md.append(f"| {mmss(t)}-{mmss(min(t + a.ventana, t_fin))} | {pw[0][0]} ({pw[0][0] / 2:g} pulsos) | {pw[0][1]} |")
            t += a.ventana
        md.append("")
        print(f"{nombre(run.name)}: tramos {[(t['L'], t['n']) for t in tramos(cs, a.min_tramo)]} · patrones "
              f"{[('+'.join(map(str, p['patron'])), p['suma'], p['vueltas']) for p in ps]} · periodos {picos(R, lags)}")
    Path(a.salida + ".md").write_text("\n".join(md), encoding="utf-8")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    tinta, gris, fondo = "#0b0b0b", "#52514e", "#fcfcfb"
    fig, ejes = plt.subplots(len(curvas), 1, figsize=(9, 1.6 * len(curvas) + 0.8), sharex=True, facecolor=fondo, squeeze=False)
    for ax, (n, R) in zip(ejes[:, 0], curvas):
        ax.bar(lags, R, color="#2a78d6", width=0.7)
        for l, r in picos(R, lags):
            ax.text(l, r + 0.01, str(l), ha="center", fontsize=8, color=tinta)
        ax.set_ylabel(n, rotation=0, ha="right", va="center", fontsize=9, color=tinta)
        ax.set_ylim(0, 1.05); ax.set_facecolor(fondo)
        for s in ("top", "right"): ax.spines[s].set_visible(False)
        ax.tick_params(labelsize=8, colors=gris)
    ejes[-1, 0].set_xlabel("distancia en corcheas (ℓ)", fontsize=9, color=gris)
    fig.suptitle("Cuánto se repite la música a cada distancia (número = mejores periodos)", fontsize=11, color=tinta, x=0.02, ha="left")
    fig.tight_layout(); fig.savefig(a.salida + ".png", dpi=170, facecolor=fondo)
    print(f"→ {a.salida}.md, {a.salida}.png")


if __name__ == "__main__":
    main()
