"""Lectura de referencias musicales externas al análisis de audio."""

from .guitarpro import GuitarProScore, parse_gp, parse_score
from .select_melody_track import select_melody_track

__all__ = ["GuitarProScore", "parse_gp", "parse_score", "select_melody_track"]
