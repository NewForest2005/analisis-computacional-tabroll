"""Separación con BS-RoFormer SW: lo que se puede probar sin audio-separator ni torch."""

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SR = load("separar_roformer", ROOT / "scripts" / "separar_roformer.py")
RS = load("run_song", ROOT / "scripts" / "run_song.py")


def touch(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    return path


def test_find_song_ignores_stems(tmp_path):
    song = touch(tmp_path / "Angine de Poitrine - Sarniezz (audio officiel).mp3")
    touch(tmp_path / "Angine de Poitrine - Sarniezz (audio officiel)_guitar.mp3")
    touch(tmp_path / "Sarniezz -Only Guitar (Isolated).mp3")
    assert SR.find_song("sarniezz", tmp_path) == song


def test_find_song_ambiguous_stops(tmp_path):
    touch(tmp_path / "Fabienk - Drumless.mp3")
    touch(tmp_path / "Fabienk - Only bass.mp3")
    with pytest.raises(SystemExit, match="no identifica"):
        SR.find_song("fabienk", tmp_path)


def test_output_paths_keep_fragments_apart(tmp_path):
    song = Path("Cancion.mp3")
    full = SR.output_paths(song, tmp_path)
    frag = SR.output_paths(song, tmp_path, 20)
    assert full["guitar"] == tmp_path / "Cancion_guitar.flac"
    assert frag["bass"] == tmp_path / "fragmentos" / "Cancion_20s_bass.flac"


def test_pick_outputs_accepts_custom_and_default_names(tmp_path):
    files = ["Cancion_guitar.flac", "Cancion_(Bass)_BS-Roformer-SW.flac", "Cancion_(Drums)_BS-Roformer-SW.flac"]
    got = SR.pick_outputs(files, tmp_path)
    assert got == {"guitar": tmp_path / "Cancion_guitar.flac", "bass": tmp_path / "Cancion_(Bass)_BS-Roformer-SW.flac"}


def test_yaml_info_reads_inference_parameters(tmp_path):
    (tmp_path / "BS-Roformer-SW.yaml").write_text(
        "audio:\n  chunk_size: 588800\n  sample_rate: 44100\ntraining:\n  instruments: ['bass', 'drums', 'other', "
        "'vocals', 'guitar', 'piano']\ninference:\n  dim_t: 801\n  num_overlap: 2\n  normalize: false\n", encoding="utf-8")
    info = SR.yaml_info(tmp_path)
    assert info["dim_t"] == "801" and info["num_overlap"] == "2" and "guitar" in info["instruments"]
    assert len(info["sha256"]) == 64


def test_run_song_roformer_stems(tmp_path):
    audio = Path("Cancion.mp3")
    with pytest.raises(SystemExit, match="separar_roformer.py"):
        RS.roformer_stems(audio, tmp_path)
    touch(tmp_path / "Cancion_guitar.flac")
    touch(tmp_path / "Cancion_bass.flac")
    (tmp_path / "Cancion.json").write_text(json.dumps({"modelo": {"sha256": "abc"}}), encoding="utf-8")
    stems, manifest = RS.roformer_stems(audio, tmp_path)
    assert stems["guitar"].name == "Cancion_guitar.flac" and manifest["modelo"]["sha256"] == "abc"


def test_run_song_accepts_separador_flag():
    with pytest.raises(SystemExit) as exit_info:
        RS.main(["--help"])
    assert exit_info.value.code == 0
