"""Lectura de referencias musicales externas al análisis de audio."""

from .guitarpro import GuitarProScore, parse_gp, parse_score

__all__ = ["GuitarProScore", "parse_gp", "parse_score"]
