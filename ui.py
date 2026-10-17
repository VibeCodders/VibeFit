"""Elementi grafici dell'interfaccia: pulsanti arrotondati con sfumatura (texture generate nel codice)."""
from panda3d.core import PNMImage, Texture

_cache = {}


def rounded_texture(aspect, radius=0.35, height_px=48):
    """Texture bianca con angoli arrotondati e sfumatura dall'alto verso il basso.

    `aspect` = larghezza/altezza del pulsante, cosi' gli angoli restano circolari.
    `radius` e' in frazione dell'altezza.
    """
    w = max(int(round(aspect * height_px)), height_px)
    key = (w, height_px, radius)
    if key in _cache:
        return _cache[key]
    h = height_px
    r = radius * h
    img = PNMImage(w, h, 4)
    for y in range(h):
        shade = 1.0 - 0.18 * (y / (h - 1))  # piu' chiaro in alto
        for x in range(w):
            # distanza dal rettangolo interno (con angoli arrotondati)
            dx = max(r - (x + 0.5), 0, (x + 0.5) - (w - r))
            dy = max(r - (y + 0.5), 0, (y + 0.5) - (h - r))
            d = (dx * dx + dy * dy) ** 0.5
            a = max(0.0, min(1.0, r - d + 0.5))
            img.setXelA(x, y, shade, shade, shade, a)
    tex = Texture("btn")
    tex.load(img)
    tex.setMinfilter(Texture.FTLinear)
    tex.setMagfilter(Texture.FTLinear)
    _cache[key] = tex
    return tex


def shade(color, f):
    """Schiarisce (f>1) o scurisce (f<1) un colore RGBA."""
    r, g, b, a = color
    return (min(r * f, 1.0), min(g * f, 1.0), min(b * f, 1.0), a)
