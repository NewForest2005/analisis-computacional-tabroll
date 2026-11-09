"""Alineación tempo-offset entre una referencia GP y el audio analizado."""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np


def _value(obj: Any, *names: str, default=None):
    if isinstance(obj, dict):
        for name in names:
            if name in obj:
                return obj[name]
    else:
        for name in names:
            if hasattr(obj, name):
                return getattr(obj, name)
    return default


def _flatten_events(reference: Any) -> list[dict[str, float | str]]:
    tracks = reference.get("tracks", []) if isinstance(reference, dict) else reference
    events: list[dict[str, float | str]] = []
    for track in tracks or []:
        name = str(_value(track, "name", "track", "id", default="track"))
        if "drum" in name.casefold():
            continue
        for event in _value(track, "events", default=[]) or []:
            pitch = _value(event, "midi_audio", "audio_pitch", default=None)
            if pitch is None:
                pitch_data = _value(event, "pitch", default={})
                pitch = _value(pitch_data, "midi_with_bend", "midi", default=None)
            # GPIF's Midi field belongs to ConcertPitch: it is already the
            # sounding MIDI height. The displayed guitar octave is transposed
            # separately in the notation name.
            onset = _value(event, "onset_beats", "onset", default=None)
            duration = _value(event, "duration_beats", "duration", "dur", default=0.0)
            if pitch is None or onset is None:
                continue
            events.append({
                "track": name,
                "onset_beats": float(onset),
                "duration_beats": max(float(duration), 0.05),
                "pitch": float(pitch),
            })
    return sorted(events, key=lambda event: (event["onset_beats"], event["pitch"]))


def _onset_score(expected: np.ndarray, observed: np.ndarray, tolerance: float) -> float:
    if not len(expected) or not len(observed):
        return 0.0
    observed = np.sort(observed)
    positions = np.searchsorted(observed, expected)
    left = observed[np.clip(positions - 1, 0, len(observed) - 1)]
    right = observed[np.clip(positions, 0, len(observed) - 1)]
    distances = np.minimum(np.abs(expected - left), np.abs(expected - right))
    return float(np.mean(np.exp(-0.5 * (distances / tolerance) ** 2)))


def _pitch_evidence(
    salience: np.ndarray | None,
    melody: np.ndarray | None,
    candidates: np.ndarray,
    times: np.ndarray,
    pitches: np.ndarray,
    sr: int,
    hop: int,
    tolerance: float,
    scale: float,
    pitch_rows: np.ndarray | None = None,
) -> float:
    if not len(times):
        return 0.0
    melody_length = len(melody) if melody is not None else 0
    available = salience.shape[1] if salience is not None and salience.ndim == 2 else melody_length
    indices = np.clip(np.rint(times * sr / hop).astype(int), 0, max(0, available - 1))
    if salience is not None and salience.ndim == 2 and salience.shape[0] == len(candidates):
        # `pitch_rows` is invariant across every tempo/offset hypothesis.
        # Computing the candidates×events distance matrix inside every
        # hypothesis is prohibitively expensive for full GP scores.
        rows = pitch_rows if pitch_rows is not None else np.abs(candidates[:, None] - pitches[None, :]).argmin(axis=0)
        values = np.maximum(salience[rows, indices], 0.0)
        return float(np.mean(np.clip(values / scale, 0.0, 1.0)))
    if melody is None or not len(melody):
        return 0.0
    values = np.asarray(melody, dtype=float)[indices]
    valid = np.isfinite(values)
    return float(np.mean(np.exp(-np.abs(values[valid] - pitches[valid]) / tolerance))) if np.any(valid) else 0.0


def _evaluate(
    events: list[dict[str, float | str]],
    offset: float,
    tempo: float,
    salience: np.ndarray | None,
    melody: np.ndarray | None,
    candidates: np.ndarray,
    guitar_onsets: np.ndarray,
    bass_onsets: np.ndarray,
    sr: int,
    hop: int,
    onset_tolerance: float,
    salience_scale: float,
    pitch_rows: np.ndarray | None = None,
) -> tuple[float, float, float]:
    seconds_per_beat = 60.0 / tempo
    expected = np.array([offset + float(event["onset_beats"]) * seconds_per_beat for event in events])
    pitches = np.array([float(event["pitch"]) for event in events])
    pitch_score = _pitch_evidence(
        salience, melody, candidates, expected, pitches, sr, hop, 0.75,
        salience_scale, pitch_rows,
    )
    guitar_mask = np.array(["bass" not in str(event["track"]).casefold() for event in events])
    bass_mask = ~guitar_mask
    guitar_score = _onset_score(expected[guitar_mask], guitar_onsets, onset_tolerance)
    bass_score = _onset_score(expected[bass_mask], bass_onsets, onset_tolerance)
    onset_score = float(np.mean([score for score, mask in ((guitar_score, guitar_mask), (bass_score, bass_mask)) if np.any(mask)] or [0.0]))
    return 0.65 * pitch_score + 0.35 * onset_score, pitch_score, onset_score


def _search(
    events: list[dict[str, float | str]],
    tempos: np.ndarray,
    offsets: np.ndarray,
    salience: np.ndarray | None,
    melody: np.ndarray | None,
    candidates: np.ndarray,
    guitar_onsets: np.ndarray,
    bass_onsets: np.ndarray,
    sr: int,
    hop: int,
    onset_tolerance: float,
    salience_scale: float,
    pitch_rows: np.ndarray | None = None,
) -> tuple[float, float, float, float, float]:
    best = (-np.inf, float(tempos[0]), float(offsets[0]), 0.0, 0.0)
    for tempo in tempos:
        for offset in offsets:
            score, pitch_score, onset_score = _evaluate(
                events, float(offset), float(tempo), salience, melody, candidates,
                guitar_onsets, bass_onsets, sr, hop, onset_tolerance,
                salience_scale, pitch_rows,
            )
            if score > best[0]:
                best = (score, float(tempo), float(offset), pitch_score, onset_score)
    return best


def align_gp_audio(
    reference: Any,
    salience: np.ndarray | None,
    candidates: np.ndarray,
    guitar_onsets: Iterable[float] | None,
    bass_onsets: Iterable[float] | None,
    tempo_bpm: float,
    *,
    melody: np.ndarray | None = None,
    sr: int,
    hop: int,
    audio_duration_s: float | None = None,
    tempo_span: float = 0.08,
    onset_tolerance: float = 0.08,
) -> dict[str, Any]:
    """Encuentra el offset y el tempo local que mejor explican el audio.

    La búsqueda se hace primero cada 250 ms y con 13 tempos alrededor del
    tempo global. Después se refina alrededor de la mejor hipótesis cada 20 ms
    y 1/20 de BPM. La función no altera el audio ni presupone que el GP empiece
    en el segundo cero.
    """
    if tempo_bpm <= 0 or sr <= 0 or hop <= 0:
        raise ValueError("tempo_bpm, sr y hop deben ser positivos")
    events = _flatten_events(reference)
    if not events:
        raise ValueError("La referencia GP no contiene eventos melódicos")
    S = None if salience is None else np.asarray(salience, dtype=float)
    cand = np.asarray(candidates, dtype=float).reshape(-1)
    melody_array = None if melody is None else np.asarray(melody, dtype=float).reshape(-1)
    guitar = np.asarray([] if guitar_onsets is None else list(guitar_onsets), dtype=float)
    bass = np.asarray([] if bass_onsets is None else list(bass_onsets), dtype=float)
    if audio_duration_s is None:
        n_frames = S.shape[1] if S is not None and S.ndim == 2 else (len(melody_array) if melody_array is not None else 0)
        audio_duration_s = n_frames * hop / sr
    salience_scale = float(np.percentile(np.maximum(S, 0.0), 90) + 1e-9) if S is not None and S.size else 1.0
    pitches = np.array([float(event["pitch"]) for event in events])
    pitch_rows = None
    if S is not None and S.ndim == 2 and S.shape[0] == len(cand):
        # This mapping depends only on the GP pitches and the salience grid,
        # never on the tempo or offset being tested.
        pitch_rows = np.abs(cand[:, None] - pitches[None, :]).argmin(axis=0)

    coarse_tempos = np.linspace(tempo_bpm * (1 - tempo_span), tempo_bpm * (1 + tempo_span), 13)
    reference_duration = max(float(event["onset_beats"]) + float(event["duration_beats"]) for event in events) * 60 / min(coarse_tempos)
    max_offset = max(0.0, float(audio_duration_s) - reference_duration)
    coarse_offsets = np.arange(0.0, max_offset + 0.125, 0.25)
    best = _search(events, coarse_tempos, coarse_offsets, S, melody_array, cand, guitar, bass, sr, hop, onset_tolerance, salience_scale, pitch_rows)

    _, best_tempo, best_offset, _, _ = best
    fine_tempos = np.arange(best_tempo - 1.0, best_tempo + 1.0001, 0.05)
    fine_offsets = np.arange(max(0.0, best_offset - 0.35), min(max_offset, best_offset + 0.35) + 0.010, 0.02)
    best = _search(events, fine_tempos, fine_offsets, S, melody_array, cand, guitar, bass, sr, hop, onset_tolerance, salience_scale, pitch_rows)
    score, tempo, offset, pitch_score, onset_score = best
    seconds_per_beat = 60.0 / tempo
    aligned_events = []
    for event in events:
        start = offset + float(event["onset_beats"]) * seconds_per_beat
        end = start + float(event["duration_beats"]) * seconds_per_beat
        aligned_events.append({**event, "start_s": round(start, 5), "end_s": round(end, 5)})
    return {
        "method": "coarse-fine-tempo-offset",
        "offset_s": round(offset, 5),
        "tempo_local_bpm": round(tempo, 5),
        "score": round(score, 5),
        "pitch_score": round(pitch_score, 5),
        "onset_score": round(onset_score, 5),
        "reference_duration_s": round(reference_duration, 5),
        "events": aligned_events,
    }
