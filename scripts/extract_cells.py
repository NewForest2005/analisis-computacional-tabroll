"""Regenerate the one-file-per-code-cell extraction from the source notebook."""

from __future__ import annotations

import ast
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
DEFAULT_OUTPUT = ROOT / "src" / "tabroll" / "cells"


def slug(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower() or "celda"


def clean_jupyter_magics(source: str) -> str:
    return "\n".join(
        f"# Notebook shell command: {line.lstrip()[1:]}"
        if line.lstrip().startswith("!")
        else line
        for line in source.splitlines()
    )


def preceding_description(cells: list[dict], index: int) -> str:
    for previous in reversed(cells[:index]):
        if previous["cell_type"] == "code":
            break
        text = "".join(previous.get("source", [])).strip()
        if text:
            return next(
                (re.sub(r"^#+\s*", "", line).strip() for line in text.splitlines() if line.strip()),
                "",
            )
    return ""


def regenerate(notebook: Path = DEFAULT_NOTEBOOK, output: Path = DEFAULT_OUTPUT) -> int:
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    output.mkdir(parents=True, exist_ok=True)
    for old_file in output.glob("*.py"):
        if old_file.name != "__init__.py":
            old_file.unlink()

    manifest: list[tuple[int, str, list[str], str]] = []
    code_number = 0
    used: set[str] = set()
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        code_number += 1
        source = clean_jupyter_magics("".join(cell.get("source", [])))
        try:
            tree = ast.parse(source)
        except SyntaxError:
            tree = ast.parse("")
        definitions = [
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        titles = [
            line.strip()[1:].replace("@title", "").strip()
            for line in source.splitlines()
            if line.strip().startswith("# @title")
        ]
        if len(definitions) == 1:
            base = definitions[0].lower().lstrip("_")
        elif definitions:
            base = slug(titles[0]) if titles else f"{definitions[0].lower().lstrip('_')}_and_helpers"
        else:
            base = slug(titles[0]) if titles else "configuracion"
        name = f"{code_number:03d}_{base}"
        if name in used:
            name += f"_cell_{index:03d}"
        used.add(name)
        description = preceding_description(cells, index)
        doc = (
            f'"""Celda {index} del notebook original.'
            + (f" Descripcion asociada: {description}." if description else "")
            + "\n\nEste modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.\n\"\"\"\n"
        )
        (output / f"{name}.py").write_text(doc + "\n" + source.rstrip() + "\n", encoding="utf-8")
        manifest.append((index, name, definitions, description))

    (output / "__init__.py").write_text('"""Celdas de codigo extraidas del notebook Tabroll."""\n', encoding="utf-8")
    index = [
        "# Inventario de celdas extraidas",
        "",
        "| Celda original | Archivo | Elementos principales | Descripcion |",
        "|---:|---|---|---|",
    ]
    index.extend(
        f'| {cell} | [`{name}.py`](../src/tabroll/cells/{name}.py) | '
        f'`{", ".join(definitions) if definitions else "configuracion / ejecucion"}` | '
        f'{description or "Sin descripcion en markdown"} |'
        for cell, name, definitions, description in manifest
    )
    (ROOT / "docs" / "cell-index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    return code_number


if __name__ == "__main__":
    print(f"Extracted {regenerate()} code cells")
