"""Copia a presentacion/img/ las gráficas que usa la presentación, desde las corridas más recientes de outputs/.

Uso:
    python scripts/presentacion_imagenes.py            # o: make presentacion-imagenes

- Las seis gráficas de resultados salen de la carpeta outputs/graficas_clave_*/diapositivas/ más reciente
  (la crea `make graficas-diapositivas`).
- Los tabroll de ejemplo son páginas de Sarniezz y Fabienk de la corrida más reciente con Demucs (sin «_roformer»).
  La de Fabienk (diapositiva 9, 4:42-4:52) se recorta al registro de la guitarra (Re♯3+ a Mi4+), con las filas al doble de alto y
  la columna de notas rehecha con letra grande: notas regulares a la izquierda, cuartos de tono («+», en azul) a la
  derecha y el grado de Mi dórico en color. En la diapositiva la página entera quedaba a una quinta parte de su tamaño.
Las imágenes que no salen de este repositorio se ponen a mano en presentacion/img/: la captura de Hooktheory
(hooktheory_fabienk.png) y las figuras del primer cuaderno, que dibuja scripts/comparacion/figuras_cuaderno_original.py:
original_*.png con su audio_arrays.npz y cuaderno_original_sarniezz.png con su mxl/score.xml (--partitura).
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
OUT = RAIZ / "outputs"
IMG = RAIZ / "presentacion" / "img"
TABROLLS = [("_sarniezz_", "tabroll24_p08.png", "tabroll_sarniezz.png"),      # ♭VII sus2 y ♭III
            ("fabienk_official", "tabroll24_p32.png", "tabroll_fabienk.png")]   # 4:42-4:52: melodía «Fabien», la que más acierta


# Geometría del tabroll de 24-EDO (render_song_graphic): filas de 11 px; en las páginas de Fabienk la fila de Mi3 está
# centrada en y = 571 y la de Mi4 en y = 307 (sus líneas de octava, grises, en y = 576 y 312). La rejilla va de y = 70 a
# y = 1140; los compases empiezan en x = 117, con 64 px por pulso y 4 px entre compases.
FILA, Y_MI3, Y_LINEAS, X_COMPAS, PX_PULSO, HUECO = 11, 571, (312, 576), 117, 64, 4
PULSOS_POR_PAGINA = 21                                                  # BEATS_PER_PAGE del cuaderno
NOTAS = ["E", "F", "F♯", "G", "G♯", "A", "A♯", "B", "C", "C♯", "D", "D♯"]
GRADOS = {"E": (1, "#ba9169"), "F♯": (2, "#c1b773"), "G": (3, "#95c574"), "A": (4, "#7eb1cb"),
          "B": (5, "#a86dcc"), "C♯": (6, "#b866b6"), "D": (7, "#b86d62")}     # Mi dórico, colores del tabroll


def compases_de_pagina(corrida: Path, pagina: int) -> list[dict]:
    """Los compases de una página del tabroll, con sus pulsos: reparte los compases de armonia.json como _pages del
    cuaderno (hasta 21 pulsos por página), con el tempo de salida.txt."""
    import json
    import re
    pulso = 60 / float(re.search(r"Tempo aproximado: ([\d.]+)", (corrida / "salida.txt").read_text()).group(1))
    paginas, actual, total = [], [], 0
    for c in json.loads((corrida / "armonia.json").read_text())["compases"]:
        c = dict(c, pulsos=max(1, round((c["fin_s"] - c["inicio_s"]) / pulso)))
        if actual and total + c["pulsos"] > PULSOS_POR_PAGINA:
            paginas.append(actual)
            actual, total = [], 0
        actual.append(c)
        total += c["pulsos"]
    return (paginas + [actual])[pagina - 1]


def funcion_completa(compas: dict) -> str:
    """La función del acorde en palabras: «Tónica relativa», «Dominante modal» (el tabroll del cuaderno pone «T rel.»)."""
    from tabroll.cells.harmony_labels import MATIZ_CORTO
    largo = {"rel.": "relativa", "nap.": "napolitana", "mixt.": "mixtura", "sens.": "con sensible", "tt": "tritono"}
    matiz = MATIZ_CORTO.get(compas.get("matiz") or "", "")
    return f"{(compas.get('funcion') or '').capitalize()} {largo.get(matiz, matiz)}".strip()


def zoom_guitarra(origen: Path, destino: Path, compases: list[dict], desde: int = -1, hasta: int = 25,
                  estirar: int = 2) -> None:
    """Recorta la página del tabroll a las filas de `desde` a `hasta` cuartos de tono sobre Mi3 y las estira. Rehace con
    letra grande las notas de la izquierda, la cabecera de pulsos y la franja de acordes (con los datos de `compases`)."""
    import sys as _sys
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib
    _sys.path.insert(0, str(RAIZ / "src"))
    from tabroll.cells.harmony_labels import harmony_labels
    im = Image.open(origen).convert("RGB")
    for y in Y_LINEAS:                                                   # comprueba que la geometría sea la esperada
        if sum(im.getpixel((470, y))) < 250:
            raise SystemExit(f"{origen.name}: la línea de octava no está en y = {y}; revisa la geometría del tabroll")
    inicios, x = [], X_COMPAS
    for c in compases:
        inicios.append(x)
        x += PX_PULSO * c["pulsos"] + HUECO
    x0, x1 = X_COMPAS - 2, x - HUECO + 4
    if x1 > im.width:
        raise SystemExit(f"{origen.name}: los compases no caben en la página; revisa la página elegida")
    y0, y1 = Y_MI3 - FILA * hasta - FILA // 2 - 1, Y_MI3 - FILA * desde + FILA // 2 + 1
    rejilla = im.crop((x0, y0, x1, y1))
    for yr in (Y_MI3 - 24 * FILA, Y_MI3):                                 # borra los rótulos «E3» y «E4» de la rejilla
        if y0 <= yr - 8 and yr + 6 <= y1:
            rejilla.paste(rejilla.crop((150 - x0, yr - 8 - y0, 176 - x0, yr + 6 - y0)), (122 - x0, yr - 8 - y0))
    rejilla = rejilla.resize((rejilla.width, rejilla.height * estirar), Image.NEAREST)

    margen, alto_fila, alto_cab, alto_acordes = 240, FILA * estirar, 84, 200
    fondo = (19, 18, 21)
    out = Image.new("RGB", (margen + rejilla.width, alto_cab + rejilla.height + alto_acordes), fondo)
    out.paste(rejilla, (margen, alto_cab))
    fuentes = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
    f = lambda nombre, t: ImageFont.truetype(str(fuentes / nombre), t)
    grande, chica = f("DejaVuSans-Bold.ttf", 34), f("DejaVuSans.ttf", 27)
    d = ImageDraw.Draw(out)

    # notas de la izquierda: grado, nota regular y cuarto de tono
    for n in range(desde, hasta + 1):
        y = alto_cab + (hasta - n) * alto_fila + alto_fila // 2 + estirar
        nota, octava = NOTAS[(n // 2) % 12], 3 + (n // 2 + 4) // 12   # Mi3 = n 0; la octava cambia en Do
        if n % 2:
            d.text((margen - 12, y), f"{nota}+", font=chica, fill="#5aa0ff", anchor="rm")
        else:
            d.text((margen - 92, y), nota + (str(octava) if nota in ("E", "C") else ""), font=grande, fill="#e8e8ea", anchor="rm")
            if nota in GRADOS:
                g, color = GRADOS[nota]
                d.text((18, y), str(g), font=grande, fill=color, anchor="lm")

    # cabecera de pulsos y franja de acordes, compás por compás
    etiquetas = {e["compas"]: e for e in harmony_labels(compases, 0)}
    romano, indice, funcion, nombre = f("DejaVuSerif.ttf", 50), f("DejaVuSerif.ttf", 32), f("DejaVuSans-Bold.ttf", 28), f("DejaVuSans.ttf", 40)
    ya = alto_cab + rejilla.height
    for c, xi in zip(compases, inicios):
        a, b = margen + xi - x0, margen + xi - x0 + PX_PULSO * c["pulsos"]
        d.line((a, 12, a + (b - a) * 0.7, 12), fill="#d9a441", width=5)
        d.text((a + 14, 50), f"{c['pulsos']} pulsos", font=f("DejaVuSans-Bold.ttf", 36), fill="#ffffff", anchor="lm")
        color = im.getpixel((xi + 40, 1150))                            # el color del grado, como en el tabroll
        d.rounded_rectangle((a, ya + 8, b, ya + 140), radius=8, fill=(40, 41, 46))
        d.rectangle((a, ya + 8, b, ya + 18), fill=color)
        d.rectangle((a, ya + 132, b, ya + 140), fill=color)
        e = etiquetas.get(c["compas"])
        if e is None:
            continue
        num = e["numeral"].replace("{+}", "+")
        base, sub = (num.split("_{")[0], num.split("_{")[1].split("}")[0]) if "_{" in num else (num.split("^{")[0], "")
        sup = num.split("^{")[1].split("}")[0] if "^{" in num else ""
        ancho = d.textlength(base, font=romano) + max(d.textlength(sub, font=indice), d.textlength(sup, font=indice))
        xc = (a + b) / 2 - ancho / 2
        d.text((xc, 66 + ya), base, font=romano, fill="#f2f2f4", anchor="ls")
        xs = xc + d.textlength(base, font=romano) + 2
        if sub:
            d.text((xs, 76 + ya), sub, font=indice, fill="#f2f2f4", anchor="ls")
        if sup:
            d.text((xs, 44 + ya), sup, font=indice, fill="#f2f2f4", anchor="ls")
        texto = funcion_completa(c)                                     # «Tónica relativa», no «T rel.»
        letra = f("DejaVuSans-Bold.ttf", 28)
        menor = (c.get("funcion_corta") or "").islower()                # el cuaderno la pone en minúscula: acorde menor
        if menor:
            renglones = [texto, "(menor)"]
        elif d.textlength(texto, font=letra) > (b - a) - 16 and " " in texto:
            renglones = texto.split(" ", 1)                             # en compases cortos, en dos renglones
        else:
            renglones = [texto]
        if len(renglones) == 1:
            d.text(((a + b) / 2, ya + 108), texto, font=letra, fill=e["annot_color"], anchor="mm")
        else:
            letra = f("DejaVuSans-Bold.ttf", 23)
            for k, renglon in enumerate(renglones):
                d.text(((a + b) / 2, ya + 93 + 23 * k), renglon, font=letra, fill=e["annot_color"], anchor="mm")
        d.text(((a + b) / 2, ya + 172), e["name"], font=nombre, fill="#e8e8ea", anchor="mm")
    out.save(destino)


def mas_reciente(patron: str, filtro=lambda p: True) -> Path | None:
    candidatos = sorted((p for p in OUT.glob(patron) if filtro(p)), key=lambda p: str(p.relative_to(OUT)))
    return candidatos[-1] if candidatos else None


def main() -> int:
    IMG.mkdir(parents=True, exist_ok=True)
    copiadas = 0
    diap = mas_reciente("graficas_clave_*/diapositivas")
    if diap is None:
        print("No hay outputs/graficas_clave_*/diapositivas: corre antes make graficas-diapositivas.", file=sys.stderr)
    else:
        for png in sorted(diap.glob("*.png")):
            shutil.copy2(png, IMG / png.name)
            copiadas += 1
        print(f"gráficas de resultados: {diap.relative_to(RAIZ)}")
    for clave, pagina, destino in TABROLLS:
        corrida = mas_reciente(f"*{clave}*", lambda p: p.is_dir() and "roformer" not in p.name
                               and any(p.glob(f"harmony_outputs/*/{pagina}")))
        if corrida is None:
            print(f"No hay una corrida de {clave.strip('_')} con {pagina}.", file=sys.stderr)
            continue
        if clave == "fabienk_official":
            n = int(pagina.rsplit("_p", 1)[1].split(".")[0])
            zoom_guitarra(next(corrida.glob(f"harmony_outputs/*/{pagina}")), IMG / destino, compases_de_pagina(corrida, n))
        else:
            shutil.copy2(next(corrida.glob(f"harmony_outputs/*/{pagina}")), IMG / destino)
        copiadas += 1
        print(f"tabroll: {corrida.name} → {destino}")
    print(f"{copiadas} imágenes en {IMG.relative_to(RAIZ)}")
    return 0 if copiadas else 1


if __name__ == "__main__":
    raise SystemExit(main())
