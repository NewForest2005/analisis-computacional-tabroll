"""Vuelve a dibujar, con letra grande para la diapositiva 8, las tres figuras del primer cuaderno (la idea inicial).

Uso:
    python scripts/comparacion/figuras_cuaderno_original.py <audio_arrays.npz> --salida presentacion/img

<audio_arrays.npz> es el que guardó el primer cuaderno (CMA_Angine_de_Poitrine) en analysis_outputs/: el bajo de
Sarniezz a 22 050 Hz. Los cálculos son los mismos del cuaderno:
- pYIN con fmin = Do2, fmax = Do7 y frame_length = 2048 (original_pyin.png);
- la desviación en cents de cada cuadro sonoro respecto del semitono más cercano (original_cents.png);
- la matriz de confusión de la red (MLP) que clasifica la sección por MFCC (original_secciones_mlp.png). Sus 7 casos
  de prueba se copian de la salida del cuaderno corregido (classification_report y ConfusionMatrixDisplay), porque
  volver a entrenar la red con otra versión de scikit-learn podría dar otra partición.
El contorno de pYIN se guarda en outputs/.f0_cuaderno_original.npz para no recalcularlo (tarda un par de minutos).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

VERDE, VERDE_CLARO, AZUL, TINTA, GRIS, REJILLA = "#06784f", "#14c486", "#2a78d6", "#29272d", "#6b6a66", "#e4e3de"
SR = 22050
SECCIONES = ["clímax", "intro", "outro", "puente", "riff", "verso"]
# Filas: sección real; columnas: sección que predijo la red (salida del cuaderno corregido, 7 fragmentos de prueba).
CONFUSION = np.array([[0, 0, 0, 0, 1, 0],
                      [0, 1, 0, 0, 0, 0],
                      [1, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 1],
                      [0, 0, 0, 0, 1, 0],
                      [0, 0, 0, 0, 1, 1]])


def contorno(arrays: Path, cache: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if cache.exists():
        d = np.load(cache)
        return d["t"], d["f0"], d["sonoro"]
    import librosa
    y = np.load(arrays)["waveform"]
    f0, sonoro, _ = librosa.pyin(y=y, sr=SR, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"), frame_length=2048)
    t = librosa.times_like(f0, sr=SR)
    np.savez_compressed(cache, t=t, f0=f0, sonoro=sonoro)
    return t, f0, sonoro


def ejes(ax) -> None:
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(REJILLA)
    ax.tick_params(colors=GRIS, labelsize=13, length=0)
    ax.grid(color=REJILLA, lw=0.8)
    ax.set_axisbelow(True)


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams["font.family"] = "DejaVu Sans"

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arrays", type=Path)
    ap.add_argument("--salida", type=Path, default=Path("presentacion/img"))
    a = ap.parse_args()
    a.salida.mkdir(parents=True, exist_ok=True)
    t, f0, sonoro = contorno(a.arrays, Path("outputs") / ".f0_cuaderno_original.npz")
    ok = sonoro & np.isfinite(f0) & (f0 > 0)

    # 1) contorno pYIN
    fig, ax = plt.subplots(figsize=(7.2, 3.1), layout="constrained", facecolor="white")
    ejes(ax)
    ax.plot(t, f0, color=VERDE_CLARO, lw=0.6)
    ax.scatter(t[ok], f0[ok], s=2, color=VERDE, lw=0)
    ax.set_xlabel("tiempo (s)", fontsize=13, color=GRIS)
    ax.set_ylabel("frecuencia (Hz)", fontsize=13, color=GRIS)
    ax.set_xlim(0, t[-1])
    fig.savefig(a.salida / "original_pyin.png", dpi=200)
    plt.close(fig)

    # 2) desviación en cents respecto del semitono más cercano
    midi = 69 + 12 * np.log2(f0[ok] / 440)
    cents = 100 * (midi - np.round(midi))
    fig, ax = plt.subplots(figsize=(5.6, 3.0), layout="constrained", facecolor="white")
    ejes(ax)
    ax.axhspan(-50, 50, color="#eef6f2", zorder=0)
    ax.scatter(t[ok], cents, s=1.5, color=AZUL, lw=0, alpha=0.6)
    for y in (-50, 50):
        ax.axhline(y, color=VERDE, lw=1.4, ls="--")
    ax.text(t[-1], 56, "±50 cents = ¼ de tono", ha="right", va="bottom", fontsize=12, color=VERDE)
    ax.set_ylim(-100, 100)
    ax.set_yticks([-100, -50, 0, 50, 100])
    ax.set_xlim(0, t[-1])
    ax.set_xlabel("tiempo (s)", fontsize=13, color=GRIS)
    ax.set_ylabel("cents", fontsize=13, color=GRIS)
    fig.savefig(a.salida / "original_cents.png", dpi=200)
    plt.close(fig)

    # 3) matriz de confusión de la red por sección
    from matplotlib.colors import LinearSegmentedColormap
    fig, ax = plt.subplots(figsize=(4.0, 3.7), layout="constrained", facecolor="white")
    ax.imshow(CONFUSION, cmap=LinearSegmentedColormap.from_list("v", ["#ffffff", VERDE]), vmin=0, vmax=1)
    for i in range(6):
        for j in range(6):
            v = CONFUSION[i, j]
            ax.text(j, i, str(v), ha="center", va="center", fontsize=12, fontweight="bold" if v else "normal",
                    color="#ffffff" if v else "#b5b4ae")
    for k in range(6):
        ax.add_patch(plt.Rectangle((k - 0.5, k - 0.5), 1, 1, fill=False, ec=TINTA, lw=1.2))   # diagonal = acierto
    ax.set_xticks(range(6), SECCIONES, rotation=45, ha="right", fontsize=12, color=TINTA)
    ax.set_yticks(range(6), SECCIONES, fontsize=12, color=TINTA)
    ax.set_xlabel("sección que predijo la red", fontsize=12, color=GRIS)
    ax.set_ylabel("sección real", fontsize=12, color=GRIS)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.savefig(a.salida / "original_secciones_mlp.png", dpi=200)
    plt.close(fig)
    print(f"{ok.sum()} cuadros sonoros de {len(f0)}; cents entre {cents.min():.1f} y {cents.max():.1f}; "
          f"aciertos de la red: {np.trace(CONFUSION)} de {CONFUSION.sum()} → {a.salida}")


if __name__ == "__main__":
    main()
