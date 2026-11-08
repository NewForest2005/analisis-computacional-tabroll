import importlib.util
from pathlib import Path


REFERENCE = Path(__file__).parents[1] / "references" / "mata_zyklek_loops.py"


def load_reference():
    spec = importlib.util.spec_from_file_location("mata_zyklek_reference", REFERENCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_mata_reference_has_complete_bar_map():
    reference = load_reference()
    assert reference.N_BARS == 240
    assert reference.BEATS == 5
    assert set(reference.ARR) == {"G1", "G2", "G3", "G4", "B1", "B2"}


def test_mata_reference_contains_all_loop_patterns():
    reference = load_reference()
    assert len(reference.L) == 34
    assert len(reference.notes(reference.GUITARS + reference.BASSES)) == 6141


def test_written_pitch_is_one_octave_above_audio_pitch():
    reference = load_reference()
    written = reference.P("G4")
    assert reference.down([(0, 1, written)])[0][2] == written - 12
