import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parents[1] / "scripts" / "parse_gp.py"
spec = importlib.util.spec_from_file_location("parse_gp", SCRIPT)
parse_gp_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(parse_gp_module)


DOWNLOADS = Path.home() / "Downloads"


@pytest.mark.parametrize(
    "filename, expected_title, expected_tracks",
    [
        ("Angine_de_Poitrine-Sarniezz.gp", "SARNIEZZ", {"E.Guitar I", "E.Guitar II", "E.Bass", "Drums"}),
        ("Angine_de_Poitrine-Mata_Zyklek.gp", "MATA ZYKLEK", {"E.Guitar I", "E.Guitar II", "E.Guitar III", "E.Bass", "Drums"}),
        ("Angine_de_poitrine-Fabienk_Live_on_KEXP.gp", "FABIENK", {"E.Guitar", "E.Bass", "Drums"}),
    ],
)
def test_parse_gp_download_file(filename, expected_title, expected_tracks):
    path = DOWNLOADS / filename
    if not path.exists():
        pytest.skip(f"No está disponible {path}")
    score = parse_gp_module.parse_gp(path)
    assert score["gp_version"] == "8.1.5"
    assert score["title"] == expected_title
    assert {track["name"] for track in score["tracks"]} == expected_tracks
    assert len(score["master_bars"]) == 8
    assert all(track["events"] for track in score["tracks"] if track["name"] != "Drums")


def test_gp_bend_is_preserved_as_quarter_tone():
    path = DOWNLOADS / "Angine_de_Poitrine-Sarniezz.gp"
    if not path.exists():
        pytest.skip(f"No está disponible {path}")
    score = parse_gp_module.parse_gp(path)
    bass = next(track for track in score["tracks"] if track["name"] == "E.Bass")
    bent = next(event for event in bass["events"] if event["pitch"]["bend_value"])
    assert bent["pitch"]["bend_value"] == 25.0
    assert bent["pitch"]["bend_semitones"] == 0.5
