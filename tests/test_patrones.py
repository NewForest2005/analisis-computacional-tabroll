from types import SimpleNamespace

from tabroll.cells.cycle_patterns import cycle_patterns

E = 8


def vuelta(k, sol=55.0, la=True, extra=False):
    t = 2.0 * k
    notas = [(t, t + 0.4, 52.0), (t + 0.5, t + 0.9, sol), (t + 1.0, t + 1.4, 59.0)]
    notas += [(t + 1.5, t + 1.9, 57.0)] if la else []
    notas += [(t + 0.25, t + 0.4, 54.0)] if extra else []
    return notas


def test_patron_y_por_que_cada_vuelta_se_acoge_o_no():
    alta = vuelta(0) + vuelta(1) + vuelta(2, sol=55.5) + vuelta(3, la=False, extra=True)
    armonia = [dict(compas=k + 1, inicio_s=2.0 * k, fin_s=2.0 * k + 2.0, fundamental_pc24=E, calidad='m', cifrado='i')
               for k in range(4)]
    ciclos = {'Voz aguda': [SimpleNamespace(label='A', start=0.0, end=8.0, period=2.0)]}
    rows, pats = cycle_patterns(armonia, ciclos, {'Voz aguda': alta, 'Voz grave': []}, [4] * 4, E)
    a = pats['Voz aguda']['A']
    assert a['vueltas'] == 4 and a['notas'] == 4 and a['slots'] == 16
    assert a['patron'] == '1.1 E3 1 (fund.) · 2.1 G3 ♭3 (3.ª) · 3.1 B3 5 (5.ª) · 4.1 A3 4 (disonante)'
    assert a['acoge'] == 87.5 and a['iguales'] == 50.0 and a['disonantes'] == 1 and a['resuelven'] == 0.0
    assert a['motivos'] == {'igual al patrón': 50.0, 'inflexión de ¼ de tono': 25.0, 'notas omitidas': 25.0,
                            'notas agregadas': 25.0}
    assert a['termina'] == '4' and a['cierra'] == 'abierto' and a['acorde_usual'] == 'i'
    assert rows[0]['acoge_aguda'] == 100.0 and rows[0]['motivo_aguda'] == 'igual al patrón'
    assert rows[2]['acoge_aguda'] == 75.0 and rows[2]['motivo_aguda'] == 'inflexión de ¼ de tono'
    assert rows[3]['motivo_aguda'] == 'notas omitidas; notas agregadas' and rows[3]['acoge_bajo'] is None


def test_resuelve_por_grado_y_cambia_el_acorde():
    alta = []
    for k in range(4):
        t = 2.0 * k
        alta += [(t, t + 0.4, 52.0), (t + 0.5, t + 0.9, 57.0), (t + 1.0, t + 1.9, 55.0)]
    armonia = [dict(compas=k + 1, inicio_s=2.0 * k, fin_s=2.0 * k + 2.0, fundamental_pc24=E, calidad='m',
                    cifrado='iv' if k == 3 else 'i') for k in range(4)]
    ciclos = {'Voz aguda': [SimpleNamespace(label='A', start=0.0, end=8.0, period=2.0)]}
    rows, pats = cycle_patterns(armonia, ciclos, {'Voz aguda': alta}, [4] * 4, E)
    a = pats['Voz aguda']['A']
    assert a['patron'] == '1.1 E3 1 (fund.) · 2.1 A3 4 (disonante → ♭3) · 3.1 G3 ♭3 (3.ª)' and a['resuelven'] == 100.0
    assert a['motivos'] == {'igual al patrón': 100.0, 'cambia el acorde': 25.0}
    assert rows[3]['motivo_aguda'] == 'igual al patrón; cambia el acorde (iv)'
