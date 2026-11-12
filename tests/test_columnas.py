from tabroll.cells.columns_summary import columns_summary
from tabroll.cells.melodic_columns import melodic_columns

E = 8                                                                  # Mi en 24-EDO (cuartos de tono desde Do)


def bar(k, t0, root=E, cal='m', conf=1.0, ciclo='A'):
    return dict(compas=k, inicio_s=t0, fin_s=t0 + 4.0, fundamental_pc24=root, calidad=cal, confianza=conf, ciclo_aguda=ciclo)


def test_columna_principal_y_columnas_de_pulso():
    alta = [(0.0, 0.9, 64.0), (1.0, 1.4, 67.0), (1.5, 1.9, 69.0), (2.0, 2.9, 71.0), (3.0, 3.9, 67.0)]   # Mi Sol La Si Sol
    bajo = [(0.0, 4.0, 52.0)]                                                                          # Mi3 todo el compás
    r, vacio = melodic_columns([bar(1, 0.0), bar(2, 4.0)], bajo, alta, [4, 4])
    assert r['columna'] == 'E4 sobre E3' and r['columna_papel'] == 'fundamental' and r['columna_intervalo'] == '1'
    assert r['columna_pulso'] == 1 and r['columnas'] == '1 E4/E3 · 2 G4/E3 · 3 B4/E3 · 4 G4/E3'   # el La a contratiempo no
    assert [c['papel'] for c in r['columnas_pulso']] == ['fundamental', 'tercera', 'quinta', 'tercera']
    assert r['columnas_pulso'][0]['midi'] == 64.0 and r['columnas_pulso'][0]['bajo_midi'] == 52.0   # para dibujarla
    assert r['arco'] == 'arco' and r['cumbre'] == 'B4' and r['ambito_st'] == 7.0
    assert vacio['columna'] is None and vacio['columnas_pulso'] == []


def test_cuarto_de_tono_fuera_del_acorde_y_bajo_que_entra_despues():
    alta = [(0.0, 1.9, 64.5), (2.0, 3.9, 65.0)]                          # E+ (a 1/4 de tono de Mi) y Fa (fuera de Mi menor)
    bajo = [(0.1, 1.9, 52.0), (2.0, 4.0, 53.0)]                          # el bajo entra 0.1 s después
    r = melodic_columns([bar(1, 0.0)], bajo, alta, [4])[0]
    p1, p3 = r['columnas_pulso']
    assert p1['papel'] == 'fundamental (a 1/4 de tono)' and p1['en_acorde'] and p1['bajo'] == 'E3'
    assert p3['papel'] == 'fuera del acorde (♭2)' and p3['en_acorde'] is False and p3['intervalo'] == '1'
    assert r['columna_pulso'] == 1 and r['arco'] == 'plano'


def test_resumen_de_columnas_por_ciclo():
    alta = [(0.0, 3.9, 71.0), (4.0, 7.9, 71.0), (8.0, 11.9, 67.0)]
    bajo = [(0.0, 12.0, 52.0)]
    rows = melodic_columns([bar(1, 0.0), bar(2, 4.0), bar(3, 8.0, conf=0.2, ciclo='B')], bajo, alta, [4, 4, 4])
    cs = columns_summary(rows)
    assert cs['compases'] == 2 and cs['papeles'] == {'quinta': 100.0} and cs['intervalos'] == {'5': 100.0}
    assert cs['en_acorde'] == 100.0 and cs['pulsos'] == {'1': 100.0} and cs['arcos'] == {'plano': 100.0}
    assert cs['por_ciclo'] == {'A': dict(compases=2, columna='B4 sobre E3 (quinta)', veces=2, arco='plano')}
