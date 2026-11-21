"""Estilo común de las figuras comparativas: colores, composición sin solapes y revisión automática.

Uso dentro de un script de scripts/comparacion/:
    from estilo_figuras import figura, guardar
    fig, cuerpo = figura(12, 6, "Título", subtitulo="Qué muestra", nota="Cómo leerla")
    ax = cuerpo.subplots()
    ...
    guardar(fig, "outputs/ejemplo.png")        # avisa si algún texto se monta o se sale

La figura tiene tres franjas: encabezado (título y subtítulo), cuerpo (los gráficos) y pie (nota). El alto del
encabezado y del pie se calcula en pulgadas a partir del texto, así que no crece con el alto de la figura. Los textos
largos se parten solos según el ancho. El cuerpo usa el modo «constrained» de matplotlib, que mide etiquetas, títulos,
barras de color y leyendas («outside …») antes de ubicarlos.


"""
from __future__ import annotations

import textwrap

TINTA, GRIS, MUTED, FONDO, REJILLA = "#0b0b0b", "#52514e", "#8a8984", "#fcfcfb", "#e4e3de"
PALETA_ARTISTA = {"Angine de Poitrine": "#2a78d6", "Primus": "#eb6834", "King Gizzard": "#1baf7a",
                  "Frank Zappa": "#eda100", "King Crimson": "#8b5fbf", "Gentle Giant": "#d1495b"}

TITULO_PT, TEXTO_PT = 16, 9.5
_MARGEN_IN = 0.22          # aire arriba del título y debajo de la nota
_INTERLINEA = 1.35
_ANCHO_LETRA = 0.56        # ancho medio de una letra de DejaVu Sans, en «em»


def preparar() -> None:
    """Backend sin ventana y la tipografía de todas las figuras."""
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.family"] = "DejaVu Sans"


def partir(texto: str, ancho_in: float, puntos: float) -> str:
    """Parte cada párrafo de `texto` para que quepa en `ancho_in` pulgadas a `puntos` de tamaño."""
    if not texto:
        return ""
    letras = max(20, int(ancho_in * 72 / (puntos * _ANCHO_LETRA)))
    return "\n".join(textwrap.fill(p, letras) if p.strip() else "" for p in texto.split("\n"))


def _alto(texto: str, puntos: float) -> float:
    return 0.0 if not texto else (texto.count("\n") + 1) * puntos * _INTERLINEA / 72


def figura(ancho: float, alto_cuerpo: float, titulo: str, subtitulo: str = "", nota: str = "",
           titulo_pt: float = TITULO_PT, texto_pt: float = TEXTO_PT):
    """Figura de `ancho` pulgadas con encabezado y pie de alto fijo; devuelve (figura, subfigura del cuerpo)."""
    import matplotlib.pyplot as plt

    util = ancho - 2 * _MARGEN_IN
    titulo = partir(titulo, util, titulo_pt)
    subtitulo = partir(subtitulo, util, texto_pt)
    nota = partir(nota, util, texto_pt)
    h_cab = _MARGEN_IN + _alto(titulo, titulo_pt) + (0.12 + _alto(subtitulo, texto_pt) if subtitulo else 0) + 0.18
    h_pie = (0.15 + _alto(nota, texto_pt) + _MARGEN_IN) if nota else _MARGEN_IN
    fig = plt.figure(figsize=(ancho, h_cab + alto_cuerpo + h_pie), facecolor=FONDO, layout="constrained")
    fig.get_layout_engine().set(w_pad=0.08, h_pad=0.06, hspace=0.0, wspace=0.0)
    cab, cuerpo, pie = fig.subfigures(3, 1, height_ratios=[h_cab, alto_cuerpo, h_pie])
    for s in (cab, cuerpo, pie):
        s.set_facecolor(FONDO)
    y = 1 - _MARGEN_IN / h_cab
    cab.text(0.5, y, titulo, ha="center", va="top", fontsize=titulo_pt, fontweight="bold", color=TINTA,
             linespacing=1.15)
    if subtitulo:
        y -= (_alto(titulo, titulo_pt) + 0.12) / h_cab
        cab.text(0.5, y, subtitulo, ha="center", va="top", fontsize=texto_pt, color=GRIS, linespacing=1.25)
    if nota:
        pie.text(_MARGEN_IN / ancho, 1 - 0.15 / h_pie, nota, ha="left", va="top", fontsize=texto_pt, color=GRIS,
                 linespacing=1.25)
    return fig, cuerpo


def estilo_ejes(ax, grid_x: bool = False, grid_y: bool = False) -> None:
    ax.set_facecolor(FONDO)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(REJILLA)
    ax.tick_params(colors=GRIS, labelsize=8.5, length=0)
    if grid_x:
        ax.grid(axis="x", color=REJILLA, lw=0.8)
    if grid_y:
        ax.grid(axis="y", color=REJILLA, lw=0.8)
    ax.set_axisbelow(True)


def sin_repetidas(handles: list) -> list:
    """Quita entradas de leyenda con la misma etiqueta (sin distinguir mayúsculas)."""
    vistas, salida = set(), []
    for h in handles:
        clave = h.get_label().strip().lower()
        if clave not in vistas:
            vistas.add(clave)
            salida.append(h)
    return salida


# ---------------------------------------------------------------- revisión automática

def _textos_dibujados(fig):
    """Textos visibles que matplotlib dibuja de verdad (las marcas fuera del eje no cuentan)."""
    from matplotlib.text import Text

    de_marcas, dibujadas = set(), []
    for ax in fig.get_axes():
        for eje in (ax.xaxis, ax.yaxis):
            for t in eje.get_major_ticks() + eje.get_minor_ticks():
                de_marcas.update({id(t.label1), id(t.label2)})
            for t in eje._update_ticks():
                dibujadas += [lab for lab in (t.label1, t.label2) if lab.get_visible()]
    otros = [t for t in fig.findobj(Text) if id(t) not in de_marcas]
    return [t for t in otros + dibujadas if t.get_visible() and t.get_text().strip() and (t.get_alpha() is None or t.get_alpha() > 0)]


def _dentro_de_leyenda(fig) -> set[int]:
    return {id(t) for leg in fig.findobj(lambda a: a.__class__.__name__ == "Legend") for t in leg.findobj()}


def revisar(fig, tolerancia: float = 1.0) -> list[str]:
    """Problemas de distribución: textos que se montan, que se salen de la figura o leyendas sobre un gráfico."""
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    borde = fig.bbox
    textos = _textos_dibujados(fig)
    en_leyenda = _dentro_de_leyenda(fig)
    cajas = [(t, t.get_window_extent(r)) for t in textos]
    corto = lambda t: repr(t.get_text().replace("\n", " ")[:40])
    problemas = []
    for t, b in cajas:
        if b.x0 < borde.x0 - tolerancia or b.y0 < borde.y0 - tolerancia or b.x1 > borde.x1 + tolerancia or b.y1 > borde.y1 + tolerancia:
            problemas.append(f"se sale de la figura: {corto(t)}")
    for i, (t1, b1) in enumerate(cajas):
        for t2, b2 in cajas[i + 1:]:
            if (min(b1.x1, b2.x1) - max(b1.x0, b2.x0) > tolerancia and min(b1.y1, b2.y1) - max(b1.y0, b2.y0) > tolerancia):
                problemas.append(f"textos montados: {corto(t1)} y {corto(t2)}")
    graficos = [ax for ax in fig.get_axes() if ax.get_label() != "<colorbar>" and ax.axison]
    for leg in fig.findobj(lambda a: a.__class__.__name__ == "Legend"):
        bl = leg.get_window_extent(r)
        for ax in graficos:
            ba = ax.get_window_extent(r)
            if min(bl.x1, ba.x1) - max(bl.x0, ba.x0) > tolerancia and min(bl.y1, ba.y1) - max(bl.y0, ba.y0) > tolerancia:
                problemas.append(f"leyenda sobre un gráfico: {ax.get_title() or ax.get_ylabel() or 'eje'!r}")
    for t, b in cajas:                     # textos sueltos de la figura (subtítulos, notas) sobre un gráfico
        if t.axes is not None or id(t) in en_leyenda:
            continue
        for ax in graficos:
            ba = ax.get_window_extent(r)
            if min(b.x1, ba.x1) - max(b.x0, ba.x0) > tolerancia and min(b.y1, ba.y1) - max(b.y0, ba.y0) > tolerancia:
                problemas.append(f"texto sobre un gráfico: {corto(t)}")
    problemas += huecos(fig, r, [b for _, b in cajas])
    return problemas


def huecos(fig, r, cajas_texto, maximo_in: float = 0.6) -> list[str]:
    """Franjas horizontales vacías de más de `maximo_in` pulgadas entre los elementos de la figura."""
    cajas = list(cajas_texto) + [ax.get_window_extent(r) for ax in fig.get_axes() if ax.axison]
    cajas += [leg.get_window_extent(r) for leg in fig.findobj(lambda a: a.__class__.__name__ == "Legend")]
    tramos = sorted((b.y0, b.y1) for b in cajas if b.height > 0)
    if not tramos:
        return []
    salida, alto = [], fig.bbox.height
    tope = tramos[0][1]
    for y0, y1 in tramos[1:]:
        if y0 > tope and (y0 - tope) / fig.dpi > maximo_in:
            salida.append(f"franja vacía de {(y0 - tope) / fig.dpi:.1f} in a {100 * (alto - y0) / alto:.0f} % desde arriba")
        tope = max(tope, y1)
    return salida


def guardar(fig, ruta: str, dpi: int = 200) -> list[str]:
    """Revisa la distribución, guarda la imagen y cierra la figura; devuelve los problemas encontrados."""
    import matplotlib.pyplot as plt

    problemas = revisar(fig)
    fig.savefig(ruta, dpi=dpi, facecolor=FONDO)
    plt.close(fig)
    print(f"→ {ruta}")
    for p in problemas:
        print(f"   aviso de distribución: {p}")
    return problemas
