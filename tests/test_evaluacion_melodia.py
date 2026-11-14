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
    assert M.song_key("angine_de_poitrine_yor_zarad_audio_officiel") == "yor_zarad"
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


def test_second_blind_round_is_in_the_references():
    sar = load("sarniezz_partitura")
    p1 = {o: p for o, d, p in sar.P1 if o in (13, 25, 28, 30, 42)}
    assert p1 == {13: sar.P("Ft5"), 25: sar.P("As4"), 28: sar.P("As4"), 30: sar.P("Ft5"), 42: sar.P("Ct5")}
    fab = load("fabienk_partitura")
    corrido = next(parts for name, n, parts, known in fab.SECTIONS if name.startswith("Corrido otra vez"))
    assert set(corrido) == {"G2", "B"}
    mata = load("mata_zyklek_loops")
    assert mata.ARR["G3"][64] == "RUN64" and mata.L["RUN64"][0] == (0, 1.5, mata.P("F5"))


def test_yor_zarad_reference_and_unmeasured_bars():
    yz = load("yor_zarad_partitura")
    assert sum(yz.largos()) == yz.inicio(202) == 2752
    tl = yz.timeline()
    assert all(abs(a[1] - b[0]) < 1e-9 for a, b in zip(tl, tl[1:]))
    off = [(round(t0 / yz.S), round(t1 / yz.S)) for t0, t1, nm, kn in tl if not kn]
    assert off == [(yz.inicio(a), yz.inicio(b + 1)) for a, b in yz.NO_MEDIBLE]
    notas = yz.notes(yz.GUITARS + yz.BASSES)
    assert len(notas) > 5000 and all(d > 0 for t, d, p, part in notas)


def test_lead_line_accepts_several_parts_and_the_bass():
    al = M.Alignment("yor_zarad")
    lead = M.lead_line(al, "yor_zarad")
    secs = al.ref["sections"]
    by = lambda pre: {n["part"] for n in lead if secs[n["sec"]][2].startswith(pre)}
    assert by("C: riff con el bajo") >= {"B"}
    assert by("I:") == {"G1", "G3"}
    assert by("H: entra la guitarra 3") and by("H: entra la guitarra 3") <= {"G1", "G2"}
