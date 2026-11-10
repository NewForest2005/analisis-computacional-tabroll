import numpy as np

from tabroll.cells.center24_by_layer import center24_by_layer
from tabroll.cells.chord24 import chord24
from tabroll.cells.harmony_layers import harmony_layers
from tabroll.cells.mode24 import mode24


def bar(k, pc, quality="5", conf=1.0, bass=None, upper=None):
    return dict(compas=k, inicio_s=float(k), fin_s=float(k + 1), fundamental_pc24=pc, calidad=quality, confianza=conf,
                perfil_bajo=bass if bass is not None else [0.0] * 24, perfil_aguda=upper if upper is not None else [0.0] * 24)


def test_center_is_the_bass_note_that_rules_the_cycle():
    bass = []
    for turn in range(4):                                                   # vuelta de 2 s: Re largo, Mi corto, vuelve a Re
        t = 2.0 * turn
        bass += [(t, t + 1.2, 38.0), (t + 1.2, t + 1.6, 40.0), (t + 1.6, t + 2.0, 38.0)]
    high = [(t, t + 0.5, 62.0) for t in np.arange(0, 8, 0.5)]
    cycles = {"Voz grave": [dict(start=0.0, end=8.0, period=2.0)], "Voz aguda": []}
    c = center24_by_layer(bass, high, cycles)
    assert c["centro_bajo_pc24"] == 4 and c["centro_pc24"] == 4               # Re
    assert 0 < c["margen"] <= 1


def test_mode_reads_degrees_2_3_6_7_in_24_edo():
    prof = np.zeros(24)
    for pc, w in ((0, 5), (3, 2), (6, 2), (14, 3), (18, 1), (20, 2)):        # 1, ♭2+, ♭3, 5, 6, ♭7
        prof[pc] = w
    m = mode24([bar(1, 0, bass=prof.tolist())], 0)
    assert m["grados"] == {"2": "♭2+", "3": "♭3", "6": "6", "7": "♭7"}


def test_layers_classify_root_motion():
    bars = [bar(1, 0), bar(2, 14), bar(3, 15), bar(4, 15), bar(5, 0, conf=0.1)]   # Do→Sol (fuerte), Sol→Sol+ (deslizamiento)
    L = harmony_layers(bars, 0)
    assert L["movimientos"]["fuerte"] == 0.5 and L["movimientos"]["deslizamiento"] == 0.5
    assert L["cambios_por_compas"] == round(2 / 3, 3)                          # el compás 5 no es confiable


def test_exact_ties_are_resolved_the_same_way():
    upper = np.zeros(24)
    upper[[4, 8, 18]] = 1.0                                                  # Re Mi La: Re sus2 = La sus4
    results = {(chord24(np.zeros(24), upper * s)["fundamental"]) for s in (1.0, 0.1, 3.0, 7.0)}
    assert len(results) == 1


def test_ear_tonic_reads_run_names():
    from tabroll.evaluation.armonia import ear_tonic
    assert ear_tonic("Angine de Poitrine - Utzp (audio officiel)") == "E"
    assert ear_tonic("2026-11-09_195916_angine_de_poitrine_yor_zarad_audio_offic_armonia_paso2") == "G"
    assert ear_tonic("otra cancion") is None


def test_bass_ties_are_the_same_on_any_machine():
    from tabroll.evaluation.armonia import _tied_max
    b = np.zeros(24)
    b[4], b[8] = 1.0, 1.0 + 1e-12
    assert _tied_max(b) == [4, 8]
    assert _tied_max(np.zeros(24)) == []
    upper = np.zeros(24)
    upper[[4, 8, 12]] = 1.0
    assert chord24(b, upper)["bajo"] == 4

