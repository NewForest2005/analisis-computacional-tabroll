"""**`detect_onsets`**: Detecta ataques a partir de una envolvente de onsets. `height` es la altura mínima del pico, en desviaciones típicas, y `win` es la ventana, en segundos, del promedio local que se resta.
"""

def detect_onsets(oenv, fps, height=0.6, win=1.0):
    z = oenv - uniform_filter1d(oenv, max(1, int(win * fps)), mode='nearest')
    z = z / (z.std() + 1e-9)
    pk, _ = find_peaks(z, height=height, prominence=0.5, distance=max(1, int(0.06 * fps)))

    return pk / fps
