"""Yor Zarad: partitura de Guitar Pro (5 pistas, 201 compases) en forma que se puede medir. Solo sirve para medir el
análisis; el cuaderno no la usa. Es la primera referencia «a ciegas»: se armó sin mirar ninguna salida del cuaderno.

De dónde sale cada dato (las notas están en yor_zarad_notas.csv):
- Alturas, cuerdas, trastes, ligados y bends: la tablatura de los PDF exportados de Guitar Pro (guitarras I, II y III y
  bajo, afinación estándar). Un «¼» sube un cuarto de tono la nota de la que sale la flecha (bend o pre-bend), «½» un
  semitono y «full» un tono. Los armónicos naturales <12>, <7> y <5> suenan una octava, una doceava y dos octavas arriba
  de la cuerda al aire.
- Ataques: los WAV que exporta Guitar Pro de la misma partitura, a negra = 107 desde t = 0. Cada ataque del PDF se
  empareja con un ataque del WAV de su pista (altura medida con YIN). Lo que no tiene ataque en el WAV (ligados de mano
  izquierda, notas repetidas que el detector no separa) se interpola por su posición en el compás y va a la fusa más
  cercana (`ataque_medido` = 0).
- Métrica: no está en el texto del PDF. Sale de los ataques: 7/8 hasta el c. 148; en H (c. 149-168), cuatro compases
  de 6/8 y uno de 2/4; en el Outro (c. 169-201), tres de 4/4 y uno de 2/4. Comprobado a la vista en el PDF.
- No están: las notas de adorno, las notas muertas (X) y la batería.

Los ligados sin cambio de altura se suman a su nota. Un ligado que cambia de altura (bend sobre la nota ligada o vuelta
del bend) queda como nota aparte con `ligada` = 1: el audio cambia de altura sin un ataque nuevo.

Comprobaciones: la altura medida en el WAV coincide con la del PDF más el bend (el render suena entre 0.1 y 0.5
semitonos alto según la pista y el registro, igual con y sin bend). El render y la grabación oficial van al mismo tempo:
la grabación empieza 4.11 s más tarde y no se desvía de esa recta (references/alineaciones/yor_zarad.json).

Verificación de oído (autor, 14-nov-2026): 20 clips de la grabación frente a la partitura sintetizada y 6 clips a
ciegas con versiones en orden al azar. Cambios respecto del PDF:
- Intro: el primer acorde de armónicos de la guitarra 2 va un cuarto de tono arriba.
- Figura del bajo (c. 24, 28, 64, 68, 72, 112, 116, 120, 124, 136, 140, 144 y 148): la nota aguda es La (no Sol#),
  elegida a ciegas en 2 de 2 clips.
- Ciclo de las guitarras 1 y 3: la nota aguda queda como en el PDF en la primera parte de H (c. 149-158), es Re en H
  con la guitarra 3 (c. 159-168) y es Sol# una octava abajo en el Outro (c. 169-199), elegidas a ciegas.
- Guitarra 2: sin los dos La# del final del c. 28; en el c. 60 la nota larga es Fa (no Si); la figura rápida de los
  c. 133-168 repite el mismo ritmo en todas las vueltas.
- Guitarra 1: sin el Sol# sobrante del c. 76; en el riff de E (c. 77-108) la última nota se parte en Fa y Sol.
- Los tiempos de las notas ligadas sin ataque salen del cambio de altura en el WAV (`ataque_medido` = 2).

NO_MEDIBLE: pasajes donde el autor oye algo distinto y no quedó fijado qué (c. 48-49, 94-99, 108 y 200-201). No se
miden. La alineación tampoco deja medir los c. 163-168.

La melodía principal de cada sección la eligió el autor (MELODIA_PRINCIPAL en src/tabroll/evaluation/melodia.py).
"""
import csv
from pathlib import Path

S = 60 / 107 / 4                                    # segundos por semicorchea
NOTAS = Path(__file__).with_name('yor_zarad_notas.csv')
GUITARS, BASSES = ('G1', 'G2', 'G3'), ('B',)
TRANSPOSE = {'G1': -12, 'G2': -12, 'G3': -12, 'B': -12}   # alturas ESCRITAS: guitarras y bajo suenan una octava abajo

# semicorcheas por compás: (primer compás, último compás, largo)
METRICA = [(1, 148, 14), (149, 152, 12), (153, 153, 8), (154, 157, 12), (158, 158, 8), (159, 162, 12), (163, 163, 8),
           (164, 167, 12), (168, 168, 8)] + [x for b in range(169, 197, 4) for x in ((b, b + 2, 16), (b + 3, b + 3, 8))] \
          + [(197, 199, 16), (200, 201, 8)]

# (nombre, primer compás, último compás, medible). Las letras son las de la partitura.
SECTIONS = [
    ('A: intro, armónicos de la guitarra 2 (c. 1-4)', 1, 4, True),
    ('B: riff de la guitarra 1 sola (c. 5-20)', 5, 20, True),
    ('C: riff con el bajo (c. 21-27)', 21, 27, True),
    ('C: entra la guitarra 2 (c. 28-44)', 28, 44, True),
    ('D: guitarra 2 sobre el riff (c. 45-76)', 45, 76, True),
    ('E: otro riff de la guitarra 1 (c. 77-92)', 77, 92, True),
    ('E: entra la guitarra 2 (c. 93-108)', 93, 108, True),
    ('F (c. 109-132)', 109, 132, True),
    ('G: figura rápida de la guitarra 2 (c. 133-148)', 133, 148, True),
    ('H: 6/8 y 2/4 (c. 149-158)', 149, 158, True),
    ('H: entra la guitarra 3 (c. 159-168)', 159, 168, True),
    ('I: outro en 4/4 (c. 169-201)', 169, 201, True),
]


# compases que no se miden (primero, último): ver la cabecera
NO_MEDIBLE = [(48, 49), (94, 99), (108, 108), (200, 201)]


def largos():
    out = {}
    for a, b, n in METRICA:
        out.update({c: n for c in range(a, b + 1)})
    return [out[c] for c in range(1, max(out) + 1)]


def inicio(compas):
    """Inicio del compás (1 = primero) en semicorcheas."""
    return sum(largos()[:compas - 1])


def notes(parts):
    """(inicio s, duración s, altura escrita, parte) de las partes pedidas."""
    out = []
    with open(NOTAS, encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if r['parte'] in parts:
                out.append((float(r['semicorchea']) * S, float(r['duracion']) * S, float(r['altura']), r['parte']))
    return sorted(out)


def timeline():
    """(inicio s, fin s, nombre, medible) por sección; los compases de NO_MEDIBLE salen como tramos aparte, no medibles."""
    out = []
    for nombre, a, b, medible in SECTIONS:
        cortes = sorted((max(a, x), min(b, y)) for x, y in NO_MEDIBLE if x <= b and y >= a)
        c = a
        for x, y in cortes:
            if x > c:
                out.append((inicio(c) * S, inicio(x) * S, nombre, medible))
            out.append((inicio(x) * S, inicio(y + 1) * S, nombre, False))
            c = y + 1
        if c <= b:
            out.append((inicio(c) * S, inicio(b + 1) * S, nombre, medible))
    return out
