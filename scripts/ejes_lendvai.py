"""Paso H2b del análisis armónico: ejes de Lendvai en cada compás, en las progresiones y en el tabroll.

Uso:
    python scripts/ejes_lendvai.py
    make extract
    make test

Lendvai agrupa las 12 clases por terceras menores en tres ejes: tónica (en Do: Do, Fa♯, La, Mi♭), subdominante (Fa, Si,
Re, La♭) y dominante (Sol, Do♯, Mi, Si♭). Cada eje tiene una rama principal (polo y contrapolo, a un tritono) y una
secundaria. Medido en semitonos sobre el centro, el eje es el grado módulo 3. En 24-EDO, un grado de cuarto de tono cae
entre dos ejes vecinos (♭2+ entre dominante y subdominante); con terceras menores de 6 cuartos de tono, esos grados forman
otros tres ejes, los neutros.

Cambios en el cuaderno:
1. `chord_roles` agrega `eje`, `eje_corto` (T, S, D o T–D, D–S, S–T) y `rama` (polo, contrapolo o rama secundaria).
2. `roles_summary` reparte el tiempo por eje.
3. `chord_progressions` clasifica cada cambio por ejes: adelante (T→S→D→T, como V-I o I-IV), atrás (T→D→S→T, como
   I-V o IV-I), dentro del mismo eje (sustitución por tercera menor o tritono), o microtonal. Columnas nuevas por compás:
   `eje_cambio` («D → T») y `paso_eje`.
4. La celda de armonía imprime los ejes; la franja del tabroll24 escribe el eje cuando no coincide con la función.
Se puede correr más de una vez: lo que ya está aplicado no se toca.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"

ROLES_EDITS = [
    ("LETRA = {'tónica': 'T', 'subdominante': 'S', 'dominante': 'D', 'neutra': 'N', 'sin función': '—'}\n",
     "LETRA = {'tónica': 'T', 'subdominante': 'S', 'dominante': 'D', 'neutra': 'N', 'sin función': '—'}\n"
     "EJES = {0: 'tónica', 1: 'dominante', 2: 'subdominante'}                # ejes de Lendvai: grado (en semitonos) módulo 3\n"
     "POLOS = {0: 0, 1: 7, 2: 5}                                             # polo de la rama principal de cada eje\n"),
    ("                       papel_aguda=None, aguda_en_acorde=None)\n",
     "                       papel_aguda=None, aguda_en_acorde=None, eje=None, eje_corto=None, rama=None)\n"),
    ("        row.update(grado24=q, cifrado=cifrado, nombre_grado=nombre,",
     "        if cuarto:                                                     # entre dos ejes: los ejes neutros de 24-EDO\n"
     "            lo, hi = EJES[d % 3], EJES[(d + 1) % 3]\n"
     "            eje, eje_corto, rama = f'entre {lo} y {hi}', f'{LETRA[lo]}–{LETRA[hi]}', None\n"
     "        else:\n"
     "            eje, rel = EJES[d % 3], (d - POLOS[d % 3]) % 12\n"
     "            eje_corto, rama = LETRA[eje], 'polo' if rel == 0 else 'contrapolo' if rel == 6 else 'rama secundaria'\n"
     "        row.update(grado24=q, cifrado=cifrado, nombre_grado=nombre,"),
    ("                   papel_aguda=papel, aguda_en_acorde=en_acorde)\n",
     "                   papel_aguda=papel, aguda_en_acorde=en_acorde, eje=eje, eje_corto=eje_corto, rama=rama)\n"),
]
DOC_ROLES_EXTRA = (" El eje sigue a Lendvai: tónica, subdominante y dominante agrupadas por terceras menores (el grado en "
                   "semitonos módulo 3), con su rama: polo, contrapolo (a un tritono del polo) o rama secundaria. Un grado "
                   "de cuarto de tono queda entre dos ejes (D–S para ♭2+), en uno de los tres ejes neutros de 24-EDO.")

SUMMARY_OLD = "                papeles_aguda=share('papel_aguda'),\n"
SUMMARY_NEW = "                papeles_aguda=share('papel_aguda'), ejes=share('eje'),\n"
DOC_SUMMARY = ("**`roles_summary`**: Reparto del tiempo de los compases confiables por función (familia y con su calidad), "
               "nombre y clase del grado, inversión, cifrado, papel de la voz aguda y eje de Lendvai (en %, de mayor a "
               "menor), y qué parte de la voz aguda cae dentro del acorde, ponderada por la duración de cada compás.")

DOC_PROG = ("**`chord_progressions`**: Progresiones entre compases, en cada cambio de fundamental. Para cada uno: la "
            "progresión («♭III → ♭VII»), el movimiento de la fundamental según Piston (pp. 22-24: quinta abajo, como V-I, "
            "la más fuerte; quinta arriba, como IV-I; tercera abajo; tercera arriba, la más débil; segunda; tritono; o "
            "microtonal), qué tan usual es según su tabla de progresiones (pp. 21-22), leída por número de grado (♭VII "
            "como VII), y el paso entre ejes de Lendvai: adelante (T→S→D→T, como V-I o I-IV), atrás (T→D→S→T, como I-V o "
            "IV-I), dentro del mismo eje (sustitución por tercera menor o tritono), en el mismo eje neutro o microtonal. "
            "Con `menor` se agregan los añadidos de Piston para el modo menor (p. 45). Da dos resúmenes, uno al lado del "
            "otro: `confiables` (compases con confianza ≥ `min_conf`) y `todos` (todos los compases con acorde). Cada uno "
            "dice qué parte de los cambios va por quintas y por ejes, las progresiones más frecuentes, las progresiones con "
            "nombre (cadencias y progresiones conocidas, por sus fundamentales) y los vaivenes entre dos acordes. Las "
            "columnas de cada compás salen de los confiables.")

CODE_PROG = '''from collections import Counter

DIATONICO = {0: 1, 1: 2, 2: 2, 3: 3, 4: 3, 5: 4, 7: 5, 8: 6, 9: 6, 10: 7, 11: 7}      # el ♯IV (6) no tiene grado diatónico
PISTON = {1: ({4, 5}, {6}, {2, 3}), 2: ({5}, {4, 6}, {1, 3}), 3: ({6}, {4}, {1, 2, 5}), 4: ({5}, {1, 2}, {3, 6}),
          5: ({1}, {4, 6}, {2, 3}), 6: ({2, 5}, {3, 4}, {1}), 7: ({1, 3}, {6}, {2, 4, 5})}
USOS = ('usual', 'a veces', 'menos a menudo')
MOVIMIENTOS = {5: 'quinta abajo (como V-I)', 7: 'quinta arriba (como IV-I)', 8: 'tercera abajo', 9: 'tercera abajo',
               3: 'tercera arriba', 4: 'tercera arriba', 1: 'segunda', 2: 'segunda', 10: 'segunda', 11: 'segunda',
               6: 'tritono'}
CON_NOMBRE = {   # semitonos de cada fundamental sobre el centro
    'cadencia auténtica V-I': (7, 0), 'cadencia plagal IV-I': (5, 0), 'cadencia rota V-VI': (7, 9),
    'cadencia rota V-♭VI': (7, 8), 'cadencia modal ♭VII-I': (10, 0), 'cadencia eólica ♭VI-♭VII-I': (8, 10, 0),
    'cadencia andaluza i-♭VII-♭VI-V': (0, 10, 8, 7), 'II-V-I': (2, 7, 0), 'I-IV-V': (0, 5, 7), 'IV-V-I': (5, 7, 0),
    'I-V-vi-IV': (0, 7, 9, 5), 'I-vi-IV-V': (0, 9, 5, 7), 'vi-IV-I-V': (9, 5, 0, 7),
    'i-♭VI-♭III-♭VII': (0, 8, 3, 10), 'círculo de quintas vi-ii-V-I': (9, 2, 7, 0)}
EJE_DE = {0: 'T', 1: 'D', 2: 'S'}                                      # eje de Lendvai: grado en semitonos módulo 3


def chord_progressions(armonia, menor=False, min_conf=0.5):
    def uso(d0, d1):                                                   # qué tan usual es d0 → d1 en la tabla de Piston
        a, b = DIATONICO.get(d0), DIATONICO.get(d1)
        if a is None or b is None:
            return 'fuera de la tabla'
        fila = PISTON[a]
        if menor:                                                      # añadidos de Piston para el modo menor (p. 45)
            if a in (1, 3):
                fila = (fila[0] | {7}, fila[1], fila[2])
            elif a == 7:
                fila = ({3}, {6}, {4}) if d0 == 10 else ({1}, set(), set())
        for nombre, grupo in zip(USOS, fila):
            if b in grupo:
                return nombre
        return 'fuera de la tabla'

    def eje(q):                                                        # T, S, D, o T–D, D–S, S–T entre dos ejes
        return EJE_DE[(q // 2) % 3] if q % 2 == 0 else f'{EJE_DE[(q // 2) % 3]}–{EJE_DE[(q // 2 + 1) % 3]}'

    def paso(q0, q):                                                   # paso entre ejes de Lendvai
        if q0 % 2 or q % 2:
            return 'mismo eje neutro' if q0 % 6 == q % 6 else 'microtonal'
        a0, a1 = (q0 // 2) % 3, (q // 2) % 3
        if a0 == a1:
            return 'mismo eje (sustitución)'
        return 'adelante (T→S→D→T)' if (a0 - a1) % 3 == 1 else 'atrás (T→D→S→T)'

    def recorrido(umbral):                                             # cambios entre los compases con confianza ≥ umbral
        seq, marcas = [], {}                                           # seq: (fila, grado en cuartos de tono, cifrado)
        usados = 0
        for i, r in enumerate(armonia):
            if r.get('cifrado') is None or r.get('grado24') is None or (r.get('confianza') or 0) < umbral:
                continue
            usados += 1
            q = r['grado24']
            if seq and seq[-1][1] == q:                                # misma fundamental: no hay cambio
                continue
            if seq:
                q0 = seq[-1][1]
                prog, ejes = f'{seq[-1][2]} → {r["cifrado"]}', f'{eje(q0)} → {eje(q)}'
                if q0 % 2 or q % 2:
                    marcas[i] = (prog, 'microtonal', 'fuera de la tabla', paso(q0, q), ejes)
                else:
                    marcas[i] = (prog, MOVIMIENTOS[(q // 2 - q0 // 2) % 12], uso(q0 // 2, q // 2), paso(q0, q), ejes)
            seq.append((i, q, r['cifrado']))

        cambios = list(marcas.values())
        n = len(cambios) or 1
        share = lambda k: {key: round(100.0 * v / n, 1) for key, v in Counter(c[k] for c in cambios).most_common()}
        grados = [q for _, q, _ in seq]
        con_nombre = {}
        for name, pat in CON_NOMBRE.items():
            p24 = [2 * x for x in pat]
            hits = [seq[k][0] for k in range(len(seq) - len(p24) + 1) if grados[k:k + len(p24)] == p24]
            if hits:
                con_nombre[name] = dict(veces=len(hits), compases=[armonia[i]['compas'] for i in hits[:10]])
        vaiven = Counter()
        for k in range(len(seq) - 3):
            if grados[k] == grados[k + 2] and grados[k + 1] == grados[k + 3]:
                vaiven[' ↔ '.join(sorted((seq[k][2], seq[k + 1][2])))] += 1
        quintas = sum(1 for c in cambios if c[1].startswith('quinta'))
        frecuentes = [[p, c] for p, c in Counter(c[0] for c in cambios).most_common(8)]
        return marcas, dict(umbral=umbral, compases=usados, cambios=len(cambios), por_quintas=round(100.0 * quintas / n, 1),
                            movimientos=share(1), uso_piston=share(2), ejes=share(3),
                            pasos_de_eje=dict(Counter(c[4] for c in cambios).most_common(6)), frecuentes=frecuentes,
                            con_nombre=con_nombre, vaivenes=dict(vaiven.most_common(5)))

    marcas, confiables = recorrido(min_conf)
    _, todos = recorrido(0.0)
    out = []
    for i, r in enumerate(armonia):
        prog, mov, usual, paso_eje, ejes = marcas.get(i, (None,) * 5)
        out.append(dict(r, progresion=prog, movimiento=mov, uso_piston=usual, eje_cambio=ejes, paso_eje=paso_eje))
    return out, dict(confiables=confiables, todos=todos)'''

OLD_TAIL_START = "modo_menor = '♭3' in"
TAIL = '''modo_menor = '♭3' in [x.strip() for x in armonia_resumen['modo']['nombre'].split(',')]
armonia, armonia_resumen['progresiones'] = chord_progressions(armonia, menor=modo_menor)
print('         grados: ' + ', '.join(f'{k} {v:.0f}%' for k, v in list(fx['nombres_grado'].items())[:5]))
print('         ejes de Lendvai: ' + ', '.join(f'{k} {v:.0f}%' for k, v in fx['ejes'].items()))
for clave, titulo in (('confiables', 'compases confiables'), ('todos', 'todos los compases')):
    pr = armonia_resumen['progresiones'][clave]
    print(f"         progresiones, {titulo} ({pr['compases']}): {pr['cambios']} cambios, {pr['por_quintas']:.0f}% por quintas | "
          'tabla de Piston: ' + ', '.join(f'{k} {v:.0f}%' for k, v in pr['uso_piston'].items()))
    print('           por ejes: ' + ', '.join(f'{k} {v:.0f}%' for k, v in pr['ejes'].items()) + ' | pasos: ' +
          ', '.join(f'{k} ×{v}' for k, v in pr['pasos_de_eje'].items()))
    print('           más frecuentes: ' + ', '.join(f'{p} ×{n}' for p, n in pr['frecuentes'][:5]))
    nombradas = [f"{k} ×{v['veces']}" for k, v in pr['con_nombre'].items()] + [f'vaivén {k} ×{v}' for k, v in pr['vaivenes'].items()]
    if nombradas:
        print('           con nombre: ' + ', '.join(nombradas))
'''

LABELS_OLD = '''                        annot=f"{row.get('funcion_corta') or ''} {MATIZ_CORTO.get(row.get('matiz') or '', '')}".strip(),'''
LABELS_NEW = '''                        annot=f"{row.get('funcion_corta') or ''} {MATIZ_CORTO.get(row.get('matiz') or '', '')}".strip()
                        + (f" · eje {row['eje_corto']}" if row.get('eje_corto') and row.get('eje') != row.get('funcion') else ''),'''
DOC_LABELS_OLD = "La anotación es la función (T, S, D, N; en minúscula si el acorde es menor) con su matiz corto, en el color de la función."
DOC_LABELS_NEW = ("La anotación es la función (T, S, D, N; en minúscula si el acorde es menor) con su matiz corto, en el "
                  "color de la función, y el eje de Lendvai cuando no coincide con la función («D sens. · eje S»).")

RENDER_OLD = '''                ax.text(cx, strip_top + st.strip_h - st.bar_h - 7, ch.annot, color=ch.annot_color or "#9a9aa0",
                        fontsize=8.0, fontweight="bold", ha="center", va="center", zorder=8)
'''
RENDER_NEW = '''                ax.text(cx, strip_top + st.strip_h - st.bar_h - 7, ch.annot, color=ch.annot_color or "#9a9aa0",
                        fontsize=max(5.5, min(8.0, 1.6 * w / max(len(ch.annot), 1))), fontweight="bold", ha="center",
                        va="center", zorder=8)
'''


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]
    src = lambda c: "".join(c["source"])
    put = lambda c, text: c.__setitem__("source", text.splitlines(keepends=True))
    idx = lambda pred: [i for i, c in enumerate(cells) if c["cell_type"] == "code" and pred(src(c))]
    done = []

    roles = idx(lambda s: "def chord_roles(" in s)
    summ = idx(lambda s: "def roles_summary(" in s)
    prog = idx(lambda s: "def chord_progressions(" in s)
    run = idx(lambda s: OLD_TAIL_START in s and "roles_summary(armonia)" in s)
    labels = idx(lambda s: "def harmony_labels(" in s)
    rend = idx(lambda s: s.startswith("def render(song: Song"))
    if not all(len(x) == 1 for x in (roles, summ, prog, run, labels, rend)):
        print("Falta alguna celda de los pasos H1 y H2. Corre antes scripts/funciones_y_progresiones.py y "
              "scripts/tabroll_armonia24.py.")
        return 1

    c, s = cells[roles[0]], src(cells[roles[0]])
    if "EJES = {" not in s:
        for old, new in ROLES_EDITS:
            if s.count(old) != 1:
                print(f"`chord_roles` no está como esperaba (no encontré: {old.strip()[:60]}…).")
                return 1
            s = s.replace(old, new)
        put(c, s)
        md = cells[roles[0] - 1]
        if md["cell_type"] == "markdown" and "Lendvai" not in src(md):
            put(md, src(md).rstrip("\n") + DOC_ROLES_EXTRA)
        done.append("chord_roles con el eje de Lendvai")

    c, s = cells[summ[0]], src(cells[summ[0]])
    if "ejes=share('eje')" not in s:
        if SUMMARY_OLD not in s:
            print("`roles_summary` no está como esperaba.")
            return 1
        put(c, s.replace(SUMMARY_OLD, SUMMARY_NEW))
        md = cells[summ[0] - 1]
        if md["cell_type"] == "markdown":
            put(md, DOC_SUMMARY)
        done.append("roles_summary con los ejes")

    if src(cells[prog[0]]) != CODE_PROG:
        put(cells[prog[0]], CODE_PROG)
        if cells[prog[0] - 1]["cell_type"] == "markdown":
            put(cells[prog[0] - 1], DOC_PROG)
        done.append("chord_progressions con los pasos entre ejes")

    s = src(cells[run[0]])
    new = s[:s.index(OLD_TAIL_START)] + TAIL
    if new != s:
        put(cells[run[0]], new)
        done.append("la celda de armonía imprime los ejes")

    c, s = cells[labels[0]], src(cells[labels[0]])
    if "eje_corto" not in s:
        if LABELS_OLD not in s:
            print("`harmony_labels` no está como esperaba.")
            return 1
        put(c, s.replace(LABELS_OLD, LABELS_NEW))
        md = cells[labels[0] - 1]
        if md["cell_type"] == "markdown" and DOC_LABELS_OLD in src(md):
            put(md, src(md).replace(DOC_LABELS_OLD, DOC_LABELS_NEW))
        done.append("harmony_labels escribe el eje")

    c, s = cells[rend[0]], src(cells[rend[0]])
    if RENDER_NEW not in s:
        if RENDER_OLD not in s:
            print("La anotación de `render` no está como la dejó scripts/tabroll_armonia24.py.")
            return 1
        put(c, s.replace(RENDER_OLD, RENDER_NEW))
        done.append("render achica la anotación en compases cortos")

    if not done:
        print("El cuaderno ya tenía los ejes de Lendvai.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
