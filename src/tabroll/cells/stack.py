"""**`_stack`**: Une las páginas, una debajo de otra, en una imagen única; si pasa de `max_h` píxeles, la parte en varias.
"""

def _stack(paths, stem, max_h=30000):
    parts, cur, h = [], [], 0

    for p in paths:
        ph = Image.open(p).size[1]

        if cur and h + ph > max_h:
            parts.append(cur); cur, h = [], 0

        cur.append(p); h += ph

    parts.append(cur)
    outs = []

    for k, grp in enumerate(parts, 1):
        ims = [Image.open(p).convert('RGB') for p in grp]
        sheet = Image.new('RGB', (max(i.size[0] for i in ims), sum(i.size[1] for i in ims)), BG)
        yy = 0

        for im in ims:
            sheet.paste(im, (0, yy)); yy += im.size[1]

        out = OUTPUT_DIR / (f'{stem}_completo.png' if len(parts) == 1 else f'{stem}_completo_{k}.png')
        sheet.save(out); outs.append(out)

    return outs
