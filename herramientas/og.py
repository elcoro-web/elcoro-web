#!/usr/bin/env python3
"""Imagen para compartir (1200x630) de cada nota, con la portada tipográfica y el titular.
Uso: python3 og.py <a.json> <carpeta_fuentes> <carpeta_salida> <marca.json>
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

A = json.load(open(sys.argv[1], encoding="utf-8"))
FD, OUT = sys.argv[2], sys.argv[3]
M = json.load(open(sys.argv[4], encoding="utf-8"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lockup import lockup, ajustar  # noqa: E402
LOGO_INK = lockup(M, FD, 300, (10, 10, 10))
os.makedirs(OUT, exist_ok=True)
BS = "BigShouldersDisplay%5Bwght%5D.ttf"
BO = "BodoniModa%5Bopsz,wght%5D.ttf"
BOI = "BodoniModa-Italic%5Bopsz,wght%5D.ttf"
IN = "Inter%5Bopsz,wght%5D.ttf"
MO = "IBMPlexMono-Medium.ttf"


def F(name, size, w=None):
    f = ImageFont.truetype(os.path.join(FD, name), size)
    if w is not None:
        try:
            vals = []
            for a in f.get_variation_axes():
                nm = a.get("name", b"")
                nm = nm.decode("utf-8", "ignore") if isinstance(nm, bytes) else str(nm)
                is_w = "eight" in nm.lower() or "wght" in nm.lower()
                vals.append(min(w, a["maximum"]) if is_w else (32 if name == IN else a["maximum"]))
            f.set_variation_by_axes(vals)
        except Exception:
            pass
    return f


def hexc(h):
    h = h.lstrip("#")
    h = "".join(c * 2 for c in h) if len(h) == 3 else h
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


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


W, H, LP = 1200, 630, 460
RED, INK, GREY = (227, 18, 11), (10, 10, 10), (110, 110, 110)
for a in A:
    cv = a["cov"] or {"f": M["nombre"], "bg": "#0a0a0a", "fg": "#fff", "c": a["sec"], "e": a["tag"]}
    im = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(im)
    bg, fg = hexc(cv["bg"]), hexc(cv["fg"])
    d.rectangle([0, 0, LP, H], fill=bg)
    if cv.get("bd") or bg == (255, 255, 255):
        d.rectangle([0, 0, LP, H], outline=INK, width=3)
    d.text((36, 40), cv["c"].upper(), font=F(MO, 22), fill=fg)
    raw = cv["f"]
    ital = "<i>" in raw
    lines = [re.sub("<[^>]+>", "", x) for x in re.split(r"<br\s*/?>", raw)]
    maxw, maxh, size = LP - 72, (380 if len(lines) == 1 else 400), 420
    while size > 40:
        f = F(BOI, size, 900) if ital else F(BS, size, 900)
        lh = [d.textbbox((0, 0), l, font=f) for l in lines]
        tw = max(b[2] - b[0] for b in lh)
        th = sum(b[3] - b[1] for b in lh) + (len(lines) - 1) * int(size * 0.08)
        if tw <= maxw and th <= maxh:
            break
        size -= 6
    y = (H - th) // 2 + 10
    for l, b in zip(lines, lh):
        x = 36 if cv.get("al") != "center" else (LP - (b[2] - b[0])) // 2
        d.text((x - b[0], y - b[1]), l, font=f, fill=fg)
        y += (b[3] - b[1]) + int(size * 0.08)
    d.text((36, H - 74), cv["e"], font=F(IN, 30, 700), fill=fg)
    X = LP + 48
    RW = W - X - 48
    lk = ajustar(LOGO_INK, RW * 0.6, 50)
    im.paste(lk, (X, 34), lk)
    lb = (X, 34, X + lk.width, 34 + lk.height)
    kt = (a["sec"] if a["tag"].lower() in ("lista", a["sec"].lower()) else a["sec"] + " · " + a["tag"]).upper()
    d.text((X, lb[3] + 26), kt, font=F(MO, 21), fill=RED)
    top, bottom = lb[3] + 70, H - 90
    title = a["title"].upper()
    for size in range(78, 34, -2):
        hf = F(BS, size, 800)
        tl = wrap(d, title, hf, RW)
        lh2 = int(size * 1.02)
        if len(tl) * lh2 <= bottom - top and len(tl) <= 5:
            break
    y = top
    for l in tl:
        d.text((X, y), l, font=hf, fill=INK)
        y += lh2
    d.rectangle([X, H - 62, X + 56, H - 56], fill=RED)
    d.text((X + 72, H - 74), M["dominio"], font=F(IN, 22, 600), fill=GREY)
    im.save(os.path.join(OUT, a["id"] + ".jpg"), quality=88, optimize=True, progressive=True)
print("  imágenes para compartir:", len(A))
