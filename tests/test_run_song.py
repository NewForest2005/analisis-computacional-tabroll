import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("run_song", ROOT / "scripts" / "run_song.py")
run_song = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_song)


def settings_cell(cells):
    return next(source for _, source in cells if source.startswith("KEY_OVERRIDE"))


def test_presets_come_from_the_notebook():
    assert {"fabienk", "mata_zyklek"} <= set(run_song.find_presets(run_song.load_code_cells()))


def test_preset_uncomments_its_line():
    source = settings_cell(run_song.apply_changes(run_song.load_code_cells(), "fabienk", {}))
    assert "\nBAR_LENGTHS, BEAT_DIV, GRID = (7, 5, 4, 2), 2, 0.5" in source
    compile(source, "ajustes", "exec")


def test_set_goes_after_the_last_assignment():
    lines = settings_cell(run_song.apply_changes(run_song.load_code_cells(), "fabienk", {"GRID": "1 / 3"})).splitlines()
    preset = next(j for j, line in enumerate(lines) if line.startswith("BAR_LENGTHS, BEAT_DIV, GRID ="))
    assert lines[preset + 1].startswith("GRID = 1 / 3")


def test_set_can_turn_off_demucs():
    cells = run_song.apply_changes(run_song.load_code_cells(), None, {"SEPARATE": "False"})
    source = next(source for _, source in cells if "SEPARATE = True" in source)
    assert "\nSEPARATE = False" in source


def test_unknown_variable_or_preset_is_rejected():
    with pytest.raises(SystemExit):
        run_song.apply_changes(run_song.load_code_cells(), None, {"NO_EXISTE": "1"})
    with pytest.raises(SystemExit):
        run_song.apply_changes(run_song.load_code_cells(), "no_existe", {})


def test_notebook_is_not_modified():
    before = (ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb").read_bytes()
    run_song.apply_changes(run_song.load_code_cells(), "fabienk", {"GRID": "0.5"})
    assert (ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb").read_bytes() == before
