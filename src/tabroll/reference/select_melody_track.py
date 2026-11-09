"""**`select_melody_track`**: elige entre las líneas de guitarra, bajo y silencio usando la saliencia, los stems, los eventos del GP y los ataques.
"""

from __future__ import annotations

from typing import Any, Iterable, NamedTuple

import numpy as np


class _State(NamedTuple):
    track: str
    pitch: float | None
    start: float
    end: float


def _event_value(event: Any, *names: str, default=None):
    if isinstance(event, dict):
        for name in names:
            if name in event:
                return event[name]
    else:
        for name in names:
            if hasattr(event, name):
                return getattr(event, name)
    return default


def _events_by_track(score_events: Any, tempo_bpm: float | None) -> dict[str, list[_State]]:
    """Normaliza eventos del JSON de referencia o de objetos NoteEvent."""
    if isinstance(score_events, dict):
        if "tracks" in score_events:
            tracks = score_events["tracks"]
        else:
            tracks = [{"name": name, "events": events} for name, events in score_events.items()]
    else:
        tracks = score_events or []

    seconds_per_beat = 60.0 / tempo_bpm if tempo_bpm else 1.0
    output: dict[str, list[_State]] = {}
    for track in tracks:
        name = _event_value(track, "name", "track", "id", default="track")
        events = _event_value(track, "events", default=track if isinstance(track, list) else [])
        if "drum" in str(name).lower():
            continue
        normalized = []
        for event in events:
            pitch = _event_value(event, "midi_with_bend", "midi", "pitch", default=None)
            if isinstance(pitch, dict):
                pitch = _event_value(pitch, "midi_with_bend", "midi", default=None)
            start = _event_value(event, "start_s", "onset_s", "onset_seconds", default=None)
            end = _event_value(event, "end_s", default=None)
            if start is None:
                start = _event_value(event, "onset_beats", "onset", default=None)
                if start is not None:
                    start = float(start) * seconds_per_beat
            duration = _event_value(event, "duration_s", default=None)
            if duration is None:
                duration = _event_value(event, "duration_beats", "dur", default=None)
                if duration is not None:
                    duration = float(duration) * seconds_per_beat
            if start is None or pitch is None:
                continue
            start, pitch = float(start), float(pitch)
            # GP guitar/bass events are written one octave above their audio.
            if _event_value(event, "audio_pitch", default=None) is not None:
                pitch = float(_event_value(event, "audio_pitch"))
            elif not bool(_event_value(event, "is_audio_pitch", default=False)):
                pitch -= 12.0
            end = float(end) if end is not None else start + max(float(duration or 0.0), 0.05)
            normalized.append(_State(str(name), pitch, start, max(end, start + 0.01)))
        output[str(name)] = sorted(normalized, key=lambda item: (item.start, item.end))
    return output


def _frame_activity(stem: Any, times: np.ndarray, sr: int, hop: int) -> np.ndarray:
    """Obtiene una actividad 0–1 de un waveform o de una envolvente ya calculada."""
    if stem is None:
        return np.zeros(len(times), dtype=float)
    values = np.asarray(stem, dtype=float).reshape(-1)
    if not len(values):
        return np.zeros(len(times), dtype=float)
    if len(values) == len(times):
        activity = np.abs(values)
    else:
        centers = np.clip((times * sr).astype(int), 0, len(values) - 1)
        window = max(1, int(hop))
        activity = np.array([np.sqrt(np.mean(values[max(0, c - window):min(len(values), c + window)] ** 2)) for c in centers])
    scale = np.percentile(activity, 90) + 1e-9
    return np.clip(activity / scale, 0.0, 1.0)


def _pitch_score(salience: np.ndarray, candidates: np.ndarray, pitch: float, tolerance: float) -> float:
    distance = np.abs(candidates - pitch)
    close = distance <= tolerance
    if not np.any(close):
        return 0.0
    weights = np.exp(-distance[close] ** 2 / max(tolerance ** 2, 1e-9))
    values = np.maximum(salience[close], 0.0)
    return float(np.max(values * weights))


def _state_key(state: _State) -> tuple[str, float | None, float, float]:
    return state.track, state.pitch, state.start, state.end


def select_melody_track(
    salience: np.ndarray,
    guitar: np.ndarray | None,
    bass: np.ndarray | None,
    score_events: Any,
    onsets: Iterable[float] | None,
    *,
    candidates: np.ndarray,
    sr: int,
    hop: int,
    tempo_bpm: float | None = None,
    onset_tolerance: float = 0.075,
    pitch_tolerance: float = 0.75,
    switch_penalty: float = 0.18,
    silence_penalty: float = 0.08,
) -> tuple[np.ndarray, list[str], np.ndarray]:
    """Selecciona una línea melódica condicionada por la partitura.

    Parameters
    ----------
    salience:
        Matriz ``(n_candidates, n_frames)`` de saliencia pitch.
    guitar, bass:
        Waveform o envolvente de cada stem. Se usan como evidencia de que la
        familia instrumental está activa; pueden ser ``None``.
    score_events:
        JSON producido por ``references/*_gp.json``, un diccionario
        ``{pista: eventos}`` o una lista de pistas/objetos con sus eventos.
    onsets:
        Ataques en segundos. Los ataques cercanos al inicio de una nota de la
        partitura reciben una pequeña bonificación.
    candidates, sr, hop:
        Alturas MIDI de las filas de ``salience`` y su escala temporal.

    Returns
    -------
    melody_n:
        Altura MIDI elegida por frame; ``np.nan`` representa silencio.
    track_path:
        Pista elegida por frame, o ``"silence"``.
    confidence:
        Confianza 0–1 basada en la separación entre las dos mejores opciones.
    """
    S = np.asarray(salience, dtype=float)
    cand = np.asarray(candidates, dtype=float).reshape(-1)
    if S.ndim != 2 or S.shape[0] != len(cand):
        raise ValueError("salience debe tener forma (len(candidates), n_frames)")
    if sr <= 0 or hop <= 0:
        raise ValueError("sr y hop deben ser positivos")

    n_frames = S.shape[1]
    times = np.arange(n_frames, dtype=float) * hop / sr
    tracks = _events_by_track(score_events, tempo_bpm)
    guitar_activity = _frame_activity(guitar, times, sr, hop)
    bass_activity = _frame_activity(bass, times, sr, hop)
    onset_times = np.asarray([] if onsets is None else list(onsets), dtype=float)

    # DP states are the score events active at each frame plus an explicit
    # silence state. The path can change only at score-note boundaries.
    states_by_frame: list[list[_State]] = []
    for time in times:
        active = [event for events in tracks.values() for event in events
                  if event.start - onset_tolerance <= time <= event.end + onset_tolerance]
        unique = {_state_key(event): event for event in active}
        states_by_frame.append(list(unique.values()) + [_State("silence", None, time, time)])

    previous_scores: dict[_State, float] = {}
    previous_paths: dict[_State, list[_State]] = {}
    margins = np.zeros(n_frames, dtype=float)
    chosen: list[_State] = []

    for frame, (time, states) in enumerate(zip(times, states_by_frame)):
        current_scores: dict[_State, float] = {}
        current_paths: dict[_State, list[_State]] = {}
        frame_salience = S[:, frame]
        for state in states:
            if state.track == "silence":
                emission = -silence_penalty
            else:
                pitch_evidence = _pitch_score(frame_salience, cand, state.pitch, pitch_tolerance)
                emission = pitch_evidence
                if "bass" in state.track.lower():
                    emission += 0.10 * bass_activity[frame]
                elif "guitar" in state.track.lower():
                    emission += 0.10 * guitar_activity[frame]
                source_evidence = bass_activity[frame] if "bass" in state.track.lower() else guitar_activity[frame]
                if pitch_evidence <= 1e-9 and source_evidence <= 1e-9:
                    emission -= 0.20
                elif abs(time - state.start) <= onset_tolerance:
                    emission += 0.08
                if len(onset_times) and np.min(np.abs(onset_times - state.start)) <= onset_tolerance:
                    emission += 0.08

            if not previous_scores:
                current_scores[state] = emission
                current_paths[state] = [state]
                continue
            best_prev, best_value = max(
                previous_scores.items(),
                key=lambda item: item[1] - (switch_penalty if item[0].track != state.track else 0.0),
            )
            current_scores[state] = emission + best_value - (switch_penalty if best_prev.track != state.track else 0.0)
            current_paths[state] = previous_paths[best_prev] + [state]

        ranked = sorted(current_scores.values(), reverse=True)
        if len(ranked) > 1:
            margins[frame] = ranked[0] - ranked[1]
        previous_scores, previous_paths = current_scores, current_paths
        best = max(current_scores, key=current_scores.get)
        chosen.append(best)

    melody_n = np.array([np.nan if state.pitch is None else state.pitch for state in chosen], dtype=float)
    track_path = [state.track for state in chosen]
    confidence = np.clip(margins / (np.abs(margins) + 0.25), 0.0, 1.0)
    return melody_n, track_path, confidence

