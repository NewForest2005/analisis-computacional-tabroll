SHELL := /bin/sh

PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python

AUDIO_DIR := Angine de Poitrine Audios
SARNIEZZ_AUDIO := $(AUDIO_DIR)/Angine de Poitrine - Sarniezz (audio officiel).mp3

.PHONY: help check-python venv install demucs check-ffmpeg extract check test run-sarniezz clean-outputs

help:
	@printf '%s\n' \
		'make install         Crear el entorno e instalar el proyecto y las pruebas' \
		'make demucs          Instalar Demucs para separar guitarra y bajo' \
		'make extract         Regenerar un archivo Python por celda' \
		'make check           Verificar extracción y sintaxis' \
		'make test            Ejecutar las pruebas' \
		'make run-sarniezz   Analizar Sarniezz y generar todos los outputs' \
		'make clean-outputs   Eliminar solo las corridas generadas en outputs/'

check-python:
	@$(PYTHON) -c 'import sys; v=sys.version_info; assert v >= (3, 10), "Se requiere Python 3.10 o superior"; print("Python", sys.version.split()[0])'

venv: check-python
	@test -x $(VENV_PYTHON) || $(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -e ".[dev]"

demucs: install
	$(VENV_PYTHON) -m pip install demucs-infer

check-ffmpeg:
	@command -v ffmpeg >/dev/null 2>&1 || \
		{ echo 'Falta ffmpeg. En macOS instala con: brew install ffmpeg' >&2; exit 1; }
	@ffmpeg -version | sed -n '1p'

extract:
	$(VENV_PYTHON) scripts/extract_cells.py

check: install
	$(VENV_PYTHON) scripts/extract_cells.py
	$(VENV_PYTHON) -m compileall -q src scripts tests

test: install
	$(VENV_PYTHON) -m pytest -q

run-sarniezz: demucs check-ffmpeg
	@test -f "$(SARNIEZZ_AUDIO)" || { echo 'No se encontró el audio de Sarniezz:' >&2; echo "  $(SARNIEZZ_AUDIO)" >&2; exit 1; }
	$(VENV_PYTHON) scripts/run_song.py "$(SARNIEZZ_AUDIO)" --nombre sarniezz

clean-outputs:
	@test -d outputs || exit 0
	find outputs -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
