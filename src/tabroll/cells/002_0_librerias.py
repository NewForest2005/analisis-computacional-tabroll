"""Celda 2 del notebook original.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

# @title 0) Librerias
from __future__ import annotations

from pathlib import Path
import zipfile

import math
import re
from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field, replace
from typing import Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import to_hex, to_rgb
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from scipy.signal import find_peaks
from scipy.ndimage import uniform_filter1d, median_filter, maximum_filter1d

import librosa
from collections import Counter
from IPython.display import display

from PIL import Image
from IPython.display import Image as IPyImage, display
