#!/usr/bin/env python3
"""Logotipo de la revista: prefijo en cursiva (ej. "el") + nombre en Bodoni (ej. "CORO"), alineados en la línea base
y con el prefijo acomodado contra la primera letra (espaciado óptico). Lee logo_pre y logo de marca.json.
Uso como módulo: from lockup import lockup; img = lockup(M, carpeta_fuentes, tamaño, color)
"""
import os
from PIL import Image, ImageDraw, ImageFont

RATIO = 0.40      # tamaño del prefijo respecto al nombre
AIRE = 0.06       # separación mínima entre prefijo y nombre (fracción del tamaño)


def _font(path, size, w=900, opsz=96):
    f = ImageFont.truetype(path, size)
    try:
        vals = []
        for a in f.get_variation_axes():
            nm = a.get("name", b"")
            nm = (nm.decode("utf-8", "ignore") if isinstance(nm, bytes) else str(nm)).lower()
            if "eight" in nm or "wght" in nm:
                vals.append(max(a["minimum"], min(w, a["maximum"])))
            elif "optic" in nm or "opsz" in nm:
                vals.append(max(a["minimum"], min(opsz, a["maximum"])))
            else:
                vals.append(a.get("default", a["minimum"]))
        f.set_variation_by_axes(vals)
    except Exception:
        pass
    return f


def partes(M):
    return (M.get("logo_pre") or "").strip(), (M.get("logo") or M["nombre"]).strip()


def _mask(text, font, W, H, x, base):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).text((x, base), text, font=font, fill=255, anchor="ls")
    return m


def lockup(M, fd, size, fill=(10, 10, 10), pad=0, ratio=RATIO, aire=AIRE):
    pre, main = partes(M)
    fm = _font(os.path.join(fd, "BodoniModa%5Bopsz,wght%5D.ttf"), size)
    W, H = int(size * (len(main) + 2)), int(size * 1.6)
    base = int(size * 1.25)
    mm = _mask(main, fm, W, H, int(size * 0.9), base)
    if pre:
        fp = _font(os.path.join(fd, "BodoniModa-Italic%5Bopsz,wght%5D.ttf"), max(8, int(size * ratio)))
        pm = _mask(pre, fp, W, H, 0, base)
        # espaciado óptico: mueve el prefijo hasta que su punto más cercano quede a 'aire' del nombre
        import numpy as np
        A, B = np.array(pm) > 40, np.array(mm) > 40
        rows = [y for y in range(H) if A[y].any() and B[y].any()]
        if rows:
            gap = min(int(np.argmax(B[y])) - (len(A[y]) - 1 - int(np.argmax(A[y][::-1]))) for y in rows)
        else:
            gap = int(np.argmax(B.any(0))) - (W - 1 - int(np.argmax(A.any(0)[::-1])))
        dx = gap - int(size * aire)
        pm = _mask(pre, fp, W, H, dx, base)
        mask = Image.fromarray(np.maximum(np.array(pm), np.array(mm)))
    else:
        mask = mm
    bb = mask.getbbox()
    mask = mask.crop(bb)
    out = Image.new("RGBA", (mask.width + 2 * pad, mask.height + 2 * pad), tuple(fill[:3]) + (0,))
    solid = Image.new("RGBA", mask.size, tuple(fill[:3]) + (255,))
    out.paste(solid, (pad, pad), mask)
    return out


def ajustar(img, maxw, maxh):
    s = min(maxw / img.width, maxh / img.height)
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)


def logo_html(M):
    """El logotipo en HTML (para la web y los posts). Debe coincidir con LOGO en build.js y dump.js."""
    pre, main = partes(M)
    if not pre:
        return main
    return f'<i style="font-style:italic;font-size:.4em;letter-spacing:-.01em;margin-right:.07em">{pre}</i>{main}'
