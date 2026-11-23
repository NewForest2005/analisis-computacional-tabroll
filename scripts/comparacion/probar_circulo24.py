"""Prueba las notas del círculo de 24-EDO contra la referencia corregida de oído de Mata Zyklek.

Uso:
    python scripts/comparacion/probar_circulo24.py outputs/<corrida de Mata Zyklek> --desde 42 --hasta 72
    python scripts/comparacion/probar_circulo24.py outputs/<corrida de Mata Zyklek> --barrido

Cuadro a cuadro (10 ms), compara el grado de 24 que dibuja el círculo (raw_high y raw_bass de line_diagnostics.json,
redondeados a 24-EDO como en exportar_circulo24.py) con el de la referencia (references/mata_zyklek_loops.py,
alineada al audio como en src/tabroll/evaluation/melodia.py): la melodía principal para la voz aguda y la línea más
grave de los bajos para la grave. Da el acuerdo, la parte del tiempo en cuartos de tono de cada lado y las confusiones
más frecuentes. Con --barrido recorre la canción en ventanas de 30 s, para elegir el fragmento del círculo.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from tabroll.evaluation import melodia as M  # noqa: E402

DT = 0.01
NOMBRES = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#", "La", "La#", "Si"]


def nombre24(g: int) -> str:
    return NOMBRES[g // 2] + ("+" if g % 2 else "")


def rejilla(notas, largo: int, desfase: float = 0.0) -> np.ndarray:
    """Grado de 24 en cada cuadro (−1 = silencio). notas: (inicio, fin, altura MIDI)."""
    g = np.full(largo, -1)
    for a, b, p in notas:
        g[max(int((a - desfase) / DT), 0):max(int((b - desfase) / DT), 0)] = int(round(p * 2)) % 24
    return g


def medir(ref: np.ndarray, det: np.ndarray) -> dict:
    ambos = (ref >= 0) & (det >= 0)
    errores: dict = {}
    for r, d in zip(ref[ambos], det[ambos]):
        if r != d:
            errores[(nombre24(r), nombre24(d))] = errores.get((nombre24(r), nombre24(d)), 0) + 1
    return dict(cuadros=int(ambos.sum()),
                acuerdo=100 * float((ref[ambos] == det[ambos]).mean()) if ambos.any() else float("nan"),
                cuartos_ref=100 * float((ref[ref >= 0] % 2).mean()) if (ref >= 0).any() else 0.0,
                cuartos_circulo=100 * float((det[det >= 0] % 2).mean()) if (det >= 0).any() else 0.0,
                sin_referencia=100 * float(((det >= 0) & (ref < 0)).sum() / max((det >= 0).sum(), 1)),
                errores=sorted(errores.items(), key=lambda x: -x[1])[:5])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corrida", type=Path)
    ap.add_argument("--desde", type=float, default=42.0)
    ap.add_argument("--hasta", type=float, default=72.0)
    ap.add_argument("--barrido", action="store_true", help="ventanas de 30 s cada 6 s")
    a = ap.parse_args()

    al = M.Alignment("mata_zyklek")
    gu, ba = M.mapped(al, al.ref["guitars"]), M.mapped(al, al.ref["basses"])
    lead, low = M.lead_line(al, "mata_zyklek"), M.top_line(ba, low=True)
    J = json.loads((a.corrida / "line_diagnostics.json").read_text(encoding="utf-8"))
    hi, lo = M._notes(J["raw_high"]), M._notes(J["raw_bass"])
    sh, sb = M.calib(M.top_line(gu), hi), M.calib(low, lo)
    fin = max(n[1] for n in hi + lo) + 1
    largo = int(fin / DT)
    RA = rejilla([(n["t"], n["te"], n["p"]) for n in lead], largo)
    RG = rejilla([(n["t"], n["te"], n["p"]) for n in low], largo)
    CA, CG = rejilla(hi, largo, sh), rejilla(lo, largo, sb)
    print(f"desfase del cuaderno respecto de la partitura alineada: aguda {1000 * sh:.0f} ms, grave {1000 * sb:.0f} ms")

    def secciones(desde, hasta):
        return [nm for t0, t1, nm, kn in al.ref["sections"] if al.t(t1) > desde and al.t(t0) < hasta and kn]

    ventanas = [(x, x + 30.0) for x in range(0, int(fin) - 30, 6)] if a.barrido else [(a.desde, a.hasta)]
    for desde, hasta in ventanas:
        s = slice(int(desde / DT), int(hasta / DT))
        ag, gr = medir(RA[s], CA[s]), medir(RG[s], CG[s])
        if a.barrido:
            print(f"{desde:5.0f}–{hasta:3.0f} s  aguda {ag['acuerdo']:5.1f} %  grave {gr['acuerdo']:5.1f} %  "
                  f"cuartos de tono: referencia {ag['cuartos_ref']:3.0f} %, círculo {ag['cuartos_circulo']:3.0f} %  "
                  f"bajo sin referencia {gr['sin_referencia']:3.0f} %")
            continue
        print(f"{desde:g}–{hasta:g} s · secciones: {' | '.join(dict.fromkeys(secciones(desde, hasta)))}")
        for voz, m in (("aguda", ag), ("grave", gr)):
            print(f"  voz {voz}: mismo grado que la referencia en {m['acuerdo']:.1f} % de {m['cuadros']} cuadros; "
                  f"cuartos de tono: referencia {m['cuartos_ref']:.0f} %, círculo {m['cuartos_circulo']:.0f} %; "
                  f"el círculo suena donde la referencia calla: {m['sin_referencia']:.0f} %")
            print("    confusiones (referencia → círculo, cuadros):",
                  ", ".join(f"{r} → {d} ({n})" for (r, d), n in m["errores"]))


if __name__ == "__main__":
    main()
