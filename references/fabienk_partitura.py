"""Fabienk: «attempted transcription» de Andrew Kahler (11 págs.) desplegada en semicorcheas, con las correcciones
que se comprobaron contra la grabación oficial. Solo sirve para medir el análisis; el cuaderno no la usa.

Alturas ESCRITAS en MIDI con cuartos de tono; guitarras (clave de sol 8vb) y bajo suenan una octava abajo (TRANSPOSE).
Alteraciones (Stein-Zimmermann): 'q' medio sostenido, 's' sostenido, 't' tres cuartos sostenido, 'n' natural.
Corchea = 256 (la partitura dice 260; la hoja del bajo del sencillo, 256). Las secciones con la guitarra 2 y el bajo en
loop de 7/8 siguen ese loop aunque la guitarra 1 vaya en 2/4.

Correcciones de oído (autor, 9-nov-2026, verificadas con clips de la guitarra real frente a la partitura sintetizada):
- Melodía «Fabien»: tresillo Mi Re Si en el c. 1; en el c. 5, Si (corchea), tresillo Si La Si, Do# y Si.
- Segunda voz V2: Do#¼ (no Do#) en el c. 3 y las cuatro últimas notas una octava arriba.
- Reparto de vueltas de c. 89-110 según la grabación: la melodía «Fabien» entra cinco vueltas después de lo que dice
  la partitura (4:29); antes suena V2, que el looper mantiene hasta el final.
- Ya confirmados sin cambios: «Guitarra 1 sola» (c. 2-6) y «Guitarra 1 dobla al bajo».

La introducción de la grabación de estudio (bajo desde 0:12, guitarra callada de 0:16 a 0:25) no sigue el reparto de
vueltas de la transcripción; esos tramos quedan fuera porque la alineación no es compatible con un tempo constante.
No medible: el acorde de los c. 59 y 74.
"""
NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
ACC = {'q': .5, 's': 1., 't': 1.5, 'd': -.5, 'b': -1., 'n': 0.}
SIX = 60 / 256 / 2                      # segundos por semicorchea


def P(s):
    return 12 * (int(s[-1]) + 1) + NAMES[s[0]] + (ACC[s[1]] if len(s) == 3 else 0.)


def pat(*notes):
    """(inicio, duración, altura) en semicorcheas."""
    return [(o, d, P(p)) for o, d, p in notes]


def up(p, k):
    return [(o, d, x + k) for o, d, x in p]


def seq(*parts):
    """Junta patrones (largo, notas) uno tras otro."""
    out, t = [], 0
    for n, notes in parts:
        out += [(o + t, d, p) for o, d, p in notes]; t += n
    return t, out


def loop(n, notes, total, start=0):
    """Repite un patrón de n semicorcheas hasta cubrir `total`, empezando en la fase `start`."""
    out = []
    for k in range(-1, total // n + 2):
        for o, d, p in notes:
            t = k * n + o - start
            if 0 <= t < total:
                out.append((t, min(d, total - t), p))
    return sorted(out)


def delay(total, notes, n_loop_total, k=4):
    """El patrón corrido k semicorcheas: empieza con su propia cola."""
    return sorted([((o + k) % n_loop_total, d, p) for o, d, p in notes if o + k < n_loop_total + k])


# ------------------------------------------------------------------ guitarra 1 (7/8 = 14 semicorcheas)
X = pat((0, 2, 'B5'), (4, 2, 'Bq5'), (6, 2, 'C6'), (8, 2, 'Cq6'), (11, 1, 'Cs6'))
Y = pat((0, 2, 'E5'), (6, 2, 'Cs5'), (8, 2, 'Ct5'), (11, 1, 'D5'))
Z = pat((0, 1, 'E5'), (1, 1, 'D5'), (2, 1, 'Dq5'), (3, 1, 'Ds5'), (4, 1, 'Dt5'), (5, 2, 'E5'), (7, 1, 'E5'), (9, 1, 'D5'), (11, 1, 'D5'))
XYXZ = seq((14, X), (14, Y), (14, X), (14, Z))[1]
# ------------------------------------------------------------------ guitarra 2
W = pat((0, 1, 'E5'), (1, 1, 'D5'), (2, 1, 'Dq5'), (3, 1, 'Ds5'), (4, 1, 'Dt5'), (5, 2, 'E5'), (7, 1, 'E5'), (9, 1, 'D5'), (11, 1, 'E5'), (13, 1, 'E5'))
# ------------------------------------------------------------------ bajo
Xb = pat((0, 2, 'B2'), (4, 2, 'Bq2'), (6, 2, 'C3'), (8, 2, 'Cq3'), (11, 1, 'Cs3'))
Yb = pat((0, 2, 'E2'), (6, 2, 'Cs3'), (8, 2, 'Ct3'), (11, 1, 'D3'))
Zb = pat((0, 1, 'E3'), (1, 1, 'D3'), (2, 1, 'Dq3'), (3, 1, 'Ds3'), (4, 1, 'Dt3'), (5, 2, 'E3'), (7, 1, 'E3'), (9, 1, 'D3'), (11, 1, 'E3'))
XYXZb = seq((14, Xb), (14, Yb), (14, Xb), (14, Zb))[1]
FILL = pat((0, 1, 'E3'), (1, 1, 'D3'), (2, 1, 'B2'), (3, 1, 'A2'), (4, 1, 'E2'), (5, 1, 'E3'), (7, 1, 'E2'), (9, 1, 'E3'), (11, 3, 'E2'))
# loop del bajo desde el c. 16 (sin correr): el «E1 E2» queda al final
Zb2 = pat((0, 1, 'E3'), (1, 1, 'D3'), (2, 1, 'Dq3'), (3, 1, 'Ds3'), (4, 1, 'Dt3'), (5, 2, 'E3'), (7, 1, 'E3'), (9, 1, 'D3'), (10, 1, 'E2'), (11, 1, 'E3'))
# ------------------------------------------------------------------ 2/4 (8 semicorcheas por compás)
# melodía «Fabien» corregida de oído por el autor (9-nov): tresillo Mi Re Si en el c. 1; en el c. 5, Si (corchea),
# tresillo Si La Si, Do# y Si (no La)
BAR5 = pat((0, 2, 'B4'), (2, .67, 'B4'), (2.67, .67, 'A4'), (3.33, .67, 'B4'), (4, 2, 'Cs5'), (6, 2, 'B4'))
M = seq((8, pat((0, 4, 'E5'), (4, 2, 'E5'), (6, .67, 'E5'), (6.67, .67, 'D5'), (7.33, .67, 'B4'))),
        (8, pat((0, 2, 'D5'), (2, 2, 'Ct5'), (4, 2, 'D5'), (6, 2, 'Ct5'))),
        (8, pat((0, 2, 'Cs5'), (2, 2, 'B4'), (4, 2, 'A4'), (6, 2, 'B4'))),
        (8, pat((0, 2, 'Cs5'), (2, 2, 'A4'), (4, 4, 'B4'))),
        (8, BAR5),
        (8, pat((0, 2, 'D5'), (2, 1, 'D5'), (3, 1, 'Cs5'), (4, 2, 'B4'), (6, 2, 'A4'))),
        (8, pat((0, 2, 'B4'), (2, 2, 'Cs5'), (4, 2, 'A4'), (6, 2, 'B4'))))[1]
L = seq((8, pat((0, 2, 'E2'), (2, 2, 'E3'), (4, 2, 'E2'), (6, 2, 'G3'))),
        (8, pat((0, 2, 'G3'), (2, 2, 'Aq2'), (4, 2, 'As2'), (6, 2, 'Aq2'))),
        (8, pat((0, 2, 'A2'), (2, 2, 'D3'), (4, 2, 'G3'), (6, 2, 'D4'))),
        (8, pat((0, 2, 'D3'), (2, 2, 'Fs3'), (4, 2, 'G3'), (6, 2, 'D3'))),
        (8, pat((0, 2, 'G2'), (2, 2, 'G3'), (4, 4, 'G2'))),
        (8, pat((0, 2, 'D3'), (2, 1, 'D4'), (3, 1, 'D4'), (4, 2, 'G3'), (6, 2, 'D3'))),
        (8, pat((0, 2, 'G2'), (2, 2, 'G3'), (4, 2, 'A2'), (6, 2, 'A3'))))[1]
L_G = up(L, 12)                              # la línea del bajo en guitarra (escrita una octava arriba)
V2 = seq((8, up(L, 12)[:4]), (8, [(o - 8, d, p) for o, d, p in up(L, 12) if 8 <= o < 16]),
         (8, pat((0, 2, 'A3'), (2, 2, 'D4'), (4, 2, 'Ct5'), (6, 2, 'D5'))),      # Do#¼ (no Do#), corregido de oído por el autor
         (8, pat((0, 2, 'Cs5'), (2, 2, 'B4'), (4, 2, 'G4'), (6, 2, 'B4'))),
         (8, pat((0, 2, 'G3'), (2, 2, 'G4'), (4, 4, 'G3'))),
         (8, pat((0, 2, 'D4'), (2, 1, 'D5'), (3, 1, 'D5'), (4, 2, 'G4'), (6, 2, 'B4'))),
         (8, pat((0, 2, 'D5'), (2, 2, 'D5'), (4, 2, 'Cs5'), (6, 2, 'Cs5'))))[1]   # una octava arriba (corregido de oído por el autor)

SECTIONS = []                          # (nombre, semicorcheas, {parte: notas}, medible)


def sec(name, n, parts, known=True):
    SECTIONS.append((name, n, parts, known))


def rep(k, n, notes):
    return [(o + i * n, d, p) for i in range(k) for o, d, p in notes]


def shifted(n_total, notes, period, k=4):
    """Un loop de `period` corrido k semicorcheas hacia adelante, n_total semicorcheas de largo."""
    return loop(period, notes, n_total, start=period - k)


sec('Anacrusa', 4, {'G1': pat((1, 1, 'D5'))})
sec('Guitarra 1 sola (c. 2-6, 4 vueltas)', 224, {'G1': rep(4, 56, XYXZ), 'B': [(210 + o, d, p) for o, d, p in FILL]})
sec('Guitarra 1 con el bajo (c. 7-10, 2 vueltas)', 112, {'G1': rep(2, 56, XYXZ), 'B': rep(2, 56, XYXZb)})
s3 = {'G1': rep(3, 56, XYXZ) + [(168 + o, d, p) for o, d, p in XYXZ if o < 42],
      'G2': rep(15, 14, W)[:0] + [n for n in loop(14, W, 210)],
      'B': rep(3, 56, XYXZb) + [(168 + o, d, p) for o, d, p in XYXZb if o < 42] + [(210 + o, d, p) for o, d, p in FILL if o < 10]}
sec('Entra la guitarra 2 (c. 11-15, 4 vueltas)', 220, s3)
U = rep(2, 56, XYXZ)
sec('Todo corrido dos corcheas (c. 16-20)', 116, {'G1': shifted(116, XYXZ, 56), 'G2': shifted(116, W, 14), 'B': shifted(116, Zb2, 14)})
sec('Vuelta al riff (c. 21-25, 4 vueltas)', 220, s3)
# desde el c. 26 la guitarra 2 y el bajo no paran su loop corrido hasta el c. 58
LOOP_SECS = [('Corrido otra vez (c. 26-29, 2 vueltas)', 112, 'XYXZ'), ('Guitarra 1 dobla al bajo (c. 30-34)', 112, 'V'),
             ('Melodía «Fabien» (c. 35-41, 4 vueltas)', 224, 'M'), ('Guitarra 1 dobla al bajo (c. 42-46)', 112, 'V'),
             ('Melodía «Fabien» otra vez (c. 47-53, 4 vueltas)', 224, 'M'), ('Guitarra 1 dobla al bajo (c. 54-58)', 112, 'V')]
for name, n, g1 in LOOP_SECS:
    parts = {'G2': shifted(n, W, 14), 'B': shifted(n, Zb2, 14)}
    parts['G1'] = {'XYXZ': shifted(n, XYXZ, 56), 'V': up(shifted(n, Zb2, 14), 12), 'M': rep(4, 56, M)}[g1]
    sec(name, n, parts)
sec('Acorde (c. 59)', 16, {}, known=False)
sec('Bajo solo (c. 60-66, 2 vueltas)', 112, {'B': rep(2, 56, L)})
sec('«Sébastien»: bajo solo (c. 67-74, 4 vueltas)', 224, {'B': rep(4, 56, L)})
sec('La guitarra 2 toca la línea del bajo (c. 75-81, 2 vueltas)', 112, {'G2': rep(2, 56, L_G), 'B': rep(2, 56, L)})
sec('Las dos guitarras (c. 82-88, 2 vueltas)', 112, {'G1': rep(2, 56, V2), 'G2': rep(2, 56, L_G), 'B': rep(2, 56, L)})
# Reparto de vueltas según la grabación (escucha del autor y alturas medidas en la pista de guitarra, 9-nov):
# la melodía «Fabien» no entra en el c. 89 sino cinco vueltas después (4:29); antes suena la segunda voz V2,
# que el looper mantiene hasta el final. La duración total (12 vueltas) no cambia.
sec('Segunda voz sobre la línea del bajo (c. 89-96, 5 vueltas, según la grabación)', 280,
    {'G1': rep(5, 56, V2), 'G2': rep(5, 56, L_G), 'B': rep(5, 56, L)})
sec('Melodía «Fabien» con la segunda voz en el loop (c. 97-110, 7 vueltas, según la grabación)', 392,
    {'G1': rep(7, 56, M), 'G2': rep(7, 56, L_G) + rep(7, 56, V2), 'B': rep(7, 56, L)})

GUITARS, BASSES = ('G1', 'G2'), ('B',)
TRANSPOSE = {'G1': -12, 'G2': -12, 'B': -12}


def timeline():
    out, t = [], 0
    for name, n, P_, known in SECTIONS:
        out.append((t, n, known, name)); t += n
    return out


def notes(parts):
    out, t = [], 0
    for k, (name, n, P_, known) in enumerate(SECTIONS):
        for part in parts:
            out += [(k, t + o, d, p, part) for o, d, p in P_.get(part, []) if o < n]
        t += n
    return sorted(out, key=lambda x: (x[1], x[3]))
