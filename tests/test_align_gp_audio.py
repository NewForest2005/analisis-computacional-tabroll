import numpy as np

from tabroll.reference.align_gp_audio import align_gp_audio


def test_align_gp_audio_recovers_offset_and_tempo():
    sr, hop = 100, 1
    candidates = np.arange(58.0, 66.0)
    salience = np.zeros((len(candidates), 900))
    reference = {
        "tracks": [
            {"name": "E.Guitar", "events": [
                *[
                    {"onset_beats": beat, "duration_beats": .5, "midi_audio": (60, 62, 64)[beat % 3]}
                    for beat in range(9)
                ],
            ]},
            {"name": "E.Bass", "events": [
                {"onset_beats": 0, "duration_beats": 1, "midi_audio": 48},
            ]},
        ]
    }
    offset, tempo = 1.2, 120.0
    for beat in range(9):
        pitch = (60, 62, 64)[beat % 3]
        frame = round((offset + beat * 60 / tempo) * sr / hop)
        salience[np.where(candidates == pitch)[0][0], frame] = 1.0
    aligned = align_gp_audio(
        reference,
        salience,
        candidates,
        [offset + beat * 0.5 for beat in range(9)],
        [offset],
        120,
        sr=sr,
        hop=hop,
        audio_duration_s=9,
    )
    assert abs(aligned["offset_s"] - offset) <= 0.06
    assert abs(aligned["tempo_local_bpm"] - tempo) <= 1.0
    assert aligned["pitch_score"] > 0.3
    assert aligned["onset_score"] > 0.8
