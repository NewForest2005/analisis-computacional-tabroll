"""Exporta un fragmento de una corrida del cuaderno al círculo de 24 notas animado (página HTML).

Uso:
    python scripts/comparacion/exportar_circulo24.py outputs/<corrida> --desde 30 --hasta 60
        [--audio <mezcla.mp3|wav>] [--guitar <guitarra.mp3|wav>] [--bass <bajo.mp3|wav>]
        [--drums <bateria.mp3|wav>] [--titulo "Fabienk"] [--recortar] [--salida carpeta]

Lee line_diagnostics.json (notas de la voz aguda y del bajo: inicio, fin y altura) y armonia.json (tónica estimada).
Escribe en outputs/<corrida>/circulo24/ (o en --salida): index.html, circulo24.js, datos.js y copias de las pistas.
Si se pasa la mezcla, busca automáticamente sus vecinos con los sufijos `_guitar`, `_bass` y `_drums`.
La página permite escuchar guitarra, bajo, ambos o ambos con batería por separado.

Con --audio la animación sigue al audio, que debe ser la grabación con la que se hizo la corrida (los tiempos son los
del cuaderno). Sin audio, la animación va con su propio reloj. Con --recortar, cada pista se corta al fragmento con
ffmpeg (la página pesa unos cientos de KB en vez de varios MB) y datos.js lleva audio_inicio = 0.

La página se puede abrir con ?disposicion=quintas para empezar con los dos campos de quintas (como la gráfica 2b).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
WEB = RAIZ / "web" / "circulo24"


def nombre(corrida: str) -> str:
    n = re.sub(r"^\d{4}-\d\d-\d\d_\d+_", "", corrida)
    n = re.sub(r"(angine_de_poitrine_|primus_|_audio_off\w*|_official_audio|_repro|_cache|_\d{4}_\w+$)", "", n)
    return n.replace("_", " ").strip().capitalize()


def notas(lista: list[dict], desde: float, hasta: float, desfase: float = 0.0) -> list[list]:
    """[[inicio, fin, grado24]] relativos a `desde`, recortados al fragmento y ordenados por inicio.
    `desfase` (s) corre todas las notas: el cuaderno marca las notas unos 50 ms antes de que suenen."""
    out = []
    for n in lista or []:
        a, e = float(n["start_s"]) + desfase, float(n["end_s"]) + desfase
        if e <= desde or a >= hasta or e <= a:
            continue
        out.append([round(max(a, desde) - desde, 3), round(min(e, hasta) - desde, 3), round(float(n["midi"]) * 2) % 24])
    return sorted(out)


def sin_sueltas(lista: list[list], min_uso: float, max_dur: float) -> tuple[list[list], list[list]]:
    """Quita las notas cortas (< max_dur s) de un grado que casi no suena en el fragmento (< min_uso del tiempo de la voz).

    Son, sobre todo, errores de quinta de la saliencia armónica (un Do donde suena Fa, su tercer armónico). Devuelve las
    notas que quedan y las quitadas."""
    total = sum(b - a for a, b, _ in lista) or 1.0
    uso: dict[int, float] = {}
    for a, b, g in lista:
        uso[g] = uso.get(g, 0.0) + (b - a)
    quedan, quitadas = [], []
    for n in lista:
        (quitadas if n[1] - n[0] < max_dur and uso[n[2]] / total < min_uso else quedan).append(n)
    return quedan, quitadas


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
    ap.add_argument("--recortar", action="store_true", help="cortar cada pista al fragmento (necesita ffmpeg)")
    # El cuaderno marca cada nota antes de que suene: su espectro (ventana de 4096 muestras, 186 ms, centrada) ya ve la
    # nota cuando la ventana empieza a cubrirla. Medido en Mata Zyklek 42-72 s con sincronia_circulo24.py (pYIN y ataques).
    ap.add_argument("--desfase-aguda", type=float, default=0.060, help="segundos que se atrasan las notas agudas")
    ap.add_argument("--desfase-grave", type=float, default=0.055, help="segundos que se atrasan las notas graves")
    ap.add_argument("--min-uso", type=float, default=0.02,
                    help="quita notas cortas de grados con menos de esta fracción del tiempo de la voz (0 = no quitar)")
    ap.add_argument("--max-suelta", type=float, default=0.15, help="duración máxima (s) de una nota suelta que se puede quitar")
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
        if a.recortar:
            destino = f"{nombre_pista}.mp3"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(origen), "-ss", f"{a.desde:.3f}", "-t", f"{hasta - a.desde:.3f}",
                            "-ac", "2", "-b:a", "160k", str(salida / destino)], check=True)
        else:
            destino = f"{nombre_pista}{origen.suffix.lower()}"
            shutil.copyfile(origen, salida / destino)
        audios[nombre_pista] = destino

    voces = {}
    for voz, clave, desfase in (("aguda", "raw_high", a.desfase_aguda), ("grave", "raw_bass", a.desfase_grave)):
        voces[voz], quitadas = sin_sueltas(notas(J.get(clave), a.desde, hasta, desfase), a.min_uso, a.max_suelta) \
            if a.min_uso > 0 else (notas(J.get(clave), a.desde, hasta, desfase), [])
        if quitadas:
            print(f"   voz {voz}: {len(quitadas)} notas sueltas quitadas ({sum(b - x for x, b, _ in quitadas):.2f} s): "
                  + ", ".join(f"{x:.2f} s grado {g}" for x, _, g in quitadas))
    datos = dict(titulo=a.titulo or nombre(a.corrida.name), corrida=a.corrida.name, desde=a.desde, hasta=hasta,
                 audio_inicio=0.0 if a.recortar else a.desde,
                 tonica_pc24=H.get("tonica_pc24"), tempo_bpm=J.get("tempo_bpm"),
                 audio=audios.get("mezcla"), audios=audios,
                 desfase_notas=dict(aguda=a.desfase_aguda, grave=a.desfase_grave),
                 voces=voces)
    (salida / "datos.js").write_text("window.CIRCULO24 = " + json.dumps(datos, ensure_ascii=False) + ";\n", encoding="utf-8")
    shutil.copyfile(WEB / "circulo24.js", salida / "circulo24.js")
    shutil.copyfile(WEB / "index.html", salida / "index.html")
    n_ag, n_gr = len(datos["voces"]["aguda"]), len(datos["voces"]["grave"])
    print(f"{datos['titulo']}: {a.desde:g}-{hasta:g} s · {n_ag} notas agudas · {n_gr} graves · pistas: "
          f"{', '.join(audios) or 'ninguna'} → {salida / 'index.html'}")


if __name__ == "__main__":
    main()
