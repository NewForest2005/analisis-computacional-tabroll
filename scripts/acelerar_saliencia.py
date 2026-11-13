"""Paso 4 del plan de trabajo: la celda de la línea calcula una sola vez lo que comparten sus dos saliencias.

Uso:
    python scripts/acelerar_saliencia.py
    make extract
    make test

La celda de la línea («2) Altura») llama dos veces a `stereo_salience`: con `gamma=0.7` para la línea que busca ciclos y
con `gamma=0.0` para la que conserva la octava de la guitarra. Las dos llamadas repetían lo caro, que no depende de
`gamma`: la STFT del canal lateral y los dos `harmonic_part` (filtros de mediana sobre todo el espectrograma). Ahora
`stereo_salience` acepta un `cache` y la segunda llamada reusa esos pasos. El resultado es idéntico; la celda tarda
cerca de un tercio menos.
Se puede correr más de una vez: lo que ya está aplicado no se toca.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "Tabroll_Angine_de_Poitrine.ipynb"

CODE_STEREO = '''def stereo_salience(S, M, stereo, cand, sr, nfft, hop, drums=True, split=47.0, min_side=0.01, gamma=0.7, cache=None):
    if stereo.ndim == 1:
        return S

    c = {} if cache is None else cache                                   # con cache, otra llamada reusa lo que no depende de gamma
    if 'lateral' not in c:
        Mx = stft_mag((stereo[0] - stereo[1]) / 2, nfft, hop)            # el bajo va al centro: L - R lo cancela
        f = np.arange(M.shape[0]) * sr / nfft
        band = (f >= 300) & (f < 4000)
        if np.sum(Mx[band] ** 2) < min_side * np.sum(M[band] ** 2):      # audio casi mono: no hay canal lateral útil
            c['lateral'] = None
        else:
            c['lateral'] = harmonic_part(Mx) if drums else Mx
            c['Sm'] = pitch_salience(harmonic_part(M), sr, nfft)[0] if drums else S
    if c['lateral'] is None:
        return S

    Sm = c['Sm']
    Sx = pitch_salience(c['lateral'], sr, nfft, gamma=gamma)[0]
    hi = cand >= split
    gain = np.percentile(Sm[hi].max(axis=0), 90) / np.percentile(Sx[hi].max(axis=0), 90)

    Sh = S.copy()
    Sh[hi] = np.sqrt(np.maximum(Sm[hi], 0) * np.maximum(Sx[hi], 0) * gain)   # debe sonar en los dos canales
    return Sh'''
DOC_STEREO_ADD = (" `cache` (un diccionario) guarda lo que no depende de `gamma`: el canal lateral ya filtrado y la saliencia "
                  "del central. Dos llamadas con la misma canción y el mismo `cache` dan lo mismo que sin él, pero la segunda "
                  "es mucho más rápida.")

LINE_EDITS = (
    ("Sh = stereo_salience(S, M, y_st, cand, sr, NFFT_P, HOP_P, HAS_DRUMS)\n",
     "cache_sal = {}                                                             # lo que comparten las dos saliencias\n"
     "Sh = stereo_salience(S, M, y_st, cand, sr, NFFT_P, HOP_P, HAS_DRUMS, cache=cache_sal)\n"),
    ("Sn = stereo_salience(S, M, y_st, cand, sr, NFFT_P, HOP_P, HAS_DRUMS, gamma=0.0)   # conserva la octava de la guitarra\n"
     "Sn = add_guitar_stem(Sn, S, stem, cand, sr, NFFT_P, HOP_P, gamma=0.0)\n",
     "Sn = stereo_salience(S, M, y_st, cand, sr, NFFT_P, HOP_P, HAS_DRUMS, gamma=0.0, cache=cache_sal)   # conserva la octava de la guitarra\n"
     "Sn = add_guitar_stem(Sn, S, stem, cand, sr, NFFT_P, HOP_P, gamma=0.0)\n"
     "del cache_sal\n"),
)


def main() -> int:
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = nb["cells"]
    src = lambda c: "".join(c["source"])
    put = lambda c, text: c.__setitem__("source", text.splitlines(keepends=True))
    code = lambda pred: [i for i, c in enumerate(cells) if c["cell_type"] == "code" and pred(src(c))]
    done = []

    st = code(lambda s: s.startswith("def stereo_salience("))
    line = code(lambda s: "melody_n = viterbi_pitch(consenso_n" in s)
    if len(st) != 1 or len(line) != 1:
        print("No encontré la celda de stereo_salience o la de la línea («2) Altura»); no cambié nada.")
        return 1

    i = st[0]
    if "cache=None" not in src(cells[i]):
        put(cells[i], CODE_STEREO)
        md = cells[i - 1]
        if md["cell_type"] == "markdown" and DOC_STEREO_ADD.strip() not in src(md):
            put(md, src(md).rstrip("\n") + DOC_STEREO_ADD)
        done.append("stereo_salience con cache")

    i = line[0]
    s = src(cells[i])
    for old, new in LINE_EDITS:
        if new in s:
            continue
        if old not in s:
            print("La celda de la línea no tiene las llamadas que esperaba; no la cambié.")
            return 1
        s = s.replace(old, new)
    if s != src(cells[i]):
        put(cells[i], s)
        done.append("la línea reusa el cache")

    if not done:
        print("El cuaderno ya calculaba una sola vez lo que comparten las saliencias.")
        return 0
    NOTEBOOK.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("Aplicado: " + "; ".join(done) + ".\nAhora corre: make extract && make test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
