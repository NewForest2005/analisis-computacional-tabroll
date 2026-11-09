import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from tabroll.reference.guitarpro import _rhythm_duration


def _load_plot_module():
    path = Path(__file__).parents[1] / "scripts" / "plot_line_diagnostics.py"
    spec = importlib.util.spec_from_file_location("plot_line_diagnostics", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_rhythm_duration_supports_double_dot_and_triplet():
    rhythm = ET.fromstring(
        '<Rhythm><NoteValue>Quarter</NoteValue>'
        '<AugmentationDot count="2"/>'
        '<PrimaryTuplet num="3" den="2"/></Rhythm>'
    )
    assert _rhythm_duration(rhythm) == pytest.approx(1.75 * 2 / 3)


def test_diagnostics_alignment_finds_offset_and_tempo():
    module = _load_plot_module()
    events = [
        {"onset_beats": beat, "duration_beats": 0.5,
         "pitch": {"midi_with_bend": pitch}}
        for beat, pitch in enumerate((60, 62, 64, 60))
    ]
    detected = [
        {"start_s": 2.0 + beat * 0.5, "end_s": 2.2 + beat * 0.5, "midi": pitch}
        for beat, pitch in enumerate((60, 62, 64, 60))
    ]
    seconds_per_beat, offset, hit = module._align(events, detected, 0.5)
    # Several nearby tempos obtain the same hit rate within the 75 ms window.
    assert abs(seconds_per_beat - 0.5) < 0.03
    assert abs(offset - 2.0) < 0.01
    assert hit == 1.0
