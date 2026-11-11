from tabroll.cells.chord_roles import chord_roles
from tabroll.cells.roles_summary import roles_summary

E = 8                                                                  # Mi en 24-EDO (cuartos de tono desde Do)


def bar(k, root, cal, bass, top, conf=1.0):
    pa = [0.0] * 24
    pa[top % 24] = 1.0
    return dict(compas=k, inicio_s=float(k), fin_s=k + 1.0, fundamental_pc24=root % 24, calidad=cal,
                bajo_pc24=bass % 24, bajo='X', perfil_aguda=pa, confianza=conf)


def test_cifrado_funcion_e_inversion():
    g = chord_roles([bar(1, E + 6, 'M', E + 6 + 14, E + 6 + 8)], E)[0]       # Sol mayor con Re en el bajo y Si arriba, en Mi
    assert g['cifrado'] == '♭III' and g['funcion'] == 'tónica' and g['matiz'] == 'relativa' and g['funcion_corta'] == 'T'
    assert g['inversion'] == '2.ª inversión' and g['cifra_bajo'] == '6/4'
    assert g['papel_aguda'] == 'tercera' and g['aguda_en_acorde'] == 100.0


def test_dominante_modal_y_grado_neutro():
    v = chord_roles([bar(1, E + 14, 'm', E + 14, E + 14)], E)[0]              # v menor: dominante sin sensible
    assert v['cifrado'] == 'v' and v['funcion'] == 'dominante' and v['matiz'] == 'modal, sin sensible'
    assert v['funcion_corta'] == 'd' and v['inversion'] == 'fundamental' and v['cifra_bajo'] == ''
    n = chord_roles([bar(1, E + 3, 'M', E + 3, E + 3)], E)[0]               # ♭2+ mayor: grado de cuarto de tono
    assert n['cifrado'] == '♭II+' and n['funcion'] == 'neutra' and n['matiz'] == 'entre ♭2 y 2' and n['funcion_corta'] == 'N'


def test_bajo_fuera_del_acorde_y_resumen():
    rows = chord_roles([bar(1, E, 'm', E + 4, E + 20), bar(2, E, 'm', E, E, conf=0.2)], E)
    assert rows[0]['inversion'] == 'bajo fuera del acorde' and rows[0]['cifra_bajo'] == '/X'
    assert rows[0]['papel_aguda'] == 'fuera del acorde (♭7 sobre la fundamental)' and rows[0]['aguda_en_acorde'] == 0.0
    s = roles_summary(rows)
    assert s['compases_confiables'] == 1 and s['funciones'] == {'tónica': 100.0} and s['cifrados'] == {'i': 100.0}
