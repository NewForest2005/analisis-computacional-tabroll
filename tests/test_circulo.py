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


def test_distances():
    a, b = np.zeros(24), np.zeros(24)
    a[0], b[12] = 1, 1
    assert circular_emd(a, a) == 0 and abs(circular_emd(a, b) - 1) < 1e-9
    c1 = harmony_circle([bar(k, 0) for k in range(1, 9)], 0)
    c2 = harmony_circle([bar(k, 14) for k in range(1, 9)], 0)
    assert circle_distance(c1, c1)["combinada"] == 0 and circle_distance(c1, c2)["combinada"] > 0.1

