"""Mata Zyklek: loops de la partitura (KEXP, transcripción de 60 páginas), en forma que se puede medir.

Cómo está escrito:
- Alturas ESCRITAS en MIDI con cuartos de tono (x.5). Guitarras y bajos suenan una octava abajo de lo escrito
  (lo comprobé en el audio: en todas las secciones aparecen los armónicos impares de la octava de abajo).
- 'Ad4' = La medio bemol 4, 'Gq4' = Sol medio sostenido 4, 'Ab4' = La bemol 4, 'En4' = Mi becuadro escrito.
- Como en la partitura, una alteración vale hasta el final del compás: por eso el último La del riff es La medio bemol,
  aunque no lleve signo.
- Tiempos en negras dentro de compases de 5/4 (negra = 186). L guarda cada loop (un compás); ARR dice qué loop toca
  cada instrumento en cada compás (1 a 240).

Lo que dejé fuera o es dudoso: la batería; las notas de adorno; la corrida de la guitarra 4 en los compases 12, 16, 20...
del intro; la nota con cabeza triangular del compás 4 de la melodía 2; el bajo 1 suelto del corte 105-120.

Comparado con el audio oficial (alineado por DTW): el oficial no tiene unos 8 compases de la figura rápida de la
guitarra 2 (c. 194-201) y hay tres corrimientos de un pulso (c. 57, 98 y 129). Lo demás coincide.
"""
NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def P(s, carry=None):
    """'Ad4' = La medio bemol 4, 'Gq4' = Sol medio sostenido 4, 'Ab4' = La bemol 4, 'En4' = Mi becuadro 4 (explícito).
    Como en la partitura, una alteración vale hasta el final del compás para la misma nota y octava (carry)."""
    name, oct_ = s[0], int(s[-1])
    acc = {'d': -0.5, 'q': 0.5, 'b': -1.0, 's': 1.0, 'n': 0.0}.get(s[1]) if len(s) == 3 else None
    if carry is not None:
        if acc is None:
            acc = carry.get((name, oct_), 0.0)
        carry[(name, oct_)] = acc
    return 12 * (oct_ + 1) + NAMES[name] + (acc or 0.0)


def bar(*notes):
    carry = {}
    return [(o, d, P(p, carry)) for o, d, p in sorted(notes)]


def down(pattern, k=12):
    return [(o, d, p - k) for o, d, p in pattern]


RUN_G = [(2.5, .5, 'F4'), (3, .5, 'G4'), (3.5, .5, 'Gq4'), (4, .5, 'Ab4'), (4.5, .5, 'Ad4')]
L = {
    # riff principal (4 compases: a, a, a, d)
    'R_a': bar((0, .5, 'G4'), (.5, .5, 'G4'), (1, .5, 'Ad4'), (1.5, .5, 'G4'), (2, .5, 'G4'), (2.5, .25, 'G4'), (2.75, .25, 'G4'),
               (3, .5, 'F4'), (3.5, .5, 'G4'), (4, .5, 'G4'), (4.5, .5, 'A4')),
    'R_acc': bar((0, 1, 'G4'), (1, .5, 'Ad4'), (1.5, .5, 'G4'), (2, .5, 'G4'), (2.5, .25, 'G4'), (2.75, .25, 'G4'),
                 (3, .5, 'F4'), (3.5, .5, 'G4'), (4, .5, 'G4'), (4.5, .5, 'A4')),
    'R_d': bar((0, .5, 'G4'), (.5, .5, 'G4'), (1, .5, 'Ad4'), (1.5, .5, 'G4'), (2, .5, 'G4'), (2.5, .5, 'F4'),
               (3, .5, 'G4'), (3.5, .5, 'Gq4'), (4, .5, 'Ab4'), (4.5, .5, 'Ad4')),
    # melodía 1 de la guitarra 3 (4 compases: a, a, a, d)
    'M1_a': bar((0, 1, 'D4'), (1, .25, 'D4'), (1.25, .25, 'Ed4'), (1.5, .25, 'D4'), (1.75, .25, 'C4'), (2, .5, 'D4'), (2.5, .5, 'E4'),
                (3, 1, 'F4'), (4, .5, 'En4'), (4.5, .5, 'Ed4')),
    'M1_d': bar((0, 1, 'D4'), (1, .25, 'D4'), (1.25, .25, 'Ed4'), (1.5, .25, 'D4'), (1.75, .25, 'C4'), (2, .5, 'D4'), (2.5, .5, 'C4'),
                (3, .5, 'D4'), (3.5, .5, 'Dq4'), (4, .5, 'Eb4'), (4.5, .5, 'Ed4')),
    # melodía 2 de la guitarra 3, con la voz «Mata Zyklek» (4 compases) y sus variantes
    'M2_1': bar((0, 1, 'B4'), (1, .5, 'B4'), (1.5, .5, 'Ad4'), (2, .5, 'G4'), (2.5, .5, 'F4'), (3.5, 1, 'D5'), (4.5, .25, 'D5'), (4.75, .25, 'Ed5')),
    'M2_2': bar((0, 1, 'B4'), (1, .5, 'Bq4'), (1.5, .5, 'C5'), (2.5, .5, 'Bb4'), (3, .5, 'Bd4'), (3.5, .5, 'Bn4'), (4.5, .5, 'Ad4')),
    'M2_3': bar((0, 1, 'G4'), (1, 1, 'Ad4'), (3, .5, 'F4'), (3.5, 1, 'G4'), (4.5, .5, 'A4')),
    'M2_4': bar(*RUN_G),
    'M2_v3': bar((0, 1, 'G4'), (1, .25, 'Ab5'), (1.25, .25, 'Ad5'), (1.5, .25, 'Ab5'), (1.75, .25, 'F5'), (2, .25, 'B4'), (2.25, .25, 'F5'),
                 (2.5, .5, 'Eb5'), (3, 1, 'Bb4'), (4.5, .5, 'C5')),
    'M2_v4': bar((0, 1, 'B4'), (1, .25, 'D5'), (1.25, .25, 'E5'), (1.5, .25, 'D5'), (1.75, .25, 'C5'), (2, .5, 'D5'), (2.5, .5, 'E5'),
                 (3, .5, 'G4'), (3.5, .5, 'Gq4'), (4, .5, 'Ab4'), (4.5, .5, 'Ad4')),
    'RUN': bar(*RUN_G),
    'PICK': bar((2.5, .5, 'C4'), (3, .5, 'D4'), (3.5, .5, 'Dq4'), (4, .5, 'Eb4'), (4.5, .5, 'Ed4')),
    'B96': bar((0, .5, 'G4'), (.5, .5, 'G4'), (1, .5, 'Ad4'), (1.5, .5, 'G4'), (2, .5, 'G4'),
               (2.5, .5, 'C4'), (3, .5, 'D4'), (3.5, .5, 'Dq4'), (4, .5, 'Eb4'), (4.5, .5, 'Ed4')),
    'T120': bar(*RUN_G),
    # guitarra 1 (sección final, 2 compases)
    'F_a': bar((0, 1, 'G4'), (1, 1, 'Ad4'), (2, 1, 'G4'), (3, .5, 'F4'), (3.5, 1, 'G4'), (4.5, .5, 'A4')),
    'F_b': bar((0, 1, 'G4'), (1, 1, 'Ad4'), (2, .5, 'G4'), (2.5, .5, 'F4'), (3, .5, 'G4'), (3.5, .5, 'Gq4'), (4, .5, 'Ab4'), (4.5, .5, 'Ad4')),
    # guitarra 2: figura rápida (1 pulso por grupo) y notas sueltas
    'G2_fig': bar(*[n for k in range(4) for n in ((k, .25, 'G4'), (k + .25, .125, 'F5'), (k + .375, .125, 'G5'), (k + .5, .25, 'G4'), (k + .75, .25, 'G5'))],
                  (4, .25, 'G4'), (4.25, .25, 'G5'), (4.5, .25, 'Gq5'), (4.75, .25, 'Ad5')),
    'G2_long': bar((0, 2, 'G4')),
    'G2_short': bar((0, 1, 'G4')),
    # sección grave (2 compases)
    'G3_lo_a': bar(*[(k, 1, 'G3') for k in range(5)]),
    'G3_lo_b': bar((0, 1, 'G4'), (1, 1, 'G3'), (2, 1, 'G3'), (3, 1, 'G3'), (4, .5, 'G3'), (4.5, .5, 'Ad3')),
    'G4_sp_a': bar((1, 1, 'G3'), (4, 1, 'G3')),
    'G4_sp_b': bar((2, 1, 'G3'), (4, .5, 'G3'), (4.5, .5, 'Ad3')),
    'G4_intro': bar((4.5, .5, 'Cd4')),
    # bajos (clave de fa, escritos)
    'B1_A_a': bar((4.5, .5, 'Ad3')),
    'B1_A_d': bar((2.5, .5, 'F3'), (3, .5, 'G3'), (3.5, .5, 'Gq3'), (4, .5, 'Ab3'), (4.5, .5, 'Ad3')),
    'B2_a': bar((0, 1, 'G2'), (1, .5, 'Ad2'), (1.5, .5, 'G2'), (2, .5, 'G2'), (2.5, .5, 'G3'), (3, .5, 'F3'), (3.5, .5, 'G3'), (4, .5, 'G2'), (4.5, .5, 'A2')),
    'B2_d': bar((0, 1, 'G2'), (1, .5, 'Ad2'), (1.5, .5, 'G2'), (2, .5, 'G2'), (2.5, .5, 'F2'), (3, .5, 'G2'), (3.5, .5, 'Gq2'), (4, .5, 'Ab2'), (4.5, .5, 'Ad2')),
    'B2_ped_a': bar(*[(k, 1, 'G2') for k in range(5)]),
    'B2_ped_b': bar((0, 1, 'G2'), (1, 1, 'G2'), (2, 1, 'G2'), (3, 1, 'G2'), (4, .5, 'G2'), (4.5, .5, 'Ad2')),
}
for k in ('R_a', 'R_acc', 'R_d'):
    L['B1_' + k] = down(L[k])


def four(start, end, a, d, first=None):
    """Loop de 4 compases (a, a, a, d) desde start hasta end inclusive."""
    return {b: (first if first and (b - start) % 4 == 0 else (d if (b - start) % 4 == 3 else a)) for b in range(start, end + 1)}


def two(start, end, a, b):
    return {k: (a if (k - start) % 2 == 0 else b) for k in range(start, end + 1)}


ARR = {p: {} for p in ('G1', 'G2', 'G3', 'G4', 'B1', 'B2')}
# guitarra 3
G3 = ARR['G3']
G3.update(four(17, 31, 'R_a', 'R_d', 'R_acc')); G3[32] = 'RUN'; G3[48] = 'PICK'
G3.update(four(49, 63, 'M1_a', 'M1_d')); G3[64] = 'RUN'
for s in (65, 69, 73, 129, 133, 137):
    G3.update({s: 'M2_1', s + 1: 'M2_2', s + 2: 'M2_3', s + 3: 'M2_4'})
G3.update({77: 'M2_1', 78: 'M2_2', 79: 'R_a', 80: 'R_d', 141: 'M2_1', 142: 'M2_2', 143: 'R_a', 144: 'R_d'})
for s, tail in ((81, 'v'), (85, 'R'), (89, 'v'), (145, 'v'), (149, 'R'), (153, 'v')):
    G3.update({s: 'M2_1', s + 1: 'M2_2'})
    G3.update({s + 2: 'M2_v3', s + 3: 'M2_v4'} if tail == 'v' else {s + 2: 'R_a', s + 3: 'R_d'})
G3.update({93: 'M2_1', 94: 'M2_2', 95: 'R_a', 96: 'B96', 157: 'M2_1', 158: 'M2_2'})
G3.update(four(97, 119, 'M1_a', 'M1_d')); G3[120] = 'T120'
G3.update(two(177, 208, 'G3_lo_a', 'G3_lo_b'))
G3[231] = 'R_a'; G3[232] = 'RUN'; G3.update(two(233, 240, 'R_a', 'R_d'))
# guitarra 4
G4 = ARR['G4']
G4.update({b: 'G4_intro' for b in range(9, 32) if (b - 9) % 4 != 3})
G4.update(four(33, 104, 'R_a', 'R_d', 'R_acc')); G4.update(four(121, 160, 'R_a', 'R_d', 'R_acc'))   # en el corte 105-120 no toca
G4.update(two(169, 208, 'G4_sp_a', 'G4_sp_b'))
# guitarra 2
G2 = ARR['G2']
G2.update({184: 'G2_long', 186: 'G2_long', 188: 'G2_short', 190: 'G2_short', 192: 'G2_short'})
G2.update({b: 'G2_fig' for b in range(193, 209)})
G2.update(two(217, 223, 'R_a', 'R_d')); G2[224] = 'RUN'; G2.update(two(225, 240, 'R_a', 'R_d'))
# guitarra 1
G1 = ARR['G1']
G1.update(two(201, 223, 'F_a', 'F_b')); G1[224] = 'RUN'; G1.update(two(225, 240, 'F_a', 'F_b'))
# bajo 1
B1 = ARR['B1']
B1.update(four(1, 31, 'B1_A_a', 'B1_A_d'))
B1.update(four(33, 104, 'B1_R_a', 'B1_R_d', 'B1_R_acc'))
B1.update(four(121, 160, 'B1_R_a', 'B1_R_d', 'B1_R_acc'))
B1.update(two(225, 240, 'B1_R_a', 'B1_R_d'))
# bajo 2
B2 = ARR['B2']
B2.update(four(41, 104, 'B2_a', 'B2_d')); B2.update(four(121, 160, 'B2_a', 'B2_d'))
B2.update(two(161, 208, 'B2_ped_a', 'B2_ped_b'))

N_BARS, BEATS = 240, 5
GUITARS = ('G1', 'G2', 'G3', 'G4')
BASSES = ('B1', 'B2')


def notes(parts):
    """Notas (compás 1-based, inicio en negras absolutas, duración, altura escrita, parte, loop)."""
    out = []
    for part in parts:
        for b, pat in ARR[part].items():
            for o, d, p in L[pat]:
                out.append((b, (b - 1) * BEATS + o, d, p, part, pat))
    return sorted(out, key=lambda x: (x[1], x[3]))


SECTIONS = [  # compases (inclusive) y qué pasa, para el informe
    (1, 16, 'Intro: bajo 1 (y guitarra 4 desde el 8) con una nota por compás'),
    (17, 32, 'Entra el riff en la guitarra 3'),
    (33, 48, 'Riff en guitarra 4 y bajo 1; bajo 2 desde el 41'),
    (49, 64, 'Melodía 1 (guitarra 3, en Re) sobre el riff'),
    (65, 96, 'Melodía 2 (guitarra 3, en Si) con la voz «Mata Zyklek»'),
    (97, 104, 'Melodía 1 de nuevo'),
    (105, 120, 'Corte: melodía 1 sola con el bajo 1 suelto'),
    (121, 128, 'Riff sin melodía'),
    (129, 160, 'Melodía 2 de nuevo'),
    (161, 192, 'Sección grave: pedal de Sol (bajo 2, guitarras 4 y 3)'),
    (193, 208, 'Figura rápida de la guitarra 2; guitarra 1 desde el 201'),
    (209, 224, 'Guitarra 1 sola, luego con el riff en la guitarra 2'),
    (225, 240, 'Final: todo en el riff de 2 compases'),
]
