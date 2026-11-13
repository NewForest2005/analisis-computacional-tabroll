from types import SimpleNamespace

from tabroll.cells.local_centers import local_centers

E = 8


def tramo(t0, vueltas, centro, otra):
    notas = []
    for k in range(vueltas):
        t = t0 + 2.0 * k
        notas += [(t, t + 1.2, centro), (t + 1.2, t + 1.6, otra), (t + 1.6, t + 2.0, centro)]
    return notas


def test_centro_por_tramo_y_modulaciones():
    bajo = tramo(0.0, 4, 40.0, 47.0) + tramo(8.0, 4, 45.0, 40.0) + tramo(16.0, 4, 44.5, 40.0)
    armonia = [dict(compas=k + 1, inicio_s=2.0 * k, fin_s=2.0 * k + 2.0, confianza=1.0,
                    perfil_bajo=[0.0] * 24, perfil_aguda=[0.0] * 24) for k in range(12)]
    ciclos = {'Voz grave': [SimpleNamespace(label=l, start=a, end=a + 8.0, period=2.0)
                            for l, a in (('A', 0.0), ('B', 8.0), ('C', 16.0))], 'Voz aguda': []}
    rows, cl = local_centers(armonia, bajo, [], ciclos, E)
    a, b, c = cl['tramos']
    assert (a['centro'], a['grado'], a['respecto_del_centro']) == ('E', '1', 'mismo centro')
    assert (b['centro'], b['grado'], b['desde_el_anterior']) == ('A', '4', 'quinta abajo')
    assert (c['centro'], c['respecto_del_centro'], c['desde_el_anterior']) == ('G#+', 'microtonal (3+)', 'microtonal (7+)')
    assert all(x['seguro'] for x in (a, b, c)) and cl['modulaciones'] == 2 and cl['centro_estable'] == 33.3
    assert rows[0]['tramo'] == '0:00 A' and rows[0]['centro_local'] == 'E' and rows[11]['centro_local'] == 'G#+'
