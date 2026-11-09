#!/usr/bin/env python3
"""Grafica pistas del GP, notas detectadas y la línea elegida por Tabroll.

Ejemplo:
    python scripts/plot_line_diagnostics.py \
        outputs/2026-11-08_170852_angine_de_poitrine_sarniezz_audio_offici_sarniezz_oficial \
        --reference references/sarniezz_gp.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt


REFERENCE_TRACKS = {
    "SARNIEZZ": "E.Guitar I",
    "MATA ZYKLEK": "E.Guitar III",
    "FABIENK": "E.Guitar",
}


def _audio_pitch(event: dict) -> float:
    """Altura que suena. GP Midi ya es la altura real, no la escrita."""
    return float(event["pitch"]["midi_with_bend"])


def _align(events: list[dict], detected: list[dict], seconds_per_beat_guess: float) -> tuple[float, float, float]:
    """Busca el tempo y desfase que mejor alinean un fragmento GP con el audio."""
    import numpy as np

    ev = [event for event in events if event["pitch"].get("midi_with_bend") is not None]
    if not ev or not detected:
        return seconds_per_beat_guess, 0.0, 0.0
    g_on = np.array([float(event["onset_beats"]) for event in ev])
    g_p = np.array([_audio_pitch(event) for event in ev])
    d_on = np.array([float(event["start_s"]) for event in detected])
    d_p = np.array([float(event["midi"]) for event in detected])
    best = (seconds_per_beat_guess, 0.0, 0.0)
    for ratio in (1.0, 2 / 3, 1.5, 0.5, 2.0):
        for fine in np.linspace(0.97, 1.03, 13):
            seconds_per_beat = seconds_per_beat_guess * ratio * fine
            gp_times = g_on * seconds_per_beat
            for index in np.flatnonzero(np.abs(d_p - g_p[0]) < 0.3):
                times = gp_times + (d_on[index] - gp_times[0])
                close = np.abs(times[:, None] - d_on[None, :]) <= 0.075
                same = np.abs(g_p[:, None] - d_p[None, :]) < 0.3
                score = float((close & same).any(axis=1).mean())
                if score > best[2]:
                    best = (seconds_per_beat, float(d_on[index] - gp_times[0]), score)
    return best


def _draw_events(ax, events, seconds_per_beat, color, label, alpha=0.65, linewidth=4, offset=0.0):
    first = True
    for event in events:
        x0 = offset + float(event["onset_beats"]) * seconds_per_beat
        x1 = x0 + float(event["duration_beats"]) * seconds_per_beat
        ax.plot([x0, x1], [_audio_pitch(event)] * 2, color=color, alpha=alpha, linewidth=linewidth,
                solid_capstyle="butt", label=label if first else None)
        first = False


def _draw_detected(ax, events, color, label):
    first = True
    for event in events:
        ax.plot([event["start_s"], event["end_s"]], [event["midi"]] * 2, color=color, linewidth=2.2,
                alpha=0.9, label=label if first else None)
        first = False


def plot_diagnostics(run_dir: Path, reference_path: Path, output: Path | None = None) -> Path:
    diagnostics = json.loads((run_dir / "line_diagnostics.json").read_text(encoding="utf-8"))
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    tempo = float(diagnostics["tempo_bpm"])
    seconds_per_beat = 60.0 / tempo
    tracks = [track for track in reference["tracks"] if "Drum" not in track["name"].lower()]
    guitars = [track for track in tracks if "guitar" in track["name"].lower()]
    bass = [track for track in tracks if "bass" in track["name"].lower()]
    preferred_name = REFERENCE_TRACKS.get(reference["title"])
    preferred = next((track for track in guitars if track["name"] == preferred_name), None)
    if preferred is None and guitars:
        preferred = max(guitars, key=lambda track: len(track["events"]))

    detected = diagnostics.get("raw_high", []) + diagnostics.get("raw_bass", [])
    seconds_per_beat, offset, hit = _align(
        preferred["events"] if preferred else [], detected, seconds_per_beat,
    )
    print(
        f"GP alineado: {60 / seconds_per_beat:.1f} negras por minuto, "
        f"empieza en {offset:.2f} s, {100 * hit:.0f}% de sus notas coinciden con notas detectadas"
    )

    fig, ax = plt.subplots(figsize=(18, 9), constrained_layout=True)
    colors = ["#4c78a8", "#f58518", "#54a24b", "#b279a2"]
    for index, track in enumerate(guitars):
        _draw_events(ax, track["events"], seconds_per_beat, colors[index % len(colors)], track["name"], alpha=0.42, linewidth=5, offset=offset)
    for track in bass:
        _draw_events(ax, track["events"], seconds_per_beat, "#e45756", track["name"], alpha=0.55, linewidth=4, offset=offset)
    if preferred is not None:
        _draw_events(ax, preferred["events"], seconds_per_beat, "#111111", f"GP: {preferred['name']} (referencia)", alpha=0.95, linewidth=1.7, offset=offset)

    hop = diagnostics["hop"]
    sr = diagnostics["sample_rate"]
    for name, color, label in (("melody_n", "#000000", "Tabroll: línea actualmente elegida"), ("melody", "#7f7f7f", "Tabroll: línea para ciclos")):
        values = diagnostics.get(name)
        if not values:
            continue
        xs = [index * hop / sr for index in range(len(values))]
        ys = [float(value) if value is not None else float("nan") for value in values]
        ax.plot(xs, ys, color=color, linewidth=1.0 if name == "melody" else 1.8, alpha=0.9, label=label)
    _draw_detected(ax, diagnostics.get("raw_high", []), "#d62728", "Notas agudas detectadas")
    _draw_detected(ax, diagnostics.get("raw_bass", []), "#e45756", "Notas graves detectadas")

    max_bar = max((event["onset_beats"] + event["duration_beats"] for track in tracks for event in track["events"]), default=0)
    ax.set_xlim(offset, offset + max_bar * seconds_per_beat)
    ax.set_xlabel("Tiempo del audio (s)")
    ax.set_ylabel("Altura en MIDI (sonido real)")
    ax.set_title(f"{reference['title']} · líneas del GP frente al análisis Tabroll")
    ax.grid(axis="y", alpha=0.2)
    ax.legend(loc="upper left", ncol=2, fontsize=9)
    output = output or run_dir / "line_diagnostics.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=160)
    plt.close(fig)
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args(argv)
    path = plot_diagnostics(args.run_dir, args.reference, args.output)
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
