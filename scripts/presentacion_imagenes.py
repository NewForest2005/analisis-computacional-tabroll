"""Copia a presentacion/img/ las gráficas que usa la presentación, desde las corridas más recientes de outputs/.

Uso:
    python scripts/presentacion_imagenes.py            # o: make presentacion-imagenes

- Las seis gráficas de resultados salen de la carpeta outputs/graficas_clave_*/diapositivas/ más reciente
  (la crea `make graficas-diapositivas`).
- Los tabroll de ejemplo son páginas de Sarniezz y Fabienk de la corrida más reciente con Demucs (sin «_roformer»).
Las imágenes que no salen de este repositorio se ponen a mano en presentacion/img/: la captura de Hooktheory
(hooktheory_fabienk.png) y las figuras del primer cuaderno: cuaderno_original_sarniezz.png se copió de sus salidas y
original_*.png las dibuja scripts/comparacion/figuras_cuaderno_original.py con su audio_arrays.npz.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "outputs"
IMG = RAIZ / "presentacion" / "img"
TABROLLS = [("_sarniezz_", "tabroll24_p08.png", "tabroll_sarniezz.png"),      # ♭VII sus2 y ♭III
            ("fabienk_official", "tabroll24_p01.png", "tabroll_fabienk.png")]   # el comienzo, para comparar con Hooktheory


def mas_reciente(patron: str, filtro=lambda p: True) -> Path | None:
    candidatos = sorted((p for p in OUT.glob(patron) if filtro(p)), key=lambda p: str(p.relative_to(OUT)))
    return candidatos[-1] if candidatos else None


def main() -> int:
    IMG.mkdir(parents=True, exist_ok=True)
    copiadas = 0
    diap = mas_reciente("graficas_clave_*/diapositivas")
    if diap is None:
        print("No hay outputs/graficas_clave_*/diapositivas: corre antes make graficas-diapositivas.", file=sys.stderr)
    else:
        for png in sorted(diap.glob("*.png")):
            shutil.copy2(png, IMG / png.name)
            copiadas += 1
        print(f"gráficas de resultados: {diap.relative_to(RAIZ)}")
    for clave, pagina, destino in TABROLLS:
        corrida = mas_reciente(f"*{clave}*", lambda p: p.is_dir() and "roformer" not in p.name
                               and any(p.glob(f"harmony_outputs/*/{pagina}")))
        if corrida is None:
            print(f"No hay una corrida de {clave.strip('_')} con {pagina}.", file=sys.stderr)
            continue
        shutil.copy2(next(corrida.glob(f"harmony_outputs/*/{pagina}")), IMG / destino)
        copiadas += 1
        print(f"tabroll: {corrida.name} → {destino}")
    print(f"{copiadas} imágenes en {IMG.relative_to(RAIZ)}")
    return 0 if copiadas else 1


if __name__ == "__main__":
    raise SystemExit(main())
