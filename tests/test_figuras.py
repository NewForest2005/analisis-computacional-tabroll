from tabroll.cells.melodic_figures import melodic_figures

E = 8                                                                  # Mi en 24-EDO (cuartos de tono desde Do)


def bar(k, t0, conf=1.0, ciclo='A'):
    return dict(compas=k, inicio_s=t0, fin_s=t0 + 4.0, fundamental_pc24=E, calidad='m', confianza=conf, ciclo_aguda=ciclo)


ALTA = [(0.0, 0.5, 64.0), (0.5, 1.0, 66.0), (1.0, 1.5, 67.0), (1.5, 2.0, 66.0),     # Mi Fa♯ Sol Fa♯
        (2.0, 2.5, 67.0), (2.5, 3.0, 67.5), (3.0, 3.5, 71.0), (3.5, 4.0, 71.0),     # Sol Sol+ Si Si
        (6.0, 6.5, 59.0)]                                                           # Si3 después de un silencio: otra frase


def test_intervalos_giros_y_espectro():
    rows, ml = melodic_figures([bar(1, 0.0), bar(2, 4.0)], ALTA, [4, 4], E)
    assert ml['notas'] == 9                                                        # 7 intervalos: ninguno entre frases
    assert ml['intervalos'] == {'semitono': 42.9, 'tono': 14.3, 'cuarto de tono': 14.3, 'tercera': 14.3, 'unísono': 14.3}
    assert ml['grado_conjunto'] == 71.4 and ml['saltos'] == 14.3 and ml['repetidas'] == 14.3
    assert ml['microtonales'] == 28.6 and ml['sube'] == 71.4 and ml['baja'] == 14.3   # ½ y 3½ semitonos son microtonales
    assert ml['giros'] == {'bordadura': 33.3, 'paso': 16.7, 'paso (¼)': 16.7, 'paso y salto (¼)': 16.7,
                           'repite y sigue (¼)': 16.7}
    assert ml['espectro'] == {'2': 22.2, '♭3': 22.2, '5': 33.3, '1': 11.1, '♭3+': 11.1} and ml['espectro_microtonal'] == 11.1
    assert rows[0]['giro_principal'] == 'bordadura' and rows[0]['salto_mayor'] == 3.5
    assert ml['por_ciclo'] == {'A': dict(giro='bordadura', parte=33.3)}


def test_notas_extranas_al_acorde():
    rows, ml = melodic_figures([bar(1, 0.0), bar(2, 4.0)], ALTA, [4, 4], E)
    assert rows[0]['notas_extranas'] == 'F#4 nota de paso; F#4 bordadura; G+4 inflexión de ¼ de tono'
    assert rows[1]['notas_extranas'] is None
    assert ml['notas_en_confiables'] == 9 and ml['extranas'] == 33.3
    assert ml['tipos_extranas'] == {'nota de paso': 33.3, 'bordadura': 33.3, 'inflexión de ¼ de tono': 33.3}
    _, poco = melodic_figures([bar(1, 0.0, conf=0.2), bar(2, 4.0, conf=0.2)], ALTA, [4, 4], E)
    assert poco['notas_en_confiables'] == 0 and poco['tipos_extranas'] == {}       # sin compases confiables no se cuentan
