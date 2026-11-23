"""Gráficas pequeñas para la presentación: una por fórmula (diapositiva 14) y el acierto de la herramienta (18).

Uso:
    python scripts/comparacion/figuras_presentacion.py outputs/<corrida> [...] --salida outputs/presentacion

Las fórmulas se ilustran con Primus (la comparación propia), no con la banda, para no adelantar en la metodología
los resultados que vienen después. Con las corridas dadas escribe:
- <salida>_formula_js.png: reparto de fundamentales de una canción frente al centro del rock y su distancia de
  Jensen-Shannon (la canción de --cancion-js, por defecto «My Name Is Mud»).
- <salida>_formula_percentil.png: distancias de las piezas del rock a su centro, dónde cae esa canción (el área
  sombreada es su percentil) y una segunda canción de contraste (--cancion-contraste, por defecto «Jerry Was a Race
  Car Driver»).
- <salida>_formula_repeticion.png: R(ℓ) de una canción (--cancion-ciclo, por defecto «Jerry Was a Race Car Driver»),
  con su mejor periodo.
- <salida>_formula_campos.png: el círculo de 24-EDO de una canción (--cancion-circulo); sin canción (por defecto),
  solo la geometría de los dos campos.
- <salida>_acierto.png: melodía, bajo y fundamental del acorde contra la referencia, por canción. Usa
  evaluacion_melodia.json y evaluacion_armonia.json de cada corrida; toma la corrida más reciente de cada canción que
  los tenga (sin las de BS-RoFormer), entre las de --evaluaciones si se dan.
Las mini-gráficas no llevan título: lo pone la diapositiva.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import estilo_figuras  # noqa: E402
from estilo_figuras import GRIS, MUTED, REJILLA, TINTA  # noqa: E402

LETRA = 1.4                 # escala del texto de las mini-gráficas de fórmulas: se ven a ~200 px en la diapositiva
CORTOS = {"my_name_is_mud": "My Name Is Mud", "jerry_was": "Jerry"}   # rótulos cortos en el histograma
VERDE, VERDE_CLARO, AMARILLO, GRIS_BARRA = "#06784f", "#14c486", "#ffb93e", "#c9c8c2"
NOMBRES = {"mata_zyklek": "Mata Zyklek", "fabienk": "Fabienk", "sarniezz": "Sarniezz", "yor_zarad": "Yor Zarad",
           "utzp": "Utzp", "angor": "Angor"}


def corrida_de(corridas: list[Path], clave: str) -> Path | None:
    """La corrida más reciente cuyo nombre contiene `clave` (sin las de BS-RoFormer)."""
    c = sorted((r for r in corridas if clave in r.name.lower() and "roformer" not in r.name), key=lambda r: r.name)
    return c[-1] if c else None


def mini(ancho: float = 3.6, alto: float = 2.4):
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(ancho, alto), facecolor="white", layout="constrained")
    estilo_figuras.estilo_ejes(ax)
    ax.tick_params(labelsize=8.5 * LETRA)
    ax.set_facecolor("white")
    return fig, ax


def guardar(fig, ruta: str) -> None:
    import matplotlib.pyplot as plt
    problemas = estilo_figuras.revisar(fig)
    fig.savefig(ruta, dpi=220, facecolor="white")
    plt.close(fig)
    print(f"→ {ruta}")
    for p in problemas:
        if not p.startswith("franja vacía"):
            print(f"   aviso de distribución: {p}")


# ---------------------------------------------------------------- fórmulas (diapositiva 14)

def formulas_estilo(run: Path, salida: str, contraste: Path | None = None) -> None:
    import verosimilitud_estilos as ve
    C = {k: list(v.values()) for k, v in json.loads(ve.CORPUS.read_text(encoding="utf-8")).items() if v}
    R = ve.preparar(C)
    c = ve.cancion(run)
    p, q = np.array(c["fundamentales"]), np.array(R["rock"]["cu"])
    d = ve.js(c["fundamentales"], R["rock"]["cu"])

    fig, ax = mini()
    x = np.arange(12)
    ax.bar(x - 0.2, 100 * p, 0.4, color=VERDE, label=ve.nombre(run.name))
    ax.bar(x + 0.2, 100 * q, 0.4, color=GRIS_BARRA, label="centro del rock")
    ax.set_xticks(x, ve.GRADOS, fontsize=7 * 1.15)                  # 12 grados: más grandes se juntan
    ax.set_ylabel("% del tiempo", fontsize=8 * LETRA, color=GRIS)
    ax.legend(frameon=False, fontsize=7.5 * LETRA, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    ax.text(0.98, 0.96, f"$D_{{JS}}$ = {d:.2f}", transform=ax.transAxes, ha="right", va="top", fontsize=9.5 * LETRA,
            color=TINTA)
    guardar(fig, salida + "_formula_js.png")

    ref = np.array(R["rock"]["du"])
    marcas = [(run, d)]
    if contraste is not None:
        marcas.append((contraste, ve.js(ve.cancion(contraste)["fundamentales"], R["rock"]["cu"])))
    fig, ax = mini()
    bins = np.linspace(0, max(ref.max(), d) * 1.05, 28)
    n, b, parches = ax.hist(ref, bins=bins, color=GRIS_BARRA)
    sombra = marcas[0][1]                        # se sombrea el percentil de la canción principal
    for pa, izq in zip(parches, b[:-1]):
        if izq + (b[1] - b[0]) / 2 >= sombra:
            pa.set_facecolor(VERDE_CLARO)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=GRIS_BARRA, label="piezas del rock"), Patch(color=VERDE_CLARO, label="más lejos")],
              frameon=False, fontsize=7 * LETRA, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    for k, (r, dk) in enumerate(marcas):
        color = VERDE if k == 0 else "#0b6e99"
        ax.axvline(dk, color=color, lw=2)
        corto = next((v for c, v in CORTOS.items() if c in r.name.lower()), ve.nombre(r.name))
        ax.text(dk, n.max() * (0.98 - 0.42 * k), f" {corto}\n p = {ve.percentil(dk, list(ref)):.1f}",
                fontsize=7.5 * LETRA, color=color, va="top", ha="left" if dk < bins[-1] * 0.75 else "right")
    ax.set_xlabel("distancia al centro del rock", fontsize=8 * LETRA, color=GRIS)
    ax.set_ylabel("piezas", fontsize=8 * LETRA, color=GRIS)
    guardar(fig, salida + "_formula_percentil.png")


def formula_repeticion(run: Path, salida: str) -> None:
    import ciclos_metricos as cm
    cs, _ = cm.compases(run)
    ts, on, pc = cm.rejilla(run, cs)
    lags = np.arange(2, 41)
    R = cm.repeticion(on, pc, lags)
    mejor = cm.picos(R, lags, 1)[0][0]
    fig, ax = mini()
    ax.bar(lags, R, 0.8, color=[VERDE if l == mejor else GRIS_BARRA for l in lags])
    ax.text(mejor, R[lags == mejor][0] + 0.015, f"ℓ = {mejor}", ha="center", fontsize=8.5 * LETRA, color=VERDE, fontweight="bold")
    ax.set_ylim(max(0, R.min() - 0.05), R.max() + 0.08)
    ax.set_xticks([4, 8, 12, 16, 20, 24, 28, 32, 36, 40])
    ax.set_xlabel("ℓ (corcheas)", fontsize=8 * LETRA, color=GRIS)
    ax.set_ylabel("R(ℓ)", fontsize=8 * LETRA, color=GRIS)
    guardar(fig, salida + "_formula_repeticion.png")


def formula_campos(run: Path | None, salida: str) -> None:
    """Círculo de 24-EDO de una canción o, sin canción, solo la geometría: los 24 grados con el mismo peso."""
    import matplotlib.pyplot as plt
    import figuras_album as fa
    if run is None:
        alt, tr, titulo = np.ones(24), np.zeros((24, 24)), ""
    else:
        alt, tr = fa.reparto(run)
        titulo = fa.nombre(run.name)
    fig, ax = plt.subplots(figsize=(2.8, 2.8), facecolor="white", layout="constrained")
    fa.dibujar_circulo(ax, alt, tr, titulo, True, letra=1.15)   # más grande, los grados tapan los puntos
    if run is None:                              # esquema: sin rótulo de % y puntos chicos para que se lean los grados
        ax.set_title("")
        for c in ax.collections:
            c.set_sizes([55])
    fig.savefig(salida + "_formula_campos.png", dpi=220, facecolor="white")
    plt.close(fig)
    print(f"→ {salida}_formula_campos.png")


# ---------------------------------------------------------------- acierto (diapositiva 18)

def datos_acierto(corridas: list[Path]) -> list[dict]:
    por = {}
    for r in sorted(corridas, key=lambda r: r.name):
        f = r / "evaluacion_melodia.json"
        if "roformer" in r.name or not f.exists():
            continue
        m = json.loads(f.read_text(encoding="utf-8"))
        a = r / "evaluacion_armonia.json"
        h = json.loads(a.read_text(encoding="utf-8")) if a.exists() else {}
        por[m["cancion"]] = dict(cancion=NOMBRES.get(m["cancion"], m["cancion"]), melodia=m["principal"],
                                 melodia_sin_octava=m["principal_sin_octava"], bajo=m["bajo"],
                                 fundamental=h.get("fundamental"), fundamental_confiables=h.get("fundamental_confiables"))
    orden = list(NOMBRES)
    return sorted(por.values(), key=lambda f: next((i for i, k in enumerate(orden) if NOMBRES[k] == f["cancion"]), 99))


def figura_acierto(filas: list[dict]):
    import matplotlib.pyplot as plt
    series = [("melodia", "Melodía principal", GRIS_BARRA), ("bajo", "Bajo", VERDE_CLARO),
              ("fundamental", "Fundamental del acorde", VERDE),
              ("fundamental_confiables", "Fundamental en compases confiables", AMARILLO)]
    # Fila final con la media simple de las canciones medidas: resume que la armonía acierta mucho más que la melodía.
    medidas = [f for f in filas if f.get("fundamental") is not None]
    if len(medidas) > 1:
        media = {"cancion": f"Media ({len(medidas)} canciones)"}
        for campo, _, _ in series:
            vals = [f[campo] for f in medidas if f.get(campo) is not None]
            media[campo] = float(np.mean(vals)) if vals else None
        filas = filas + [media]
    fig, ax = plt.subplots(figsize=(6.4, 5.0), facecolor="white", layout="constrained")
    estilo_figuras.estilo_ejes(ax, grid_x=True)
    ax.set_facecolor("white")
    alto = 0.19
    y = np.arange(len(filas))[::-1].astype(float)
    if len(medidas) > 1:
        y[-1] -= 0.25                                   # la media, un poco aparte de las canciones
        ax.axhline(y[-1] + 0.6, color=REJILLA, lw=1)
        conf = media.get("fundamental_confiables")
        if conf is not None:
            ax.axvline(conf, color=AMARILLO, lw=1.4, ls="--", zorder=0)
            ax.text(conf, y[0] + 0.62, f"armonía ≈ {conf:.0f} %", ha="center", va="bottom", fontsize=8.5,
                    color="#9a6200", fontweight="bold")
    for k, (campo, rotulo, color) in enumerate(series):
        pos = y + (1.5 - k) * alto
        vals = [f.get(campo) for f in filas]
        ax.barh(pos, [v or 0 for v in vals], alto * 0.92, color=color, label=rotulo)
        for yy, v in zip(pos, vals):
            if v is not None:
                ax.text(v + 1, yy, f"{v:.0f}", va="center", fontsize=7.5, color=TINTA,
                        bbox=dict(facecolor="white", edgecolor="none", pad=0.6), zorder=3)
    for yy, f in zip(y, filas):
        if f.get("fundamental") is None:
            ax.text(1, yy - alto, "sin referencia armónica", va="center", fontsize=7.5, color=MUTED)
    ax.set_yticks(y, [f["cancion"] + (" (a ciegas)" if f["cancion"] == "Yor Zarad" else "") for f in filas], fontsize=9, color=TINTA)
    if len(medidas) > 1:
        ax.get_yticklabels()[-1].set_fontweight("bold")
    ax.set_xlim(0, 112)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel("acierto contra la referencia corregida de oído (%)", fontsize=8.5, color=GRIS)
    fig.legend(loc="outside lower center", ncol=2, frameon=False, fontsize=8)
    return fig


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--salida", default="outputs/presentacion")
    ap.add_argument("--cancion-js", default="my_name_is_mud")
    ap.add_argument("--cancion-contraste", default="jerry_was", help="segunda canción en el histograma del percentil")
    ap.add_argument("--cancion-ciclo", default="jerry_was")
    ap.add_argument("--cancion-circulo", default="", help="vacío: solo la geometría de los dos campos")
    ap.add_argument("--evaluaciones", nargs="*", type=Path, default=[],
                    help="corridas con evaluacion_melodia.json para la gráfica de acierto (por defecto, las mismas corridas)")
    a = ap.parse_args()
    estilo_figuras.preparar()
    fallos = 0
    contraste = corrida_de(a.corridas, a.cancion_contraste)
    if not a.cancion_circulo:
        formula_campos(None, a.salida)
    for clave, funcion in ((a.cancion_js, lambda r, s: formulas_estilo(r, s, contraste)), (a.cancion_ciclo, formula_repeticion),
                           (a.cancion_circulo, formula_campos)):
        if not clave:
            continue
        run = corrida_de(a.corridas, clave)
        if run is None:
            print(f"no hay corrida de {clave}", file=sys.stderr)
            fallos += 1
            continue
        funcion(run, a.salida)
    filas = datos_acierto(a.evaluaciones or a.corridas)
    if filas:
        guardar(figura_acierto(filas), a.salida + "_acierto.png")
        for f in filas:
            print("  ", " · ".join(f"{k} {v:.1f}" if isinstance(v, float) else str(v) for k, v in f.items()))
    else:
        print("ninguna corrida tiene evaluacion_melodia.json", file=sys.stderr)
        fallos += 1
    raise SystemExit(1 if fallos else 0)


if __name__ == "__main__":
    main()
