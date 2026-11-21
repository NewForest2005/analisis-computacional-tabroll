"""Regenera la extracción de una celda de código por archivo a partir del notebook.

El notebook es la fuente de verdad. Cada extracción guarda en
``src/tabroll/cells/.extraccion.json`` el hash de los archivos que escribió; si un
módulo cambió a mano desde entonces, la extracción se detiene en lugar de
borrar ese cambio. Pasa el cambio al notebook o usa ``--force`` para descartarlo.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
DEFAULT_OUTPUT = ROOT / "src" / "tabroll" / "cells"
DEFAULT_INDEX = ROOT / "docs" / "cell-index.md"
MANIFEST_NAME = ".extraccion.json"
INIT_TEXT = '"""Celdas de codigo extraidas del notebook Tabroll."""\n'


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


def definitions(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]


def module_name(order: int, source: str, names: list[str]) -> str:
    titles = [
        line.strip()[1:].replace("@title", "").strip()
        for line in source.splitlines()
        if line.strip().startswith("# @title")
    ]
    if titles:
        return re.sub(r"^\d+[a-z]?_", "", slug(titles[0]))
    if len(names) == 1:
        return names[0].lower().lstrip("_")
    if names:
        return f"{names[0].lower().lstrip('_')}_and_helpers"
    return f"configuracion_{order:03d}"


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def plan(notebook: Path = DEFAULT_NOTEBOOK) -> tuple[dict[str, str], str]:
    """Devuelve {archivo: contenido} de los módulos y el texto del inventario."""
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    files: dict[str, str] = {}
    manifest: list[tuple[int, str, list[str], str]] = []
    code_number = 0
    used: set[str] = set()
    for index, cell in enumerate(cells):
        if cell["cell_type"] != "code":
            continue
        code_number += 1
        source = clean_jupyter_magics("".join(cell.get("source", [])))
        names = definitions(source)
        name = module_name(code_number, source, names)
        if name in used:
            name += f"_cell_{code_number:03d}"
        used.add(name)
        description = preceding_description(cells, index)
        doc = f'"""{description or "Celda de configuración o ejecución."}\n"""\n'
        files[f"{name}.py"] = doc + "\n" + source.rstrip() + "\n"
        manifest.append((index, name, names, description))

    lines = [
        "# Inventario de celdas extraidas",
        "",
        "| Celda original | Archivo | Elementos principales | Descripcion |",
        "|---:|---|---|---|",
    ]
    lines.extend(
        f'| {cell} | [`{name}.py`](../src/tabroll/cells/{name}.py) | '
        f'`{", ".join(defs) if defs else "configuracion / ejecucion"}` | '
        f'{description or "Sin descripcion en markdown"} |'
        for cell, name, defs, description in manifest
    )
    return files, "\n".join(lines) + "\n"


def read_manifest(output: Path) -> dict[str, str]:
    path = output / MANIFEST_NAME
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def compare(files: dict[str, str], output: Path) -> dict[str, list[str]]:
    """Clasifica las diferencias entre lo que hay en disco y lo que genera el notebook.

    ``editados`` son módulos cuyo contenido cambió desde la última extracción (o que
    no figuran en el manifiesto y no coinciden con el notebook): sobrescribirlos
    perdería trabajo.
    """
    recorded = read_manifest(output)
    existing = {p.name: p.read_text(encoding="utf-8") for p in output.glob("*.py") if p.name != "__init__.py"}
    report: dict[str, list[str]] = {"nuevos": [], "actualizados": [], "eliminados": [], "editados": []}
    for name in sorted(set(files) | set(existing)):
        current = existing.get(name)
        wanted = files.get(name)
        if current == wanted:
            continue
        if current is not None and recorded.get(name) != digest(current):
            report["editados"].append(name)
        elif current is None:
            report["nuevos"].append(name)
        elif wanted is None:
            report["eliminados"].append(name)
        else:
            report["actualizados"].append(name)
    return report


def regenerate(
    notebook: Path = DEFAULT_NOTEBOOK,
    output: Path = DEFAULT_OUTPUT,
    index_file: Path = DEFAULT_INDEX,
    force: bool = False,
) -> int:
    files, index_text = plan(notebook)
    report = compare(files, output)
    if report["editados"] and not force:
        raise SystemExit(
            "Estos módulos cambiaron a mano desde la última extracción y se perderían:\n"
            + "".join(f"  - {output / name}\n" for name in report["editados"])
            + "Pasa esos cambios al notebook y vuelve a correr la extracción,\n"
            "o usa --force para descartarlos."
        )
    output.mkdir(parents=True, exist_ok=True)
    for old_file in output.glob("*.py"):
        if old_file.name != "__init__.py" and old_file.name not in files:
            old_file.unlink()
    for name, text in files.items():
        path = output / name
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
    (output / "__init__.py").write_text(INIT_TEXT, encoding="utf-8")
    manifest = {name: digest(text) for name, text in sorted(files.items())}
    (output / MANIFEST_NAME).write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    index_file.parent.mkdir(parents=True, exist_ok=True)
    index_file.write_text(index_text, encoding="utf-8")
    return len(files)


def check(notebook: Path = DEFAULT_NOTEBOOK, output: Path = DEFAULT_OUTPUT, index_file: Path = DEFAULT_INDEX) -> int:
    """Informa las diferencias sin escribir nada. Devuelve 0 si todo coincide."""
    files, index_text = plan(notebook)
    report = compare(files, output)
    labels = {
        "editados": "Editados a mano (no coinciden con el notebook)",
        "actualizados": "Desactualizados respecto al notebook",
        "nuevos": "Faltan (celdas nuevas en el notebook)",
        "eliminados": "Sobran (la celda ya no está en el notebook)",
    }
    problems = 0
    for key, label in labels.items():
        if report[key]:
            problems += len(report[key])
            print(f"{label}:")
            print("".join(f"  - {name}\n" for name in report[key]), end="")
    if not index_file.is_file() or index_file.read_text(encoding="utf-8") != index_text:
        problems += 1
        print(f"Inventario desactualizado: {index_file}")
    manifest = {name: digest(text) for name, text in sorted(files.items())}
    if not report["editados"] and read_manifest(output) != manifest:
        problems += 1
        print(f"Manifiesto desactualizado: {output / MANIFEST_NAME}")
    if problems:
        print("\nCorre `python scripts/extract_cells.py` (o `make extract`) para sincronizar.")
        return 1
    print(f"Extracción al día: {len(files)} celdas de código.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extrae cada celda de código del notebook a un módulo en src/tabroll/cells.",
    )
    parser.add_argument("--notebook", type=Path, default=DEFAULT_NOTEBOOK, help="notebook de origen")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="carpeta de módulos")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX, help="inventario en Markdown")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="solo informa diferencias; no escribe nada")
    mode.add_argument("--force", action="store_true", help="sobrescribe también módulos editados a mano")
    args = parser.parse_args(argv)
    if args.check:
        return check(args.notebook, args.output, args.index)
    print(f"Extracted {regenerate(args.notebook, args.output, args.index, force=args.force)} code cells")
    return 0


if __name__ == "__main__":
    sys.exit(main())
