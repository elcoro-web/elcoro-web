#!/usr/bin/env python3
"""Reel de El Coro (video 9:16, 1080x1920) con 1 a 3 notas.
Diseño "titular en grande": cada nota es una pantalla de color plano con la cifra o palabra grande (las cifras cuentan
desde 0), el titular en mayúsculas condensadas, la bajada, la línea en inglés y el pie "1 / 3 · ELCOROMAGAZINE.COM".
Las pantallas entran con una cortina de color desde abajo. Con 2 o 3 notas abre con "N NOTICIAS QUE TIENES QUE SABER".
Cierra con el logo y "La música del mundo, en tiempo real". Lleva una base rítmica original (sin derechos de terceros).

Ajustes opcionales por nota en redes/reel/<id>.json (solo con datos que estén en la nota):
  {"titular": "...", "bajada": "...", "hero": "11", "kicker": "Nominaciones", "chip": "Grammy 2027",
   "datos": [["2018", "El Mal Querer"], ["2022", "Motomami"], ["2026", "LUX"]], "destacar": 2,
   "barra": [8, 26]}

Uso: python3 reel.py <salida.mp4> <marca.json> <carpeta_fuentes> <nota1.json> [nota2.json nota3.json] [--sin-audio]
"""
import json, math, os, re, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from lockup import lockup, ajustar  # noqa: E402

args = [x for x in sys.argv[1:] if not x.startswith("--")]
SIN_AUDIO = "--sin-audio" in sys.argv
SALIDA, M, FD = args[0], json.load(open(args[1], encoding="utf-8")), args[2]
NOTAS = [json.load(open(p, encoding="utf-8")) for p in args[3:6]]

W, H, FPS = 1080, 1920, 30
X0, X1 = 72, 1008                  # márgenes laterales
Y_TOP, Y_PIE = 250, 1490           # cabecera y línea del pie (zona segura 4:5 centrada)
BS = "BigShouldersDisplay%5Bwght%5D.ttf"
IN = "Inter%5Bopsz,wght%5D.ttf"
MO = "IBMPlexMono-Medium.ttf"
_cache = {}


def F(name, size, w=None, opsz=None):
    k = (name, size, w, opsz)
    if k in _cache:
        return _cache[k]
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
    _cache[k] = f
    return f


def limpio(t):
    t = re.sub(r"<[^>]+>", " ", t or "")
    for k, v in (("&amp;", "&"), ("&nbsp;", " "), ("&quot;", '"'), ("&#39;", "'")):
        t = t.replace(k, v)
    return re.sub(r"\s+", " ", t).strip()


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = max(0.0, min(1.0, x))
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def wrap(d, text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def espaciado(d, xy, text, font, fill, track=0.18, anchor_right=False):
    """Texto monoespaciado con tracking (PIL no tiene letter-spacing)."""
    size = font.size
    adv = [d.textlength(c, font=font) + size * track for c in text]
    total = sum(adv) - size * track
    x, y = xy
    if anchor_right:
        x -= total
    for c, a in zip(text, adv):
        d.text((x, y), c, font=font, fill=fill)
        x += a
    return total


_DD = ImageDraw.Draw(Image.new("RGB", (8, 8)))

# Temas: fondo, cifra, texto, texto suave, chip (fondo, letra), acento de datos
TEMAS = {
    "blanco":   dict(bg=(255, 255, 255), hero=(225, 18, 11), txt=(10, 10, 10), suave=(70, 70, 70), gris=(140, 140, 140),
                     chip=((225, 18, 11), (255, 255, 255)), acento=(225, 18, 11), caja=(236, 236, 236)),
    "negro":    dict(bg=(10, 10, 10), hero=(242, 242, 242), txt=(242, 242, 242), suave=(205, 205, 205), gris=(140, 140, 140),
                     chip=((255, 255, 255), (10, 10, 10)), acento=(225, 18, 11), caja=(38, 38, 38)),
    "amarillo": dict(bg=(255, 212, 0), hero=(10, 10, 10), txt=(10, 10, 10), suave=(40, 40, 40), gris=(90, 80, 30),
                     chip=((10, 10, 10), (255, 212, 0)), acento=(225, 18, 11), caja=(240, 196, 0)),
    "noche":    dict(bg=(10, 10, 10), hero=(255, 212, 0), txt=(255, 212, 0), suave=(242, 242, 242), gris=(150, 150, 150),
                     chip=((255, 212, 0), (10, 10, 10)), acento=(255, 212, 0), caja=(38, 38, 38)),
    "negrorojo": dict(bg=(10, 10, 10), hero=(225, 18, 11), txt=(242, 242, 242), suave=(205, 205, 205), gris=(140, 140, 140),
                      chip=((225, 18, 11), (255, 255, 255)), acento=(225, 18, 11), caja=(38, 38, 38)),
    "rojo":     dict(bg=(225, 18, 11), hero=(255, 255, 255), txt=(255, 255, 255), suave=(255, 230, 228), gris=(255, 190, 186),
                     chip=((255, 255, 255), (225, 18, 11)), acento=(10, 10, 10), caja=(200, 14, 8)),
}
ROTACION = ["negrorojo", "rojo"]  # identidad negro y rojo


def tema_de(n, i, usados):
    bg = ((n.get("cov") or {}).get("bg") or "").lower()
    pref = None
    if pref and pref not in usados:
        return pref
    for t in ROTACION[i:] + ROTACION[:i]:
        if t not in usados:
            return t
    return ROTACION[i % len(ROTACION)]


def datos_nota(n):
    aj = {}
    pa = os.path.join(os.path.dirname(AQUI), "redes", "reel", n["id"] + ".json")
    if os.path.exists(pa):
        aj = json.load(open(pa, encoding="utf-8"))
    cov = n.get("cov") or {}
    titulo = limpio(n["title"])
    tit, baj = titulo, ""
    if ";" in titulo:
        tit, baj = [x.strip() for x in titulo.split(";", 1)]
    elif ":" in titulo and len(titulo.split(":")[0]) <= 42:
        tit, baj = [x.strip() for x in titulo.split(":", 1)]
    if baj:
        baj = baj[0].upper() + baj[1:]
        if not baj.endswith("."):
            baj += "."
    hero = limpio(re.sub(r"<br\s*/?>", " ", cov.get("f", ""))) or n.get("tag", "")
    en = limpio(n.get("titleEn", ""))
    return dict(
        id=n["id"], hero=aj.get("hero", hero), kicker=aj.get("kicker", cov.get("c", "")),
        chip=aj.get("chip", n.get("tag", "")), titular=aj.get("titular", tit), bajada=aj.get("bajada", baj),
        en=("EN — " + en) if en else "", datos=aj.get("datos"), destacar=aj.get("destacar"), barra=aj.get("barra"),
    )


# ---------------- pantallas ----------------
_LK = {}


def cabecera(im, d, T, chip_txt, logo_col, k=1.0):
    if logo_col not in _LK:
        _LK[logo_col] = ajustar(lockup(M, FD, 220, logo_col), 270, 62)
    lk = _LK[logo_col]
    im.paste(lk, (X0, Y_TOP), lk)
    if chip_txt:
        f = F(MO, 30)
        txt = chip_txt.upper()
        tw = sum(d.textlength(c, font=f) + 30 * 0.18 for c in txt) - 30 * 0.18
        bx1 = X1
        bx0 = bx1 - tw - 44
        cb, cf = T["chip"]
        d.rectangle([bx0, Y_TOP + 6, bx1, Y_TOP + 62], fill=cb)
        espaciado(d, (bx0 + 22, Y_TOP + 16), txt, f, cf)


def pie(d, T, idx, total, t):
    largo = X0 + (X1 - X0) * (0.12 + 0.88 * ease((t - 0.3) / 1.0))
    d.rectangle([X0, Y_PIE, largo, Y_PIE + 3], fill=T["txt"])
    f = F(MO, 30)
    if total > 1:
        espaciado(d, (X0, Y_PIE + 26), f"{idx} / {total}", f, T["txt"], track=0.35)
    espaciado(d, (X1, Y_PIE + 26), "ELCOROMAGAZINE.COM", f, T["txt"], track=0.22, anchor_right=True)


def revela(im, texto, font, x, y, alto, color, k):
    """Línea que sube dentro de una máscara (efecto titular)."""
    if k <= 0:
        return
    capa = Image.new("RGBA", (W, alto), (0, 0, 0, 0))
    ImageDraw.Draw(capa).text((x, int(alto * (1 - k)) + int(alto * 0.02)), texto, font=font, fill=color + (255,))
    im.paste(capa, (0, y), capa)


def ajusta(text, fuente, peso, maxw, maxh, grande, chico, inter, max_lineas):
    for size in range(grande, chico - 1, -2):
        f = F(fuente, size, peso)
        ls = wrap(_DD, text, f, maxw)
        lh = int(size * inter)
        if len(ls) <= max_lineas and len(ls) * lh <= maxh and all(_DD.textlength(l, font=f) <= maxw for l in ls):
            return f, ls, lh
    return f, ls, lh


class Nota:
    def __init__(self, n, idx, total, tema):
        self.D = datos_nota(n)
        self.idx, self.total, self.T = idx, total, TEMAS[tema]
        D = self.D
        # cifra grande: cabe en el ancho y en 420 px de alto
        hero = D["hero"].upper()
        size = 520
        while size > 80:
            f = F(BS, size, 900)
            b = _DD.textbbox((0, 0), hero, font=f)
            if b[2] - b[0] <= X1 - X0 and b[3] - b[1] <= 430:
                break
            size -= 6
        self.fh, self.hb = f, b
        self.hero = hero
        self.cuenta = int(hero) if re.fullmatch(r"\d{1,4}", hero) else None
        self.centrar = len(hero) <= 4 and not self.cuenta
        # bloque de texto
        self.fk = F(BS, 46, 800)
        self.ft, self.lt, self.lht = ajusta(D["titular"].upper(), BS, 800, X1 - X0, 330, 112, 60, 0.98, 3)
        self.fb, self.lb, self.lhb = ajusta(D["bajada"], IN, 500, X1 - X0, 140, 38, 28, 1.3, 3) if D["bajada"] else (None, [], 0)
        self.fe, self.le, self.lhe = ajusta(D["en"], IN, 400, X1 - X0, 76, 28, 24, 1.35, 2) if D["en"] else (None, [], 0)

    def dibuja(self, t):
        T, D = self.T, self.D
        im = Image.new("RGB", (W, H), T["bg"])
        d = ImageDraw.Draw(im)
        cabecera(im, d, T, D["chip"], T["txt"] if T["bg"] != (255, 212, 0) else (10, 10, 10))
        # cifra
        y_hero = Y_TOP + 130
        b = self.hb
        if self.cuenta is not None:
            v = round(self.cuenta * ease_io((t - 0.25) / 0.9))
            txt = str(v)
        else:
            txt = self.hero
        bb = d.textbbox((0, 0), txt, font=self.fh)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0] if self.centrar else X0 - bb[0]
        alto_h = b[3] - b[1]
        k = ease((t - 0.2) / 0.55)
        if k > 0:
            capa = Image.new("RGBA", (W, alto_h + 20), (0, 0, 0, 0))
            ImageDraw.Draw(capa).text((x, int((alto_h + 20) * (1 - k)) - b[1]), txt, font=self.fh, fill=T["hero"] + (255,))
            im.paste(capa, (0, y_hero), capa)
        # bloque inferior, anclado sobre el pie
        bloques = []
        if D["kicker"]:
            bloques.append(("k", 54))
        bloques.append(("t", len(self.lt) * self.lht))
        if self.lb:
            bloques.append(("b", 14 + len(self.lb) * self.lhb))
        if D["datos"]:
            bloques.append(("d", 30 + 170))
        if D["barra"]:
            bloques.append(("r", 0))
        if self.le:
            bloques.append(("e", 22 + len(self.le) * self.lhe))
        alto = sum(h for _, h in bloques)
        y_b = min(y_hero + alto_h + 80, Y_PIE - 50 - alto)
        if D["barra"]:      # la barra va arriba del titular
            y_b = min(y_hero + alto_h + 60, Y_PIE - 50 - alto - 74)
            n_on, n_tot = D["barra"]
            seg = (X1 - X0) / n_tot
            on = int(round(n_tot * ease((t - 0.9) / 1.0)))
            for s in range(n_tot):
                c = T["acento"] if s < n_on else T["txt"]
                if s < on:
                    d.rectangle([X0 + s * seg, y_b, X0 + (s + 1) * seg - 5, y_b + 34], fill=c)
            y_b += 34 + 40
        y = y_b
        tk = t - 0.75
        if D["kicker"]:
            revela(im, D["kicker"].upper(), self.fk, X0, y, 54, T["txt"] if T["hero"] == T["txt"] else T["txt"], ease(tk / 0.4))
            y += 54
        for i, l in enumerate(self.lt):
            revela(im, l, self.ft, X0, y, self.lht, T["txt"], ease((tk - 0.1 - 0.12 * i) / 0.45))
            y += self.lht
        if self.lb:
            y += 14
            k = ease((t - 1.45) / 0.5)
            if k > 0:
                c = tuple(int(T["bg"][j] + (T["suave"][j] - T["bg"][j]) * k) for j in range(3))
                for l in self.lb:
                    d.text((X0, y + int(12 * (1 - k))), l, font=self.fb, fill=c)
                    y += self.lhb
            else:
                y += len(self.lb) * self.lhb
        if D["datos"]:
            y += 30
            n = len(D["datos"])
            gap = 18
            w = (X1 - X0 - gap * (n - 1)) / n
            for i, (grande, chico) in enumerate(D["datos"]):
                k = ease((t - 1.7 - 0.25 * i) / 0.35)
                if k <= 0:
                    continue
                dest = D.get("destacar") == i
                caja = T["acento"] if dest else T["caja"]
                letra = (255, 255, 255) if dest or T["bg"] == (10, 10, 10) else T["txt"]
                bx = X0 + i * (w + gap)
                yy = y + int(30 * (1 - k))
                d.rectangle([bx, yy, bx + w, yy + 170], fill=caja)
                d.text((bx + 22, yy + 18), str(grande), font=F(BS, 84, 800), fill=letra)
                d.text((bx + 22, yy + 116), str(chico), font=F(IN, 28, 600), fill=letra)
            y += 170
        if self.le:
            y += 22
            k = ease((t - 2.1) / 0.6)
            if k > 0:
                c = tuple(int(T["bg"][j] + (T["gris"][j] - T["bg"][j]) * k) for j in range(3))
                for l in self.le:
                    d.text((X0, y), l, font=self.fe, fill=c)
                    y += self.lhe
        pie(d, T, self.idx, self.total, t)
        return im


class Portada:
    def __init__(self, total):
        self.total = total
        self.T = TEMAS["rojo"]
        self.lineas = [f"{total} NOTICIAS", "QUE TIENES", "QUE SABER"]

    def dibuja(self, t):
        T = self.T
        im = Image.new("RGB", (W, H), T["bg"])
        d = ImageDraw.Draw(im)
        cabecera(im, d, T, "HOY", (255, 255, 255))
        f = F(BS, 168, 900)
        y = 610
        for i, l in enumerate(self.lineas):
            revela(im, l, f, X0 - 4, y, 172, (255, 255, 255), ease((t - 0.1 - 0.12 * i) / 0.45))
            y += 160
        k = ease((t - 0.7) / 0.5)
        if k > 0:
            d.text((X0, y + 40), f"{self.total} stories you need to know", font=F(IN, 36, 500),
                   fill=tuple(int(T["bg"][j] + (255 - T["bg"][j]) * k) for j in range(3)))
        espaciado(d, (X0, Y_PIE + 26), "MÚSICA · EN TIEMPO REAL", F(MO, 30), (255, 255, 255), track=0.3)
        return im


class Cierre:
    def __init__(self):
        self.T = TEMAS["rojo"]
        self.lk = ajustar(lockup(M, FD, 400, (255, 255, 255)), 860, 240)

    def dibuja(self, t):
        T = self.T
        im = Image.new("RGB", (W, H), T["bg"])
        d = ImageDraw.Draw(im)
        k = ease(t / 0.7)
        s = 1.12 - 0.12 * k
        lk = self.lk.resize((int(self.lk.width * s), int(self.lk.height * s)), Image.LANCZOS)
        im.paste(lk, ((W - lk.width) // 2, 760 - lk.height // 2), lk)
        f = F(BS, 74, 800)
        for i, l in enumerate(("LA MÚSICA DEL MUNDO,", "EN TIEMPO REAL.")):
            tw = d.textlength(l, font=f)
            capa = Image.new("RGBA", (W, 84), (0, 0, 0, 0))
            kk = ease((t - 0.45 - 0.12 * i) / 0.45)
            if kk > 0:
                ImageDraw.Draw(capa).text(((W - tw) / 2, int(84 * (1 - kk))), l, font=f, fill=(255, 255, 255, 255))
                im.paste(capa, (0, 930 + i * 80), capa)
        kk = ease((t - 1.0) / 0.5)
        if kk > 0:
            c = tuple(int(T["bg"][j] + (255 - T["bg"][j]) * kk) for j in range(3))
            fs = F(IN, 36, 600)
            tx = "Sigue a El Coro para más"
            d.text(((W - d.textlength(tx, font=fs)) / 2, 1130), tx, font=fs, fill=c)
            fm = F(MO, 30)
            tw = sum(d.textlength(ch, font=fm) + 30 * 0.3 for ch in "ELCOROMAGAZINE.COM") - 9
            espaciado(d, ((W - tw) / 2, 1196), "ELCOROMAGAZINE.COM", fm, c, track=0.3)
        return im


# ---------------- línea de tiempo ----------------
WIPE = 0.45
escenas = []
total = len(NOTAS)
if total > 1:
    escenas.append((Portada(total), 2.4))
usados = []
for i, n in enumerate(NOTAS):
    tema = tema_de(n, i, usados[-1:])
    usados.append(tema)
    escenas.append((Nota(n, i + 1, total, tema), 7.2 if total == 1 else 6.4))
escenas.append((Cierre(), 3.0))
DUR = sum(d for _, d in escenas)


def cuadro(t):
    acc = 0.0
    for j, (e, dur) in enumerate(escenas):
        if t < acc + dur or j == len(escenas) - 1:
            lt = t - acc
            im = e.dibuja(lt)
            if j > 0 and lt < WIPE:      # cortina desde abajo sobre la pantalla anterior
                prev, pdur = escenas[j - 1]
                base = prev.dibuja(pdur)
                y = int(H * (1 - ease_io(lt / WIPE)))
                base.paste(im.crop((0, y, W, H)), (0, y))
                return base
            return im
        acc += dur


def audio(path, dur, bpm=112):
    """Base original: bombo, hi-hat y un bajo de dos notas. Nada de terceros."""
    sr = 44100
    n = int(dur * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    beat = 60 / bpm
    rng = np.random.default_rng(7)
    for b in range(int(dur / beat) + 1):
        s = int(b * beat * sr)
        L = int(0.35 * sr)
        tt = np.arange(L) / sr
        kick = np.sin(2 * np.pi * (48 + 90 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)
        out[s:s + L] += 0.9 * kick[: max(0, min(L, n - s))]
        h = int((b + 0.5) * beat * sr)
        Lh = int(0.06 * sr)
        hat = rng.standard_normal(Lh) * np.exp(-np.arange(Lh) / sr * 70)
        hat = np.diff(hat, prepend=0)
        out[h:h + Lh] += 0.18 * hat[: max(0, min(Lh, n - h))]
        if b % 4 == 2:
            Ls = int(0.12 * sr)
            sn = rng.standard_normal(Ls) * np.exp(-np.arange(Ls) / sr * 30)
            out[s:s + Ls] += 0.28 * sn[: max(0, min(Ls, n - s))]
    notas_bajo = [55.0, 55.0, 65.41, 49.0]
    for bar in range(int(dur / (beat * 4)) + 1):
        f0 = notas_bajo[bar % 4]
        for q in (0, 1.5, 2.5):
            s = int((bar * 4 + q) * beat * sr)
            L = int(beat * 0.9 * sr)
            tt = np.arange(L) / sr
            tone = (np.sin(2 * np.pi * f0 * tt) + 0.3 * np.sin(2 * np.pi * 2 * f0 * tt)) * np.exp(-tt * 3)
            out[s:s + L] += 0.35 * tone[: max(0, min(L, n - s))]
    fade = int(1.2 * sr)
    out[-fade:] *= np.linspace(1, 0, fade)
    out[: int(0.02 * sr)] *= np.linspace(0, 1, int(0.02 * sr))
    out = out / (np.abs(out).max() + 1e-9) * 0.6
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


os.makedirs(os.path.dirname(os.path.abspath(SALIDA)), exist_ok=True)
tmp_wav = tempfile.mktemp(suffix=".wav")
if SIN_AUDIO:
    entrada_audio = ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
else:
    audio(tmp_wav, DUR)
    entrada_audio = ["-i", tmp_wav]
cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       *entrada_audio, "-shortest", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
       "-profile:v", "high", "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-movflags", "+faststart", SALIDA]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for i in range(int(DUR * FPS)):
    p.stdin.write(cuadro(i / FPS).tobytes())
p.stdin.close()
ok = p.wait() == 0
if os.path.exists(tmp_wav):
    os.remove(tmp_wav)
if not ok:
    sys.exit("ffmpeg falló")
# portada del video: la primera nota ya armada
primera = escenas[1 if total > 1 else 0][0]
primera.dibuja(5.0).save(SALIDA.rsplit(".", 1)[0] + ".jpg", quality=90)
print("listo:", SALIDA, f"({DUR:.1f} s)")
