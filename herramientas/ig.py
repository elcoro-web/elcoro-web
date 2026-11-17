#!/usr/bin/env python3
"""Imágenes de El Coro para redes, a partir de una nota.
Genera en <carpeta_salida>:
  <id>-1.jpg      portada del carrusel (1080x1350, 4:5)
  <id>-2.jpg      "Lo esencial" con los puntos clave (1080x1350)
  <id>-story.jpg  historia (1080x1920, 9:16)
Uso: python3 ig.py <nota.json> <carpeta_fuentes> <carpeta_salida> <marca.json>
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

a = json.load(open(sys.argv[1], encoding="utf-8"))
FD, OUT = sys.argv[2], sys.argv[3]
M = json.load(open(sys.argv[4], encoding="utf-8"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lockup import lockup, ajustar  # noqa: E402
os.makedirs(OUT, exist_ok=True)

BS = "BigShouldersDisplay%5Bwght%5D.ttf"
BO = "BodoniModa%5Bopsz,wght%5D.ttf"
BOI = "BodoniModa-Italic%5Bopsz,wght%5D.ttf"
IN = "Inter%5Bopsz,wght%5D.ttf"
MO = "IBMPlexMono-Medium.ttf"
RED, INK, GREY, WHITE = (227, 18, 11), (10, 10, 10), (105, 105, 105), (255, 255, 255)
SECC = {"noticias": "Noticias", "premios": "Premios", "listas": "Listas", "lanzamientos": "Lanzamientos",
        "critica": "Crítica", "industria": "Industria", "artistas": "Para artistas"}


def F(name, size, w=None, opsz=None):
    f = ImageFont.truetype(os.path.join(FD, name), size)
    try:
        vals = []
        for ax in f.get_variation_axes():
            nm = ax.get("name", b"")
            nm = (nm.decode("utf-8", "ignore") if isinstance(nm, bytes) else str(nm)).lower()
            if "eight" in nm or "wght" in nm:
                vals.append(max(ax["minimum"], min(w or ax["default"], ax["maximum"])))
            elif "optic" in nm or "opsz" in nm:
                vals.append(max(ax["minimum"], min(opsz or ax["maximum"], ax["maximum"])))
            else:
                vals.append(ax.get("default", ax["minimum"]))
        f.set_variation_by_axes(vals)
    except Exception:
        pass
    return f


def hexc(h):
    h = h.lstrip("#")
    h = "".join(c * 2 for c in h) if len(h) == 3 else h
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def limpio(t):
    t = re.sub(r"<[^>]+>", "", t or "")
    for k, v in (("&amp;", "&"), ("&nbsp;", " "), ("&quot;", '"'), ("&#39;", "'"), ("&lt;", "<"), ("&gt;", ">")):
        t = t.replace(k, v)
    return re.sub(r"\s+", " ", t).strip()


def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def ajusta_texto(d, text, fuente, peso, maxw, maxh, grande, chico, inter=1.08, max_lineas=6, opsz=None):
    for size in range(grande, chico - 1, -2):
        f = F(fuente, size, peso, opsz)
        ls = wrap(d, text, f, maxw)
        lh = int(size * inter)
        if len(ls) * lh <= maxh and len(ls) <= max_lineas:
            return f, ls, lh
    return f, ls, lh


cv = a.get("cov") or {"f": M["nombre"], "bg": "#0a0a0a", "fg": "#fff", "c": a["sec"], "e": a["tag"]}
BG, FG = hexc(cv["bg"]), hexc(cv["fg"])
seccion = SECC.get(a["sec"], a["sec"].capitalize())
kicker = (seccion if a["tag"].lower() in ("lista", a["sec"].lower(), seccion.lower()) else seccion + " · " + a["tag"]).upper()
titulo = limpio(a["title"])


def bloque_portada(im, x0, y0, x1, y1, logo=True):
    """La portada tipográfica de la nota (cifra o palabra grande) dentro del rectángulo dado."""
    d = ImageDraw.Draw(im)
    W, H = x1 - x0, y1 - y0
    d.rectangle([x0, y0, x1, y1], fill=BG)
    if cv.get("bd") or BG == WHITE:
        d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=INK, width=4)
    m = 56
    if logo:
        lk = ajustar(lockup(M, FD, 220, FG), W * 0.30, 70)
        im.paste(lk, (x0 + m, y0 + m - 6), lk)
    ct = cv.get("c", "").upper()
    fc = F(MO, 26)
    d.text((x1 - m - d.textlength(ct, font=fc), y0 + m + 10), ct, font=fc, fill=FG)
    raw = cv["f"]
    ital = "<i>" in raw
    lines = [limpio(x) for x in re.split(r"<br\s*/?>", raw)]
    maxw, maxh, size = W - 2 * m, int(H * 0.62), 620
    while size > 50:
        f = F(BOI, size, 900) if ital else F(BS, size, 900)
        bb = [d.textbbox((0, 0), l, font=f) for l in lines]
        tw = max(b[2] - b[0] for b in bb)
        th = sum(b[3] - b[1] for b in bb) + (len(lines) - 1) * int(size * 0.08)
        if tw <= maxw and th <= maxh:
            break
        size -= 8
    y = y0 + (H - th) // 2 + 20
    for l, b in zip(lines, bb):
        x = x0 + (W - (b[2] - b[0])) // 2 if cv.get("al") == "center" or len(lines) == 1 else x0 + m
        d.text((x - b[0], y - b[1]), l, font=f, fill=FG)
        y += (b[3] - b[1]) + int(size * 0.08)
    fe = F(IN, 34, 700)
    d.text((x0 + m, y1 - m - 34), cv.get("e", ""), font=fe, fill=FG)


def pie(d, W, y, texto="elcoromagazine.com"):
    d.rectangle([64, y + 14, 64 + 64, y + 21], fill=RED)
    d.text((64 + 84, y), texto, font=F(IN, 28, 600), fill=GREY)


# 1 · portada del carrusel (4:5)
W, H = 1080, 1350
im = Image.new("RGB", (W, H), WHITE)
d = ImageDraw.Draw(im)
bloque_portada(im, 0, 0, W, 780)
d.text((64, 832), kicker, font=F(MO, 26), fill=RED)
f, ls, lh = ajusta_texto(d, titulo, BO, 700, W - 128, 1220 - 890, 74, 44, inter=1.08, max_lineas=5, opsz=20)
y = 884
for l in ls:
    d.text((64, y), l, font=f, fill=INK)
    y += lh
pie(d, W, 1262, "Nota completa: link en la bio  ·  elcoromagazine.com")
im.save(os.path.join(OUT, a["id"] + "-1.jpg"), quality=90, optimize=True, progressive=True)

# 2 · lo esencial (4:5)
im = Image.new("RGB", (W, H), WHITE)
d = ImageDraw.Draw(im)
lk = ajustar(lockup(M, FD, 220, INK), 250, 70)
im.paste(lk, (64, 58), lk)
d.text((W - 64 - d.textlength(kicker, font=F(MO, 24)), 82), kicker, font=F(MO, 24), fill=RED)
d.rectangle([64, 168, W - 64, 172], fill=INK)
d.rectangle([64, 228, 64 + 26, 228 + 26], fill=RED)
d.text((112, 222), "LO ESENCIAL", font=F(IN, 34, 800), fill=INK)
puntos = [limpio(b) for b in (a.get("brief") or [])][:4] or [limpio(a.get("dek", ""))]
zona_alta, zona_baja = 300, 1200
disp = zona_baja - zona_alta - (len(puntos) - 1) * 44
for size in range(48, 28, -2):
    fp = F(IN, size, 500, 32)
    lh = int(size * 1.3)
    bloques = [wrap(d, p, fp, W - 128 - 70) for p in puntos]
    if sum(len(b) for b in bloques) * lh <= disp:
        break
y = zona_alta
for i, b in enumerate(bloques):
    d.text((64, y + 2), f"{i + 1:02d}", font=F(MO, 28), fill=RED)
    for l in b:
        d.text((134, y), l, font=fp, fill=INK)
        y += lh
    y += 44
d.rectangle([64, 1236, W - 64, 1238], fill=(220, 220, 220))
pie(d, W, 1262, "Nota completa: link en la bio  ·  elcoromagazine.com")
im.save(os.path.join(OUT, a["id"] + "-2.jpg"), quality=90, optimize=True, progressive=True)

# 3 · historia (9:16)
W, H = 1080, 1920
im = Image.new("RGB", (W, H), WHITE)
d = ImageDraw.Draw(im)
bloque_portada(im, 0, 0, W, 1060)
d.text((64, 1122), kicker, font=F(MO, 28), fill=RED)
f, ls, lh = ajusta_texto(d, titulo, BO, 700, W - 128, 1600 - 1180, 84, 50, inter=1.08, max_lineas=6, opsz=20)
y = 1176
for l in ls:
    d.text((64, y), l, font=f, fill=INK)
    y += lh
bw, bh = 520, 92
bx, by = (W - bw) // 2, 1700
d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=46, fill=INK)
cta = "LEE LA NOTA · LINK EN BIO"
fc = F(IN, 28, 800)
d.text((bx + (bw - d.textlength(cta, font=fc)) / 2, by + 30), cta, font=fc, fill=WHITE)
fd = F(IN, 28, 600)
d.text(((W - d.textlength("elcoromagazine.com", font=fd)) / 2, 1830), "elcoromagazine.com", font=fd, fill=GREY)
im.save(os.path.join(OUT, a["id"] + "-story.jpg"), quality=90, optimize=True, progressive=True)
print("listo:", a["id"])
