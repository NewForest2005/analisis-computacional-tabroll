"""Test de verosimilitud por bloques de rasgos y conjunta: ¿la banda es un estilo existente, una síntesis nueva de lenguajes
existentes, o tiene rasgos que ningún corpus explica?

Uso:
    python scripts/comparacion/corpus_bloques.py                     # una vez (y otra por cada corpus descargado)
    python scripts/comparacion/verosimilitud_por_bloques.py outputs/<corrida> [...] [--control outputs/<corrida_primus> ...] \
        --salida outputs/bloques

Cuatro bloques por canción, cada uno comparado con cada corpus que lo tenga:
- Armonía: fundamentales (12 grados) y cambios de fundamental (intervalo × llegada), igual que verosimilitud_estilos.py.
- Escala (12 notas): la melodía (voz aguda; si no hay, la grave) en 12 grados respecto de la tónica, por duración; cada
  cuarto de tono se reparte mitad y mitad entre los dos semitonos vecinos. ¿Existe esta escala en algún estilo?
- Cuartos de tono: qué grados en cuarto de tono usa la melodía (reparto del tiempo entre los 12 grados en ¼, sin los
  semitonos), comparado solo con corpus microtonales (familia «microtonal»: SymbTr, Radif,
  andalusí). Antes se filtra con los controles: si la concentración de los cuartos de tono (% de su tiempo en los dos
  grados en cuarto de tono más usados) no supera a la de los controles por al menos 2 desviaciones (z ≥ 2), la canción
  se trata como de 12 notas y este bloque no cuenta. El % de tiempo en cuartos de tono no sirve de filtro: Primus marca
  9-13 % y Utzp 11 %; la concentración sí separa (Primus 28-37 %, la banda 48-82 %): en la banda caen en grados fijos.
  Si la canción pasa el filtro y no hay corpus microtonal, el bloque queda «sin vecino (sin corpus microtonal)».
- Metro: reparto del tiempo por familia de compás (2·4·8 | 3·6·12 | 5 | 7 | 9 | otro impar).
Antes había un solo bloque de altura en 24 grados contra el RS 200; se separó porque dos de los tres controles de Primus
(sin cuartos de tono) quedaban «sin vecino»: mezclaba qué escala se usa con si hay cuartos de tono.
Tipicidad de un bloque en un corpus (percentil): se busca la k-ésima pieza del corpus más parecida a la canción (k = 5,
distancia de Jensen-Shannon) y se da el % de piezas del corpus cuya k-ésima más parecida está igual o más lejos (sin
contarse a sí mismas ni a la otra versión de la misma canción). 50 = típica; 0 = no hay nada parecido en el corpus.
Se usan vecinos y no la distancia al promedio del estilo porque un estilo puede tener varias zonas (un corpus con 93 %
de temas en 4 y 7 % en 3 tiene un promedio «en 4 con un poco de 3» que no se parece a ninguno).
Armonía = media de las distancias de fundamentales y de cambios.

Conjunta en un corpus (con al menos dos bloques en común): lo mismo, pero el parecido se mide en todos los bloques a la
vez (suma de las distancias de cada bloque divididas por su mediana en el corpus). Contesta: ¿hay piezas en el corpus que
se parezcan a la canción en todo junto? Una canción puede tener vecinos en cada bloque por separado y ninguno en conjunto.

Modelo de medición: el cuaderno marca 9-13 % de cuartos de tono en música que no los tiene y lee mal algunos compases
de un 4/4 (Primus). Para comparar en igualdad, cada pieza de corpus pasa por el mismo error: en la altura, ε del tiempo
de cada grado se reparte entre sus dos vecinos a ¼ de tono; en el metro, η del tiempo pasa a las familias de compás en
que el cuaderno se equivoca, con el reparto del control. ε y η se miden en las corridas --control (canciones en 4/4 y
sin cuartos de tono) o valen lo medido en Tommy the Cat.

Veredicto (umbral u, por defecto 5 %, como un contraste a una cola):
- «estilo existente (X)»: algún corpus X con todos los bloques medidos tiene percentil conjunto ≥ u. Un conjunto
  parcial (corpus al que le falta un bloque, p. ej. el rock sin cuartos de tono) no basta para llamarlo existente.
- «variante atípica de X»: cada bloque es típico en X por separado, pero la combinación no lo es.
- «síntesis de lenguajes existentes»: cada bloque es típico (≥ u) en algún corpus, pero ningún corpus tiene todos los
  bloques típicos y ninguno explica la combinación (conjunto < u en todos).
- «rasgo sin vecino: …»: algún bloque no es típico en ningún corpus (lo que no se explica con los corpus disponibles).
Solo cuentan para el veredicto los corpus con 100 piezas o más (--min-piezas): en uno chico y disperso casi todo
parece típico. Si ningún corpus tiene todos los bloques, el conjunto usa los que tenga y se avisa.
Calibración: el mismo veredicto se aplica a cada pieza de los corpus con al menos tres bloques (contra las demás)
para saber cuántas veces llama «síntesis» o «sin vecino» a una pieza real de un estilo conocido (falsos positivos).

Escribe <salida>.json, <salida>.csv, <salida>_bloques.png (percentiles por bloque y corpus) y <salida>_sintesis.png
(de qué corpus viene cada bloque y el veredicto).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verosimilitud_estilos import cambios_dist, cancion as armonia_cancion, nombre  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
BLOQUES_DIR = RAIZ / "references" / "corpus" / "bloques"
BLOQUES = ["armonia", "escala", "microtono", "metro"]
TITULO = {"armonia": "Armonía", "escala": "Escala (12 notas)", "microtono": "Cuartos de tono", "metro": "Metro"}
MARCA = {"banda": "★ ", "control": "◆ ", "comparar": "▲ "}
CONTROL_CONC = (32.0, 4.4)                                               # concentración en Primus (Tommy, Mud, Jerry), por defecto
FAMILIA_COLOR = {"rock/pop": "#2a78d6", "clasica": "#eb6834", "jazz": "#1baf7a", "folk": "#eda100", "microtonal": "#e87ba4", "otro": "#6250d6"}
NOMBRE_TIPO = {"existente": "estilo existente", "sin_vecino": "rasgo sin vecino", "sintesis": "síntesis", "variante": "variante atípica"}


# ───────────────────────── distancias ─────────────────────────
def js_pares(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Jensen-Shannon (bits) entre cada fila de A y cada fila de B, por trozos."""
    A, B = A.astype(np.float32), B.astype(np.float32)
    hA = -(np.where(A > 0, A * np.log2(np.where(A > 0, A, 1)), 0)).sum(1)
    hB = -(np.where(B > 0, B * np.log2(np.where(B > 0, B, 1)), 0)).sum(1)
    out = np.empty((len(A), len(B)), dtype=np.float32)
    paso = max(1, int(3e7 // max(1, len(B) * A.shape[1])))
    for a0 in range(0, len(A), paso):
        M = (A[a0:a0 + paso, None, :] + B[None, :, :]) / 2
        hM = -(np.where(M > 0, M * np.log2(np.where(M > 0, M, 1)), 0)).sum(2)
        out[a0:a0 + paso] = hM - (hA[a0:a0 + paso, None] + hB[None, :]) / 2
    return np.clip(out, 0, 1)


def fuga(v: np.ndarray, eps: float) -> np.ndarray:
    """Modelo de medición: ε de cada grado de 24 se va a sus vecinos a ¼ de tono (mitad a cada lado)."""
    return (1 - eps) * v + eps / 2 * (np.roll(v, 1, axis=-1) + np.roll(v, -1, axis=-1))


def plegar(v: np.ndarray) -> np.ndarray:
    """24 grados → 12: cada cuarto de tono se reparte mitad y mitad entre sus dos semitonos vecinos."""
    par, impar = v[..., 0::2], v[..., 1::2]
    return par + impar / 2 + np.roll(impar, 1, axis=-1) / 2


def concentracion(alt24: np.ndarray) -> tuple[float, float]:
    """(% del tiempo en cuartos de tono, % de ese tiempo en los dos grados en cuarto de tono más usados)."""
    impar = alt24[1::2]
    q = float(impar.sum())
    return 100 * q, (100 * float(np.sort(impar)[::-1][:2].sum()) / q if q else 0.0)


def solo_cuartos(v: np.ndarray) -> np.ndarray | None:
    """Reparto del tiempo entre los 12 grados en cuarto de tono (cuáles se usan), sin los semitonos."""
    o = np.asarray(v)[..., 1::2]
    s = o.sum(-1, keepdims=True)
    return np.where(s > 0, o / np.where(s > 0, s, 1), 0)


def kesimo(d: np.ndarray, k: int) -> float:
    d = d[np.isfinite(d)]
    if not len(d):
        return float("nan")
    return float(np.partition(d, min(k, len(d)) - 1)[min(k, len(d)) - 1])


class Corpus:
    """Un corpus en los tres bloques. Tipicidad de algo = distancia a su k-ésima pieza más parecida, comparada con la de
    cada pieza del corpus a sus k más parecidas (sin ella misma ni la otra versión de la misma canción)."""

    def __init__(self, path: Path, eps: float, k: int, maximo: int, error_metro: np.ndarray | None = None):
        D = json.loads(path.read_text(encoding="utf-8"))
        self.nombre, self.familia, self.fuente = D["nombre"], D.get("familia", "otro"), D.get("fuente", "")
        P = D["piezas"]
        if len(P) > maximo:
            P = [P[i] for i in sorted(np.random.default_rng(0).choice(len(P), maximo, replace=False))]
        self.P, self.n, self.k, self.eps = P, len(P), k, eps
        self.error_metro = error_metro if error_metro is not None else np.zeros(6)
        self.micro = self.familia == "microtonal"
        grupo = [re.sub(r"_(dt|tdc)$", "", str(p.get("id", i))).split("|")[0] for i, p in enumerate(P)]   # misma canción o grabación
        mismo = np.array([[a == b for b in grupo] for a in grupo]) if self.n <= 5000 else np.eye(self.n, dtype=bool)
        self.V = {b: [self._vec(p, b) for p in P] for b in ("fund", "camb", "escala", "microtono", "metro")}
        self.D, self.escala, self.ref = {}, {}, {}
        # resolución: lo que cambia una pieza al pasar por el modelo de medición; diferencias menores no se distinguen
        self.res = {b: 0.0 for b in BLOQUES}
        crudas = [np.array(p["altura"]) for p in P if p.get("altura")]
        if crudas:
            A = np.array(crudas)
            self.res["escala"] = float(np.median(np.diag(js_pares(plegar(A), plegar(fuga(A, eps))))))
            # En cuartos de tono no hay piso de resolución: la fuga (que viene de los semitonos, mucho más abundantes)
            # cambia tanto el reparto en ¼ de una pieza que el piso hacía iguales a casi todas (percentiles 0 o 100).
            # El modelo de medición ya se aplica a cada pieza del corpus, así que se comparan tal cual.
        pura = np.eye(6)[0]
        eta = self.error_metro.sum()
        self.res["metro"] = float(js_pares(pura[None], ((1 - eta) * pura + self.error_metro)[None])[0, 0])
        for b in BLOQUES:
            Db = self._pares(b)
            if Db is None:
                continue
            Db[mismo] = np.nan
            tiene = np.isfinite(Db).any(1)
            if tiene.sum() < 10:
                continue
            tri = Db[np.triu_indices(self.n, 1)]
            tri = np.maximum(tri[np.isfinite(tri)] - self.res[b], 0)
            self.escala[b] = max(float(np.median(tri)) if len(tri) else 0.0, self.res[b], 1e-3)
            self.D[b] = Db
            self.ref[b] = np.maximum(np.array([kesimo(Db[i], k) if tiene[i] else np.nan for i in range(self.n)]), self.res[b])
        self._conj = {}

    def _vec(self, p: dict, b: str):
        if b == "fund":
            return np.array(p["fundamentales"]) if p.get("fundamentales") else None
        if b == "camb":
            return np.array(cambios_dist([tuple(x) for x in p["cambios"]])) if p.get("cambios") and len(p["cambios"]) >= 3 else None
        if b == "escala":
            return plegar(fuga(np.array(p["altura"]), self.eps)) if p.get("altura") else None
        if b == "microtono":
            return solo_cuartos(fuga(np.array(p["altura"]), self.eps)) if p.get("altura") and self.micro else None
        if not p.get("metro"):
            return None
        eta = self.error_metro.sum()                                     # modelo de medición del compás
        return (1 - eta) * np.array(p["metro"]) + self.error_metro

    def _pares(self, b: str) -> np.ndarray | None:
        return self.distancias({c: self.V[c] for c in self.V}, b)

    def distancias(self, R: dict, b: str) -> np.ndarray | None:
        """Matriz (len(R) × n) de distancias en el bloque b; R[sub] = lista de vectores o None."""
        subs = ["fund", "camb"] if b == "armonia" else [b]
        mats = []
        for sb in subs:
            filas = [i for i, v in enumerate(R[sb]) if v is not None]
            cols = [j for j, v in enumerate(self.V[sb]) if v is not None]
            M = np.full((len(R[sb]), self.n), np.nan, dtype=np.float32)
            if filas and cols:
                M[np.ix_(filas, cols)] = js_pares(np.array([R[sb][i] for i in filas]), np.array([self.V[sb][j] for j in cols]))
            mats.append(M)
        if not np.isfinite(mats[0]).any():
            return None
        if b == "armonia":
            return np.where(np.isfinite(mats[1]), (mats[0] + mats[1]) / 2, mats[0])
        return mats[0]

    def bloques(self) -> list[str]:
        return [b for b in BLOQUES if b in self.D]

    def _pct(self, ref: np.ndarray, d: float) -> float:
        ref = ref[np.isfinite(ref)]
        return 100.0 * float((ref >= d - 1e-9).sum()) / len(ref)

    def medir(self, rasgos: dict) -> dict:
        """Distancias de una canción a cada pieza, por bloque."""
        R = {"fund": [rasgos.get("fundamentales")], "camb": [rasgos.get("cambios_v")], "escala": [rasgos.get("escala")],
             "microtono": [rasgos.get("microtono")], "metro": [rasgos.get("metro")]}
        out = {}
        for b in self.bloques():
            d = self.distancias(R, b)
            if d is not None and np.isfinite(d[0]).any():
                out[b] = d[0]
        return out

    def percentiles(self, dist: dict) -> dict:
        return {b: self._pct(self.ref[b], max(kesimo(d, self.k), self.res[b])) for b, d in dist.items()}

    def _ref_conj(self, comunes: tuple) -> tuple[np.ndarray, np.ndarray]:
        if comunes not in self._conj:
            Dj = np.max([np.maximum(self.D[b] - self.res[b], 0) / self.escala[b] for b in comunes], axis=0)
            ok = np.all([np.isfinite(self.D[b]).any(1) for b in comunes], axis=0)
            Dj[:, ~ok] = np.nan
            ref = np.array([kesimo(Dj[i], self.k) if ok[i] else np.nan for i in range(self.n)])
            self._conj[comunes] = (ref, ok)
        return self._conj[comunes]

    def conjunto(self, dist: dict) -> tuple[float | None, list[str]]:
        """Tipicidad en los bloques que comparten la canción y el corpus a la vez (al menos dos)."""
        comunes = tuple(b for b in BLOQUES if b in dist)
        if len(comunes) < 2:
            return None, list(comunes)
        ref, ok = self._ref_conj(comunes)
        if ok.sum() < 10:
            return None, list(comunes)
        dj = np.max([np.maximum(dist[b] - self.res[b], 0) / self.escala[b] for b in comunes], axis=0)
        dj = np.where(ok, dj, np.nan)
        return self._pct(ref, kesimo(dj, self.k)), list(comunes)

    def pieza(self, i: int) -> tuple[dict, tuple]:
        """Percentiles por bloque y conjunto de una pieza propia (contra las demás)."""
        ps = {b: self._pct(self.ref[b], self.ref[b][i]) for b in self.bloques() if np.isfinite(self.ref[b][i])}
        comunes = tuple(ps)
        conj = (None, list(comunes))
        if len(comunes) >= 2:
            ref, ok = self._ref_conj(comunes)
            if ok[i]:
                conj = (self._pct(ref, ref[i]), list(comunes))
        return ps, conj

    def rasgos(self, i: int) -> dict:
        return dict(fundamentales=self.V["fund"][i], cambios_v=self.V["camb"][i], escala=self.V["escala"][i], microtono=self.V["microtono"][i],
                    metro=self.V["metro"][i])


def veredicto(por_corpus: dict, conj: dict, corpora: dict, u: float, minimo: int = 100, microtonal: bool = False) -> dict:
    """Solo cuentan para el veredicto los corpus con al menos `minimo` piezas: en uno chico y disperso casi todo parece típico."""
    validos = {c for c in por_corpus if corpora[c].n >= minimo}
    mejor = {}
    for b in BLOQUES:
        cand = [(v[b], c) for c, v in por_corpus.items() if b in v and c in validos]
        if cand:
            p, c = max(cand)
            mejor[b] = dict(corpus=c, percentil=round(p, 1))
    medidos = list(mejor)
    sin_vecino = [TITULO[b] for b in medidos if mejor[b]["percentil"] < u]
    if microtonal and "microtono" not in mejor:                          # pasa el filtro y no hay corpus con qué comparar
        sin_vecino.append("Cuartos de tono (sin corpus microtonal)")
    completos = {c: v for c, (v, comunes) in conj.items() if v is not None and set(comunes) == set(medidos) and c in validos}
    parciales = {c: v for c, (v, comunes) in conj.items() if v is not None and c in validos}
    cubre_todo = [c for c in validos if all(por_corpus[c].get(b, -1) >= u for b in medidos)]
    usar = completos or parciales
    mejor_conj = max(usar.items(), key=lambda kv: kv[1]) if usar else (None, None)
    aviso = "" if completos else (" (conjunto con menos bloques: ningún corpus los tiene todos)" if parciales else " (sin corpus con dos bloques)")
    if sin_vecino:
        texto, tipo = "rasgo sin vecino: " + ", ".join(sin_vecino), "sin_vecino"
    elif completos and mejor_conj[1] is not None and mejor_conj[1] >= u:     # solo con un corpus que tenga todos los bloques
        texto, tipo = f"estilo existente ({mejor_conj[0]})", "existente"
    elif cubre_todo:
        texto, tipo = f"variante atípica de {cubre_todo[0]}", "variante"
    else:
        texto, tipo = "síntesis de lenguajes existentes", "sintesis"
    return dict(mejor_por_bloque=mejor, conjunto_mejor=dict(corpus=mejor_conj[0], percentil=None if mejor_conj[1] is None else round(mejor_conj[1], 1)),
                veredicto=texto + aviso, tipo=tipo)


# ───────────────────────── canción ─────────────────────────
def rasgos_cancion(run: Path) -> dict:
    H = json.loads((run / "armonia.json").read_text(encoding="utf-8"))
    J = json.loads((run / "line_diagnostics.json").read_text(encoding="utf-8"))
    a = armonia_cancion(run)
    ton = H.get("tonica_pc24") or 0
    notas = J.get("raw_high") or J.get("raw_bass") or []
    alt = np.zeros(24)
    for n in notas:
        alt[(round(n["midi"] * 2) - ton) % 24] += max(0.0, n["end_s"] - n["start_s"])
    bpm = J.get("tempo_bpm") or 120.0
    met = np.zeros(6)
    from corpus_bloques import familia_metro
    for b in H["compases"]:
        d = b["fin_s"] - b["inicio_s"]
        met[familia_metro(max(1, round(d / (60.0 / bpm))))] += d
    return dict(fundamentales=np.array(a["fundamentales"]) if sum(a["fundamentales"]) else None,
                cambios_v=np.array(a["cambios_v"]) if a["cambios_v"] else None,
                alt24=alt / alt.sum() if alt.sum() else None, escala=plegar(alt / alt.sum()) if alt.sum() else None, microtono=None,
                metro=met / met.sum() if met.sum() else None,
                cuartos=round(100 * alt[1::2].sum() / alt.sum(), 1) if alt.sum() else None,
                segundos_cuartos=round(float(alt[1::2].sum()), 1),
                concentracion=round(concentracion(alt / alt.sum())[1], 1) if alt.sum() else None,
                voz="aguda" if J.get("raw_high") else "grave")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corridas", nargs="+", type=Path)
    ap.add_argument("--control", nargs="*", type=Path, default=[], help="corridas de control sin cuartos de tono (Primus)")
    ap.add_argument("--comparar", nargs="*", type=Path, default=[],
                    help="corridas de un repertorio a comparar canción por canción (p. ej. King Gizzard); no votan ni miden el error")
    ap.add_argument("--umbral", type=float, default=5.0)
    ap.add_argument("--eps", type=float, help="fuga a cuartos de tono del modelo de medición (si no, se mide en --control)")
    ap.add_argument("--min-piezas", type=int, default=100, help="tamaño mínimo de un corpus para el veredicto")
    ap.add_argument("--k", type=int, default=5, help="vecinos para la tipicidad (k-ésima pieza más parecida)")
    ap.add_argument("--maximo", type=int, default=2500, help="piezas por corpus como máximo (muestra fija)")
    ap.add_argument("--min-segundos-cuartos", type=float, default=10.0,
                    help="segundos mínimos de melodía en cuarto de tono para medir la concentración (filtro microtonal)")
    ap.add_argument("--efecto-campos", type=float, default=30.0,
                    help="% mínimo de mezcla vertical evitada frente al azar para contar como grado fijo")
    ap.add_argument("--alfa-campos", type=float, default=0.01,
                    help="p máximo de la separación de campos (campos_haba.py) para contar como grado fijo; 1 = no se exige")
    ap.add_argument("--permutaciones-campos", type=int, default=500)
    ap.add_argument("--salida", default="outputs/bloques")
    a = ap.parse_args()

    archivos = sorted(BLOQUES_DIR.glob("*.json"))
    if not archivos:
        raise SystemExit("Falta references/corpus/bloques/: corre antes scripts/comparacion/corpus_bloques.py")
    canciones, vistos = [], set()
    for grupo, lista in (("banda", a.corridas), ("control", a.control), ("comparar", a.comparar)):
        for r in lista:
            if r.resolve() not in vistos:                                 # sin repetidas (globs que se solapan)
                vistos.add(r.resolve())
                canciones.append((r, grupo))
    R = {}
    for run, grupo in canciones:
        if (run / "armonia.json").exists() and (run / "line_diagnostics.json").exists():
            R[run] = rasgos_cancion(run)
        else:
            print(f"faltan armonia.json o line_diagnostics.json: {run}")
    eps = a.eps
    if eps is None:
        cs = [R[r]["cuartos"] for r in a.control if r in R and R[r]["cuartos"] is not None]
        eps = sum(cs) / len(cs) / 100 if cs else 0.11
    ms = [R[r]["metro"] for r in a.control if r in R and R[r]["metro"] is not None]
    error_metro = np.mean(ms, 0) if ms else np.array([0.862, 0.040, 0.009, 0.089, 0, 0])
    error_metro = error_metro.copy()
    error_metro[0] = 0.0                                                 # control en 4/4: todo lo que no es 2·4·8 es error
    origen = " (medido en el control)" if a.control else " (por defecto: Tommy the Cat)"
    print(f"modelo de medición: fuga a cuartos de tono ε = {eps:.3f}; compases mal leídos η = {error_metro.sum():.3f}{origen}")

    cc = [R[r]["concentracion"] for r in a.control if r in R and R[r]["concentracion"] is not None]
    media, de = (float(np.mean(cc)), max(float(np.std(cc, ddof=1)), 2.0)) if len(cc) >= 2 else CONTROL_CONC
    # Regla combinada de «grado fijo» en cuarto de tono. Las tres condiciones:
    # 1) concentración con z >= 2 frente al control; 2) al menos --min-segundos-cuartos de melodía en cuarto de tono
    #    (con 0.1 % del tiempo la concentración es ruido: Discipline); 3) separación de campos de Hába significativa
    #    (campos_haba.py): bajo y voz aguda evitan sonar en campos distintos al menos un --efecto-campos % más que el
    #    azar y con p < --alfa-campos. Hace falta el tamaño del efecto y no solo p: con muchos compases, un 7 % evitado
    #    (Level Five) ya da p = 0.002. 30 % ≈ el doble del máximo de Primus (14 %), el control sin cuartos de tono.
    # La 3) quita los falsos positivos que la concentración sola deja pasar (Red de King Crimson, confirmado de oído:
    # 25 % del tiempo «en ¼» por distorsión, sin cuartos de tono). El error de medición cae al azar entre bajo y guitarra;
    # un cuarto de tono fijo vive en una voz de forma estable. Se declara en el artículo: la medida es también un resultado.
    from campos_haba import medir as medir_campos
    rng = np.random.default_rng(0)
    for run, r in R.items():
        r["z_concentracion"] = round((r["concentracion"] - media) / de, 1) if r["concentracion"] is not None else None
        r["p_campos"] = None
        previo = bool(r["z_concentracion"] is not None and r["z_concentracion"] >= 2
                      and r.get("segundos_cuartos", 0) >= a.min_segundos_cuartos)
        if previo and a.alfa_campos < 1:
            try:
                c, _ = medir_campos(run, a.permutaciones_campos, rng)
                r["p_campos"], r["campos_evitada"] = c["p_mezcla"], (round(100 * (c["mezcla_nula"] - c["mezcla_vertical"]) / c["mezcla_nula"], 1)
                                                                    if c["mezcla_nula"] else None)
            except Exception as e:                                       # noqa: BLE001
                print(f"  sin prueba de campos para {run.name}: {e}")
        r["microtonal"] = bool(previo and (a.alfa_campos >= 1 or (r["p_campos"] is not None and r["p_campos"] < a.alfa_campos
                                                                  and (r.get("campos_evitada") or 0) >= a.efecto_campos)))
        r["microtono"] = solo_cuartos(r["alt24"]) if r["microtonal"] else None
    print(f"filtro de cuartos de tono: concentración del control {media:.1f} ± {de:.1f} %; cuenta si z ≥ 2, "
          f"hay al menos {a.min_segundos_cuartos:g} s en cuarto de tono y la separación de campos evita ≥ {a.efecto_campos:g} % con p < {a.alfa_campos:g}")

    corpora = {}
    for f in archivos:
        c = Corpus(f, eps, a.k, a.maximo, error_metro)
        if c.bloques():
            corpora[c.nombre] = c
            print(f"  {c.nombre:14s} {c.familia:10s} bloques: {', '.join(c.bloques())}")

    filas = []
    for run, grupo in canciones:
        ctl = grupo != "banda"
        if run not in R:
            continue
        r = R[run]
        dist = {n: c.medir(r) for n, c in corpora.items()}
        por = {n: c.percentiles(dist[n]) for n, c in corpora.items()}
        conj = {n: c.conjunto(dist[n]) for n, c in corpora.items()}
        v = veredicto(por, conj, corpora, a.umbral, a.min_piezas, r["microtonal"])
        f = dict(corrida=run.name, cancion=nombre(run.name), control=ctl, grupo=grupo, voz=r["voz"], cuartos_de_tono=r["cuartos"],
                 concentracion=r["concentracion"], z_concentracion=r["z_concentracion"], microtonal=r["microtonal"],
                 segundos_cuartos=r.get("segundos_cuartos"), p_campos=r.get("p_campos"), campos_evitada=r.get("campos_evitada"),
                 percentiles={n: {b: round(x, 1) for b, x in p.items()} for n, p in por.items()},
                 conjunto={n: (None if x is None else round(x, 1)) for n, (x, _) in conj.items()}, **v)
        filas.append(f)
        mb = " · ".join(f"{TITULO[b].split(' ')[0]}←{m['corpus']} {m['percentil']:g}" for b, m in v["mejor_por_bloque"].items())
        mb += f" · ¼ tono {r['cuartos']:g} % ({r.get('segundos_cuartos', 0):g} s), concentración {r['concentracion']:g} % (z {r['z_concentracion']:g})"
        if r.get("p_campos") is not None:
            mb += f", campos evitados {r.get('campos_evitada')} % (p {r['p_campos']:g})"
        print(f"{ {'banda': '', 'control': '[control] ', 'comparar': '[comparado] '}[grupo]}{f['cancion']}: {mb} | conjunto {v['conjunto_mejor']['corpus']} {v['conjunto_mejor']['percentil']} → {v['veredicto']}")

    # canción más parecida de cada grupo de comparación, por bloque (distancia de Jensen-Shannon entre canciones)
    parecidas = []
    grupos_ref = {g: [r for r, gg in canciones if gg == g and r in R] for g in ("comparar", "control")}
    if grupos_ref["comparar"]:
        def d_bloque(x: dict, y: dict, b: str) -> float | None:
            if b == "armonia":
                if x["fundamentales"] is None or y["fundamentales"] is None:
                    return None
                d = float(js_pares(x["fundamentales"][None], y["fundamentales"][None])[0, 0])
                if x["cambios_v"] is not None and y["cambios_v"] is not None:
                    d = (d + float(js_pares(x["cambios_v"][None], y["cambios_v"][None])[0, 0])) / 2
                return d
            k = {"escala": "escala", "microtono": "alt24", "metro": "metro"}[b]
            if x[k] is None or y[k] is None:
                return None
            if b == "microtono":                                         # solo qué grados en ¼ de tono se usan
                return float(js_pares(solo_cuartos(x[k])[None], solo_cuartos(y[k])[None])[0, 0])
            return float(js_pares(x[k][None], y[k][None])[0, 0])
        print("\nCanción más parecida por bloque (distancia de Jensen-Shannon; 0 = igual):")
        for run, grupo in canciones:
            if grupo != "banda" or run not in R:
                continue
            fila = dict(cancion=nombre(run.name))
            partes = []
            for b in BLOQUES:
                for g in ("comparar", "control"):
                    ds = [(d_bloque(R[run], R[o], b), nombre(o.name)) for o in grupos_ref[g]]
                    ds = [x for x in ds if x[0] is not None]
                    if ds:
                        d, n = min(ds)
                        fila[f"{b}_{g}"] = n
                        fila[f"{b}_{g}_distancia"] = round(d, 3)
                if f"{b}_comparar" in fila:
                    partes.append(f"{TITULO[b].split(' ')[0]}: {fila[f'{b}_comparar']} {fila[f'{b}_comparar_distancia']:.2f}"
                                  + (f" (control {fila[f'{b}_control']} {fila[f'{b}_control_distancia']:.2f})" if f"{b}_control" in fila else ""))
            parecidas.append(fila)
            print(f"  {fila['cancion']}: " + " · ".join(partes))
        with open(a.salida + "_parecidas.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=sorted({k for f in parecidas for k in f}, key=lambda k: (k != "cancion", k)))
            w.writeheader()
            w.writerows(parecidas)

    # calibración: piezas reales de los corpus con los tres bloques
    calib = {}
    for n, c in corpora.items():
        if len(c.bloques()) < 3:
            continue
        tipos = {}
        for i in range(c.n):
            ps, cj = c.pieza(i)
            if len(ps) < 3:
                continue
            r = c.rasgos(i)
            dist = {m: d.medir(r) for m, d in corpora.items() if m != n}
            por = {n: ps, **{m: d.percentiles(dist[m]) for m, d in corpora.items() if m != n}}
            conj = {n: cj, **{m: d.conjunto(dist[m]) for m, d in corpora.items() if m != n}}
            v = veredicto(por, conj, corpora, a.umbral, a.min_piezas, False)
            tipos[v["tipo"]] = tipos.get(v["tipo"], 0) + 1
        tot = sum(tipos.values())
        if tot:
            calib[n] = {k: round(100 * x / tot, 1) for k, x in sorted(tipos.items())} | {"piezas": tot}
            print(f"calibración en {n} ({tot} piezas reales): " + " · ".join(f"{k} {x}%" for k, x in calib[n].items() if k != "piezas"))

    Path(a.salida + ".json").write_text(json.dumps(dict(umbral=a.umbral, eps=round(eps, 4), control_concentracion=[round(media, 1), round(de, 1)], error_metro=[round(float(x), 4) for x in error_metro], k=a.k, canciones=filas, parecidas=parecidas, calibracion=calib,
                                                        corpus={n: dict(familia=c.familia, fuente=c.fuente, bloques=c.bloques(), piezas=c.n)
                                                                for n, c in corpora.items()}), ensure_ascii=False, indent=1), encoding="utf-8")
    with open(a.salida + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        cols = [(n, b) for n, c in corpora.items() for b in c.bloques()]
        w.writerow(["cancion", "control", "veredicto", "cuartos_de_tono", "concentracion", "z_concentracion"] + [f"{b}_{n}" for n, b in cols] +
                   [f"conjunto_{n}" for n in corpora])
        for f in filas:
            w.writerow([f["cancion"], f["control"], f["veredicto"], f["cuartos_de_tono"], f["concentracion"], f["z_concentracion"]] + [f["percentiles"][n].get(b, "") for n, b in cols] +
                       ["" if f["conjunto"][n] is None else f["conjunto"][n] for n in corpora])
    dibujar(filas, corpora, calib, a.umbral, eps, float(error_metro.sum()), a.salida, (media, de))


# ───────────────────────── gráficas ─────────────────────────
def dibujar(filas: list[dict], corpora: dict, calib: dict, u: float, eps: float, eta: float, salida: str, ctl: tuple) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    tinta, gris, fondo, rejilla = "#0b0b0b", "#52514e", "#fcfcfb", "#e4e3df"
    cmap = LinearSegmentedColormap.from_list("azul", ["#f1f0ea", "#a9c8ef", "#2a78d6", "#0d3c78"])
    grupos = [(b, [n for n, c in corpora.items() if b in c.bloques()]) for b in BLOQUES] + [("conjunto", [n for n, c in corpora.items() if len(c.bloques()) >= 2])]
    cols = [(g, n) for g, ns in grupos for n in ns]
    M = np.full((len(filas), len(cols)), np.nan)
    for i, f in enumerate(filas):
        for j, (g, n) in enumerate(cols):
            x = f["conjunto"].get(n) if g == "conjunto" else f["percentiles"][n].get(g)
            if x is not None:
                M[i, j] = x
    fig, ax = plt.subplots(figsize=(2.8 + 0.95 * len(cols), 3.6 + 0.55 * len(filas)), facecolor=fondo)
    imagen = ax.imshow(np.nan_to_num(M, nan=0), cmap=cmap, vmin=0, vmax=100, aspect="auto")
    barra = fig.colorbar(imagen, ax=ax, fraction=0.018, pad=0.025, shrink=0.88, anchor=(0.0, 0.78), ticks=[0, 25, 50, 75, 100])
    barra.set_label("Verosimilitud / percentil (%)", color=gris, fontsize=9, labelpad=10)
    barra.ax.tick_params(labelsize=8, colors=gris)
    for i in range(len(filas)):
        for j in range(len(cols)):
            v = M[i, j]
            if np.isnan(v):
                ax.add_patch(plt.Rectangle((j - .5, i - .5), 1, 1, color=fondo))
                ax.text(j, i, "—", ha="center", va="center", fontsize=9, color=gris)
            else:
                ax.text(j, i, f"{v:.0f}" if v >= 1 else f"{v:.1f}", ha="center", va="center", fontsize=9.5,
                        fontweight="bold" if v >= u else "normal", color="#ffffff" if v >= 30 else tinta)
    x0 = 0
    for g, ns in grupos:
        if ns:
            ax.text(x0 + (len(ns) - 1) / 2, -1.25, TITULO.get(g, "Conjunto"), ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=tinta)
            if x0:
                ax.axvline(x0 - .5, color=fondo, lw=4)
        x0 += len(ns)
    def cobertura(c, bloque: str) -> int:
        if bloque == "conjunto":
            return sum(all(p.get(b) for b in BLOQUES if b in c.bloques()) for p in c.P)
        clave = {"armonia": "fundamentales", "escala": "altura", "microtono": "altura", "metro": "metro"}[bloque]
        return sum(bool(p.get(clave)) and (bloque != "microtono" or c.micro) for p in c.P)

    # Fila inferior alineada con cada columna: cobertura real del corpus para ese bloque.
    for j, (g, n) in enumerate(cols):
        ax.text(j, len(filas) + 0.58, f"n={cobertura(corpora[n], g)}", ha="center", va="top", fontsize=8.5, color=gris)
    ax.set_xticks(range(len(cols)), [n + ("*" if corpora[n].n < 100 else "") for g, n in cols], fontsize=8.5, color=tinta, rotation=0)
    ax.set_yticks(range(len(filas)), [MARCA[f["grupo"]] + f["cancion"] for f in filas], fontsize=10, color=tinta)
    for i, f in enumerate(filas):
        if i and f["grupo"] != filas[i - 1]["grupo"]:
            ax.axhline(i - .5, color=fondo, lw=4)
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlabel("Bloque de rasgo y corpus de comparación", color=gris, fontsize=11, labelpad=28)
    ax.set_ylabel("Canción", color=gris, fontsize=10, labelpad=8)
    fig.suptitle("Verosimilitud por bloque de rasgos y conjunta", x=0.5, y=0.98, ha="center",
                 fontsize=16, fontweight="bold", color=tinta)
    descripcion = (
        "Verosimilitud por bloque = qué tan habitual es cada rasgo de la banda frente a piezas reales de cada corpus.\n"
        "La casilla conjunta pregunta si algún corpus explica a la vez la armonía, la escala, los cuartos de tono y el metro."
    )
    nota = (
        "★ Banda\n\n◆ Control: Primus\n\n"
        + ("▲ Repertorio comparado\n\n" if any(f["grupo"] == "comparar" for f in filas) else "")
        + "— Sin datos para ese bloque\n\n"
        "* Corpus con menos de 100 piezas: no cuenta para el veredicto\n\n"
        f"ε = {eps:.2f}: fuga de medición hacia ¼ de tono\n"
        f"η = {eta:.2f}: error de lectura del metro"
    )
    fig.text(0.5, 0.945, descripcion, ha="center", va="top", fontsize=10.2, color=gris, linespacing=1.15)
    fig.text(0.01, 0.025, nota + "\n\nn = piezas del corpus con datos válidos para el bloque de la columna superior.", ha="left", va="bottom", fontsize=8.2, color=gris, linespacing=1.15)
    fig.subplots_adjust(left=0.13, right=0.995, top=0.84, bottom=0.30)
    fig.savefig(salida + "_bloques.png", dpi=200, facecolor=fondo)
    plt.close(fig)

    # síntesis: por canción, de qué corpus viene cada bloque (fichas del color de la familia) y el veredicto
    fig, ax = plt.subplots(figsize=(17.0, 3.7 + 0.68 * len(filas)), facecolor=fondo)
    ax.set_xlim(0, 16.1)
    ax.set_ylim(len(filas) + 0.2, -1.2)
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, -1.02), 15.95, len(filas) + 1.12, facecolor="#f7f7f4",
                               edgecolor="#d9d8d2", lw=1.0, zorder=0))
    xs = {"armonia": 3.55, "escala": 5.75, "microtono": 7.95, "metro": 10.15}
    for b, x in xs.items():
        ax.text(x, -0.68, TITULO[b], ha="center", fontsize=10.5, fontweight="bold", color=tinta)
    ax.text(12.45, -0.68, "Conjunto (mejor)", ha="center", fontsize=10.5, fontweight="bold", color=tinta)
    ax.text(13.75, -0.68, "Veredicto", ha="left", fontsize=10.5, fontweight="bold", color=tinta)
    for i, f in enumerate(filas):
        corto = f["cancion"] if len(f["cancion"]) <= 20 else f["cancion"][:19] + "…"
        ax.text(0.1, i, MARCA[f["grupo"]] + corto, va="center", fontsize=10, color=tinta)
        for b, x in xs.items():
            m = f["mejor_por_bloque"].get(b)
            if b == "microtono" and not m:
                rosa = FAMILIA_COLOR["microtonal"]
                if f["microtonal"]:                                      # grado fijo y sin corpus con qué comparar
                    ax.add_patch(plt.Rectangle((x - 0.95, i - 0.3), 1.9, 0.6, facecolor=fondo, edgecolor=rosa, lw=1.6, ls="--"))
                    ax.text(x, i, f"grado fijo (z {f['z_concentracion']:g})", ha="center", va="center", fontsize=8.5, color=tinta)
                else:
                    ax.text(x, i, f"como el control (z {f['z_concentracion']:g})", ha="center", va="center", fontsize=8.5, color=gris)
                continue
            if not m:
                ax.text(x, i, "—", ha="center", va="center", color=gris)
                continue
            col = FAMILIA_COLOR.get(corpora[m["corpus"]].familia, "#6250d6")
            ok = m["percentil"] >= u
            ax.add_patch(plt.Rectangle((x - 0.95, i - 0.3), 1.9, 0.6, facecolor=col if ok else fondo, edgecolor=col, lw=1.6))
            ax.text(x, i, f"{m['corpus']} {m['percentil']:g}", ha="center", va="center", fontsize=8.8, color="#ffffff" if ok else tinta,
                    fontweight="bold" if ok else "normal")
        cm = f["conjunto_mejor"]
        ax.text(12.45, i, "—" if cm["percentil"] is None else f"{cm['corpus']} {cm['percentil']:g}", ha="center", va="center", fontsize=9,
                color=tinta, fontweight="bold" if (cm["percentil"] or 0) >= u else "normal")
        veredicto_visible = (f["veredicto"].replace(" (conjunto con menos bloques: ningún corpus los tiene todos)", "")
                            .replace("rasgo sin vecino: ", "SIN VECINO: ")
                            .replace("síntesis de lenguajes existentes", "SÍNTESIS DE LENGUAJES EXISTENTES")
                            .replace("estilo existente (", "ESTILO EXISTENTE (")
                            .replace("variante atípica de ", "VARIANTE ATÍPICA DE "))
        import textwrap
        veredicto_envuelto = textwrap.fill(veredicto_visible.replace(": ", ":\n"), width=25, replace_whitespace=False)
        ax.text(13.72, i, veredicto_envuelto,
                va="center", fontsize=7.8, color=tinta, linespacing=1.05, wrap=True)
    fams = sorted({c.familia for c in corpora.values()})
    fig.suptitle("Lenguaje más probable para cada bloque de rasgos", x=0.5, y=0.98, ha="center",
                 fontsize=16, fontweight="bold", color=tinta)
    descripcion = (
        "Cada casilla identifica el corpus cuyo perfil se parece más a ese rasgo de la banda.\n"
        "La columna conjunta comprueba si un mismo corpus explica varios rasgos a la vez."
    )
    nota = (
        f"CUARTOS DE TONO / CONTROL: z compara la concentración de la banda con Primus ({ctl[0]:.0f} ± {ctl[1]:.0f} %).\n"
        "Como el control = la concentración no supera el umbral de grado fijo; no se interpreta como escala microtonal.\n\n"
        "CASILLA VACÍA = hay datos, pero el percentil queda bajo el umbral.  — = no hay datos comparables.\n\n"
        "VEREDICTOS: ESTILO EXISTENTE = un corpus explica la combinación.\n"
        "SÍNTESIS DE LENGUAJES EXISTENTES = distintos corpus explican bloques distintos.\n"
        "SIN VECINO = algún bloque no tiene un corpus suficientemente parecido."
    )
    fig.text(0.04, 0.945, descripcion, ha="left", va="top", fontsize=10.2, color=gris, linespacing=1.15)
    fig.text(0.04, 0.855, nota, fontsize=9.2, color=gris, linespacing=1.15, va="top")
    fig.legend(handles=[plt.Line2D([0], [0], color=FAMILIA_COLOR.get(fam, "#6250d6"), lw=8, label=fam) for fam in fams],
               loc="upper right", bbox_to_anchor=(0.98, 0.88), ncol=1, frameon=False, fontsize=8.8,
               title="Paleta de corpus", title_fontsize=9.5)
    fig.subplots_adjust(left=0.04, right=0.99, top=0.78, bottom=0.29)
    fig.savefig(salida + "_sintesis.png", dpi=200, facecolor=fondo)
    plt.close(fig)


if __name__ == "__main__":
    main()
