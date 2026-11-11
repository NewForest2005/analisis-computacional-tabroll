from tabroll.cells.chord_progressions import chord_progressions
from tabroll.cells.chord_roles import chord_roles
from tabroll.cells.harmony_labels import harmony_labels
from tabroll.cells.roles_summary import roles_summary

E = 8                                                                  # Mi en 24-EDO (cuartos de tono desde Do)


def bar(k, root, cal, bass, top, conf=1.0):
    pa = [0.0] * 24
    pa[top % 24] = 1.0
    return dict(compas=k, inicio_s=float(k), fin_s=k + 1.0, fundamental_pc24=root % 24, calidad=cal,
                bajo_pc24=bass % 24, bajo='X', perfil_aguda=pa, confianza=conf)


def test_cifrado_grado_funcion_e_inversion():
    g = chord_roles([bar(1, E + 6, 'M', E + 6 + 14, E + 6 + 8)], E)[0]       # Sol mayor con Re en el bajo y Si arriba, en Mi
    assert g['cifrado'] == '♭III' and g['nombre_grado'] == 'mediante rebajada' and g['clase_grado'] == 'modal'
    assert g['funcion'] == 'tónica' and g['funcion_texto'] == 'tónica mayor (relativa)' and g['funcion_corta'] == 'T'
    assert g['inversion'] == '2.ª inversión' and g['cifra_bajo'] == '6/4'
    assert g['papel_aguda'] == 'tercera' and g['aguda_en_acorde'] == 100.0


def test_dominante_menor_subtonica_y_grado_neutro():
    v = chord_roles([bar(1, E + 14, 'm', E + 14, E + 14)], E)[0]              # v menor: dominante sin sensible
    assert v['cifrado'] == 'v' and v['nombre_grado'] == 'dominante' and v['funcion_corta'] == 'd'
    assert v['funcion_texto'] == 'dominante menor (modal, sin sensible)' and v['inversion'] == 'fundamental'
    s = chord_roles([bar(1, E + 20, 'M', E + 20, E + 20)], E)[0]              # ♭VII mayor: subtónica
    assert s['cifrado'] == '♭VII' and s['nombre_grado'] == 'subtónica' and s['funcion'] == 'dominante'
    iv = chord_roles([bar(1, E + 10, 'm', E + 10, E + 10)], E)[0]             # iv: subdominante menor
    assert iv['funcion_texto'] == 'subdominante menor' and iv['nombre_grado'] == 'subdominante'
    n = chord_roles([bar(1, E + 3, 'M', E + 3, E + 3)], E)[0]               # ♭2+ mayor: supertónica neutra
    assert n['cifrado'] == '♭II+' and n['nombre_grado'] == 'supertónica neutra' and n['funcion'] == 'neutra'
    assert n['matiz'] == 'entre ♭2 y 2' and n['funcion_corta'] == 'N'


def test_bajo_a_un_cuarto_de_tono_y_fuera_del_acorde():
    a = chord_roles([bar(1, E, 'sus2', E + 3, E)], E)[0]                     # el bajo, un cuarto de tono bajo la 2.ª
    assert a['inversion'] == '1.ª inversión (bajo a 1/4 de tono)' and a['cifra_bajo'] == '6'
    rows = chord_roles([bar(1, E, 'm', E + 10, E + 20), bar(2, E, 'm', E, E, conf=0.2)], E)
    assert rows[0]['inversion'] == 'bajo fuera del acorde' and rows[0]['cifra_bajo'] == '/X'
    assert rows[0]['papel_aguda'] == 'fuera del acorde (♭7 sobre la fundamental)' and rows[0]['aguda_en_acorde'] == 0.0
    s = roles_summary(rows)
    assert s['compases_confiables'] == 1 and s['funciones'] == {'tónica': 100.0} and s['nombres_grado'] == {'tónica': 100.0}


def test_progresiones_piston_y_con_nombre():
    seq = [(E, 'm'), (E + 20, 'M'), (E + 16, 'M'), (E + 14, 'M'), (E, 'm')]   # i - ♭VII - ♭VI - V - i
    rows = chord_roles([bar(k, r, c, r, r) for k, (r, c) in enumerate(seq, 1)], E)
    rows, pr = chord_progressions(rows, menor=True)
    pr = pr['confiables']
    assert rows[1]['progresion'] == 'i → ♭VII' and rows[1]['uso_piston'] == 'usual' and rows[1]['movimiento'] == 'segunda'
    assert rows[2]['uso_piston'] == 'a veces'                                  # ♭VII → ♭VI en menor (p. 45)
    assert rows[4]['movimiento'] == 'quinta abajo (como V-I)' and rows[4]['uso_piston'] == 'usual'
    assert pr['cambios'] == 4 and pr['por_quintas'] == 25.0 and pr['compases'] == 5
    assert 'cadencia andaluza i-♭VII-♭VI-V' in pr['con_nombre'] and 'cadencia auténtica V-I' in pr['con_nombre']


def test_vaiven_entre_dos_acordes():
    seq = [E + 6, E + 20, E + 6, E + 20, E + 6]                               # ♭III ↔ ♭VII, como en Sarniezz
    rows = chord_roles([bar(k, r, 'M', r, r) for k, r in enumerate(seq, 1)], E)
    rows, pr = chord_progressions(rows, menor=True)
    assert pr['confiables']['vaivenes'] == {'♭III ↔ ♭VII': 2} and pr['confiables']['por_quintas'] == 100.0
    assert pr['todos'] == {**pr['confiables'], 'umbral': 0.0}                 # todos confiables: los dos resúmenes coinciden


def test_dos_resumenes_confiables_y_todos():
    seq = [(E, 1.0), (E + 3, 0.2), (E, 1.0), (E + 3, 0.2), (E, 1.0)]          # I5 ↔ ♭II+5 con el ♭II+ poco confiable
    rows = chord_roles([bar(k, r, '5', r, r, conf=c) for k, (r, c) in enumerate(seq, 1)], E)
    rows, pr = chord_progressions(rows)
    assert pr['confiables']['cambios'] == 0 and pr['confiables']['compases'] == 3
    assert pr['todos']['cambios'] == 4 and pr['todos']['compases'] == 5 and pr['todos']['por_quintas'] == 0.0
    assert pr['todos']['vaivenes'] == {'I5 ↔ ♭II+5': 2} and pr['todos']['movimientos'] == {'microtonal': 100.0}
    assert all(r['progresion'] is None for r in rows)                         # las columnas salen de los confiables


def test_etiquetas_del_tabroll():
    rows = chord_roles([bar(1, E + 6, 'M', E + 6 + 14, E + 6),                # Sol con Re en el bajo
                        bar(2, E + 20, 'sus2', E, E, conf=0.3),                # Re sus2 con Mi en el bajo, poco confiable
                        bar(3, E + 3, '5', E + 3, E + 3),                      # ♭II+ sin tercera
                        bar(4, E, 'dism', E, E),
                        bar(5, E + 22, 'M', E + 22, E + 22)], E)               # VII mayor: función D, eje S
    g, d, n, i, v = harmony_labels(rows, tonic_midi=64)                       # Mi4: la escala del tabroll empieza en Mi
    assert g['numeral'] == '♭III^{6}_{4}' and g['name'] == 'G/D' and g['annot'] == 'T rel.'
    assert g['annot_color'] == '#f2d49b' and g['tones'] == [300.0, 700.0, 1000.0]
    assert d['numeral'] == '(♭VII_{sus2}^{6})' and d['name'] == '(Dsus2/E)' and d['annot'] == 'D modal'
    assert n['numeral'] == '♭II{+}_{5}' and n['name'] == 'F+5' and n['annot'] == 'N · eje D–S' and n['tones'][0] == 150.0
    assert i['numeral'] == 'i^{°}' and i['name'] == 'E°' and i['annot'] == 't'
    assert v['numeral'] == 'VII' and v['annot'] == 'D sens. · eje S'


def test_ejes_de_lendvai():
    grados = {0: ('tónica', 'polo'), 12: ('tónica', 'contrapolo'), 6: ('tónica', 'rama secundaria'),
              18: ('tónica', 'rama secundaria'), 14: ('dominante', 'polo'), 2: ('dominante', 'contrapolo'),
              8: ('dominante', 'rama secundaria'), 20: ('dominante', 'rama secundaria'), 10: ('subdominante', 'polo'),
              22: ('subdominante', 'contrapolo'), 4: ('subdominante', 'rama secundaria'), 16: ('subdominante', 'rama secundaria')}
    rows = chord_roles([bar(k, E + q, 'M', E + q, E + q) for k, q in enumerate(grados, 1)], E)
    assert [(r['eje'], r['rama']) for r in rows] == list(grados.values())
    n = chord_roles([bar(1, E + 3, '5', E + 3, E + 3)], E)[0]               # ♭2+: entre ♭2 (dominante) y 2 (subdominante)
    assert n['eje'] == 'entre dominante y subdominante' and n['eje_corto'] == 'D–S' and n['rama'] is None


def test_pasos_entre_ejes():
    seq = [(E, 'M'), (E + 6, 'M'), (E + 20, 'M'), (E, 'M'), (E + 10, 'M'), (E + 3, '5')]   # I ♭III ♭VII I IV ♭II+
    rows = chord_roles([bar(k, r, c, r, r) for k, (r, c) in enumerate(seq, 1)], E)
    rows, pr = chord_progressions(rows)
    assert [r['paso_eje'] for r in rows[1:]] == ['mismo eje (sustitución)', 'atrás (T→D→S→T)', 'adelante (T→S→D→T)',
                                                  'adelante (T→S→D→T)', 'microtonal']
    assert [r['eje_cambio'] for r in rows[1:]] == ['T → T', 'T → D', 'D → T', 'T → S', 'S → D–S']
    assert pr['confiables']['ejes'] == {'adelante (T→S→D→T)': 40.0, 'mismo eje (sustitución)': 20.0,
                                        'atrás (T→D→S→T)': 20.0, 'microtonal': 20.0}
    assert roles_summary(rows)['ejes'] == {'tónica': 50.0, 'dominante': 16.7, 'subdominante': 16.7,
                                           'entre dominante y subdominante': 16.7}


def test_evaluacion_compara_funciones_y_progresiones():
    from tabroll.evaluation.armonia import _progressions, _shares
    seq = [E + 6, E + 20, E + 6, E + 20, E + 6]                               # ♭III ↔ ♭VII: 3 compases de tónica, 2 de dominante
    rows = chord_roles([bar(k, r, 'M', r, r) for k, r in enumerate(seq, 1)], E)
    assert _shares(rows, 'funcion') == {'tónica': 60.0, 'dominante': 40.0}
    p = _progressions(rows, menor=True)
    assert p['cambios'] == 4 and p['por_quintas'] == 100.0 and p['vaivenes'] == {'♭III ↔ ♭VII': 2}
