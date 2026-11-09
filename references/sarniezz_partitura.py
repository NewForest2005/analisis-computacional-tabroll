"""Sarniezz: partitura de Andrew Kahler («attempted transcription», 11 págs) desplegada en corcheas, con las
correcciones que se comprobaron contra la grabación oficial. Solo sirve para medir el análisis; el cuaderno no la usa.

Alturas ESCRITAS en MIDI con cuartos de tono: guitarras en clave de sol 8vb y bajo eléctrico suenan una octava abajo
(TRANSPOSE). Alteraciones (Stein-Zimmermann): 'q' medio sostenido, 's' sostenido, 't' tres cuartos sostenido,
'd' medio bemol, 'b' bemol. Cada nota alterada lleva su signo, así que una nota sin signo es natural.

Correcciones de oído (autor, 9-nov-2026, verificadas con clips de la guitarra real frente a la partitura sintetizada):
- Frase 1, posiciones 39-47: Re La¼ Re Do#¼ Do# Do#¼ Re Do#¼ Do#. El La¼ va arriba (el audio no tiene La¼ grave).
- Frase 2 (guitarra 2): Sol# en 5, 7 y 18; Re6 en 8 (no Fa6; octava comprobada en el audio); Si¼-Si en semicorcheas en
  15; Si¼ en 22 y Si en 23. Confirmada en c. 43-51 y c. 64-69.
- Patrón del bajo tocado por la guitarra 1: Sol#¼ en 8, Do#¼ en 12.5 y Do# en 13. El bajo queda como en la partitura.
- Ya confirmados sin cambios: el riff (c. 15-18) y la guitarra 2 una octava abajo en c. 37-42.

No medible: c. 1-14 (casi solo bajo), «go go» c. 52-56 (solo ritmo), c. 58-63 (suena una línea de la guitarra 1 que
la partitura no tiene y cuyo ritmo no quedó fijado) y la improvisación de la guitarra 1 en c. 77-82.
"""
NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
ACC = {'q': .5, 's': 1., 't': 1.5, 'd': -.5, 'b': -1.}


def P(s):
    return 12 * (int(s[-1]) + 1) + NAMES[s[0]] + (ACC[s[1]] if len(s) == 3 else 0.)


def pat(*notes):
    return [(o, d, P(p)) for o, d, p in notes]


def up(p, k):
    return [(o, d, x + k) for o, d, x in p]


def cat(*parts):
    """Junta patrones seguidos: cada uno es (largo, notas)."""
    out, t = [], 0
    for n, notes in parts:
        out += [(o + t, d, p) for o, d, p in notes]; t += n
    return t, out


def rot(n, notes, k):
    """Patrón de n corcheas que empieza k corcheas más adelante («all motifs shift 3 ♪'s back»)."""
    return n, sorted(((o - k) % n, d, p) for o, d, p in notes)


# ---------------------------------------------------------------- bajo
A12 = pat((0, 1, 'D3'), (1, 1, 'Dq3'), (2, 1, 'Ds3'), (3, 1, 'Dt3'), (4, 1, 'E3'), (5, 1, 'D3'), (6, 1, 'Dq3'), (7, 1, 'Ds3'),
          (8, 1, 'Dt3'), (9, 1, 'E3'), (10, 1, 'E3'), (11, 1, 'Dt3'))   # Re#+ (gp oficial; el audio lo confirma en 28 de 36)
BLO = pat((0, 1, 'Ds3'), (1, 1, 'Dq3'), (2, 1, 'D3'), (3, 1, 'B2'), (4, 1, 'D3'), (5, 1, 'B2'), (6, 1, 'E2'), (7, 1, 'G2'),
          (8, 1, 'Gq2'), (9, 1, 'Gs2'), (10, 1, 'Gq2'), (11, 1, 'G2'))
BHI = [(o, d, p + 12 if o >= 7 else p) for o, d, p in BLO]
B14 = pat((0, 1, 'Ds3'), (1, 1, 'Dq3'), (2, 1, 'D3'), (3, 1, 'B2'), (7, 1, 'G3'), (8, 1, 'Gq3'), (9, 1, 'Gs3'), (10, 1, 'Gq3'), (11, 1, 'G3'))
INTRO_A, INTRO_B = pat((0, 3, 'E2'), (10, 2, 'E2')), pat((0, 3, 'E2'))
B27, B28 = pat((0, 1, 'D3'), (3, 1, 'E3'), (6, 1, 'D3'), (8, 1, 'E2')), pat((7, 5, 'G3'))
B30 = pat((7, 1, 'G3'), (8, 1, 'Gq3'), (9, 1, 'Gs3'), (10, 1, 'Gq3'), (11, 1, 'G3'))
S48 = cat((12, A12), (12, BLO), (12, A12), (12, BHI))[1]
BP = pat((0, 2, 'E3'), (2, 1, 'E3'), (3, .5, 'E3'), (3.5, .5, 'E3'), (4, 1, 'D3'), (5, 1, 'E3'), (7, 1, 'A3'),
         (8, 1, 'Gs3'), (9, 1, 'Gs3'), (10, 1, 'Gq3'), (11, 1, 'G3'), (12, .5, 'D4'), (12.5, .5, 'Cs4'), (13, 1, 'Cq4'), (14, 1, 'E3'), (15, 1, 'A3'),
         (16, 1, 'G2'), (17, 1, 'D3'), (18, 1, 'G3'), (19, 1, 'D3'), (20, 1, 'G3'), (21, 1, 'D3'), (22, 1, 'G3'), (23, 1, 'D3'))

# ---------------------------------------------------------------- guitarras
P1 = pat((0, 1, 'D5'), (1, 1, 'D5'), (2, 1, 'D5'), (3, 1, 'E5'), (6, 2, 'A4'), (8, 1, 'D5'), (8, 1, 'Fs5'), (10, 1, 'Gs5'), (11, 1, 'Gq5'),
         (12, 1, 'G5'), (13, 1, 'Fs5'), (14, 1, 'Fs5'), (15, 1, 'D5'), (16, 1, 'Cq6'), (17, 1, 'E5'), (18, 1, 'D5'),
         (19, 5, 'Cs5'), (19, 5, 'D5'), (19, 5, 'Fs5'),
         (24, 1, 'A4'), (25, 1, 'Aq4'), (26, 1, 'Fs5'), (27, 1, 'A4'), (28, 1, 'Aq4'), (29, 1, 'Fs5'), (30, 1, 'Fs5'), (31, 1, 'G5'),
         (32, 1, 'Gq5'), (33, 1, 'Gs5'), (34, 1, 'Cs5'), (35, 1, 'Cq5'), (36, 1, 'C5'), (37, 1, 'Bq4'), (38, 1, 'B4'), (39, 1, 'D5'),
         (40, 1, 'Aq5'), (41, 1, 'D5'), (42, 1, 'Ct5'), (43, 1, 'Cs5'), (44, 1, 'Ct5'), (45, 1, 'D5'), (46, 1, 'Ct5'), (47, 1, 'Cs5'))
# 39-47 corregidas de oído por el autor (9-nov): «D A1/4 D C#1/4 C# C#1/4 D C#1/4 C#», misma métrica; el La¼ va arriba (el audio no tiene La¼3)
# guitarra 2 en 37-42: la frase una octava abajo (el primer compás al unísono)
P1LOW = [(o, d, p if o < 8 else p - 12) for o, d, p in P1
         if not (o == 8 and p == P('D5')) and o not in (16, 40) and not (o == 19 and p != P('Cs5'))]
# frase 2 corregida de oído por el autor (9-nov, escuchada en c. 64-69): Sol# en 5, 7 y 18 (no Sol), Re6 en 8 (no Fa6;
# el audio confirma la octava), Si¼-Si en semicorcheas en 15 (no silencio), Si¼ en 22 y Si en 23 (no Si y Si-¼)
P2 = pat((0, 1, 'D5'), (1, 1, 'D5'), (2, 1, 'B5'), (3, 1, 'Gs5'), (5, 1, 'Gs5'), (6, 1, 'B5'), (7, 1, 'Gs5'),
         (8, 1, 'D6'), (10, 1, 'Cs6'), (11, 1, 'Cq6'), (12, 1, 'C6'), (13, 1, 'Bq5'), (14, 1, 'B5'), (15, .5, 'Bq5'), (15.5, .5, 'B5'),
         (16, 1, 'Gs5'), (17, 1, 'B5'), (18, 1, 'Gs5'), (19, 1, 'Cs6'), (20, 1, 'Cq6'), (21, 1, 'E5'), (22, 1, 'Bq5'), (23, 1, 'B5'))
DYAD20 = pat((7, 3, 'D5'), (7, 3, 'Fs5'))
G13 = pat((10, 1, 'E4'), (11, 1, 'Ds4'))
G14 = pat((0, 1, 'Ds4'), (1, 1, 'Dq4'), (2, 1, 'D4'), (3, 1, 'B3'), (7, 1, 'G3'), (8, 1, 'Gq3'), (9, 1, 'Gs3'), (10, 1, 'Gq3'), (11, 1, 'G3'))
# la guitarra 1 toca el patrón del bajo con tres alturas distintas (corregidas de oído por el autor, 9-nov):
# posición 8 Sol#¼ (no Sol#), 12.5 Do#¼ (no Do#), 13 Do# (no Do¼). El bajo se deja como en la partitura.
BPG = [(o, d, {8: P('Gt3'), 12.5: P('Ct4'), 13: P('Cs4')}.get(o, p)) for o, d, p in BP]
BP12, BP24 = up(BPG, 12), up(BPG, 24)
CRAZY = cat((8, [(o, d, (P('C5') if o == 7 else p)) for o, d, p in BP12 if o < 8]), (16, [(o - 8, d, p) for o, d, p in BP12 if o >= 8]),
            (8, [(o, d, (P('E4') if o == 7 else p)) for o, d, p in BP12 if o < 8]),
            (8, [(o - 8, d, {0: P('Ds4'), 1: P('Ds4'), 2: P('Dq4'), 3: P('D4')}.get(o - 8, p)) for o, d, p in BP12 if 8 <= o < 16]),
            (8, [(o - 16, d, p) for o, d, p in BP12 if o >= 16]))

# ---------------------------------------------------------------- despliegue (secciones en orden)
E1, E2 = 60 / 342, 60 / 360            # corchea a negra con puntillo = 114 y, desde el c. 52, a negra = 180
SECTIONS = []                          # (nombre, corcheas, segundos por corchea, {parte: notas}, medible)


def sec(name, n, parts, eighth=E1, known=True):
    SECTIONS.append((name, n, eighth, parts, known))


def rep(k, n, notes):
    return [(o + i * n, d, p) for i in range(k) for o, d, p in notes]


sec('Intro: bajo solo (c. 1-8)', 96, {'B': cat(*[(12, INTRO_A if i % 2 == 0 else INTRO_B) for i in range(8)])[1]})
sec('Riff del bajo (c. 9-13)', 84, {'B': cat((12, A12), (12, BLO), (12, A12), (12, BHI), (12, A12), (12, BLO), (12, A12))[1],
                                    'G2': [(72 + o, d, p) for o, d, p in G13]})
sec('Riff, puente (c. 14)', 12, {'B': B14, 'G2': G14})
riff = cat((12, A12), (12, BLO), (12, A12), (12, BHI))[1]
sec('Riff en bajo y guitarra 2 (c. 15-18)', 96, {'B': rep(2, 48, riff), 'G2': rep(2, 48, up(riff, 12))})
sec('Riff + acorde de la guitarra 1 (c. 19-22)', 96, {'B': rep(2, 48, riff), 'G2': rep(2, 48, up(riff, 12)),
                                                     'G1': rep(2, 48, [(12 + o, d, p) for o, d, p in DYAD20])})
sec('Frase 1 de la guitarra 1 sobre el riff (c. 23-26)', 96, {'B': rep(2, 48, riff), 'G2': rep(2, 48, up(riff, 12)), 'G1': rep(2, 48, P1)})
sec('Frase 1 con bajo suelto (c. 27-30, 4 veces)', 192, {'G1': rep(4, 48, P1), 'B': rep(4, 48, cat((12, B27), (12, B28), (12, B27), (12, B30))[1])})
sec('Frase 1 en 4/4 (c. 31-36)', 96, {'G1': rep(2, 48, P1), 'B': rep(2, 48, S48)})
sec('Frase 1 con la guitarra 2 una octava abajo (c. 37-42, 4 veces)', 192, {'G1': rep(4, 48, P1), 'G2': rep(4, 48, P1LOW), 'B': rep(4, 48, S48)})
sec('Frase 1 + frase 2 aguda de la guitarra 2 (c. 43-51)', 192, {'G1': rep(4, 48, P1), 'G2': rep(8, 24, P2), 'B': rep(4, 48, S48)})
sec('«Go go» (c. 52-56, solo ritmo)', 40, {}, E2, known=False)
sec('Silencio (c. 57)', 3, {}, E2)
# c. 58-63 no se mide: el autor oye en 3:23 una línea de la guitarra 1 que no está aquí (ritmo sin fijar)
sec('Todo corrido 3 corcheas (c. 58-63)', 96, {'G1': rep(2, 48, rot(48, P1, 3)[1]), 'G2': rep(4, 24, rot(24, P2, 3)[1]), 'B': rep(4, 24, BP)}, E2, known=False)
sec('Patrón del bajo en guitarra 1 (c. 64-69, 4 veces)', 192, {'G1': rep(8, 24, BP12), 'G2': rep(8, 24, rot(24, P2, 3)[1]), 'B': rep(8, 24, BP)}, E2)
sec('Patrón del bajo en las tres partes (c. 70-76)', 96, {'G1': rep(4, 24, BP12), 'G2': [n for n in rep(4, 24, BP24) if n[0] < 88], 'B': rep(4, 24, BP)}, E2)
sec('Final libre de la guitarra 1 (c. 77-82)', 96, {'G1': rep(2, 48, CRAZY[1]), 'G2': rep(4, 24, BP12), 'B': rep(4, 24, BP)}, E2)
sec('Cierre (c. 83)', 8, {'G1': [n for n in BP12 if n[0] < 6], 'G2': [n for n in BP12 if n[0] < 6], 'B': [n for n in BP if n[0] < 6]}, E2)

GUITARS, BASSES = ('G1', 'G2'), ('B',)


def notes(parts):
    """Notas desplegadas: (sección, inicio en corcheas, duración en corcheas, altura escrita, parte)."""
    out, t = [], 0
    for k, (name, n, eighth, P_, known) in enumerate(SECTIONS):
        for part in parts:
            out += [(k, t + o, d, p, part) for o, d, p in P_.get(part, [])]
        t += n
    return sorted(out, key=lambda x: (x[1], x[3]))


def timeline():
    """(inicio en corcheas, corcheas, seg/corchea, medible) por sección."""
    out, t = [], 0
    for name, n, eighth, P_, known in SECTIONS:
        out.append((t, n, eighth, known, name)); t += n
    return out


TRANSPOSE = {'G1': -12, 'G2': -12, 'B': -12}
