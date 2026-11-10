from types import SimpleNamespace

from tabroll.cells.drop_loose_notes import drop_loose_notes


def test_short_notes_must_return_in_both_neighbouring_turns():
    cycles = {"Voz aguda": [SimpleNamespace(start=0.0, end=10.0, period=1.0)], "Voz grave": []}
    riff = [(k + 0.0, k + 0.05, 60.0) for k in range(10)]                      # nota corta que vuelve en cada vuelta
    loose = [(4.5, 4.55, 67.0)]                                                 # pedazo suelto
    long_ = [(6.3, 6.6, 70.0)]                                                  # larga, aunque no vuelva
    outside = [(12.0, 12.04, 72.0)]                                             # fuera del ciclo
    kept = drop_loose_notes(sorted(riff + loose + long_ + outside), cycles)
    assert (4.5, 4.55, 67.0) not in kept
    assert all(n in kept for n in riff[1:-1] + long_ + outside)
    assert (0.0, 0.05, 60.0) not in kept and (9.0, 9.05, 60.0) not in kept    # primera y última vuelta: les falta una vecina


def test_attacks_may_move_a_little_between_turns():
    cycles = {"Voz aguda": [SimpleNamespace(start=0.0, end=4.0, period=1.0)]}
    notes = [(0.0, 0.05, 60.0), (1.04, 1.09, 60.0), (1.97, 2.02, 60.0)]           # hasta 75 ms de corrimiento
    assert (1.04, 1.09, 60.0) in drop_loose_notes(notes, cycles)
    notes[2] = (1.95, 2.00, 60.0)                                                 # 90 ms: ya no cuenta como la misma
    assert (1.04, 1.09, 60.0) not in drop_loose_notes(notes, cycles)

