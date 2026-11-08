import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
CELLS = ROOT / "src" / "tabroll" / "cells"
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
REGENERATE = "El notebook cambió y los módulos no: corre `python scripts/extract_cells.py`."

spec = importlib.util.spec_from_file_location("extract_cells", ROOT / "scripts" / "extract_cells.py")
extract_cells = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_cells)


def code_cells():
    cells = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
    return [(i, "".join(cell["source"])) for i, cell in enumerate(cells) if cell["cell_type"] == "code"]


def modules():
    return sorted(path for path in CELLS.glob("*.py") if path.name != "__init__.py")


def test_source_notebook_is_preserved():
    assert NOTEBOOK.is_file()


def test_one_module_per_code_cell():
    assert len(modules()) == len(code_cells()), REGENERATE


def test_modules_match_the_notebook():
    for order, (i, source) in enumerate(code_cells(), start=1):
        names = extract_cells.definitions(extract_cells.clean_jupyter_magics(source))
        expected = extract_cells.module_name(order, extract_cells.clean_jupyter_magics(source), names)
        path = CELLS / f"{expected}.py"
        assert path.is_file(), f"{path.name}: {REGENERATE}"
        text = path.read_text(encoding="utf-8")
        body = text.split('"""\n', 1)[1].strip("\n")
        assert path.stem == expected, f"{path.name}: {REGENERATE}"
        assert body == extract_cells.clean_jupyter_magics(source).strip("\n").rstrip(), f"{path.name}: {REGENERATE}"


def test_extracted_cells_are_valid_python():
    for path in modules():
        compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_function_named_modules_exist():
    names = {path.stem for path in modules()}
    assert {"find_stem", "separate_stems", "render_song_graphic", "plot_cycle_map"} <= names
