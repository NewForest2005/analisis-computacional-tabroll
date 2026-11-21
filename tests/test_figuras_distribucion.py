"""Distribución de las figuras comparativas: nada se monta, nada se sale y no quedan franjas vacías grandes.

Las figuras se arman con datos sintéticos del mismo tamaño que los reales (6 canciones de la banda, 36 en total).
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("matplotlib")

ROOT = Path(__file__).parents[1]
CARPETA = ROOT / "scripts" / "comparacion"
sys.path.insert(0, str(CARPETA))

import estilo_figuras  # noqa: E402

estilo_figuras.preparar()
ARTISTAS = list(estilo_figuras.PALETA_ARTISTA)
BANDA = ["Fabienk", "Mata zyklek", "Sarniezz", "Utzp", "Yor zarad", "Angor"]
NOMBRES = BANDA + [f"Canción de referencia con nombre largo {i}" for i in range(30)]


def cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, CARPETA / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def sin_problemas(fig):
    import matplotlib.pyplot as plt

    problemas = estilo_figuras.revisar(fig)
    plt.close(fig)
    assert problemas == []


def test_clasificacion():
    rng = np.random.default_rng(0)
    corpora = ["rock", "jazz", "hindustani", "pop", "clasica", "radif"]
    bloques = ["armonia", "escala", "microtono", "metro"]
    canciones = [{"cancion": c, "grupo": "banda",
                  "percentiles": {k: {b: float(rng.uniform(0, 80)) for b in bloques[:2]} for k in corpora},
                  "mejor_por_bloque": {b: {"corpus": corpora[i % 2 * 5], "percentil": float(rng.uniform(0, 20))}
                                       for i, b in enumerate(bloques)}} for c in BANDA]
    sin_problemas(cargar("figuras_album").figura_clasificacion({"umbral": 5, "canciones": canciones}))


def test_tarjetas():
    modulo = cargar("comparar_tarjetas")
    rng = np.random.default_rng(1)
    filas = [{"grupo": ARTISTAS[min(i // 6, 5)], "cancion": n, "cambios_distintos": int(rng.integers(0, 40)),
              **{m: (None if i == 1 and m == "novedad_progresion" else round(float(rng.uniform(0, 90)), 1)) for m, _ in modulo.MEDIDAS}}
             for i, n in enumerate(NOMBRES)]
    sin_problemas(modulo.dibujar(filas, list(dict.fromkeys(f["grupo"] for f in filas))))


def test_verosimilitud_matriz_y_mapa():
    modulo = cargar("verosimilitud_estilos")
    rng = np.random.default_rng(2)
    est = list(modulo.ESTILOS)
    filas = [{"cancion": n, "corrida": n.lower(), "fundamentales_cuarto_de_tono": float(i % 3) * 4.2,
              "fundamentales": {g: float(v) for g, v in zip(modulo.GRADOS, rng.dirichlet(np.ones(12)) * 100)},
              **{f"percentil_{e}": round(float(rng.uniform(0, 90)), 1) for e in est}} for i, n in enumerate(NOMBRES)]
    C = {e: [{"fundamentales": list(rng.dirichlet(np.ones(12)))} for _ in range(80)] for e in est}
    sin_problemas(modulo.figura_matriz(filas, est))
    sin_problemas(modulo.figura_mapa(filas, C))


def test_ciclos():
    modulo = cargar("ciclos_metricos")
    rng = np.random.default_rng(3)
    lags = np.arange(2, 41)
    curvas = [(n[:28], rng.uniform(0.2, 0.9, len(lags)), ARTISTAS[min(i // 6, 5)]) for i, n in enumerate(NOMBRES)]
    sin_problemas(modulo.dibujar(curvas, lags))


def test_revisar_detecta_problemas():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1], [0, 1], label="datos")
    ax.legend(loc="center")
    ax.text(0.5, 0.5, "montado sobre la leyenda", transform=ax.transAxes)
    fig.text(0.98, 0.5, "este texto se sale por la derecha")
    problemas = estilo_figuras.revisar(fig)
    plt.close(fig)
    assert any("leyenda sobre un gráfico" in p for p in problemas)
    assert any("textos montados" in p for p in problemas)
    assert any("se sale de la figura" in p for p in problemas)


def test_partir_respeta_el_ancho():
    texto = estilo_figuras.partir("palabra " * 60, 4.0, 10)
    assert max(len(linea) for linea in texto.split("\n")) <= int(4.0 * 72 / (10 * 0.56))
