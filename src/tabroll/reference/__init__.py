"""Lectura de referencias musicales externas al análisis de audio."""

from .guitarpro import GuitarProScore, parse_gp, parse_score
from .select_melody_track import select_melody_track
from .align_gp_audio import align_gp_audio

__all__ = ["GuitarProScore", "parse_gp", "parse_score", "select_melody_track", "align_gp_audio"]
