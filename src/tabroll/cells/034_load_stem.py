"""Celda 65 del notebook original.

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def load_stem(path, n, sr):
    if not path:
        return None

    x = librosa.load(path, sr=sr, mono=True)[0]
    if abs(len(x) - n) > sr:
        raise ValueError(f'{Path(path).name} no corresponde al audio de entrada.')

    return np.pad(x, (0, max(n - len(x), 0)))[:n]
