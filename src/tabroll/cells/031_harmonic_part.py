"""Celda 59 del notebook original. Descripcion asociada: **`harmonic_part`**: atenúa los golpes de batería en el espectrograma y conserva lo que se sostiene en el tiempo..

Este modulo conserva el orden y la logica de la celda para facilitar la trazabilidad.
"""


def harmonic_part(M, kt=7, kf=31):
    H = median_filter(M, size=(1, kt))                                   # lo que se sostiene en el tiempo
    P = median_filter(M, size=(kf, 1))                                   # lo que se abre en frecuencia: golpes
    return M * H ** 2 / (H ** 2 + P ** 2 + 1e-9)
