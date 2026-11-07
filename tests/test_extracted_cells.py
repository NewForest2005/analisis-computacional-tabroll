from pathlib import Path


ROOT = Path(__file__).parents[1]
CELLS = ROOT / "src" / "tabroll" / "cells"


def test_extracted_cells_are_python_files():
    files = sorted(CELLS.glob("*.py"))
    assert len(files) == 95  # 94 celdas + __init__.py
    assert all(path.read_text(encoding="utf-8").startswith('"""') for path in files)


def test_source_notebook_is_preserved():
    assert (ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb").is_file()


def test_function_named_modules_exist():
    expected = {"005_find_stem.py", "006_separate_stems.py", "076_render_song_graphic.py", "092_plot_cycle_map.py"}
    assert expected.issubset({path.name for path in CELLS.glob("*.py")})
