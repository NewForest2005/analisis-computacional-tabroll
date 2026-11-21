SHELL := /bin/sh

PYTHON ?= $(shell if command -v python3.12 >/dev/null 2>&1; then command -v python3.12; else command -v python3; fi)
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python

AUDIO_DIR := Angine de Poitrine Audios
SARNIEZZ_AUDIO := $(AUDIO_DIR)/Angine de Poitrine - Sarniezz (audio officiel).mp3

.PHONY: help check-python venv install demucs check-ffmpeg extract check test run-sarniezz todo graficas graficas-completas graficas-diapositivas graficas-clave defensa presentacion graficas-actuales graficas-primus roformer-entorno separar-roformer run-roformer clean-outputs

help:
	@printf '%s\n' \
		'make install         Crear el entorno e instalar el proyecto y las pruebas' \
		'make demucs          Instalar Demucs para separar guitarra y bajo' \
		'make extract         Regenerar un archivo Python por celda (se detiene si hay módulos editados a mano)' \
		'make check           Verificar extracción (sin escribir) y sintaxis' \
		'make test            Ejecutar las pruebas' \
		'make run-sarniezz   Analizar Sarniezz y generar todos los outputs' \
		'make graficas       Reunir comparativas no-tabroll de banda, repertorios y corpus' \
		'make graficas-completas Alias de make graficas' \
		'make graficas-diapositivas Solo las seis gráficas de la presentación (outputs/graficas_clave_*/diapositivas)' \
		'make defensa        PDF con los puntos para la defensa (docs/defensa) y copia en ~/Downloads' \
		'make presentacion   Servir la presentación (presentacion/index.html) en http://localhost:8000' \
		'make graficas-actuales Reunir gráficas básicas usando las corridas existentes más recientes' \
		'make graficas-primus Correr las cinco y comparar también con las corridas de Primus' \
		'make roformer-entorno Crear .venv-rof (conda-forge) con audio-separator para BS-RoFormer SW' \
		'make separar-roformer CANCION=Sarniezz  Separar guitarra y bajo con BS-RoFormer SW' \
		'make run-roformer CANCION=Sarniezz      Correr el cuaderno con las pistas de BS-RoFormer SW' \
		'make clean-outputs   Eliminar solo las corridas generadas en outputs/'

check-python:
	@$(PYTHON) -c 'import sys; v=sys.version_info; assert (3, 10) <= v < (3, 13), "Se requiere Python 3.10, 3.11 o 3.12; en Mac Intel se recomienda 3.12"; print("Python", sys.version.split()[0])'

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
	$(VENV_PYTHON) scripts/extract_cells.py --check
	$(VENV_PYTHON) -m compileall -q src scripts tests
	$(VENV_PYTHON) -m pip check

test: install
	$(VENV_PYTHON) -m pytest -q

run-sarniezz: demucs check-ffmpeg
	@test -f "$(SARNIEZZ_AUDIO)" || { echo 'No se encontró el audio de Sarniezz:' >&2; echo "  $(SARNIEZZ_AUDIO)" >&2; exit 1; }
	$(VENV_PYTHON) scripts/run_song.py "$(SARNIEZZ_AUDIO)" --nombre sarniezz

todo: check-python
	$(VENV_PYTHON) scripts/todo.py

graficas: check-python
	@test -x $(VENV_PYTHON) || { echo 'Falta $(VENV_PYTHON); ejecuta make install una vez con conexión.' >&2; exit 1; }
	$(VENV_PYTHON) scripts/graficas_completas.py

graficas-completas: graficas

graficas-diapositivas: check-python
	@test -x $(VENV_PYTHON) || { echo 'Falta $(VENV_PYTHON); ejecuta make install una vez con conexión.' >&2; exit 1; }
	$(VENV_PYTHON) scripts/graficas_completas.py --clave

graficas-clave: graficas-diapositivas

PUERTO ?= 8000

presentacion:
	@echo "Presentación en http://localhost:$(PUERTO)  (Ctrl+C para cerrar)"
	@(sleep 1 && open "http://localhost:$(PUERTO)") &
	cd presentacion && python3 -m http.server $(PUERTO)

DEFENSA_TMP := .tmp_defensa
DESCARGAS ?= $(HOME)/Downloads

defensa:
	@command -v xelatex >/dev/null || { echo 'Falta xelatex (MacTeX).' >&2; exit 1; }
	@mkdir -p $(DEFENSA_TMP)
	xelatex -interaction=nonstopmode -halt-on-error -output-directory=$(DEFENSA_TMP) docs/defensa/puntos_defensa.tex >/dev/null \
		|| { tail -30 $(DEFENSA_TMP)/puntos_defensa.log >&2; exit 1; }
	cp $(DEFENSA_TMP)/puntos_defensa.pdf docs/defensa/puntos_defensa.pdf
	cp docs/defensa/puntos_defensa.pdf "$(DESCARGAS)/puntos_defensa.pdf"
	@echo "→ docs/defensa/puntos_defensa.pdf y $(DESCARGAS)/puntos_defensa.pdf"

graficas-actuales: check-python
	$(VENV_PYTHON) scripts/todo.py --otras primus

graficas-primus: demucs check-ffmpeg
	$(VENV_PYTHON) scripts/todo.py --correr --otras primus

CONDA ?= $(HOME)/miniforge3/bin/conda
ROFORMER_ENV := .venv-rof
AUDIO_SEPARATOR_VERSION := 0.48.0
CANCION ?= Sarniezz
ROFORMER_CONDA_DEPS := torchvision numba llvmlite librosa=0.11 audioread onnxruntime pysoundfile scipy resampy

roformer-entorno:
	@test -x "$(CONDA)" || { echo 'Falta conda: instala Miniforge (ver docs/separacion_roformer.md).' >&2; exit 1; }
	@test -x $(ROFORMER_ENV)/bin/python || "$(CONDA)" create -y -p $(ROFORMER_ENV) -c conda-forge python=3.12 pytorch torchvision ffmpeg
	# En Mac Intel, PyPI no tiene ruedas de estas dependencias (torchvision solo para torch 2.2; llvmlite
	# habría que compilarlo con LLVM): vienen de conda-forge y pip ya no intenta reemplazarlas.
	"$(CONDA)" install -y -p $(ROFORMER_ENV) -c conda-forge $(ROFORMER_CONDA_DEPS)
	$(ROFORMER_ENV)/bin/python -m pip install "audio-separator[cpu]==$(AUDIO_SEPARATOR_VERSION)"
	$(ROFORMER_ENV)/bin/python scripts/separar_roformer.py --entorno

separar-roformer:
	@test -x $(ROFORMER_ENV)/bin/python || { echo 'Falta $(ROFORMER_ENV); corre make roformer-entorno.' >&2; exit 1; }
	$(ROFORMER_ENV)/bin/python scripts/separar_roformer.py "$(CANCION)"

run-roformer: check-python
	$(VENV_PYTHON) scripts/run_song.py "$(CANCION)" --separador roformer

clean-outputs:
	@test -d outputs || exit 0
	find outputs -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} +
