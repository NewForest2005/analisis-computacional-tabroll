import numpy as np

from tabroll.cells.harmony_circle import harmony_circle
from tabroll.cells.harmony_layers import harmony_layers
from tabroll.evaluation.circulo import circle_distance, circular_emd


def bar(k, pc, conf=1.0, label="A"):
    prof = np.zeros(24)
    prof[pc] = 1.0
    return dict(compas=k, inicio_s=float(k), fin_s=float(k + 1), fundamental_pc24=pc, calidad="5", confianza=conf,
                ciclo_bajo=label, perfil_bajo=prof.tolist(), perfil_aguda=prof.tolist())


def test_circle_is_counted_from_the_center_and_normalized():
    c = harmony_circle([bar(1, 8), bar(2, 8), bar(3, 22)], center_pc24=8)       # Mi, Mi, Si con centro en Mi
    assert abs(sum(c["fundamentales"]) - 1) < 1e-3 and c["fundamentales"][0] > c["fundamentales"][14] > 0
    assert c["posiciones"][14] == "5" and c["cambios"] == 1 and c["movimientos"]["fuerte"] == 1.0


def test_neutral_intervals_are_intermediate():
    c = harmony_circle([bar(1, 0), bar(2, 3), bar(3, 0), bar(4, 7)], 0)        # 1 → ♭2+ → 1 → ♭3+
    assert c["movimientos"]["intermedio"] == 1.0
    assert harmony_layers([bar(1, 0), bar(2, 7)], 0)["movimientos"]["intermedio"] == 1.0


def test_each_distinct_cycle_counts_once():
    bars = [bar(k, 0, label="A") for k in range(1, 10)] + [bar(10, 14, label="B")]
    c = harmony_circle(bars, 0)
    assert c["fundamentales_por_ciclo"][0] == c["fundamentales_por_ciclo"][14] == 0.5


def test_bars_without_cycle_count_together_as_one_more_cycle():
    bars = [bar(k, 0, label="A") for k in range(1, 10)] + [bar(k, 14, label=None) for k in range(10, 40)]
    c = harmony_circle(bars, 0)
    assert c["fundamentales_por_ciclo"][0] == c["fundamentales_por_ciclo"][14] == 0.5
    assert c["ciclos_distintos"] == 1 and abs(c["tiempo_sin_ciclo"] - 100 * 30 / 39) < 0.1


def test_distances():
    a, b = np.zeros(24), np.zeros(24)
    a[0], b[12] = 1, 1
    assert circular_emd(a, a) == 0 and abs(circular_emd(a, b) - 1) < 1e-9
    c1 = harmony_circle([bar(k, 0) for k in range(1, 9)], 0)
    c2 = harmony_circle([bar(k, 14) for k in range(1, 9)], 0)
    assert circle_distance(c1, c1)["combinada"] == 0 and circle_distance(c1, c2)["combinada"] > 0.1


def test_figure_does_not_need_pyplot_or_a_window(tmp_path):
    import subprocess
    import sys
    from pathlib import Path
    code = (
        "import sys; from tabroll.cells.draw_harmony_circle import draw_harmony_circle\n"
        "from tabroll.cells.harmony_circle import harmony_circle\n"
        "bars = [dict(compas=k, inicio_s=float(k), fin_s=k + 1.0, fundamental_pc24=k % 2 * 14, calidad='5', confianza=1.0,\n"
        "             perfil_bajo=[1.0] + [0.0] * 23, perfil_aguda=[1.0] + [0.0] * 23) for k in range(8)]\n"
        f"p = draw_harmony_circle(harmony_circle(bars, 0), r'{tmp_path / 'c.png'}')\n"
        "assert p.stat().st_size > 1000 and 'matplotlib.pyplot' not in sys.modules\n")
    env = {"MPLBACKEND": "macosx", "PATH": "", "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src"),
           "MPLCONFIGDIR": str(tmp_path)}
    r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_refresh_rewrites_circle_and_figure_of_a_run(tmp_path):
    import json
    from tabroll.evaluation.circulo import refresh_run
    bars = [bar(k, 8 if k % 2 else 22) for k in range(1, 9)]
    (tmp_path / "armonia.json").write_text(json.dumps(dict(compases=bars, resumen=dict(centro="E", modo=dict(nombre="2, ♭3, 6, ♭7")))), encoding="utf-8")
    (tmp_path / "resumen.json").write_text(json.dumps(dict(cancion="Prueba")), encoding="utf-8")
    png = refresh_run(tmp_path)
    c = json.loads((tmp_path / "circulo.json").read_text(encoding="utf-8"))
    assert png.exists() and c["formato"].endswith("v2") and c["cancion"] == "Prueba" and c["centro"] == "E"



def test_transitions_and_movements_weigh_by_their_changes():
    from tabroll.evaluation.circulo import change_weight
    assert change_weight(4) == 0 and change_weight(6) == 0.3 and change_weight(20) == change_weight(80) == 1
    few_a = harmony_circle([bar(k, 0 if k % 2 else 14) for k in range(1, 8)], 0)      # 6 cambios 1 ↔ 5
    few_b = harmony_circle([bar(k, 0 if k % 2 else 3) for k in range(1, 8)], 0)       # 6 cambios 1 ↔ ♭2+
    d = circle_distance(few_a, few_b)
    assert d["peso_cambios"] == 0.3 and d["transiciones"] == d["movimientos"] == 1.0
    others = [v for k, v in d.items() if k not in ("transiciones", "movimientos", "combinada", "peso_cambios") and v is not None]
    assert abs(d["combinada"] - (sum(others) + 0.3 * 2) / (len(others) + 0.6)) < 2e-3
