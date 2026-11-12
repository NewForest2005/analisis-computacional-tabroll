"""Paso M1 del análisis melódico: intervalos, giros, espectro y notas extrañas de la voz aguda.

Uso:
    python scripts/figuras_melodicas.py
    make extract
    make test

La voz aguda se corta en frases (notas separadas por menos de un pulso). En cada frase:
- intervalos entre notas seguidas, por clase (unísono, cuarto de tono, semitono, tres cuartos, tono, tercera, cuarta o
  quinta, sexta o más), con la parte microtonal (los que no son un número entero de semitonos);
- giros: la figura de cada nota con la anterior y la siguiente (paso, bordadura, vuelta por grado, salto y vuelta,
  arpegio, zigzag...), marcados con (¼) si tienen un intervalo microtonal;
- espectro: cuánto tiempo suena cada grado de 24-EDO sobre el centro;
- notas extrañas: las que no son del acorde del compás, por tipo (nota de paso, bordadura, apoyatura, escapada, retardo,
  anticipación, inflexión de ¼ de tono, libre).
Cambios en el cuaderno, antes del tabroll24: celda nueva `melodic_figures` y la celda que la aplica e imprime el resumen.
Se puede correr más de una vez: lo que ya está aplicado no se toca.
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
H2_HEADER = "## Tabroll con la armonía en 24-EDO (paso H2)"

DOC_M1 = ("## Figuras melódicas (paso M1)\n\n"
          "Intervalos, giros, espectro y notas extrañas de la voz aguda, en cada compás y en la canción.")

DOC_FIGURES = ("**`melodic_figures`**: Figuras de la voz aguda. La corta en frases (notas separadas por menos de un pulso) "
               "y en cada una mide los intervalos entre notas seguidas (en semitonos, con cuartos de tono), los giros (la "
               "figura de cada nota con la anterior y la siguiente: repetición, paso, bordadura, vuelta por grado, salto y "
               "paso, salto y vuelta, paso y salto, arpegio, zigzag; con «(¼)» si hay un intervalo microtonal), el "
               "espectro (tiempo de cada grado de 24-EDO sobre `tonic_pc24`) y las notas extrañas al acorde del compás, "
               "por tipo: inflexión de ¼ de tono (a un cuarto de tono de una nota del acorde), retardo, anticipación, nota "
               "de paso, bordadura, vuelta, apoyatura, salto a nota extraña, escapada o libre. Las notas extrañas solo se "
               "cuentan en compases con confianza ≥ `min_conf`. Agrega a cada compás `giro_principal`, `giros_compas`, "
               "`salto_mayor` y `notas_extranas`, y devuelve el resumen de la canción, con el giro principal de cada ciclo "
               "de la voz aguda.")

DOC_RUN_M1 = ("Figuras melódicas de la canción: agrega los giros y las notas extrañas a cada compás de `armonia` y el "
              "resumen a `armonia_resumen['melodia']`.")

CODE_FIGURES = '''from collections import Counter

import numpy as np

from tabroll.cells.chord24 import CHORDS24
from tabroll.cells.harmony_by_bar import DEG24_NAMES, PC24_NAMES

CLASES = ((0.25, 'unísono'), (0.75, 'cuarto de tono'), (1.25, 'semitono'), (1.75, 'tres cuartos de tono'), (2.25, 'tono'),
          (4.75, 'tercera'), (7.25, 'cuarta o quinta'), (99.0, 'sexta o más'))     # límites en semitonos


def melodic_figures(armonia, raw_high, lens, tonic_pc24, min_conf=0.5):
    clase = lambda x: next(nombre for lim, nombre in CLASES if abs(x) < lim)
    paso = lambda x: x is not None and 0.25 <= abs(x) <= 2.25
    salto = lambda x: x is not None and abs(x) > 2.25
    igual = lambda x: x is not None and abs(x) < 0.25
    micro = lambda *xs: any(x is not None and round(2 * x) % 2 for x in xs)
    pc = lambda m: int(round(2 * m)) % 24
    nombre = lambda m: PC24_NAMES[pc(m)] + str(int(round(2 * m)) // 24 - 1)

    def giro(a, b):                                                    # figura de tres notas: entra con a, sale con b
        if igual(a) and igual(b):
            g = 'repetición'
        elif igual(a) or igual(b):
            g = 'repite y sigue'
        elif paso(a) and paso(b):
            g = 'paso' if np.sign(a) == np.sign(b) else 'bordadura' if abs(a + b) < 0.25 else 'vuelta por grado'
        elif salto(a) and paso(b):
            g = 'salto y paso' if np.sign(a) == np.sign(b) else 'salto y vuelta'
        elif paso(a):
            g = 'paso y salto'
        else:
            g = 'arpegio' if np.sign(a) == np.sign(b) else 'zigzag'
        return g + (' (¼)' if micro(a, b) else '')

    spans = [(r['inicio_s'], r['fin_s'], max(int(round(L)), 1)) for r, L in zip(armonia, lens)]
    inicios = np.array([s[0] for s in spans])

    def compas(t):
        k = int(np.searchsorted(inicios, t + 0.03, side='right')) - 1
        return k if 0 <= k < len(spans) and t < spans[k][1] - 0.03 else None

    frases, actual = [], []                                            # frases: notas separadas por menos de un pulso
    for n in sorted(map(tuple, raw_high)):
        if actual:
            k = compas(actual[-1][0])
            beat = (spans[k][1] - spans[k][0]) / spans[k][2] if k is not None else 0.5
            if n[0] - actual[-1][1] > beat:
                frases.append(actual)
                actual = []
        actual.append(n)
    if actual:
        frases.append(actual)

    notas = []                                                          # (nota, compás, intervalo de entrada, de salida, compás de la anterior, de la siguiente)
    for f in frases:
        for j, n in enumerate(f):
            notas.append((n, compas(n[0]), n[2] - f[j - 1][2] if j else None, f[j + 1][2] - n[2] if j + 1 < len(f) else None,
                          compas(f[j - 1][0]) if j else None, compas(f[j + 1][0]) if j + 1 < len(f) else None))

    por_compas = [dict(giros=Counter(), extranas=[], saltos=[]) for _ in spans]
    intervalos, giros, extranas, espectro = Counter(), Counter(), Counter(), Counter()
    sube = baja = n_conf = n_micro = 0
    for (a, b, p), k, i_in, i_out, k_prev, k_next in notas:
        espectro[DEG24_NAMES[(pc(p) - tonic_pc24) % 24]] += b - a
        if i_out is not None:
            intervalos[clase(i_out)] += 1
            sube, baja = sube + (i_out >= 0.25), baja + (i_out <= -0.25)
            n_micro += micro(i_out)
        if k is None:
            continue
        if i_in is not None and i_out is not None:
            g = giro(i_in, i_out)
            giros[g] += 1
            por_compas[k]['giros'][g] += 1
        if salto(i_out):
            por_compas[k]['saltos'].append(abs(i_out))
        row = armonia[k]
        root, cal = row.get('fundamental_pc24'), row.get('calidad')
        if root is None or cal not in CHORDS24 or (row.get('confianza') or 0) < min_conf:
            continue
        n_conf += 1
        rel = (pc(p) - root) % 24
        dist = min(min((rel - x) % 24, (x - rel) % 24) for x in CHORDS24[cal])
        if dist == 0:
            continue
        t0, t1, nb = spans[k]
        pos = (a - t0) / ((t1 - t0) / nb)
        en_pulso = abs(pos - round(pos)) <= 0.15
        if dist == 1:
            tipo = 'inflexión de ¼ de tono'                                # nota del acorde, desplazada un cuarto de tono
        elif igual(i_in) and k_prev is not None and k_prev < k and en_pulso:
            tipo = 'retardo'
        elif igual(i_out) and k_next is not None and k_next > k:
            tipo = 'anticipación'
        elif paso(i_in) and paso(i_out):
            tipo = 'nota de paso' if np.sign(i_in) == np.sign(i_out) else 'bordadura' if abs(i_in + i_out) < 0.25 else 'vuelta'
        elif salto(i_in) and paso(i_out):
            tipo = 'apoyatura' if en_pulso else 'salto a nota extraña'
        elif paso(i_in) and salto(i_out):
            tipo = 'escapada'
        else:
            tipo = 'libre'
        extranas[tipo] += 1
        por_compas[k]['extranas'].append(f'{nombre(p)} {tipo}')

    out = []
    for row, pk in zip(armonia, por_compas):
        g = pk['giros'].most_common(1)
        out.append(dict(row, giro_principal=g[0][0] if g else None, giros_compas=dict(pk['giros']),
                        salto_mayor=max(pk['saltos']) if pk['saltos'] else None,
                        notas_extranas='; '.join(pk['extranas']) or None))
    pct = lambda c: {k: round(100.0 * v / (sum(c.values()) or 1), 1) for k, v in c.most_common()}
    n_int = sum(intervalos.values()) or 1
    conj = sum(v for k, v in intervalos.items() if k in ('cuarto de tono', 'semitono', 'tres cuartos de tono', 'tono'))
    ciclos = {}
    for c in sorted({r.get('ciclo_aguda') for r in out if r.get('ciclo_aguda')}):
        cg = Counter()
        for r in out:
            if r.get('ciclo_aguda') == c:
                cg.update(r['giros_compas'])
        if cg:
            ciclos[c] = dict(giro=cg.most_common(1)[0][0], parte=round(100.0 * cg.most_common(1)[0][1] / sum(cg.values()), 1))
    tot_esp = sum(espectro.values()) or 1.0
    return out, dict(notas=len(notas), intervalos=pct(intervalos), grado_conjunto=round(100.0 * conj / n_int, 1),
                     saltos=round(100.0 * sum(v for k, v in intervalos.items() if k in ('tercera', 'cuarta o quinta', 'sexta o más')) / n_int, 1),
                     repetidas=round(100.0 * intervalos['unísono'] / n_int, 1),
                     microtonales=round(100.0 * n_micro / n_int, 1), sube=round(100.0 * sube / n_int, 1),
                     baja=round(100.0 * baja / n_int, 1), giros=pct(giros),
                     espectro={k: round(100.0 * v / tot_esp, 1) for k, v in espectro.most_common()},
                     espectro_microtonal=round(100.0 * sum(v for k, v in espectro.items() if '+' in k) / tot_esp, 1),
                     notas_en_confiables=n_conf, extranas=round(100.0 * sum(extranas.values()) / (n_conf or 1), 1),
                     tipos_extranas=pct(extranas), por_ciclo=ciclos)'''

CODE_RUN_M1 = '''armonia, armonia_resumen['melodia'] = melodic_figures(armonia, raw_high, lens, tonic_pc24)
ml = armonia_resumen['melodia']
top = lambda d, n=6: ', '.join(f'{k} {v:.0f}%' for k, v in list(d.items())[:n])
print(f"Melodía ({ml['notas']} notas de la voz aguda): grado conjunto {ml['grado_conjunto']:.0f}%, saltos {ml['saltos']:.0f}%, "
      f"notas repetidas {ml['repetidas']:.0f}%, intervalos microtonales {ml['microtonales']:.0f}% | sube {ml['sube']:.0f}%, baja {ml['baja']:.0f}%")
print('          intervalos: ' + top(ml['intervalos'], 8))
print('          giros: ' + top(ml['giros']))
print(f"          espectro: {top(ml['espectro'], 8)} | en grados de cuarto de tono {ml['espectro_microtonal']:.0f}%")
print(f"          notas extrañas: {ml['extranas']:.0f}% de {ml['notas_en_confiables']} notas en compases confiables | " + top(ml['tipos_extranas']))
if ml['por_ciclo']:
    print('          giro principal por ciclo de la voz aguda: ' + '; '.join(f"{c}: {d['giro']} {d['parte']:.0f}%" for c, d in ml['por_ciclo'].items()))'''


def _cell(kind: str, text: str) -> dict:
    cell = {"id": uuid.uuid4().hex[:12], "cell_type": kind, "metadata": {}, "source": text.splitlines(keepends=True)}
    if kind == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]
    src = lambda c: "".join(c["source"])
    put = lambda c, text: c.__setitem__("source", text.splitlines(keepends=True))
    done = []
    pares = ((DOC_FIGURES, CODE_FIGURES, "def melodic_figures("), (DOC_RUN_M1, CODE_RUN_M1, "= melodic_figures(armonia"))
    found = [[i for i, c in enumerate(cells) if c["cell_type"] == "code" and mark in src(c)] for _, _, mark in pares]
    if all(len(f) == 1 for f in found):
        for (doc, code, mark), (i,) in zip(pares, found):
            if src(cells[i]) != code or src(cells[i - 1]) != doc:
                put(cells[i - 1], doc)
                put(cells[i], code)
                done.append("melodic_figures" if mark.startswith("def") else "celda de figuras")
    elif not any(found):
        head = [i for i, c in enumerate(cells) if c["cell_type"] == "markdown" and src(c).startswith(H2_HEADER)]
        cols = [c for c in cells if c["cell_type"] == "code" and "armonia = melodic_columns(armonia" in src(c)]
        if len(head) != 1 or len(cols) != 1:
            print("No encontré la celda de las notas columna o el encabezado del tabroll24. Corre antes scripts/notas_columna.py.")
            return 1
        new = [_cell("markdown", DOC_M1)]
        for doc, code, _ in pares:
            new += [_cell("markdown", doc), _cell("code", code)]
        cells[head[0]:head[0]] = new
        done.append("celdas nuevas melodic_figures y la de figuras, antes del tabroll24")
    else:
        print("Las celdas de las figuras melódicas están incompletas; restaura el cuaderno desde git y vuelve a correr.")
        return 1
    if not done:
        print("El cuaderno ya tenía las figuras melódicas.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
