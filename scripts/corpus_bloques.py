"""Pasa cada corpus de estilo a tres bloques de rasgos por pieza, para el test de verosimilitud por bloques.

Uso:
    python scripts/corpus_bloques.py                               # los que ya están en el repo (RS 200, Kostka-Payne, iRealPro, pop)
    python scripts/corpus_bloques.py --hooktheory Hooktheory.json.gz
    python scripts/corpus_bloques.py --symbtr SymbTr/txt
    python scripts/corpus_bloques.py --musicxml arab-andalusian-music/scores-musicxml --nombre andalusi --familia microtonal
    python scripts/corpus_bloques.py --midi RadifCorpus --nombre radif --familia microtonal --sin-metro
    python scripts/corpus_bloques.py --kern essen-folksong-collection --nombre essen --familia folk
    python scripts/corpus_bloques.py --session TheSession-data/csv/tunes.csv
    python scripts/corpus_bloques.py --wjd wjazzd.db [--tipos MODAL,BLUES --nombre wjd_modal]
    python scripts/corpus_bloques.py --dcml distant_listening_corpus/debussy_suite_bergamasque --nombre debussy --familia clasica
    python scripts/corpus_bloques.py --chordonomicon chordonomicon.csv --subgeneros "progressive rock,math rock,funk metal" --nombre prog

Escribe references/corpus/bloques/<nombre>.json con, por pieza (lo que el corpus tenga; lo que no, null):
- armonía: «fundamentales» (12 grados respecto de la tónica, por duración) y «cambios» (pares de fundamentales seguidas);
- altura: «altura», 24 grados (cuartos de tono) respecto de la tónica, por duración; un corpus de 12 notas usa solo los
  grados pares;
- metro: «metro», reparto del tiempo por familia de compás: 2·4·8 | 3·6·12 | 5 | 7 | 9 | otro impar.
Los compases compuestos occidentales (6/8, 9/8, 12/8) cuentan en negras con puntillo (2, 3, 4 pulsos). Los usul turcos
cuentan en su unidad (aksak 9, curcuna 10, devr-i hindî 7).

Solo se publican en el repo estos resúmenes, nunca los datos crudos (varios corpus son CC BY-NC o se piden por correo).
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
import sqlite3
import sys
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_estilos import LETRA, leer_har, leer_jazz, leer_kp, leer_pop, raiz_romana, resumen  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
RAW = RAIZ / "references" / "corpus" / "raw"
DEST = RAIZ / "references" / "corpus" / "bloques"
FAMILIAS_METRO = ["2·4·8", "3·6·12", "5", "7", "9", "otro impar"]


# ───────────────────────── utilidades comunes ─────────────────────────
def familia_metro(pulsos: int) -> int:
    n = max(1, int(pulsos))
    while n % 2 == 0 and n > 1:
        n //= 2
    return {1: 0, 3: 1, 5: 2, 7: 3, 9: 4}.get(n, 5)


def pulsos_compas(num: int, den: int) -> int:
    """Pulsos de un compás occidental: los compuestos (6/8, 9/8, 12/8, 6/16…) en negras con puntillo."""
    if den >= 8 and num in (6, 9, 12):
        return num // 3
    return num


def normaliza(v: list[float]) -> list[float] | None:
    s = sum(v)
    return [round(x / s, 5) for x in v] if s > 0 else None


def pieza(id_: str, seq_armonia=None, altura24=None, metro=None) -> dict:
    p = dict(id=id_, fundamentales=None, cambios=None, altura=None, metro=None)
    if seq_armonia and len(seq_armonia) >= 4:
        p.update(resumen(seq_armonia))
    if altura24 is not None:
        p["altura"] = normaliza(altura24)
    if metro is not None:
        p["metro"] = normaliza(metro)
    return p


def escribir(nombre: str, familia: str, fuente: str, piezas: list[dict], licencia: str = "") -> None:
    piezas = [p for p in piezas if p["fundamentales"] or p["altura"] or p["metro"]]
    DEST.mkdir(parents=True, exist_ok=True)
    cuenta = {b: sum(1 for p in piezas if p[k]) for b, k in (("armonia", "fundamentales"), ("altura", "altura"), ("metro", "metro"))}
    (DEST / f"{nombre}.json").write_text(json.dumps(dict(nombre=nombre, familia=familia, fuente=fuente, licencia=licencia,
                                                         piezas_por_bloque=cuenta, piezas=piezas), ensure_ascii=False), encoding="utf-8")
    print(f"{nombre} ({familia}): {len(piezas)} piezas · armonía {cuenta['armonia']} · altura {cuenta['altura']} · metro {cuenta['metro']}"
          f" → {DEST / (nombre + '.json')}")


def tonica_de(nombre: str) -> int | None:
    """«Eb», «F#», «Bb-maj», «C-min», «Edorian», «Cs» → 0-11."""
    m = re.match(r"\s*([A-Ga-g])([#♯sb♭-]?)", nombre or "")
    if not m:
        return None
    acc = m.group(2)
    return (LETRA[m.group(1).upper()] + (1 if acc in "#♯s" and acc else -1 if acc in "b♭-" and acc else 0)) % 12


def sin_tildes(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.replace("ı", "i")).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", s.lower())


# ───────────────────────── RS 200 (ya en el repo) ─────────────────────────
GRADO_MAYOR = [0, 2, 4, 5, 7, 9, 11]


def leer_mel(path: Path) -> list[float]:
    """Melodía del RS 200 (.mel) → 24 grados por duración. Dígitos 1-7 = grados de la escala mayor de la tonalidad del
    momento, alterados por la firma «[..b...b]» (b3 y b7 por defecto) y por b/#/n delante. Cada tiempo del compás se
    reparte en partes iguales entre sus símbolos; «.» y «=» sostienen la nota anterior; «_», «-» y R son silencio."""
    v = [0.0] * 24
    firma = [0] * 7
    actual = None
    for linea in path.read_text(encoding="latin-1").splitlines():
        linea = linea.split("%")[0]
        for etiqueta in re.findall(r"\[([^\]]*)\]", linea):
            if re.fullmatch(r"[.b#]{7}", etiqueta):
                firma = [-1 if c == "b" else 1 if c == "#" else 0 for c in etiqueta]
            elif re.fullmatch(r"[A-G][b#]?", etiqueta):
                firma = [0] * 7                                       # cambio de tonalidad: vuelve a mayor salvo nueva firma
        linea = re.sub(r"\[[^\]]*\]", " ", linea)
        for compas in linea.split("|"):
            tiempos = compas.split()
            for t in tiempos:
                if re.fullmatch(r"R(\*\d+)?", t):
                    actual = None
                    continue
                if t == "=":
                    if actual is not None:
                        v[actual] += 1.0
                    continue
                if t in ("_", "-"):
                    actual = None
                    continue
                simbolos = re.findall(r"[\^v]*[b#n]?[1-7]|\.|_|-", t)
                if not simbolos:
                    continue
                w = 1.0 / len(simbolos)
                for s in simbolos:
                    if s == ".":
                        if actual is not None:
                            v[actual] += w
                        continue
                    if s in "_-":
                        actual = None
                        continue
                    m = re.fullmatch(r"[\^v]*([b#n]?)([1-7])", s)
                    g = int(m.group(2)) - 1
                    alt = {"b": -1, "#": 1, "n": 0}.get(m.group(1), firma[g])
                    actual = (2 * (GRADO_MAYOR[g] + alt)) % 24
                    v[actual] += w
    return v


def metro_har(path: Path) -> list[float] | None:
    """Reparto por familia de compás de un .har del RS 200 (lee las marcas «[3/4]», «[12/8]» de la secuencia expandida)."""
    defs = {}
    for linea in path.read_text(encoding="latin-1").splitlines():
        linea = linea.split("%")[0].strip()
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", linea)
        if m:
            defs[m.group(1)] = m.group(2)

    def expandir(texto: str, prof: int = 0) -> list[str]:
        out = []
        for tok in texto.split():
            m = re.fullmatch(r"\$([A-Za-z0-9_]+)(?:\*(\d+))?", tok)
            if m and prof < 20:
                out += expandir(defs.get(m.group(1), ""), prof + 1) * int(m.group(2) or 1)
            else:
                out.append(tok)
        return out

    v = [0.0] * 6
    num, den = 4, 4
    for tok in expandir(defs.get("S", "")):
        m = re.fullmatch(r"\[(\d+)/(\d+)\]", tok)
        if m:
            num, den = int(m.group(1)), int(m.group(2))
            continue
        m = re.fullmatch(r"\|(?:\*(\d+))?", tok)
        if m:
            p = pulsos_compas(num, den)
            v[familia_metro(p)] += p * int(m.group(1) or 1)
    return v if sum(v) else None


def metro_jazz(path: Path) -> list[float] | None:
    v = [0.0] * 6
    actual = None
    for linea in path.read_text(encoding="latin-1").splitlines():
        m = re.match(r"^\*M(\d+)/(\d+)", linea.strip())
        if m:
            actual = pulsos_compas(int(m.group(1)), int(m.group(2)))
        elif linea.startswith("=") and actual:
            v[familia_metro(actual)] += actual
    return v if sum(v) else None


def incluidos() -> None:
    rs = RAW / "rock_corpus_v2-1"
    piezas = []
    for f in sorted((rs / "rs200_harmony").glob("*.har")):
        cancion = re.sub(r"_(dt|tdc)$", "", f.stem)
        mel = next((m for m in (rs / "rs200_melody").glob(f"{cancion}_*.mel")), None)
        piezas.append(pieza(f.stem, leer_har(f), leer_mel(mel) if mel else None, metro_har(f)))
    escribir("rock", "rock/pop", "Rolling Stone 200 (de Clercq y Temperley 2011): armonía de dos analistas, melodía y compases", piezas,
             "uso académico")
    piezas = [pieza(n, seq) for n, seq in leer_kp(RAW / "kostka_payne" / "kp-chord-list-2").items()]
    escribir("clasica", "clasica", "Kostka-Payne (Temperley 2009): solo armonía", piezas, "uso académico")
    piezas = [pieza(f.stem, leer_jazz(f), None, metro_jazz(f)) for f in sorted((RAW / "irealb-v1.0" / "iRb_v1-0").glob("*.jazz"))]
    escribir("jazz", "jazz", "iRealPro (Shanahan y Broze 2017): armonía y compases", piezas, "CC BY-NC-SA")
    pop = RAIZ / "references" / "corpus" / "albumes_progresiones.csv"
    if pop.exists():
        escribir("pop", "rock/pop", "9 álbumes de Hooktheory (bucles): solo armonía", [pieza(k, s) for k, s in leer_pop(pop).items()])


# ───────────────────────── Hooktheory (SheetSage) ─────────────────────────
def hooktheory(path: Path, nombre: str) -> None:
    """Hooktheory.json.gz de github.com/chrisdonahue/sheetsage: por id, annotations{keys, meters, harmony, melody} en tiempos."""
    with gzip.open(path, "rt", encoding="utf-8") if path.suffix == ".gz" else open(path, encoding="utf-8") as fh:
        D = json.load(fh)
    piezas = []
    for id_, x in D.items():
        a = x.get("annotations") or x
        keys = sorted(a.get("keys") or [], key=lambda k: k.get("beat", 0))
        if not keys:
            continue
        def tonica(b: float) -> int:
            ks = [k for k in keys if k.get("beat", 0) <= b + 1e-6]
            return (ks[-1] if ks else keys[0])["tonic_pitch_class"]

        seq = [((h["root_pitch_class"] - tonica(h["onset"])) % 12, h["offset"] - h["onset"]) for h in a.get("harmony") or []
               if h.get("root_pitch_class") is not None and h["offset"] > h["onset"]]
        alt = [0.0] * 24
        for n in a.get("melody") or []:
            if n.get("pitch_class") is not None and n["offset"] > n["onset"]:
                alt[(2 * (n["pitch_class"] - tonica(n["onset"]))) % 24] += n["offset"] - n["onset"]
        met = [0.0] * 6
        ms = sorted(a.get("meters") or [], key=lambda m: m.get("beat", 0))
        fin = a.get("num_beats") or (max([h["offset"] for h in a.get("harmony") or []] + [0]))
        for i, m in enumerate(ms):
            hasta = ms[i + 1]["beat"] if i + 1 < len(ms) else fin
            p = pulsos_compas(m.get("beats_per_bar", 4), m.get("beat_unit", 4))
            met[familia_metro(p)] += max(0.0, hasta - m.get("beat", 0))
        piezas.append(pieza(id_, seq, alt if sum(alt) else None, met if sum(met) else None))
    escribir(nombre, "rock/pop", "Hooktheory / SheetSage (Donahue et al. 2022)", piezas, "CC BY-NC-SA 3.0")


# ───────────────────────── SymbTr (makam turco) ─────────────────────────
USUL = {"aksak": 9, "agiraksak": 9, "raksaksagi": 9, "evfer": 9, "oynak": 9, "curcuna": 10, "kapalicurcuna": 10, "aksaksemai": 10,
        "devrihindi": 7, "devrituran": 7, "turkaksagi": 5, "duyek": 8, "agirduyek": 8, "musemmen": 8, "ciftesofyan": 8, "sofyan": 4,
        "nimsofyan": 2, "semai": 3, "senginsemai": 6, "yuruksemai": 6, "agirsenginsemai": 6, "frenkcin": 12, "fahte": 20,
        "devrikebir": 28, "remel": 28, "muhammes": 32, "hafif": 32, "berefsan": 32, "nimsakil": 24, "nimhafif": 16,
        "cifteduyek": 16, "nimdevir": 18, "devirrevan": 13, "devrirevan": 13, "sarkidevrirevani": 13, "yuruksemaiii": 6, "azeriyuruksemai": 6,
        "agiraksaksemai": 10, "agirevfer": 9, "musemmenii": 8, "cenber": 24, "agircenber": 24, "darbifetih": 88, "zencir": 120, "lenkfahte": 10, "nimevsat": 10, "evsat": 26,
        "darbeyn": 0, "serbest": 0, "usulsuz": 0}


def a_24(cents: float, suave: float) -> list[tuple[int, float]]:
    """Reparte una altura en cents (respecto de la tónica) entre los 24 grados: redondeo, o gaussiana de ancho `suave`."""
    if not suave:
        return [(round(cents / 50) % 24, 1.0)]
    pesos = []
    for b in range(24):
        d = abs((cents - 50 * b + 600) % 1200 - 600)
        if d < 3 * suave:
            pesos.append((b, pow(2.718281828, -d * d / (2 * suave * suave))))
    s = sum(w for _, w in pesos)
    return [(b, w / s) for b, w in pesos]


def symbtr(carpeta: Path, nombre: str, suave: float = 0.0) -> None:
    """SymbTr txt (Karaosmanoğlu 2012): columnas Kod, Koma53 (altura en comas de Holder, 53 por octava), Pay/Payda
    (duración). Tónica = última nota (karar). El usul sale del nombre del archivo «makam--forma--usul--nombre--compositor».
    Las alturas pasan a cents (1 coma = 1200/53) y de ahí a 24 grados. Ojo: en la notación Arel-Ezgi-Uzdilek casi todos
    los grados «neutros» caen más cerca de un semitono que de un cuarto de tono (segâh en uşşak: 8 comas = 181 cents), así
    que el redondeo los vuelve 12-EDO. Con --suave σ cada nota se reparte con una gaussiana de σ cents entre los grados
    vecinos; correr con 0 y con 25 y ver si cambia la conclusión."""
    piezas, sin_usul = [], defaultdict(int)
    for f in sorted(carpeta.glob("*.txt")):
        filas = list(csv.DictReader(open(f, encoding="utf-8", errors="replace"), delimiter="\t"))
        notas = []
        for r in filas:
            try:
                k, pay, payda = int(float(r.get("Koma53") or -1)), float(r.get("Pay") or 0), float(r.get("Payda") or 0)
            except ValueError:
                continue
            if k > 0 and pay > 0 and payda > 0:
                notas.append((k, pay / payda))
        if len(notas) < 8:
            continue
        ton = notas[-1][0] % 53
        alt = [0.0] * 24
        for k, d in notas:
            for b, w in a_24(((k - ton) % 53) * 1200 / 53, suave):
                alt[b] += d * w
        partes = f.stem.split("--")
        usul = sin_tildes(partes[2]) if len(partes) > 2 else ""
        met = None
        if USUL.get(usul):
            met = [0.0] * 6
            met[familia_metro(USUL[usul])] = 1.0
        elif usul:
            sin_usul[usul] += 1
        piezas.append(pieza(f.stem, None, alt, met))
    if sin_usul:
        print("usul sin tabla (sin metro):", dict(sorted(sin_usul.items(), key=lambda kv: -kv[1])[:15]))
    escribir(nombre, "microtonal", f"SymbTr (Karaosmanoğlu 2012), 53 comas → cents → 24 grados ({'gaussiana σ = %g cents' % suave if suave else 'redondeo'})",
             piezas, "CC BY-NC-SA 4.0")


# ───────────────────────── MusicXML genérico (andalusí, Radif, SymbTr xml…) ─────────────────────────
PASO = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def leer_musicxml(path: Path, tonica: str, sin_metro: bool) -> dict | None:
    try:
        raiz = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    for e in raiz.iter():                                             # quita espacios de nombres
        if "}" in e.tag:
            e.tag = e.tag.split("}", 1)[1]
    parte = raiz.find("part")
    if parte is None:
        return None
    div, num, den = 1.0, 4, 4
    notas, met = [], [0.0] * 6
    clave = None
    for compas in parte.findall("measure"):
        at = compas.find("attributes")
        if at is not None:
            if at.findtext("divisions"):
                div = float(at.findtext("divisions"))
            t = at.find("time")
            if t is not None and t.findtext("beats") and t.findtext("beat-type"):
                try:
                    num, den = int(t.findtext("beats").split("+")[0]), int(t.findtext("beat-type"))
                except ValueError:
                    pass
            k = at.find("key")
            if k is not None and k.findtext("fifths") is not None and clave is None:
                clave = (int(k.findtext("fifths")) * 7 + (9 if (k.findtext("mode") or "").lower() == "minor" else 0)) % 12
        largo = 0.0
        for n in compas.findall("note"):
            if n.find("grace") is not None:
                continue
            d = float(n.findtext("duration") or 0) / div
            if n.find("chord") is None:
                largo += d
            p = n.find("pitch")
            if p is None or d <= 0:
                continue
            q = 2 * (PASO[p.findtext("step")] + float(p.findtext("alter") or 0) + 12 * int(p.findtext("octave") or 4))
            notas.append((round(q), d))
        if largo > 0:
            met[familia_metro(pulsos_compas(num, den))] += largo
    if len(notas) < 8:
        return None
    ton = {"final": notas[-1][0] % 24, "primera": notas[0][0] % 24}.get(tonica, (2 * clave) if clave is not None else notas[-1][0] % 24)
    alt = [0.0] * 24
    for q, d in notas:
        alt[(q - ton) % 24] += d
    return dict(altura=alt, metro=None if sin_metro else met)


def musicxml(carpeta: Path, nombre: str, familia: str, tonica: str, sin_metro: bool) -> None:
    piezas = []
    for f in sorted(list(carpeta.rglob("*.xml")) + list(carpeta.rglob("*.musicxml"))):
        r = leer_musicxml(f, tonica, sin_metro)
        if r:
            piezas.append(pieza(f.stem, None, r["altura"], r["metro"]))
    escribir(nombre, familia, f"MusicXML de {carpeta.name} (tónica: {tonica})", piezas)


# ───────────────────────── MIDI con pitch bend (Radif) ─────────────────────────
def leer_midi(path: Path, rango_bend: float = 2.0) -> dict | None:
    """MIDI estándar sin librerías. Altura = nota + pitch bend del canal (rango ±`rango_bend` semitonos), en cuartos de
    tono. En el Radif el koron es «un semitono abajo + bend de 2048» = ¼ de tono exacto. Duración en ticks; compases
    desde los eventos de compás (0xFF 0x58). Tónica = última nota."""
    datos = path.read_bytes()
    if datos[:4] != b"MThd":
        return None
    ntracks = int.from_bytes(datos[10:12], "big")
    pos = 8 + int.from_bytes(datos[4:8], "big")
    eventos = []                                                       # (tick, tipo, canal, a, b)
    for _ in range(ntracks):
        if datos[pos:pos + 4] != b"MTrk":
            break
        fin = pos + 8 + int.from_bytes(datos[pos + 4:pos + 8], "big")
        i, tick, estado = pos + 8, 0, 0
        while i < fin:
            delta = 0
            while True:
                c = datos[i]; i += 1
                delta = (delta << 7) | (c & 0x7F)
                if c < 0x80:
                    break
            tick += delta
            c = datos[i]
            if c == 0xFF:
                tipo, i = datos[i + 1], i + 2
                largo = 0
                while True:
                    c = datos[i]; i += 1
                    largo = (largo << 7) | (c & 0x7F)
                    if c < 0x80:
                        break
                if tipo == 0x58:
                    eventos.append((tick, "compas", 0, datos[i], 2 ** datos[i + 1]))
                i += largo
                continue
            if c in (0xF0, 0xF7):
                i += 1
                largo = 0
                while True:
                    c = datos[i]; i += 1
                    largo = (largo << 7) | (c & 0x7F)
                    if c < 0x80:
                        break
                i += largo
                continue
            if c >= 0x80:
                estado, i = c, i + 1
            tipo, canal = estado & 0xF0, estado & 0x0F
            if tipo in (0xC0, 0xD0):
                i += 1
                continue
            a, b = datos[i], datos[i + 1]
            i += 2
            if tipo == 0x90 and b > 0:
                eventos.append((tick, "on", canal, a, b))
            elif tipo == 0x80 or (tipo == 0x90 and b == 0):
                eventos.append((tick, "off", canal, a, 0))
            elif tipo == 0xE0:
                eventos.append((tick, "bend", canal, (b << 7) | a, 0))
        pos = fin
    orden = {"compas": 0, "bend": 1, "off": 2, "on": 3}
    eventos.sort(key=lambda e: (e[0], orden[e[1]]))
    bend = defaultdict(lambda: 8192)
    abiertas, notas, compases = {}, [], []
    for tick, tipo, canal, a, b in eventos:
        if tipo == "bend":
            bend[canal] = a
        elif tipo == "compas":
            compases.append((tick, a, b))
        elif tipo == "on":
            abiertas[(canal, a)] = (tick, a + (bend[canal] - 8192) / 8192 * rango_bend)
        elif (canal, a) in abiertas:
            t0, altura = abiertas.pop((canal, a))
            if tick > t0:
                notas.append((t0, round(2 * altura), tick - t0))
    if len(notas) < 8:
        return None
    notas.sort()
    ton = notas[-1][1] % 24
    alt = [0.0] * 24
    for _, q, d in notas:
        alt[(q - ton) % 24] += d
    met = None
    if compases:
        met = [0.0] * 6
        fin_t = max(t + d for t, _, d in notas)
        for k, (t, num, den) in enumerate(compases):
            hasta = compases[k + 1][0] if k + 1 < len(compases) else fin_t
            met[familia_metro(pulsos_compas(num, den))] += max(0, hasta - t)
    return dict(altura=alt, metro=met if met and sum(met) else None)


def midi(carpeta: Path, nombre: str, familia: str, sin_metro: bool, rango_bend: float) -> None:
    piezas = []
    for f in sorted(list(carpeta.rglob("*.mid")) + list(carpeta.rglob("*.midi"))):
        try:
            r = leer_midi(f, rango_bend)
        except (IndexError, ValueError):
            r = None
        if r:
            piezas.append(pieza(f.stem, None, r["altura"], None if sin_metro else r["metro"]))
    escribir(nombre, familia, f"MIDI de {carpeta.name} (pitch bend ±{rango_bend:g} semitonos; tónica: última nota)", piezas)


# ───────────────────────── Humdrum **kern (Essen) ─────────────────────────
def leer_kern(path: Path) -> dict | None:
    notas, met = [], [0.0] * 6
    ton, p_actual = None, 4
    for linea in path.read_text(encoding="latin-1").splitlines():
        if not linea or linea.startswith("!"):
            continue
        tok = linea.split("\t")[0]
        m = re.fullmatch(r"\*([A-Ga-g])([#-]*):", tok)
        if m:
            ton = (LETRA[m.group(1).upper()] + m.group(2).count("#") - m.group(2).count("-")) % 12
            continue
        m = re.match(r"\*M(\d+)/(\d+)", tok)
        if m:
            p_actual = pulsos_compas(int(m.group(1)), int(m.group(2)))
            continue
        if tok.startswith(("*", "=")):
            continue
        for sub in tok.split():
            m = re.match(r"(\d+)(\.*)", sub)
            if not m or int(m.group(1)) == 0:
                continue
            d = 4.0 / int(m.group(1)) * (1.5 ** len(m.group(2)))
            met[familia_metro(p_actual)] += d
            m2 = re.search(r"([A-Ga-g])\1*([#-]*)", sub)
            if m2 and "r" not in sub:
                notas.append(((LETRA[m2.group(1).upper()] + m2.group(2).count("#") - m2.group(2).count("-")) % 12, d))
    if len(notas) < 8:
        return None
    ton = ton if ton is not None else notas[-1][0]
    alt = [0.0] * 24
    for pc, d in notas:
        alt[(2 * (pc - ton)) % 24] += d
    return dict(altura=alt, metro=met)


def kern(carpeta: Path, nombre: str, familia: str) -> None:
    piezas = []
    for f in sorted(carpeta.rglob("*.krn")):
        r = leer_kern(f)
        if r:
            piezas.append(pieza(f.stem, None, r["altura"], r["metro"]))
    escribir(nombre, familia, f"Humdrum kern de {carpeta.name}", piezas)


# ───────────────────────── The Session (abc) ─────────────────────────
MODOS = {"major": [0, 2, 4, 5, 7, 9, 11], "ionian": [0, 2, 4, 5, 7, 9, 11], "minor": [0, 2, 3, 5, 7, 8, 10], "aeolian": [0, 2, 3, 5, 7, 8, 10],
         "dorian": [0, 2, 3, 5, 7, 9, 10], "mixolydian": [0, 2, 4, 5, 7, 9, 10], "phrygian": [0, 1, 3, 5, 7, 8, 10], "lydian": [0, 2, 4, 6, 7, 9, 11],
         "locrian": [0, 1, 3, 5, 6, 8, 10]}


def leer_abc(abc: str, modo: str, meter: str) -> dict | None:
    m = re.match(r"([A-G])([#b]?)(\w+)", modo or "")
    if not m or m.group(3).lower() not in MODOS:
        return None
    ton = (LETRA[m.group(1)] + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)) % 12
    escala = [(ton + i) % 12 for i in MODOS[m.group(3).lower()]]
    firma = {}
    for letra, base in PASO.items():                                  # alteración de cada letra en esta armadura
        firma[letra] = next((a for a in (0, 1, -1) if (base + a) % 12 in escala), 0)
    mm = re.match(r"(\d+)/(\d+)", meter or "4/4")
    num, den = (int(mm.group(1)), int(mm.group(2))) if mm else (4, 4)
    unidad = 1 / 16 if num / den < 0.75 else 1 / 8
    abc = re.sub(r'"[^"]*"|![^!]*!|\{[^}]*\}|\+[^+]*\+', " ", abc)
    alt = [0.0] * 24
    accidentes = {}
    for tok in re.finditer(r"(\|)|([\^=_]*)([A-Ga-gz])([,']*)(\d*)(/*)(\d*)", abc):
        if tok.group(1):
            accidentes = {}
            continue
        letra = tok.group(3)
        n1 = int(tok.group(5)) if tok.group(5) else 1
        barras = len(tok.group(6))
        n2 = int(tok.group(7)) if tok.group(7) else (2 ** barras if barras else 1)
        d = unidad * n1 / n2 * 4
        if letra == "z":
            continue
        L = letra.upper()
        acc = tok.group(2)
        if acc:
            accidentes[L] = {"^": 1, "^^": 2, "_": -1, "__": -2, "=": 0}.get(acc, 0)
        a = accidentes.get(L, firma.get(L, 0))
        alt[(2 * (PASO[L] + a - ton)) % 24] += d
    if sum(alt) == 0:
        return None
    met = [0.0] * 6
    met[familia_metro(pulsos_compas(num, den))] = 1.0
    return dict(altura=alt, metro=met)


def session(path: Path, nombre: str, maximo: int) -> None:
    piezas, vistos = [], set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            if r.get("tune_id") in vistos:                            # una versión por tema
                continue
            res = leer_abc(r.get("abc", ""), r.get("mode", ""), r.get("meter", ""))
            if res:
                vistos.add(r.get("tune_id"))
                piezas.append(pieza(f"{r.get('tune_id')} {r.get('name', '')}", None, res["altura"], res["metro"]))
            if maximo and len(piezas) >= maximo:
                break
    escribir(nombre, "folk", "The Session (tunes.csv), una versión por tema", piezas, "licencia de la base de The Session (verificar)")


# ───────────────────────── Weimar Jazz Database ─────────────────────────
def wjd(path: Path, nombre: str, tipos: list[str] | None) -> None:
    con = sqlite3.connect(path)
    info = {r[0]: r[1:] for r in con.execute("SELECT melid, key, signature, tonality_type FROM solo_info")}
    piezas = []
    for melid, (key, firma, tipo) in info.items():
        if tipos and (tipo or "").upper() not in tipos:
            continue
        ton = tonica_de(key or "")
        if ton is None:
            continue
        alt = [0.0] * 24
        for pitch, dur in con.execute("SELECT pitch, duration FROM melody WHERE melid=?", (melid,)):
            if pitch is not None and dur:
                alt[(2 * (int(round(pitch)) - ton)) % 24] += dur
        seq = []
        for (acorde,) in con.execute("SELECT chord FROM beats WHERE melid=? ORDER BY onset", (melid,)):
            r = tonica_de(acorde or "")
            if r is not None and not (acorde or "").startswith("NC"):
                seq.append(((r - ton) % 12, 1.0))
        met = None
        m = re.match(r"(\d+)/(\d+)", firma or "")
        if m:
            met = [0.0] * 6
            met[familia_metro(pulsos_compas(int(m.group(1)), int(m.group(2))))] = 1.0
        piezas.append(pieza(str(melid), seq, alt if sum(alt) else None, met))
    escribir(nombre, "jazz", f"Weimar Jazz Database{' (' + ','.join(tipos) + ')' if tipos else ''}", piezas, "ODbL")


# ───────────────────────── DCML (TSV) ─────────────────────────
def dcml(carpeta: Path, nombre: str, familia: str) -> None:
    piezas = []
    for h in sorted(carpeta.rglob("*.harmonies.tsv")) or sorted((carpeta / "harmonies").glob("*.tsv")):
        base = h.name.split(".")[0]
        filas = list(csv.DictReader(open(h, encoding="utf-8"), delimiter="\t"))
        if not filas:
            continue
        gk = filas[0].get("globalkey", "C")
        ton = tonica_de(gk) or 0
        seq = []
        for r in filas:
            num = r.get("numeral") or ""
            if not num or num in ("@none",):
                continue
            rel = r.get("relativeroot") or ""
            lk = r.get("localkey") or "I"
            raiz_local = raiz_romana(lk, gk[:1].islower())
            raiz = raiz_romana(num + ("/" + rel if rel else ""), lk[-1:].islower() if lk else False)
            try:
                d = float(r.get("duration_qb") or 0)
            except ValueError:
                d = 0
            if raiz is not None and raiz_local is not None and d > 0:
                seq.append((raiz, d))                                    # relativo a la tonalidad local
        alt = [0.0] * 24
        notas = next(iter(h.parent.parent.rglob(f"{base}.notes.tsv")), None) or next(iter(h.parent.parent.glob(f"notes/{base}*.tsv")), None)
        if notas:
            for r in csv.DictReader(open(notas, encoding="utf-8"), delimiter="\t"):
                try:
                    alt[(2 * (int(r["midi"]) - ton)) % 24] += float(r.get("duration_qb") or 0)
                except (KeyError, ValueError):
                    pass
        met = [0.0] * 6
        compases = next(iter(h.parent.parent.rglob(f"{base}.measures.tsv")), None) or next(iter(h.parent.parent.glob(f"measures/{base}*.tsv")), None)
        if compases:
            for r in csv.DictReader(open(compases, encoding="utf-8"), delimiter="\t"):
                m = re.match(r"(\d+)/(\d+)", r.get("timesig") or "")
                if m:
                    p = pulsos_compas(int(m.group(1)), int(m.group(2)))
                    met[familia_metro(p)] += float(r.get("act_dur") or 1) if re.fullmatch(r"[\d.]+", r.get("act_dur") or "") else 1
        piezas.append(pieza(base, seq, alt if sum(alt) else None, met if sum(met) else None))
    escribir(nombre, familia, f"DCML ({carpeta.name})", piezas, "verificar en el repositorio DCML")


# ───────────────────────── Chordonomicon ─────────────────────────
def chordonomicon(path: Path, nombre: str, subgeneros: list[str], maximo: int) -> None:
    """Sin duraciones ni tonalidad: cada acorde vale 1; la tónica es la fundamental que hace más parecido el reparto al
    centro del RS 200 (sesgo hacia el rock: esto es una aproximación, se informa)."""
    rock = json.loads((DEST / "rock.json").read_text(encoding="utf-8")) if (DEST / "rock.json").exists() else None
    centro = [0.33, 0, 0.05, 0.03, 0.01, 0.23, 0, 0.17, 0.03, 0.05, 0.08, 0]
    if rock:
        vs = [p["fundamentales"] for p in rock["piezas"] if p["fundamentales"]]
        centro = [sum(v[k] for v in vs) / len(vs) for k in range(12)]
    csv.field_size_limit(10 ** 8)
    piezas, cuenta = [], defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            etiqueta = " ".join([r.get("rock_genre") or "", r.get("genres") or "", r.get("main_genre") or ""]).lower()
            grupo = next((s for s in subgeneros if s in etiqueta), None) if subgeneros else "todo"
            if not grupo or (maximo and cuenta[grupo] >= maximo):
                continue
            raices = []
            for t in re.sub(r"<[^>]*>", " ", r.get("chords") or "").split():
                m = re.match(r"([A-G])(s|b)?", t)
                if m:
                    raices.append((LETRA[m.group(1)] + (1 if m.group(2) == "s" else -1 if m.group(2) == "b" else 0)) % 12)
            if len(raices) < 8:
                continue
            cuenta_r = [raices.count(k) for k in range(12)]
            ton = max(range(12), key=lambda t: sum(cuenta_r[(t + k) % 12] * centro[k] for k in range(12)))
            piezas.append(pieza(f"{r.get('id')} {grupo}", [((x - ton) % 12, 1.0) for x in raices]))
            cuenta[grupo] += 1
    print("por subgénero:", dict(cuenta))
    escribir(nombre, "rock/pop", f"Chordonomicon ({', '.join(subgeneros) or 'todo'}; tónica estimada)", piezas, "CC BY-NC 4.0")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hooktheory", type=Path)
    ap.add_argument("--symbtr", type=Path)
    ap.add_argument("--musicxml", type=Path)
    ap.add_argument("--kern", type=Path)
    ap.add_argument("--midi", type=Path, help="carpeta de MIDI con pitch bend (Radif)")
    ap.add_argument("--rango-bend", type=float, default=2.0, help="MIDI: rango del pitch bend en semitonos")
    ap.add_argument("--session", type=Path)
    ap.add_argument("--wjd", type=Path)
    ap.add_argument("--dcml", type=Path)
    ap.add_argument("--chordonomicon", type=Path)
    ap.add_argument("--suave", type=float, default=0.0, help="SymbTr: σ en cents para repartir cada nota entre grados vecinos (0 = redondeo)")
    ap.add_argument("--nombre")
    ap.add_argument("--familia", default="otro", choices=["rock/pop", "clasica", "jazz", "folk", "microtonal", "otro"])
    ap.add_argument("--tonica", default="final", choices=["final", "primera", "armadura"], help="MusicXML: cómo fijar la tónica")
    ap.add_argument("--sin-metro", action="store_true", help="MusicXML: corpus no métrico (Radif)")
    ap.add_argument("--tipos", help="WJD: tonality_type a incluir, p. ej. MODAL,BLUES")
    ap.add_argument("--subgeneros", default="", help="Chordonomicon: lista separada por comas")
    ap.add_argument("--maximo", type=int, default=0, help="Session/Chordonomicon: máximo de piezas (por subgénero)")
    a = ap.parse_args()
    algo = False
    if a.hooktheory:
        hooktheory(a.hooktheory, a.nombre or "hooktheory"); algo = True
    if a.symbtr:
        symbtr(a.symbtr, a.nombre or "symbtr", a.suave); algo = True
    if a.musicxml:
        musicxml(a.musicxml, a.nombre or a.musicxml.name, a.familia, a.tonica, a.sin_metro); algo = True
    if a.midi:
        midi(a.midi, a.nombre or a.midi.name, a.familia, a.sin_metro, a.rango_bend); algo = True
    if a.kern:
        kern(a.kern, a.nombre or "essen", a.familia if a.familia != "otro" else "folk"); algo = True
    if a.session:
        session(a.session, a.nombre or "session", a.maximo); algo = True
    if a.wjd:
        wjd(a.wjd, a.nombre or "wjd", [t.strip().upper() for t in a.tipos.split(",")] if a.tipos else None); algo = True
    if a.dcml:
        dcml(a.dcml, a.nombre or a.dcml.name, a.familia if a.familia != "otro" else "clasica"); algo = True
    if a.chordonomicon:
        chordonomicon(a.chordonomicon, a.nombre or "chordonomicon", [s.strip().lower() for s in a.subgeneros.split(",") if s.strip()], a.maximo)
        algo = True
    if not algo:
        incluidos()


if __name__ == "__main__":
    main()
