#!/usr/bin/env python3
"""Reel de El Coro (video 9:16, 1080x1920, ~12 s, sin música) a partir de una nota.
Tres escenas con la identidad de las imágenes de ig.py:
  1. portada: la cifra o palabra grande y el titular, que entra línea por línea;
  2. lo esencial: los puntos clave, uno tras otro;
  3. cierre: "Lee la nota completa · link en la bio".
Genera <carpeta_salida>/<id>-reel.mp4 y <id>-reel.jpg (portada del video).
Uso: python3 reel.py <nota.json> <carpeta_fuentes> <carpeta_salida> <marca.json>
"""
import os, subprocess, sys
from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
# Reutiliza fuentes, colores y la portada tipográfica de ig.py (solo sus definiciones, sin generar imágenes).
_src = open(os.path.join(AQUI, "ig.py"), encoding="utf-8").read().split("# 1 · portada")[0]
_ns = {"__file__": os.path.join(AQUI, "ig.py"), "__name__": "ig"}
exec(compile(_src, "ig.py", "exec"), _ns)
g = _ns.__getitem__
a, OUT, M, FD = g("a"), g("OUT"), g("M"), g("FD")
F, wrap, ajusta_texto, bloque_portada, limpio = g("F"), g("wrap"), g("ajusta_texto"), g("bloque_portada"), g("limpio")
lockup, ajustar = g("lockup"), g("ajustar")
BS, BO, IN, MO = g("BS"), g("BO"), g("IN"), g("MO")
RED, INK, GREY, WHITE, BG, FG = g("RED"), g("INK"), g("GREY"), g("WHITE"), g("BG"), g("FG")
kicker, titulo = g("kicker"), g("titulo")

W, H, FPS = 1080, 1920, 30
puntos = [limpio(b) for b in (a.get("brief") or [])][:4] or [limpio(a.get("dek", ""))]
T1 = 3.6                       # portada
T2 = 1.0 + 2.2 * len(puntos)   # lo esencial
T3 = 2.6                       # cierre
TOTAL = T1 + T2 + T3


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


# ---------- capas fijas ----------
TOP = 1060
cover = Image.new("RGB", (W, TOP), WHITE)
bloque_portada(cover, 0, 0, W, TOP)
_d = ImageDraw.Draw(Image.new("RGB", (W, H)))
ft, lt, lht = ajusta_texto(_d, titulo, BO, 700, W - 128, 1640 - 1190, 84, 50, inter=1.08, max_lineas=6, opsz=20)

fp = None
for size in range(64, 30, -2):
    fp = F(IN, size, 500, 32)
    lhp = int(size * 1.32)
    bloques = [wrap(_d, p, fp, W - 128 - 80) for p in puntos]
    if sum(len(b) for b in bloques) * lhp + (len(puntos) - 1) * 60 <= 1380:
        break
lk_ink = ajustar(lockup(M, FD, 220, INK), 260, 72)
lk_fg = ajustar(lockup(M, FD, 220, FG), 360, 100)


def escena_portada(t):
    im = Image.new("RGB", (W, H), WHITE)
    s = 1.10 - 0.10 * ease(t / 2.4)          # zoom suave hacia atrás
    cw, ch = int(W * s), int(TOP * s)
    c = cover.resize((cw, ch), Image.LANCZOS).crop(((cw - W) // 2, (ch - TOP) // 2, (cw - W) // 2 + W, (ch - TOP) // 2 + TOP))
    im.paste(c, (0, 0))
    d = ImageDraw.Draw(im)
    k = ease((t - 0.5) / 0.4)
    if k > 0:
        d.text((64, 1122 + int(20 * (1 - k))), kicker, font=F(MO, 28), fill=RED)
    y = 1186
    for i, l in enumerate(lt):
        k = ease((t - 0.7 - 0.18 * i) / 0.45)
        if k > 0:
            capa = Image.new("RGBA", (W, lht + 20), (255, 255, 255, 0))
            ImageDraw.Draw(capa).text((64, 0), l, font=ft, fill=INK + (int(255 * k),))
            im.paste(capa, (0, y + int(40 * (1 - k))), capa)
        y += lht
    fd = F(IN, 30, 600)
    d.text((64, 1820), "elcoromagazine.com", font=fd, fill=GREY)
    return im


def escena_esencial(t):
    im = Image.new("RGB", (W, H), WHITE)
    d = ImageDraw.Draw(im)
    im.paste(lk_ink, (64, 96), lk_ink)
    fk = F(MO, 26)
    d.text((W - 64 - d.textlength(kicker, font=fk), 122), kicker, font=fk, fill=RED)
    d.rectangle([64, 210, W - 64, 214], fill=INK)
    d.rectangle([64, 214, 64 + int((W - 128) * min(1, t / T2)), 222], fill=RED)   # barra de avance
    d.rectangle([64, 290, 64 + 30, 290 + 30], fill=RED)
    d.text((116, 282), "LO ESENCIAL", font=F(IN, 40, 800), fill=INK)
    total = sum(len(b) for b in bloques) * lhp + (len(puntos) - 1) * 60
    y = 400 + max(0, (1380 - total) // 2) // 2
    for i, b in enumerate(bloques):
        k = ease((t - 0.5 - 2.2 * i) / 0.5)
        if k > 0:
            alto = len(b) * lhp
            capa = Image.new("RGBA", (W, alto + 30), (255, 255, 255, 0))
            cd = ImageDraw.Draw(capa)
            a8 = int(255 * k)
            cd.text((64, 6), f"{i + 1:02d}", font=F(MO, 32), fill=RED + (a8,))
            yy = 0
            for l in b:
                cd.text((144, yy), l, font=fp, fill=INK + (a8,))
                yy += lhp
            im.paste(capa, (int(-30 * (1 - k)), y), capa)
        y += len(b) * lhp + 60
    d.text((64, 1820), "elcoromagazine.com", font=F(IN, 30, 600), fill=GREY)
    return im


def escena_cierre(t):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    k = ease(t / 0.5)
    im.paste(lk_fg, ((W - lk_fg.width) // 2, 560 + int(30 * (1 - k))), lk_fg)
    f = F(BO, 96, 700, 20)
    for i, l in enumerate(("Lee la nota", "completa")):
        kk = ease((t - 0.25 - 0.15 * i) / 0.45)
        if kk > 0:
            tw = d.textlength(l, font=f)
            capa = Image.new("RGBA", (W, 130), (0, 0, 0, 0))
            ImageDraw.Draw(capa).text(((W - tw) / 2, 0), l, font=f, fill=FG + (int(255 * kk),))
            im.paste(capa, (0, 800 + i * 112 + int(30 * (1 - kk))), capa)
    kk = ease((t - 0.8) / 0.4)
    if kk > 0:
        bw, bh, by = 560, 100, 1110
        bx = (W - bw) // 2
        ink_btn = INK if sum(BG) > 300 else WHITE
        txt_btn = WHITE if ink_btn == INK else INK
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=50, fill=ink_btn)
        cta = "LINK EN LA BIO"
        fc = F(IN, 34, 800)
        d.text((bx + (bw - d.textlength(cta, font=fc)) / 2, by + 30), cta, font=fc, fill=txt_btn)
        fd = F(IN, 32, 600)
        d.text(((W - d.textlength("elcoromagazine.com", font=fd)) / 2, 1260), "elcoromagazine.com", font=fd, fill=FG)
    return im


def cuadro(t):
    if t < T1:
        return escena_portada(t)
    if t < T1 + T2:
        return escena_esencial(t - T1)
    return escena_cierre(t - T1 - T2)


os.makedirs(OUT, exist_ok=True)
mp4 = os.path.join(OUT, a["id"] + "-reel.mp4")
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
       "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
       "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", mp4]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
n = int(TOTAL * FPS)
for i in range(n):
    p.stdin.write(cuadro(i / FPS).tobytes())
p.stdin.close()
if p.wait() != 0:
    sys.exit("ffmpeg falló")
cuadro(T1 - 0.01).save(os.path.join(OUT, a["id"] + "-reel.jpg"), quality=90)
print("listo:", mp4, f"({TOTAL:.1f} s)")
