"""Exporta un fragmento de una corrida del cuaderno al círculo de 24 notas animado (página HTML).

Uso:
    python scripts/exportar_circulo24.py outputs/<corrida> --desde 30 --hasta 60
        [--audio <mezcla.mp3|wav>] [--guitar <guitarra.mp3|wav>] [--bass <bajo.mp3|wav>]
        [--drums <bateria.mp3|wav>] [--titulo "Fabienk"]

Lee line_diagnostics.json (notas de la voz aguda y del bajo: inicio, fin y altura) y armonia.json (tónica estimada).
Escribe en outputs/<corrida>/circulo24/ (o en --salida): index.html, circulo24.js, datos.js y copias de las pistas.
Si se pasa la mezcla, busca automáticamente sus vecinos con los sufijos `_guitar`, `_bass` y `_drums`.
La página permite escuchar guitarra, bajo, ambos o ambos con batería por separado.

Con --audio la animación sigue al audio, que debe ser la grabación con la que se hizo la corrida (los tiempos son los
del cuaderno). Sin audio, la animación va con su propio reloj.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
WEB = RAIZ / "web" / "circulo24"


def nombre(corrida: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", corrida)
    n = re.sub(r"(angine_de_poitrine_|primus_|_audio_off\w*|_official_audio|_repro|_cache|_\d{4}_\w+$)", "", n)
    return n.replace("_", " ").strip().capitalize()


def notas(lista: list[dict], desde: float, hasta: float) -> list[list]:
    """[[inicio, fin, grado24]] relativos a `desde`, recortados al fragmento y ordenados por inicio."""
    out = []
    for n in lista or []:
        a, e = float(n["start_s"]), float(n["end_s"])
        if e <= desde or a >= hasta or e <= a:
            continue
        out.append([round(max(a, desde) - desde, 3), round(min(e, hasta) - desde, 3), round(float(n["midi"]) * 2) % 24])
    return sorted(out)


def buscar_pista(audio: Path | None, sufijos: tuple[str, ...]) -> Path | None:
    """Busca un stem junto a la mezcla, conservando la extensión de la mezcla o probando audio común."""
    if audio is None:
        return None
    extensiones = [audio.suffix.lower(), ".mp3", ".wav", ".flac", ".m4a"]
    for sufijo in sufijos:
        for ext in dict.fromkeys(extensiones):
            p = audio.with_name(audio.stem + sufijo + ext)
            if p.exists():
                return p
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corrida", type=Path)
    ap.add_argument("--desde", type=float, default=0.0, help="segundo de inicio del fragmento")
    ap.add_argument("--hasta", type=float, help="segundo final (por defecto, el final de la última nota)")
    ap.add_argument("--audio", type=Path, help="audio de la canción (el mismo que usó el cuaderno)")
    ap.add_argument("--guitar", type=Path, help="pista de guitarra; si falta, se busca junto a --audio")
    ap.add_argument("--bass", type=Path, help="pista de bajo; si falta, se busca junto a --audio")
    ap.add_argument("--drums", type=Path, help="pista de batería; si falta, se busca junto a --audio")
    ap.add_argument("--titulo")
    ap.add_argument("--salida", type=Path, help="carpeta de salida (por defecto <corrida>/circulo24)")
    a = ap.parse_args()

    J = json.loads((a.corrida / "line_diagnostics.json").read_text(encoding="utf-8"))
    H = json.loads((a.corrida / "armonia.json").read_text(encoding="utf-8")) if (a.corrida / "armonia.json").exists() else {}
    todas = (J.get("raw_high") or []) + (J.get("raw_bass") or [])
    if not todas:
        raise SystemExit("line_diagnostics.json no tiene notas (raw_high ni raw_bass)")
    hasta = a.hasta if a.hasta is not None else max(float(n["end_s"]) for n in todas)
    if hasta <= a.desde:
        raise SystemExit("--hasta tiene que ser mayor que --desde")

    salida = a.salida or (a.corrida / "circulo24")
    salida.mkdir(parents=True, exist_ok=True)
    pistas = {
        "mezcla": a.audio,
        "guitarra": a.guitar or buscar_pista(a.audio, ("_guitar", "_guitarra")),
        "bajo": a.bass or buscar_pista(a.audio, ("_bass", "_bajo")),
        "bateria": a.drums or buscar_pista(a.audio, ("_drums", "_drum", "_bateria")),
    }
    audios = {}
    for nombre_pista, origen in pistas.items():
        if origen is None:
            continue
        if not origen.exists():
            raise SystemExit(f"no existe la pista {nombre_pista}: {origen}")
        destino = f"{nombre_pista}{origen.suffix.lower()}"
        shutil.copyfile(origen, salida / destino)
        audios[nombre_pista] = destino

    datos = dict(titulo=a.titulo or nombre(a.corrida.name), corrida=a.corrida.name, desde=a.desde, hasta=hasta,
                 tonica_pc24=H.get("tonica_pc24"), tempo_bpm=J.get("tempo_bpm"),
                 audio=audios.get("mezcla"), audios=audios,
                 voces=dict(aguda=notas(J.get("raw_high"), a.desde, hasta), grave=notas(J.get("raw_bass"), a.desde, hasta)))
    (salida / "datos.js").write_text("window.CIRCULO24 = " + json.dumps(datos, ensure_ascii=False) + ";\n", encoding="utf-8")
    shutil.copyfile(WEB / "circulo24.js", salida / "circulo24.js")
    shutil.copyfile(WEB / "index.html", salida / "index.html")
    n_ag, n_gr = len(datos["voces"]["aguda"]), len(datos["voces"]["grave"])
    print(f"{datos['titulo']}: {a.desde:g}-{hasta:g} s · {n_ag} notas agudas · {n_gr} graves · pistas: "
          f"{', '.join(audios) or 'ninguna'} → {salida / 'index.html'}")


if __name__ == "__main__":
    main()
