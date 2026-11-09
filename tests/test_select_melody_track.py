import importlib.util
from pathlib import Path

import numpy as np


MODULE = Path(__file__).parents[1] / "src/tabroll/reference/select_melody_track.py"
spec = importlib.util.spec_from_file_location("select_melody_track", MODULE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_select_melody_track_switches_between_score_lines():
    candidates = np.arange(60.0, 65.0)
    salience = np.zeros((len(candidates), 8))
    salience[0, :4] = 1.0
    salience[4, 4:] = 1.0
    score = {
        "Guitar I": [{"onset_s": 0.0, "duration_s": 0.4, "midi": 60, "is_audio_pitch": True}],
        "Guitar III": [{"onset_s": 0.4, "duration_s": 0.4, "midi": 64, "is_audio_pitch": True}],
    }
    melody, path, confidence = module.select_melody_track(
        salience, np.ones(8), None, score, [0.0, 0.4], candidates=candidates, sr=10, hop=1
    )
    assert np.allclose(melody[:4], 60)
    assert np.allclose(melody[4:], 64)
    assert path[:4] == ["Guitar I"] * 4
    assert path[4:] == ["Guitar III"] * 4
    assert np.all((confidence >= 0) & (confidence <= 1))


def test_select_melody_track_can_return_silence():
    candidates = np.arange(60.0, 62.0)
    salience = np.zeros((2, 4))
    score = {"Guitar I": [{"onset_s": 0.2, "duration_s": 0.1, "midi": 60, "is_audio_pitch": True}]}
    melody, path, _ = module.select_melody_track(
        salience, None, None, score, [], candidates=candidates, sr=10, hop=1
    )
    assert np.all(np.isnan(melody))
    assert path == ["silence"] * 4
