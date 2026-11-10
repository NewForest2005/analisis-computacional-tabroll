import numpy as np

from tabroll.cells.bar_spans import bar_spans
from tabroll.cells.chord24 import chord24
from tabroll.cells.fold_bar_profiles import fold_bar_profiles
from tabroll.cells.notetable import NoteTable


def profile(*pcs):
    h = np.zeros(24)
    for pc in pcs:
        h[pc] += 1.0
    return h


def test_bar_spans_follow_the_real_beats():
    assert bar_spans(np.arange(8.0), [4, 4]) == [(0.0, 4.0), (4.0, 8.0)]


def test_major_minor_neutral_and_fifth():
    assert chord24(profile(0), profile(0, 8, 14))["calidad"] == "M"       # Do Mi Sol
    assert chord24(profile(0), profile(0, 6, 14))["calidad"] == "m"       # Do Mib Sol
    assert chord24(profile(0), profile(0, 7, 14))["calidad"] == "n"       # Do Mib+ Sol: tercera neutra
    r = chord24(profile(0), profile(0, 14))
    assert (r["fundamental"], r["calidad"]) == (0, "5")


def test_quarter_tone_root():
    r = chord24(profile(9), profile(9, 17, 23))                            # Mi+ con tríada mayor sobre Mi+
    assert r["fundamental"] == 9 and r["calidad"] == "M"


def test_folding_sums_the_turns_of_a_cycle():
    notes = [(t, t + 1.0, 60.0) for t in (0.0, 2.0, 4.0, 6.0)]           # el mismo Do en cada vuelta de 2 s
    cycle = dict(start=0.0, end=8.0, period=2.0, label="A")
    prof, info = fold_bar_profiles([(0.0, 2.0)], NoteTable(notes), [cycle])
    assert info[0]["vueltas"] == 4 and abs(info[0]["acuerdo"] - 1.0) < 1e-9
    assert abs(prof[0][0] - 4.0) < 1e-9


def test_short_notes_do_not_count():
    t = NoteTable([(0.0, 0.05, 61.0), (0.0, 1.0, 60.0)])
    assert t.profile(0.0, 1.0, min_dur=0.1)[2] == 0.0
