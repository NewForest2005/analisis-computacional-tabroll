"""La extracción no debe borrar en silencio cambios hechos a mano en los módulos."""

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("extract_cells", ROOT / "scripts" / "extract_cells.py")
extract_cells = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_cells)


def write_notebook(path: Path, body: str) -> None:
    cells = [
        {"cell_type": "markdown", "metadata": {}, "source": ["# Saludo"]},
        {"cell_type": "code", "metadata": {}, "source": [body], "outputs": [], "execution_count": None},
    ]
    path.write_text(json.dumps({"cells": cells, "metadata": {}, "nbformat": 4, "nbformat_minor": 5}), encoding="utf-8")


@pytest.fixture
def project(tmp_path):
    notebook = tmp_path / "nb.ipynb"
    output = tmp_path / "cells"
    index = tmp_path / "index.md"
    write_notebook(notebook, "def saludo():\n    return 'hola'\n")
    extract_cells.regenerate(notebook, output, index)
    return notebook, output, index


def test_check_passes_right_after_extraction(project):
    assert extract_cells.check(*project) == 0


def test_notebook_change_is_applied(project):
    notebook, output, index = project
    write_notebook(notebook, "def saludo():\n    return 'buenas'\n")
    assert extract_cells.check(*project) == 1
    extract_cells.regenerate(notebook, output, index)
    assert "buenas" in (output / "saludo.py").read_text(encoding="utf-8")
    assert extract_cells.check(*project) == 0


def test_hand_edit_blocks_extraction(project):
    notebook, output, index = project
    module = output / "saludo.py"
    edited = module.read_text(encoding="utf-8").replace("hola", "editado a mano")
    module.write_text(edited, encoding="utf-8")

    assert extract_cells.check(*project) == 1
    with pytest.raises(SystemExit, match="saludo.py"):
        extract_cells.regenerate(notebook, output, index)
    assert module.read_text(encoding="utf-8") == edited


def test_force_discards_hand_edit(project):
    notebook, output, index = project
    module = output / "saludo.py"
    module.write_text(module.read_text(encoding="utf-8").replace("hola", "editado"), encoding="utf-8")
    extract_cells.regenerate(notebook, output, index, force=True)
    assert "hola" in module.read_text(encoding="utf-8")


def test_check_writes_nothing(project):
    notebook, output, index = project
    write_notebook(notebook, "def saludo():\n    return 'otra'\n")
    before = {p.name: p.read_text(encoding="utf-8") for p in output.iterdir()}
    extract_cells.check(*project)
    assert {p.name: p.read_text(encoding="utf-8") for p in output.iterdir()} == before


def test_main_help_does_not_extract(tmp_path, capsys):
    with pytest.raises(SystemExit) as exit_info:
        extract_cells.main(["--help", "--output", str(tmp_path / "cells")])
    assert exit_info.value.code == 0
    assert not (tmp_path / "cells").exists()
