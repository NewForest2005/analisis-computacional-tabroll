"""Armonía en 24-EDO, paso 2: centro y modo por capa, y las capas del círculo que no dependen del centro.

Cambios en el cuaderno:
1. `chord24`: los empates exactos se resuelven igual en cualquier máquina.
2. Celdas nuevas, antes de la ejecución de la armonía: `center24_by_layer`, `mode24` y `harmony_layers`.
3. La celda de ejecución de la armonía elige el centro (por defecto, la tónica de la celda de tonalidad, que coincide con
   el oído del autor en las cinco canciones) y guarda centro, modo y capas en `armonia_resumen`.

Uso, desde la raíz del repo (con el paso 1 ya aplicado):
    python scripts/agregar_armonia_paso2.py
    make extract
    make test

Se puede correr más de una vez: si un cambio ya está, lo deja como está.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"
MARKER = "**`center24_by_layer`**"

OLD_TIES = "    best = S.max(axis=1)\n"
NEW_TIES = ("    S = np.round(S, 9)                                                         # empates exactos iguales en cualquier máquina\n"
            "    best = S.max(axis=1)\n")

NEW_RUN = """CENTRO = 'cuaderno'   # 'cuaderno': la tónica de la celda de tonalidad (coincide con el oído en las 5 canciones) | 'auto': medida de centro en 24-EDO | o una nota: 'E', 'D+', ...

centro24 = center24_by_layer(raw_bass, raw_high, cycles)
tonica_cuaderno_pc24 = (2 * tonic_pc) % 24
if CENTRO == 'auto':
    tonic_pc24 = centro24['centro_pc24']
elif CENTRO == 'cuaderno':
    tonic_pc24 = tonica_cuaderno_pc24
else:
    tonic_pc24 = PC24_NAMES.index(CENTRO)

armonia = harmony_by_bar(raw_bass, raw_high, beat_times, lens, cycles, tonic_pc24)
armonia_resumen = harmony_summary(armonia, tonic_pc24)
armonia_resumen.update(
    centro=PC24_NAMES[tonic_pc24], regla_centro=CENTRO,
    centro_24edo=PC24_NAMES[centro24['centro_pc24']], margen_centro=centro24['margen'],
    centro_bajo=PC24_NAMES[centro24['centro_bajo_pc24']], centro_aguda=PC24_NAMES[centro24['centro_aguda_pc24']],
    tonica_cuaderno=PC24_NAMES[tonica_cuaderno_pc24],
    modo=mode24(armonia, tonic_pc24), capas=harmony_layers(armonia, tonic_pc24),
    ciclos={voz: [dict(start=round(float(c.start), 3), end=round(float(c.end), 3), period=round(float(c.period), 4),
                       label=getattr(c, 'label', None)) for c in cs] for voz, cs in cycles.items()})   # para medir con los mismos ciclos

capas = armonia_resumen['capas']
grados = sorted(armonia_resumen['fundamentales_por_grado'].items(), key=lambda kv: -kv[1])[:5]
print(f"Armonía: centro {armonia_resumen['centro']} (bajo {armonia_resumen['centro_bajo']}, voz aguda {armonia_resumen['centro_aguda']}, "
      f"tónica de 12 clases {armonia_resumen['tonica_cuaderno']}) | modo {armonia_resumen['modo']['nombre']}")
print(f"         {len(armonia)} compases | confiable el {armonia_resumen['tiempo_confiable']:.0f}% del tiempo | "
      "fundamentales: " + ', '.join(f'{g} {100 * v:.0f}%' for g, v in grados if v > 0))
print(f"         movimientos: " + ', '.join(f'{k} {100 * v:.0f}%' for k, v in capas['movimientos'].items()) +
      f" | cambios por compás {capas['cambios_por_compas']:.2f}")"""

OLD_DEFAULT = "CENTRO = 'auto'   # 'auto': medida de centro en 24-EDO | 'cuaderno': la tónica de 12 clases de arriba | o una nota: 'E', 'D+', ..."
NEW_DEFAULT = "CENTRO = 'cuaderno'   # 'cuaderno': la tónica de la celda de tonalidad (coincide con el oído en las 5 canciones) | 'auto': medida de centro en 24-EDO | o una nota: 'E', 'D+', ..."

NEW_CELLS = [
    ("markdown", MARKER + ": Centro en 24-EDO, medido por capa como propone Piston para la música sin dominante. "
     "En cada capa (bajo y voz aguda) se suman tres partes, con el mismo peso:\n\n"
     "- **Tiempo:** la nota que más tiempo suena.\n"
     "- **Bordes de vuelta:** la que más aparece al principio y al final de cada vuelta del ciclo.\n"
     "- **Regresos:** la que más vuelve después de alejarse.\n\n"
     "El centro de la canción combina las dos capas, con el bajo al doble de peso. `margen` dice cuánto le gana el centro "
     "a la segunda candidata, de 0 a 1."),
    ("code", """import numpy as np

def center24_by_layer(raw_bass, raw_high, cycles, w_bass=2.0):
    get = lambda c, k: c[k] if isinstance(c, dict) else getattr(c, k)

    def layer(notes, cyc):
        notes = sorted((float(n[0]), float(n[1]), float(n[2])) for n in notes)
        pcs = [int(round(p * 2)) % 24 for a, b, p in notes]
        tiempo, bordes, regresos = np.zeros(24), np.zeros(24), np.zeros(24)
        for (a, b, p), c in zip(notes, pcs):
            tiempo[c] += b - a
        T = np.array([n[0] for n in notes])
        for cy in cyc:
            s, e, P = get(cy, 'start'), get(cy, 'end'), get(cy, 'period')
            k = s
            while P > 0 and k + P <= e + 0.05:                                  # una vuelta cada periodo
                i0, i1 = np.searchsorted(T, k - 0.05), np.searchsorted(T, k + P - 0.05)
                if i1 > i0:
                    bordes[pcs[i0]] += 1
                    bordes[pcs[i1 - 1]] += 1
                k += P
        last = {}
        for i, c in enumerate(pcs):
            if c in last and i - last[c] >= 3:                                  # vuelve tras al menos dos notas
                regresos[c] += 1
            last[c] = i
        parts = [x / x.sum() for x in (tiempo, bordes, regresos) if x.sum() > 0]
        return sum(parts) / len(parts) if parts else np.zeros(24)

    sb = layer(raw_bass, cycles.get('Voz grave', []))
    sh = layer(raw_high, cycles.get('Voz aguda', []))
    total = (w_bass * sb + sh) / (w_bass + 1)
    order = np.argsort(-total)
    return dict(centro_pc24=int(order[0]), centro_bajo_pc24=int(sb.argmax()), centro_aguda_pc24=int(sh.argmax()),
                margen=round(float((total[order[0]] - total[order[1]]) / max(total[order[0]], 1e-9)), 3),
                puntaje=np.round(total, 4).tolist())"""),
    ("markdown", "**`mode24`**: Modo descrito por los grados 2, 3, 6 y 7, cada uno en su versión menor, neutra o mayor. Por ejemplo, «♭2+, ♭3, 6, ♭7». En 24-EDO no se fuerza un nombre de 12 tonos. Usa los perfiles de los compases confiables, con el bajo a peso 1 y la voz aguda a 0.6."),
    ("code", """import numpy as np

def mode24(bars, center_pc24, min_conf=0.5, wm=0.6):
    names = ['1', '1+', '♭2', '♭2+', '2', '2+', '♭3', '♭3+', '3', '3+', '4', '4+',
             '♯4', '♯4+', '5', '5+', '♭6', '♭6+', '6', '6+', '♭7', '♭7+', '7', '7+']
    use = [b for b in bars if b.get('confianza', 0) >= min_conf] or bars
    prof = sum((np.asarray(b['perfil_bajo'], float) + wm * np.asarray(b['perfil_aguda'], float) for b in use), np.zeros(24))
    rel = np.roll(prof, -center_pc24)
    grados = {}
    for grado, opciones in (('2', (2, 3, 4)), ('3', (6, 7, 8)), ('6', (16, 17, 18)), ('7', (20, 21, 22))):
        v = rel[list(opciones)]
        grados[grado] = names[opciones[int(v.argmax())]] if v.max() > 0 else None
    return dict(grados=grados, nombre=', '.join(g for g in grados.values() if g))"""),
    ("markdown", "**`harmony_layers`**: Capas del círculo armónico calculadas con los compases confiables.\n\n"
     "- **No dependen del centro:**\n"
     "  - `movimientos`: cómo se mueve la fundamental entre compases seguidos. Fuerte es por 4.ª o 5.ª; débil, por 3.ª o "
     "6.ª; color, por 2.ª, 7.ª o tritono; deslizamiento, por cuarto de tono; intermedio, por otro intervalo microtonal.\n"
     "  - `cambios_por_compas`: el ritmo armónico.\n"
     "  - `calidades`: la proporción de tiempo de cada calidad.\n"
     "- **Dependen del centro:** `transiciones`, que cuenta los pasos entre grados."),
    ("code", """import numpy as np

def harmony_layers(bars, center_pc24, min_conf=0.5):
    names = ['1', '1+', '♭2', '♭2+', '2', '2+', '♭3', '♭3+', '3', '3+', '4', '4+',
             '♯4', '♯4+', '5', '5+', '♭6', '♭6+', '6', '6+', '♭7', '♭7+', '7', '7+']
    kinds = {10: 'fuerte', 6: 'débil', 7: 'débil', 8: 'débil', 2: 'color', 4: 'color', 12: 'color', 1: 'deslizamiento'}
    ok = {b['compas']: b for b in bars if b.get('fundamental_pc24') is not None and b.get('confianza', 0) >= min_conf}
    mov = dict.fromkeys(['fuerte', 'débil', 'color', 'deslizamiento', 'intermedio'], 0.0)
    trans = {}
    pares = cambios = 0
    for k, b in ok.items():
        a = ok.get(k - 1)
        if a is None:
            continue
        pares += 1
        r0, r1 = (a['fundamental_pc24'] - center_pc24) % 24, (b['fundamental_pc24'] - center_pc24) % 24
        if r0 == r1:
            continue
        cambios += 1
        i = min((r1 - r0) % 24, (r0 - r1) % 24)
        mov[kinds.get(i, 'intermedio')] += 1
        trans[(names[r0], names[r1])] = trans.get((names[r0], names[r1]), 0) + 1
    calidades = {}
    for b in ok.values():
        calidades[b['calidad']] = calidades.get(b['calidad'], 0.0) + b['fin_s'] - b['inicio_s']
    tc = sum(calidades.values()) or 1.0
    return dict(compases_confiables=len(ok),
                movimientos={k: round(v / max(cambios, 1), 3) for k, v in mov.items()},
                cambios_por_compas=round(cambios / max(pares, 1), 3),
                calidades={k: round(v / tc, 3) for k, v in sorted(calidades.items(), key=lambda kv: -kv[1])},
                transiciones=[dict(de=a, a=b, veces=n) for (a, b), n in sorted(trans.items(), key=lambda kv: -kv[1])])"""),
]


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
    done = []
    ch = [c for c in cells if c["cell_type"] == "code" and "def chord24(" in src(c)]
    if not ch:
        print("No encontré la celda de `chord24`: aplica primero el paso 1 (scripts/agregar_armonia.py).")
        return 1
    if "np.round(S, 9)" in src(ch[0]):
        done.append("chord24: el cambio ya estaba")
    else:
        ch[0]["source"] = src(ch[0]).replace(OLD_TIES, NEW_TIES).splitlines(keepends=True)
        done.append("chord24: empates resueltos igual en cualquier máquina")
    run = [i for i, c in enumerate(cells) if c["cell_type"] == "code" and "armonia = harmony_by_bar(" in src(c)]
    if not run:
        print("No encontré la celda de ejecución de la armonía: aplica primero el paso 1.")
        return 1
    i = run[0]
    if any(MARKER in src(c) for c in cells if c["cell_type"] == "markdown"):
        done.append("funciones del paso 2: ya estaban")
    else:
        at = i - 1 if i > 0 and cells[i - 1]["cell_type"] == "markdown" else i     # antes del texto de la ejecución
        cells[at:at] = [_cell(k, t) for k, t in NEW_CELLS]
        i += len(NEW_CELLS)
        done.append("funciones del paso 2: center24_by_layer, mode24 y harmony_layers agregadas")
    if "center24_by_layer(raw_bass" in src(cells[i]):
        if OLD_DEFAULT in src(cells[i]):
            cells[i]["source"] = src(cells[i]).replace(OLD_DEFAULT, NEW_DEFAULT).splitlines(keepends=True)
            done.append("ejecución: el centro por defecto pasa a ser la tónica de 12 clases")
        else:
            done.append("ejecución: ya estaba")
    else:
        cells[i]["source"] = NEW_RUN.splitlines(keepends=True)
        if i > 0 and cells[i - 1]["cell_type"] == "markdown":
            cells[i - 1]["source"] = ("Armonía de la canción: centro y modo en 24-EDO, una fila por compás (`armonia`) y el resumen "
                                      "con las capas del círculo (`armonia_resumen`). `CENTRO` permite fijar el centro a mano "
                                      "para comparar. `run_song.py` lo guarda todo en `armonia.json`.").splitlines(keepends=True)
        done.append("ejecución: centro, modo y capas")
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("\n".join(done))
    print("Ahora: make extract && make test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

