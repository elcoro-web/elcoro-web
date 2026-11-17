#!/usr/bin/env python3
"""Genera logos, íconos, favicon e imagen por defecto para compartir a partir de marca.json.
El logotipo (prefijo en cursiva + nombre) lo dibuja lockup.py.
Uso: python3 logos.py <marca.json> <carpeta_fuentes> <carpeta_salida>
"""
import json, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lockup import lockup, ajustar, partes, _font

marca, fuentes, out = sys.argv[1:4]
M = json.load(open(marca, encoding="utf-8"))
RED, INK, WHITE = (227, 18, 11), (10, 10, 10), (255, 255, 255)
BASE = {c: lockup(M, fuentes, 700, c) for c in (INK, WHITE)}


def lienzo(W, H, bg, fg, fw, fh, mode="RGB"):
    im = Image.new(mode, (W, H), bg)
    lk = ajustar(BASE[fg], W * fw, H * fh)
    im.paste(lk, ((W - lk.width) // 2, (H - lk.height) // 2), lk)
    return im


os.makedirs(out, exist_ok=True)
J = lambda n: os.path.join(out, n)
lienzo(2400, 900, WHITE, INK, 0.86, 0.5).save(J("logo-negro-fondo-blanco.png"))
lienzo(2400, 900, INK, WHITE, 0.86, 0.5).save(J("logo-blanco-fondo-negro.png"))
lienzo(2400, 900, (0, 0, 0, 0), INK, 0.86, 0.5, "RGBA").save(J("logo-negro-transparente.png"))
lienzo(2400, 900, (255, 255, 255, 0), WHITE, 0.86, 0.5, "RGBA").save(J("logo-blanco-transparente.png"))
icon = lienzo(1080, 1080, RED, WHITE, 0.86, 0.34)
icon.save(J("icono-rojo.png"))
lienzo(1200, 630, INK, WHITE, 0.62, 0.4).save(J("og-default.jpg"), quality=90)
for s, n in ((180, "apple-touch-icon.png"), (192, "icon-192.png"), (512, "icon-512.png")):
    icon.resize((s, s), Image.LANCZOS).save(J(n))

# favicon: la primera letra del nombre principal (la C de CORO), blanca sobre rojo
inicial = partes(M)[1][:1]
fav = Image.new("RGB", (256, 256), RED)
d = ImageDraw.Draw(fav)
f = _font(os.path.join(fuentes, "BodoniModa%5Bopsz,wght%5D.ttf"), 210)
b = d.textbbox((0, 0), inicial, font=f)
d.text(((256 - (b[2] - b[0])) // 2 - b[0], (256 - (b[3] - b[1])) // 2 - b[1]), inicial, font=f, fill=WHITE)
fav.resize((32, 32), Image.LANCZOS).save(J("favicon-32.png"))
fav.save(J("favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
print("  logos listos para", M["nombre"])
