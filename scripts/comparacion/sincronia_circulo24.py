"""Prueba lo que de verdad reproduce el círculo de 24-EDO de la presentación: datos.js y las pistas recortadas.

Uso:
    python scripts/comparacion/sincronia_circulo24.py presentacion/circulo24

A diferencia de probar_circulo24.py (que mide las notas del cuaderno, line_diagnostics.json), esta prueba lee el
paquete exportado, el mismo que abre la diapositiva:

1. Pistas: duración de mezcla, guitarra y bajo, y desfase entre ellas (correlación de la envolvente de ataques).
   Deben durar lo mismo que el fragmento y no estar corridas entre sí.
2. Sincronía notas-audio: pYIN sobre guitarra.mp3 (voz aguda) y bajo.mp3 (voz grave), redondeado a 24-EDO, contra
   las notas de datos.js, desplazando las notas de −300 a +300 ms. El mejor desfase debe estar cerca de 0.
3. Melodía: las notas de datos.js contra la referencia corregida de oído de Mata Zyklek (references/mata_zyklek_loops.py,
   alineada como en src/tabroll/evaluation/melodia.py), cuadro a cuadro, y los grados del círculo que no aparecen en
   ninguna voz de la referencia del fragmento.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "src"))

DT = 0.01
SR = 22050
NOMBRES = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]


def nombre24(g: int) -> str:
    return NOMBRES[g // 2] + ("+" if g % 2 else "")


def leer_datos(carpeta: Path) -> dict:
    s = (carpeta / "datos.js").read_text(encoding="utf-8")
    return json.loads(s[s.index("{"): s.rindex("}") + 1])


def rejilla(notas, largo: int, desfase: float = 0.0) -> np.ndarray:
    """Grado de 24 por cuadro (−1 = silencio). notas: (inicio, fin, grado 0-23), en segundos del fragmento."""
    g = np.full(largo, -1)
    for a, b, p in notas:
        i, j = int(round((a + desfase) / DT)), int(round((b + desfase) / DT))
        g[max(i, 0):max(min(j, largo), 0)] = int(p) % 24
    return g


def pyin24(y: np.ndarray, fmin: float, fmax: float, largo: int) -> np.ndarray:
    import librosa
    f0, voz, _ = librosa.pyin(y, fmin=fmin, fmax=fmax, sr=SR, frame_length=2048, hop_length=int(SR * DT))
    g = np.full(largo, -1)
    ok = voz & np.isfinite(f0)
    midi = librosa.hz_to_midi(np.where(ok, f0, 1.0))
    q = (np.round(midi * 2).astype(int)) % 24
    n = min(largo, len(q))
    g[:n] = np.where(ok[:n], q[:n], -1)
    return g


def acuerdo(a: np.ndarray, b: np.ndarray) -> tuple[float, int]:
    ambos = (a >= 0) & (b >= 0)
    return (100 * float((a[ambos] == b[ambos]).mean()) if ambos.any() else float("nan")), int(ambos.sum())


def envolvente(y: np.ndarray) -> np.ndarray:
    import librosa
    return librosa.onset.onset_strength(y=y, sr=SR, hop_length=int(SR * DT))


def desfase_pistas(a: np.ndarray, b: np.ndarray, max_ms: int = 300) -> int:
    """Desfase (ms) que mejor alinea dos envolventes; positivo = b va atrasada."""
    n = min(len(a), len(b))
    a, b = (a[:n] - a[:n].mean()), (b[:n] - b[:n].mean())
    mejores = []
    for k in range(-max_ms // 10, max_ms // 10 + 1):
        x, z = (a[:n - k], b[k:]) if k >= 0 else (a[-k:], b[:n + k])
        mejores.append((float(np.dot(x, z) / (np.linalg.norm(x) * np.linalg.norm(z) + 1e-9)), k))
    return 10 * max(mejores)[1]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("carpeta", type=Path, nargs="?", default=RAIZ / "presentacion" / "circulo24")
    a = ap.parse_args()
    import librosa

    D = leer_datos(a.carpeta)
    dur = D["hasta"] - D["desde"]
    largo = int(round(dur / DT))
    print(f"{D['titulo']}: {D['desde']:g}–{D['hasta']:g} s ({dur:g} s), corrida {D['corrida']}, audio_inicio {D['audio_inicio']}")

    # 1. Pistas
    y = {k: librosa.load(a.carpeta / v, sr=SR, mono=True)[0] for k, v in D["audios"].items()}
    for k, v in y.items():
        print(f"  pista {k}: {len(v) / SR:.2f} s")
    env = {k: envolvente(v) for k, v in y.items()}
    for k in ("guitarra", "bajo"):
        print(f"  desfase mezcla → {k}: {desfase_pistas(env['mezcla'], env[k])} ms")

    # 2. Sincronía notas-audio
    voces = {"aguda": ("guitarra", 110.0, 1400.0), "grave": ("bajo", 30.0, 400.0)}
    print("Sincronía de las notas de datos.js con el audio (pYIN, mismo grado de 24):")
    for voz, (pista, fmin, fmax) in voces.items():
        medido = pyin24(y[pista], fmin, fmax, largo)
        curva = []
        for ms in range(-300, 301, 5):
            ac, n = acuerdo(rejilla(D["voces"][voz], largo, ms / 1000), medido)
            curva.append((ac, ms, n))
        cero = next(c for c in curva if c[1] == 0)
        mejor = max(curva)
        pm50 = [c[0] for c in curva if abs(c[1]) == 50]
        print(f"  voz {voz} ({pista}): sin desfase {cero[0]:.1f} % de {cero[2]} cuadros; mejor desfase {mejor[1]:+d} ms "
              f"({mejor[0]:.1f} %); a ±50 ms {min(pm50):.1f}–{max(pm50):.1f} %")

    # 3. Melodía contra la referencia corregida de oído
    from tabroll.evaluation import melodia as M
    al = M.Alignment("mata_zyklek")
    ba = M.mapped(al, al.ref["basses"])
    lead, low = M.lead_line(al, "mata_zyklek"), M.top_line(ba, low=True)
    ref = {"aguda": lead, "grave": low}
    print("Melodía de datos.js contra la referencia corregida de oído:")
    for voz, notas in ref.items():
        R = rejilla([(n["t"] - D["desde"], n["te"] - D["desde"], int(round(n["p"] * 2))) for n in notas
                     if n["te"] > D["desde"] and n["t"] < D["hasta"]], largo)
        C = rejilla(D["voces"][voz], largo)
        ac, n = acuerdo(R, C)
        errores: dict = {}
        ambos = (R >= 0) & (C >= 0)
        for r, c in zip(R[ambos], C[ambos]):
            if r != c:
                errores[(nombre24(r), nombre24(c))] = errores.get((nombre24(r), nombre24(c)), 0) + 1
        top = ", ".join(f"{r} → {c} ({k})" for (r, c), k in sorted(errores.items(), key=lambda x: -x[1])[:4])
        print(f"  voz {voz}: mismo grado en {ac:.1f} % de {n} cuadros; confusiones: {top or 'ninguna'}")
    en_ref = {int(round(n["p"] * 2)) % 24 for n in M.mapped(al, al.ref["guitars"]) + ba if n["te"] > D["desde"] and n["t"] < D["hasta"]}
    for voz in ("aguda", "grave"):
        extra: dict = {}
        for x, b, g in D["voces"][voz]:
            if g not in en_ref:
                extra[nombre24(g)] = extra.get(nombre24(g), 0.0) + (b - x)
        print(f"  voz {voz}: grados que la referencia no tiene en el fragmento: "
              + (", ".join(f"{k} ({v:.2f} s)" for k, v in extra.items()) or "ninguno"))


if __name__ == "__main__":
    main()
