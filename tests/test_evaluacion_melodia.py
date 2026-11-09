import importlib.util
from pathlib import Path

import pytest

from tabroll.evaluation import melodia as M

REFS = Path(__file__).parents[1] / "references"


def load(name):
    spec = importlib.util.spec_from_file_location(name, REFS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_song_key_reads_run_folder_names():
    assert M.song_key("2026-11-09_004558_angine_de_poitrine_sarniezz_audio_offici") == "sarniezz"
    assert M.song_key("Angine de Poitrine - Mata Zyklek (audio officiel)") == "mata_zyklek"
    assert M.song_key("fabienk_official_audio") == "fabienk"
    assert M.song_key("utzp_audio_officiel") is None


@pytest.mark.parametrize("song", sorted(M.CANCIONES))
def test_alignment_keeps_most_of_the_song(song):
    al = M.Alignment(song)
    assert 0.6 < al.kept <= 1.0
    assert len(M.mapped(al, al.ref["guitars"])) > 500


@pytest.mark.parametrize("song", sorted(M.CANCIONES))
def test_perfect_detection_scores_one_hundred(song):
    al = M.Alignment(song)
    lead = M.lead_line(al, song)
    low = M.top_line(M.mapped(al, al.ref["basses"]), low=True)
    r = M.evaluate(song, [(n["t"], n["te"], n["p"]) for n in lead], [(n["t"], n["te"], n["p"]) for n in low])
    assert r["principal"] > 99
    assert r["bajo"] > 99


def test_unison_between_instruments_counts_once():
    a = dict(t=1.0, te=1.2, p=60.0, part="G1", sec=0)
    b = dict(t=1.0, te=1.2, p=60.0, part="G2", sec=0)
    assert len(M.top_line([a, b])) == 1


def test_corrections_by_ear_are_in_the_references():
    sar = load("sarniezz_partitura")
    assert dict((o, p) for o, d, p in sar.P1)[40] == sar.P("Aq5")
    assert dict((o, p) for o, d, p in sar.P2)[8] == sar.P("D6")
    fab = load("fabienk_partitura")
    assert [p for o, d, p in fab.V2][-4:] == [fab.P(n) for n in ("D5", "D5", "Cs5", "Cs5")]
