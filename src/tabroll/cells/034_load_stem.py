"""Celda 65 del notebook original. Descripcion asociada: **`load_stem`**: Carga una pista de Demucs en mono, a la frecuencia del análisis y con la misma duración que la canción. Si dura más de un segundo distinto, avisa que no corresponde a este audio. Sin pista devuelve `None`..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""

def load_stem(path, n, sr):
    if not path:
        return None

    x = librosa.load(path, sr=sr, mono=True)[0]
    if abs(len(x) - n) > sr:
        raise ValueError(f'{Path(path).name} no corresponde al audio de entrada.')

    return np.pad(x, (0, max(n - len(x), 0)))[:n]
