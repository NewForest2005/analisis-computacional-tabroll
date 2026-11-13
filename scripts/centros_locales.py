"""Paso M3 del análisis melódico y armónico: centro por tramo, para ver si la canción modula.

Uso:
    python scripts/centros_locales.py
    make extract
    make test

La canción se corta en tramos: los ciclos de la voz principal (el bajo, si tiene ciclos) y los huecos entre ellos. En
cada tramo se mide el centro con la misma regla que el de la canción (`center24_by_layer`) y su modo (`mode24`).
"""
from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
H2_HEADER = "## Tabroll con la armonía en 24-EDO (paso H2)"

DOC_M3 = ("## Centros por tramo (paso M3)\n\n"
          "El centro y el modo de cada tramo de la canción, para ver si modula y cómo: por quinta, por tercera, dentro del "
          "mismo eje de Lendvai o por un cuarto de tono.")

DOC_CENTERS = ("**`local_centers`**: Centro de cada tramo. Los tramos son los ciclos de la voz principal (el bajo si tiene "
               "ciclos, si no la voz aguda) y los huecos entre ellos, con al menos `min_compases` compases. En cada tramo, "
               "el centro se mide con `center24_by_layer` sobre las notas y los ciclos del tramo, y el modo con `mode24` "
               "sobre sus compases. Cada centro se compara con el de la canción (`tonic_pc24`) y con el del tramo "
               "anterior. Un tramo con margen menor que `margen_min` queda como dudoso («?»). Agrega a cada compás `tramo` y "
               "`centro_local`, y devuelve los tramos y los cambios de centro.")

DOC_RUN_M3 = ("Centros por tramo de la canción: agrega el tramo y su centro a cada compás de `armonia` y el resumen a "
              "`armonia_resumen['centros_locales']`.")

CODE_CENTERS = '''from collections import Counter
from types import SimpleNamespace

from tabroll.cells.center24_by_layer import center24_by_layer
from tabroll.cells.harmony_by_bar import DEG24_NAMES, PC24_NAMES
from tabroll.cells.mode24 import mode24

SALTOS = {0: 'mismo centro', 5: 'quinta abajo', 7: 'quinta arriba', 3: 'tercera menor arriba', 9: 'tercera menor abajo',
          4: 'tercera mayor arriba', 8: 'tercera mayor abajo', 2: 'segunda arriba', 10: 'segunda abajo', 1: 'semitono arriba',
          11: 'semitono abajo', 6: 'tritono'}


def local_centers(armonia, raw_bass, raw_high, cycles, tonic_pc24, min_compases=4, margen_min=0.1):
    mmss = lambda t: f'{int(t // 60)}:{int(t % 60):02d}'
    get = lambda c, k: c[k] if isinstance(c, dict) else getattr(c, k)
    principal = 'Voz grave' if cycles.get('Voz grave') else 'Voz aguda'
    segs = sorted((float(get(c, 'start')), float(get(c, 'end')), float(get(c, 'period')), get(c, 'label') or '?')
                  for c in cycles.get(principal, []))
    fin_cancion = armonia[-1]['fin_s'] if armonia else 0.0
    tramos, t = [], armonia[0]['inicio_s'] if armonia else 0.0
    for a, b, P, l in segs:
        if a - t > 0:
            tramos.append((t, a, None, '—'))
        tramos.append((a, b, P, l))
        t = max(t, b)
    if fin_cancion - t > 0:
        tramos.append((t, fin_cancion, None, '—'))

    def relacion(q):
        if q % 2:
            return f'microtonal ({DEG24_NAMES[q]})'
        return SALTOS[q // 2] + ('' if q == 0 or (q // 2) % 3 else ', mismo eje de Lendvai')

    out = [dict(r, tramo=None, centro_local=None) for r in armonia]
    lista, previo = [], None
    for a, b, P, l in tramos:
        idx = [k for k, r in enumerate(armonia) if a - 0.05 <= (r['inicio_s'] + r['fin_s']) / 2 < b + 0.05]
        if len(idx) < min_compases:
            continue
        dentro = lambda notas: [n for n in notas if a - 0.05 <= n[0] < b + 0.05]
        tr_cycles = {principal: [SimpleNamespace(start=a, end=b, period=P)] if P else []}
        otra = 'Voz aguda' if principal == 'Voz grave' else 'Voz grave'
        tr_cycles[otra] = [SimpleNamespace(start=max(a, float(get(c, 'start'))), end=min(b, float(get(c, 'end'))),
                                              period=float(get(c, 'period'))) for c in cycles.get(otra, [])
                           if float(get(c, 'start')) < b and float(get(c, 'end')) > a]
        c24 = center24_by_layer(dentro(raw_bass), dentro(raw_high), tr_cycles)
        centro = c24['centro_pc24']
        q = (centro - tonic_pc24) % 24
        seguro = c24['margen'] >= margen_min
        tr = dict(inicio=mmss(a), fin=mmss(b), inicio_s=round(a, 2), fin_s=round(b, 2), ciclo=l, compases=len(idx),
                  centro=PC24_NAMES[centro], grado=DEG24_NAMES[q], margen=c24['margen'], seguro=seguro,
                  modo=mode24([armonia[k] for k in idx], centro)['nombre'], respecto_del_centro=relacion(q),
                  desde_el_anterior=None if previo is None else relacion((centro - previo) % 24))
        lista.append(tr)
        previo = centro
        for k in idx:
            out[k].update(tramo=f'{tr["inicio"]} {l}', centro_local=tr['centro'] + ('' if seguro else '?'))

    seguros = [x for x in lista if x['seguro']]
    dur = lambda x: x['fin_s'] - x['inicio_s']
    total = sum(dur(x) for x in lista) or 1.0
    cambios = [x for x in lista[1:] if x['desde_el_anterior'] != 'mismo centro']
    return out, dict(voz=principal, tramos=lista,
                     centro_estable=round(100.0 * sum(dur(x) for x in lista if x['grado'] == '1') / total, 1),
                     modulaciones=len([x for x in cambios if x['seguro']]),
                     cambios_de_centro=dict(Counter(x['desde_el_anterior'] for x in cambios)),
                     centros=dict(Counter(x['centro'] for x in seguros)),
                     tramos_dudosos=len(lista) - len(seguros))'''

CODE_RUN_M3 = '''armonia, armonia_resumen['centros_locales'] = local_centers(armonia, raw_bass, raw_high, cycles, tonic_pc24)
cl = armonia_resumen['centros_locales']
print(f"Centros por tramo (ciclos de la {cl['voz'].lower()}): el centro de la canción ocupa el {cl['centro_estable']:.0f}% | "
      f"{cl['modulaciones']} cambios de centro seguros, {cl['tramos_dudosos']} tramos dudosos")
for x in cl['tramos']:
    print(f"  {x['inicio']}–{x['fin']} {x['ciclo']:2s} centro {x['centro']}{'' if x['seguro'] else '?'} ({x['grado']}: "
          f"{x['respecto_del_centro']}) | modo {x['modo']} | margen {x['margen']:.2f}" +
          (f" | desde el anterior: {x['desde_el_anterior']}" if x['desde_el_anterior'] else ''))'''


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
    pares = ((DOC_CENTERS, CODE_CENTERS, "def local_centers("), (DOC_RUN_M3, CODE_RUN_M3, "= local_centers(armonia"))
    found = [[i for i, c in enumerate(cells) if c["cell_type"] == "code" and mark in src(c)] for _, _, mark in pares]
    if all(len(f) == 1 for f in found):
        for (doc, code, mark), (i,) in zip(pares, found):
            if src(cells[i]) != code or src(cells[i - 1]) != doc:
                put(cells[i - 1], doc)
                put(cells[i], code)
                done.append("local_centers" if mark.startswith("def") else "celda de centros")
    elif not any(found):
        head = [i for i, c in enumerate(cells) if c["cell_type"] == "markdown" and src(c).startswith(H2_HEADER)]
        pats = [c for c in cells if c["cell_type"] == "code" and "= cycle_patterns(armonia" in src(c)]
        if len(head) != 1 or len(pats) != 1:
            print("No encontré la celda de patrones de ciclo o el encabezado del tabroll24. Corre antes scripts/patrones_ciclo.py.")
            return 1
        new = [_cell("markdown", DOC_M3)]
        for doc, code, _ in pares:
            new += [_cell("markdown", doc), _cell("code", code)]
        cells[head[0]:head[0]] = new
        done.append("celdas nuevas local_centers y la de centros, antes del tabroll24")
    else:
        print("Las celdas de los centros por tramo están incompletas; restaura el cuaderno desde git y vuelve a correr.")
        return 1
    if not done:
        print("El cuaderno ya tenía los centros por tramo.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
