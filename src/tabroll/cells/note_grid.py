"""**`note_grid`**: mira en qué parte del pulso caen los ataques. Si caen en tercios, el pulso se divide en tres corcheas, como en el 12/8 de Sarniezz, y la cuantización pasa a 1/6 de pulso para que cada corchea quede en su sitio. Si no, deja GRID como está.
"""

def note_grid(onsets_t, pos, grid):
    f = pos(onsets_t) % 1                                                                    # dónde cae cada ataque dentro del pulso
    R = [abs(np.mean(np.exp(2j * np.pi * s * f))) for s in (2, 3, 4)]

    return 1 / 6 if R[1] > 2 * max(R[0], R[2]) else grid                                     # pulso que se divide en 3 (6/8, 12/8): rejilla de 1/6
