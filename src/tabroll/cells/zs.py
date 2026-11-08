"""Compases (longitud variable)
"""

def _zs(v, win=31):
    r = v - uniform_filter1d(v, win, mode='nearest')
    return r / (r.std() + 1e-9)
