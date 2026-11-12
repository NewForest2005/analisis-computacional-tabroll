"""**`melodic_columns`**: Notas columna de cada compás. Cada nota de la voz aguda recibe un peso con cuatro reglas de preferencia, a la manera de la reducción de Lerdahl y Jackendoff: dónde cae el ataque (primer pulso 1, mitad del compás 0.85, otro pulso 0.7, corchea 0.45, el resto 0.3), si es nota del acorde del compás (1; a un cuarto de tono, 0.7; fuera, 0.2), cuánto dura (hasta un pulso) y si es un punto alto o bajo del contorno (`PESOS` las combina). En cada pulso queda la nota de más peso con el bajo que suena en ese momento: la columna del pulso (`columnas`, «1 D3/D2 · 2 E3/E2 …», y `columnas_pulso`, con la altura MIDI de la nota aguda y del bajo para dibujarla). La de más peso del compás es la columna principal: nota aguda, bajo, intervalo entre los dos, qué es la nota en el acorde y en qué pulso cae. El arco dice la forma de la voz aguda en el compás: arco (sube y baja), valle, asciende, desciende o plano, con su cumbre y su ámbito en semitonos. Las notas de menos de `min_beats` pulsos no cuentan si hay otras.
"""

import numpy as np

from tabroll.cells.chord24 import CHORDS24
from tabroll.cells.harmony_by_bar import DEG24_NAMES, PC24_NAMES

PESOS = dict(metrica=0.3, acorde=0.35, duracion=0.2, contorno=0.15)   # reglas de preferencia: dónde cae el ataque, si es
PAPELES = {0: 'fundamental', 4: 'segunda (sus2)', 6: 'tercera', 7: 'tercera', 8: 'tercera', 10: 'cuarta (sus4)',
           12: 'quinta', 14: 'quinta', 16: 'quinta'}                    # del acorde, cuánto dura y si es un punto alto o bajo


def melodic_columns(armonia, raw_bass, raw_high, lens, min_beats=0.2):
    pc = lambda m: int(round(2 * m)) % 24                              # altura MIDI (con cuartos de tono) → clase de 24
    nombre = lambda m: PC24_NAMES[pc(m)] + str(int(round(2 * m)) // 24 - 1)
    high, bass = sorted(map(tuple, raw_high)), sorted(map(tuple, raw_bass))
    b_ini = np.array([n[0] for n in bass]) if bass else np.zeros(0)

    def bajo_en(t, beat):                                              # la nota del bajo que suena en t
        k = int(np.searchsorted(b_ini, t + 0.05, side='right')) - 1
        if k >= 0 and bass[k][1] > t:
            return bass[k][2]
        k += 1                                                         # o la que entra poco después
        return bass[k][2] if k < len(bass) and bass[k][0] - t < 0.5 * beat else None

    out = []
    for row, nb in zip(armonia, lens):
        row = dict(row)
        t0, t1 = row['inicio_s'], row['fin_s']
        nb = max(int(round(nb)), 1)
        beat = (t1 - t0) / nb
        en_compas = [n for n in high if t0 - 0.03 <= n[0] < t1 - 0.03]
        notas = [n for n in en_compas if n[1] - n[0] >= min_beats * beat] or en_compas
        if not notas:
            row.update(columna=None, columna_aguda=None, columna_bajo=None, columna_intervalo=None, columna_papel=None,
                       columna_en_acorde=None, columna_pulso=None, columna_peso=None, columnas=None, columnas_pulso=[],
                       arco=None, cumbre=None, ambito_st=None)
            out.append(row)
            continue

        root, cal = row.get('fundamental_pc24'), row.get('calidad')
        iv = CHORDS24.get(cal, ()) if root is not None else ()
        alturas = [n[2] for n in notas]
        cols = {}
        for i, (a, b, p) in enumerate(notas):
            pos = (a - t0) / beat
            j = min(max(int(np.floor(pos + 0.15)), 0), nb - 1)          # el pulso al que pertenece el ataque
            if abs(pos - round(pos)) <= 0.15:
                metrica = 1.0 if j == 0 else 0.85 if nb % 2 == 0 and j == nb // 2 else 0.7
            else:
                metrica = 0.45 if abs(2 * pos - round(2 * pos)) <= 0.15 else 0.3
            if iv:                                                     # qué es la nota en el acorde del compás
                rel = (pc(p) - root) % 24
                x = min(iv, key=lambda x: min((rel - x) % 24, (x - rel) % 24))
                dist = min((rel - x) % 24, (x - rel) % 24)
                acorde = 1.0 if dist == 0 else 0.7 if dist == 1 else 0.2
                papel = (PAPELES[x] + (' (a 1/4 de tono)' if dist else '')) if dist <= 1 else f'fuera del acorde ({DEG24_NAMES[rel]})'
            else:
                dist, acorde, papel = None, 0.5, None
            vecinos = alturas[max(i - 1, 0):i] + alturas[i + 1:i + 2]
            if len(alturas) == 1:
                contorno = 1.0
            elif len(vecinos) == 1:
                contorno = 0.8                                         # primera o última nota del compás
            else:
                contorno = 1.0 if p > max(vecinos) or p < min(vecinos) else 0.6
            peso = (PESOS['metrica'] * metrica + PESOS['acorde'] * acorde + PESOS['duracion'] * min(1.0, (b - a) / beat)
                    + PESOS['contorno'] * contorno)
            if j in cols and cols[j]['peso'] >= peso:
                continue
            pb = bajo_en(a, beat)
            cols[j] = dict(pulso=j + 1, t=round(a, 3), midi=round(p, 2), bajo_midi=None if pb is None else round(pb, 2),
                           aguda=nombre(p), bajo=None if pb is None else nombre(pb),
                           intervalo=None if pb is None else DEG24_NAMES[(pc(p) - pc(pb)) % 24], papel=papel,
                           en_acorde=None if dist is None else dist <= 1, peso=round(peso, 3))

        prin = max(cols.values(), key=lambda c: c['peso'])
        hi, lo = int(np.argmax(alturas)), int(np.argmin(alturas))
        ini, fin = alturas[0], alturas[-1]
        sube = alturas[hi] - max(ini, fin) if 0 < hi < len(alturas) - 1 else 0.0
        baja = min(ini, fin) - alturas[lo] if 0 < lo < len(alturas) - 1 else 0.0
        if max(sube, baja) >= 1:
            arco = 'arco' if sube >= baja else 'valle'
        else:
            arco = 'asciende' if fin - ini >= 1 else 'desciende' if ini - fin >= 1 else 'plano'
        row.update(columna=f"{prin['aguda']} sobre {prin['bajo']}" if prin['bajo'] else prin['aguda'],
                   columna_aguda=prin['aguda'], columna_bajo=prin['bajo'], columna_intervalo=prin['intervalo'],
                   columna_papel=prin['papel'], columna_en_acorde=prin['en_acorde'], columna_pulso=prin['pulso'],
                   columna_peso=prin['peso'],
                   columnas=' · '.join(f"{j + 1} {cols[j]['aguda']}/{cols[j]['bajo'] or '–'}" if j in cols else f'{j + 1} –'
                                       for j in range(nb)),
                   columnas_pulso=[cols[j] for j in sorted(cols)], arco=arco, cumbre=nombre(alturas[hi]),
                   ambito_st=round(float(max(alturas) - min(alturas)), 1))
        out.append(row)
    return out
