#!/usr/bin/env python3
"""Series de El Coro para Instagram (carruseles 4:5, 1080x1350) con concepto de "franquicia", al estilo de las
listas y los cuadros de nominados de las revistas grandes, pero 100 % tipográficos: sin fotos de artistas ni portadas
de discos (no tenemos derechos sobre ellas).

Formatos (campo "tipo" de cada lámina):
  portada    - lámina de entrada de la serie: etiqueta en caja + palabra o cifra gigante + título
  lista      - ranking tipo chart: puesto, nombre, detalle, dato a la derecha, chips ("DEBUT", "5 SEMANAS EN EL NO. 1")
  nominados  - cuadro de nominados de una categoría: casillas tipográficas con la obra y el artista
  barras     - ranking con barras proporcionales (ej. los más nominados)
  cierre     - "Lee la nota completa · link en la bio"

Uso: python3 series.py <serie.json> <carpeta_salida>
El JSON: {"id": "...", "serie": "LISTA", "fuente": "Billboard / Luminate", "laminas": [{...}, ...]}
Todo dato tiene que venir de una nota publicada en elcoromagazine.com.
"""
import json, os, re, sys
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
from lockup import lockup, ajustar  # noqa: E402

FD = os.path.join(RAIZ, "marca", "fuentes")
M = json.load(open(os.path.join(RAIZ, "marca.json"), encoding="utf-8"))
BS = "BigShouldersDisplay%5Bwght%5D.ttf"
BO = "BodoniModa%5Bopsz,wght%5D.ttf"
BOI = "BodoniModa-Italic%5Bopsz,wght%5D.ttf"
IN = "Inter%5Bopsz,wght%5D.ttf"
MO = "IBMPlexMono-Medium.ttf"
W, H = 1080, 1350
X0, X1 = 64, 1016
RED, INK, WHITE, YEL, CREAM = (225, 18, 11), (12, 12, 12), (255, 255, 255), (255, 212, 0), (240, 235, 225)
GRIS, LINEA = (150, 150, 150), (60, 60, 60)
TEMAS = {
    "rojo": dict(banda=RED, banda_txt=WHITE, fondo=INK, txt=WHITE, acento=RED, suave=(170, 170, 170)),
    "amarillo": dict(banda=YEL, banda_txt=INK, fondo=INK, txt=WHITE, acento=YEL, suave=(170, 170, 170)),
    "blanco": dict(banda=INK, banda_txt=WHITE, fondo=WHITE, txt=INK, acento=RED, suave=(95, 95, 95)),
    "negro": dict(banda=INK, banda_txt=WHITE, fondo=INK, txt=WHITE, acento=RED, suave=(170, 170, 170), grande_c=RED),
    "crema": dict(banda=RED, banda_txt=WHITE, fondo=CREAM, txt=INK, acento=RED, suave=(95, 90, 80)),
}
CASILLAS = [(225, 18, 11), (255, 212, 0), (30, 58, 160), (16, 110, 72), (240, 235, 225), (12, 12, 12), (232, 90, 40),
            (120, 40, 140)]
_c = {}


def F(name, size, w=None, opsz=None):
    k = (name, size, w, opsz)
    if k not in _c:
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
        _c[k] = f
    return _c[k]


def tl(d, t, f, tr=0.0):
    return sum(d.textlength(c, font=f) + f.size * tr for c in t) - (f.size * tr if t else 0)


def esp(d, xy, t, f, c, tr=0.2, derecha=False, centro=False):
    x, y = xy
    w = tl(d, t, f, tr)
    if derecha:
        x -= w
    elif centro:
        x -= w / 2
    for ch in t:
        d.text((x, y), ch, font=f, fill=c)
        x += d.textlength(ch, font=f) + f.size * tr
    return w


def wrap(d, text, f, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            out.append(cur)
            cur = w
    return out + ([cur] if cur else [])


def cabe(d, text, fuente, peso, maxw, maxh, grande, chico, inter=1.0, max_l=3):
    for s in range(grande, chico - 1, -2):
        f = F(fuente, s, peso)
        ls = wrap(d, text, f, maxw)
        if len(ls) <= max_l and len(ls) * s * inter <= maxh and all(d.textlength(l, font=f) <= maxw for l in ls):
            return f, ls, int(s * inter)
    return f, ls, int(s * inter)


def chip(d, x, y, t, fondo, letra, f=None, tr=0.12, alto=46):
    f = f or F(MO, 24)
    w = tl(d, t, f, tr) + 40
    d.rounded_rectangle([x, y, x + w, y + alto], radius=alto // 2, fill=fondo)
    esp(d, (x + 20, y + (alto - f.size) // 2 - 2), t, f, letra, tr)
    return w


def pie(im, d, T, n, total, fuente):
    y = H - 92
    d.rectangle([X0, y - 26, X1, y - 24], fill=LINEA if T["fondo"] == INK else (210, 205, 195))
    lk = ajustar(lockup(M, FD, 220, T["txt"]), 150, 40)
    im.paste(lk, (X0, y - 4), lk)
    f = F(MO, 22)
    if fuente:
        esp(d, ((X0 + X1) / 2, y + 6), ("FUENTE: " + fuente).upper(), f, T["suave"], 0.1, centro=True)
    esp(d, (X1, y + 6), f"{n}/{total}", f, T["txt"], 0.2, derecha=True)


def banda(im, d, T, etiqueta, grande, sub=None, alto=330):
    d.rectangle([0, 0, W, alto], fill=T["banda"])
    c = T["banda_txt"]
    lk = ajustar(lockup(M, FD, 220, c), 210, 56)
    im.paste(lk, (X0, 48), lk)
    if sub:
        esp(d, (X1, 64), sub.upper(), F(MO, 24), c, 0.12, derecha=True)
    # etiqueta en caja (como "ARTIST") + palabra/cifra gigante
    fe = F(BS, 150, 900)
    eb = d.textbbox((0, 0), etiqueta.upper(), font=fe)
    ew = eb[2] - eb[0]
    bx0, by0 = X0, 130
    bx1, by1 = bx0 + ew + 44, by0 + (eb[3] - eb[1]) + 44
    d.rectangle([bx0, by0, bx1, by1], outline=c, width=7)
    d.text((bx0 + 22 - eb[0], by0 + 22 - eb[1]), etiqueta.upper(), font=fe, fill=c)
    if grande:
        resto = X1 - bx1 - 30
        size = 260
        while size > 60:
            fg = F(BS, size, 900)
            gb = d.textbbox((0, 0), grande, font=fg)
            if gb[2] - gb[0] <= resto and gb[3] - gb[1] <= by1 - 120:
                break
            size -= 6
        d.text((X1 - (gb[2] - gb[0]) - gb[0], by1 - (gb[3] - gb[1]) - gb[1]), grande, font=fg, fill=c)


def l_portada(L, T, n, total, S):
    im = Image.new("RGB", (W, H), T["banda"])
    d = ImageDraw.Draw(im)
    c = T["banda_txt"]
    lk = ajustar(lockup(M, FD, 220, c), 240, 62)
    im.paste(lk, (X0, 64), lk)
    if L.get("chip"):
        f = F(MO, 26)
        w = tl(d, L["chip"].upper(), f, 0.18) + 40
        d.rectangle([X1 - w, 70, X1, 122], fill=c)
        esp(d, (X1 - w + 20, 82), L["chip"].upper(), f, T["banda"], 0.18)
    # etiqueta en caja
    fe = F(BS, 120, 900)
    et = L["etiqueta"].upper()
    eb = d.textbbox((0, 0), et, font=fe)
    d.rectangle([X0, 230, X0 + eb[2] - eb[0] + 40, 230 + eb[3] - eb[1] + 40], outline=c, width=7)
    d.text((X0 + 20 - eb[0], 250 - eb[1]), et, font=fe, fill=c)
    # gigante
    g = L["grande"].upper()
    size = 560
    while size > 80:
        fg = F(BS, size, 900)
        gb = d.textbbox((0, 0), g, font=fg)
        if gb[2] - gb[0] <= X1 - X0 and gb[3] - gb[1] <= L.get("alto_grande", 470):
            break
        size -= 8
    d.text((X0 - gb[0], 420 - gb[1]), g, font=fg, fill=T.get("grande_c", c))
    y = 420 + (gb[3] - gb[1]) + 50
    f, ls, lh = cabe(d, L["titulo"].upper(), BS, 800, X1 - X0, max(170, H - 230 - y), 124, 54, 0.98, 3)
    for l in ls:
        d.text((X0, y), l, font=f, fill=c)
        y += lh
    if L.get("bajada"):
        fb = F(IN, 34, 500)
        y += 14
        for l in wrap(d, L["bajada"], fb, X1 - X0)[:2]:
            d.text((X0, y), l, font=fb, fill=c)
            y += 44
    yb = H - 110
    d.rectangle([X0, yb, X1, yb + 3], fill=c)
    esp(d, (X0, yb + 28), "DESLIZA →", F(MO, 26), c, 0.3)
    esp(d, (X1, yb + 28), "ELCOROMAGAZINE.COM", F(MO, 26), c, 0.2, derecha=True)
    return im


def l_lista(L, T, n, total, S):
    im = Image.new("RGB", (W, H), T["fondo"])
    d = ImageDraw.Draw(im)
    banda(im, d, T, L.get("etiqueta", "LISTA"), L.get("grande"), L.get("sub"))
    filas = L["filas"]
    y0, y1 = 380, H - 140
    fh = (y1 - y0) / len(filas)
    if L.get("columna"):
        esp(d, (X1, y0 - 34), L["columna"].upper(), F(MO, 20), T["acento"], 0.12, derecha=True)
    fp = F(BS, min(110, int(fh * 0.62)), 800)
    for i, r in enumerate(filas):
        y = y0 + i * fh
        cy = y + fh / 2
        pb = d.textbbox((0, 0), str(r["pos"]), font=fp)
        d.text((X0 + 50 - (pb[2] - pb[0]) / 2 - pb[0], cy - (pb[3] - pb[1]) / 2 - pb[1]), str(r["pos"]), font=fp, fill=T["txt"])
        x = X0 + 140
        maxw = X1 - x - 190
        fn, ls, lh = cabe(d, r["nombre"].upper(), IN, 800, maxw, fh * 0.42, 50, 30, 1.05, 1)
        bloque = lh + (40 if r.get("detalle") else 0) + (56 if r.get("chip") else 0)
        yy = cy - bloque / 2
        if r.get("chip"):
            chip(d, x, yy, r["chip"].upper(), T["acento"], WHITE if T["acento"] == RED else INK, F(MO, 22), alto=42)
            yy += 56
        d.text((x, yy), ls[0], font=fn, fill=T["txt"])
        yy += lh + 4
        if r.get("detalle"):
            fd = F(IN, 28, 400)
            det = r["detalle"]
            while d.textlength(det, font=fd) > maxw and len(det) > 4:
                det = det[:-2].rstrip() + "…"
            d.text((x, yy), det, font=fd, fill=T["suave"])
        if r.get("dato"):
            fdt = F(BS, 68, 800)
            d.text((X1 - d.textlength(str(r["dato"]), font=fdt), cy - 40), str(r["dato"]), font=fdt, fill=T["acento"])
        if i < len(filas) - 1:
            d.rectangle([x, y + fh - 1, X1, y + fh], fill=T["acento"] if T["fondo"] == INK else (215, 210, 200))
    pie(im, d, T, n, total, S.get("fuente"))
    return im


def casilla(obra, artista, color, lado):
    im = Image.new("RGB", (lado, lado), color)
    d = ImageDraw.Draw(im)
    claro = sum(color) > 450
    c = INK if claro else WHITE
    f, ls, lh = cabe(d, obra, BOI, 800, lado - 44, lado - 90, 96, 30, 1.02, 4)
    th = len(ls) * lh
    y = (lado - 40 - th) / 2
    for l in ls:
        d.text((22, y), l, font=f, fill=c)
        y += lh
    return im


def l_nominados(L, T, n, total, S):
    im = Image.new("RGB", (W, H), T["fondo"])
    d = ImageDraw.Draw(im)
    c = T["txt"]
    lk = ajustar(lockup(M, FD, 220, c), 190, 50)
    im.paste(lk, (X0, 44), lk)
    esp(d, (X1, 58), L.get("sub", "").upper(), F(MO, 22), T["acento"], 0.12, derecha=True)
    d.rectangle([X0, 120, X1, 123], fill=c)
    fT = F(BS, 128, 900)
    t = L["evento"]
    d.text(((W - d.textlength(t, font=fT)) / 2, 128), t, font=fT, fill=c)
    fN = F(BS, 64, 800)
    t2 = L.get("rotulo", "NOMINADOS")
    esp(d, (W / 2, 268), t2, fN, c, 0.04, centro=True)
    d.rectangle([X0, 352, X1, 354], fill=c)
    fc, lsc, lhc = cabe(d, L["categoria"].upper(), MO, None, X1 - X0 - 140, 120, 46, 30, 1.15, 2)
    yc = 372
    for l in lsc:
        w = tl(d, l, fc, 0.04)
        x = (W - w) / 2
        esp(d, (x, yc), l, fc, c, 0.04)
        yc += lhc
    estrella = F(IN, 40, 800)
    d.text((X0 + 8, 372 + (len(lsc) * lhc - 40) / 2), "★", font=estrella, fill=T["acento"])
    d.text((X1 - 48, 372 + (len(lsc) * lhc - 40) / 2), "★", font=estrella, fill=T["acento"])
    ytop = yc + 14
    d.rectangle([X0, ytop, X1, ytop + 2], fill=c)
    noms = L["nominados"]
    n_nom = len(noms)
    cols = 3 if n_nom in (3, 5, 6, 9) else (4 if n_nom in (4, 7, 8) else 3)
    filas = -(-n_nom // cols)
    gap = 26
    disp_h = H - 140 - ytop - 30
    lado = int(min((X1 - X0 - gap * (cols - 1)) / cols, disp_h / filas - 96))
    y = ytop + 30
    k = 0
    for fi in range(filas):
        fila = noms[k:k + cols]
        k += cols
        ancho = len(fila) * lado + (len(fila) - 1) * gap
        x = (W - ancho) / 2
        for j, nm in enumerate(fila):
            col = CASILLAS[(fi * cols + j + L.get("desfase", 0)) % len(CASILLAS)]
            if col == T["fondo"]:
                col = CASILLAS[(fi * cols + j + 3) % len(CASILLAS)]
            im.paste(casilla(nm["obra"], nm["artista"], col, lado), (int(x), int(y)))
            if col == T["fondo"] or (T["fondo"] == WHITE and sum(col) > 700):
                d.rectangle([x, y, x + lado - 1, y + lado - 1], outline=c, width=2)
            fo = F(IN, 26, 600)
            ob = "“" + nm["obra"] + "”" if L.get("comillas") else nm["obra"]
            while d.textlength(ob, font=fo) > lado + gap - 6 and len(ob) > 4:
                ob = ob[:-2].rstrip() + "…"
            d.text((x + lado / 2 - d.textlength(ob, font=fo) / 2, y + lado + 12), ob, font=fo, fill=c)
            fa = F(MO, 20)
            ar = nm["artista"].upper()
            while tl(d, ar, fa, 0.06) > lado + gap - 6 and len(ar) > 4:
                ar = ar[:-2].rstrip() + "…"
            esp(d, (x + lado / 2, y + lado + 48), ar, fa, T["suave"] if T["fondo"] == WHITE else (210, 210, 210), 0.06, centro=True)
            x += lado + gap
        y += lado + 96
    pie(im, d, T, n, total, S.get("fuente"))
    return im


def l_barras(L, T, n, total, S):
    im = Image.new("RGB", (W, H), T["fondo"])
    d = ImageDraw.Draw(im)
    banda(im, d, T, L.get("etiqueta", "TOP"), L.get("grande"), L.get("sub"))
    filas = L["filas"]
    mx = max(r["valor"] for r in filas)
    y0, y1 = 390, H - 150
    fh = (y1 - y0) / len(filas)
    fv = F(BS, int(min(96, fh * 0.9)), 900)
    for i, r in enumerate(filas):
        y = y0 + i * fh
        fn = F(BS, int(min(52, fh * 0.42)), 800)
        d.text((X0, y + 2), r["nombre"].upper(), font=fn, fill=T["txt"])
        by = y + fh * 0.52
        bh = fh * 0.36
        largo = (X1 - X0 - 140) * r["valor"] / mx
        col = T["acento"] if i == 0 or r.get("destacar") else (T["suave"] if T["fondo"] != INK else (80, 80, 80))
        d.rectangle([X0, by, X0 + largo, by + bh], fill=col)
        vb = d.textbbox((0, 0), str(r["valor"]), font=fv)
        d.text((X0 + largo + 18 - vb[0], by + bh / 2 - (vb[3] - vb[1]) / 2 - vb[1]), str(r["valor"]), font=fv, fill=T["txt"])
    pie(im, d, T, n, total, S.get("fuente"))
    return im


def l_cierre(L, T, n, total, S):
    im = Image.new("RGB", (W, H), T["banda"])
    d = ImageDraw.Draw(im)
    c = T["banda_txt"]
    lk = ajustar(lockup(M, FD, 420, c), 820, 230)
    im.paste(lk, ((W - lk.width) // 2, 300), lk)
    lineas = L.get("lineas", ["LA LISTA COMPLETA,", "EN LA NOTA."])
    size = 96
    while size > 50 and max(d.textlength(l, font=F(BS, size, 900)) for l in lineas) > X1 - X0:
        size -= 4
    f = F(BS, size, 900)
    y = 620
    for l in lineas:
        d.text(((W - d.textlength(l, font=f)) / 2, y), l, font=f, fill=c)
        y += int(size * 1.04)
    by = y + 50
    bw, bh = 560, 96
    bx = (W - bw) // 2
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=48, fill=c)
    fc = F(IN, 32, 800)
    t = "LINK EN LA BIO"
    d.text((bx + (bw - d.textlength(t, font=fc)) / 2, by + 28), t, font=fc, fill=T["banda"])
    esp(d, (W / 2, by + 150), "ELCOROMAGAZINE.COM", F(MO, 28), c, 0.25, centro=True)
    esp(d, (W / 2, H - 90), f"{n}/{total}", F(MO, 22), c, 0.2, centro=True)
    return im


TIPOS = dict(portada=l_portada, lista=l_lista, nominados=l_nominados, barras=l_barras, cierre=l_cierre)

def l_esencial(L, T, n, total, S):
    im = Image.new("RGB", (W, H), T["fondo"])
    d = ImageDraw.Draw(im)
    banda(im, d, T, "LO ESENCIAL", None, L.get("sub"), alto=300)
    pts = L["puntos"][:4]
    y0, y1 = 380, H - 150
    gap = 44
    for size in range(54, 30, -2):
        f = F(IN, size, 600)
        lh = int(size * 1.28)
        bl = [wrap(d, p, f, X1 - X0 - 120) for p in pts]
        if sum(len(b) for b in bl) * lh + gap * (len(pts) - 1) <= y1 - y0:
            break
    total_h = sum(len(b) for b in bl) * lh + gap * (len(pts) - 1)
    y = y0 + max(0, (y1 - y0 - total_h) // 2)
    fnum = F(BS, 76, 900)
    for i, b in enumerate(bl):
        d.text((X0, y - 8), f"{i + 1:02d}", font=fnum, fill=T["acento"])
        for l in b:
            d.text((X0 + 120, y), l, font=f, fill=T["txt"])
            y += lh
        y += gap
    pie(im, d, T, n, total, S.get("fuente"))
    return im


def l_paso(L, T, n, total, S):
    """Un paso de una guía para artistas: número gigante, título y explicación corta. Una lámina por paso (se guarda y se comparte)."""
    T = TEMAS["negro"]
    im = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(im)
    lk = ajustar(lockup(M, FD, 220, WHITE), 200, 52)
    im.paste(lk, (X0, 56), lk)
    f = F(MO, 24)
    t = "PARA ARTISTAS"
    w = tl(d, t, f, 0.18) + 40
    d.rectangle([X1 - w, 60, X1, 108], fill=RED)
    esp(d, (X1 - w + 20, 71), t, f, WHITE, 0.18)
    fn = F(BS, 330, 900)
    num = f"{L['num']:02d}"
    nb = d.textbbox((0, 0), num, font=fn)
    d.text((X0 - nb[0], 170 - nb[1]), num, font=fn, fill=RED)
    y = 170 + (nb[3] - nb[1]) + 60
    ft, ls, lh = cabe(d, L["titulo"].upper(), BS, 800, X1 - X0, 300, 96, 50, 1.0, 3)
    for l in ls:
        d.text((X0, y), l, font=ft, fill=WHITE)
        y += lh
    y += 30
    d.rectangle([X0, y, X0 + 90, y + 6], fill=RED)
    y += 40
    disponible = H - 170 - y
    for size in range(48, 28, -2):
        fb = F(IN, size, 500)
        lb = wrap(d, L["texto"], fb, X1 - X0)
        if len(lb) * int(size * 1.36) <= disponible:
            break
    for l in lb:
        if y + int(size * 1.36) > H - 170:
            break
        d.text((X0, y), l, font=fb, fill=(225, 225, 225))
        y += int(size * 1.36)
    pie(im, d, T, n, total, S.get("fuente"))
    return im


TIPOS_EXTRA = dict(esencial=l_esencial, paso=l_paso)

ETIQUETAS = {"noticias": "NOTICIA", "premios": "PREMIOS", "listas": "LISTAS", "lanzamientos": "ESTRENOS",
             "critica": "CRÍTICA", "industria": "INDUSTRIA", "artistas": "PARA ARTISTAS"}


def limpio(t):
    t = (t or "").replace("{{NOMBRE_LARGO}}", M["nombre_largo"]).replace("{{NOMBRE}}", M["nombre"])
    t = re.sub(r"<br\s*/?>", " ", t)
    t = re.sub(r"<[^>]+>", "", t)
    for k, v in (("&amp;", "&"), ("&nbsp;", " "), ("&quot;", '"'), ("&#39;", "'")):
        t = t.replace(k, v)
    return re.sub(r"\s+", " ", t).strip()


def foto_de_banco(n):
    """Slug del banco de fotos de prensa (redes/fotos/banco.json) si la nota es sobre un artista que tiene foto."""
    bj = os.path.join(RAIZ, "redes", "fotos", "banco.json")
    if not os.path.exists(bj):
        return None
    banco = {k: v for k, v in json.load(open(bj, encoding="utf-8")).items()
             if not k.startswith("_") and os.path.exists(os.path.join(RAIZ, "redes", "fotos", k + ".jpg"))}
    nombres = sorted(((x.lower(), k) for k, v in banco.items() for x in [v["n"]] + v.get("a", [])), key=lambda t: -len(t[0]))
    for texto in ((n.get("cov") or {}).get("e", ""), limpio(n.get("title", ""))):
        t = texto.lower().strip()
        for nm, k in nombres:
            if t == nm or t.startswith(nm + " ") or t.startswith(nm + ",") or t.startswith(nm + " ·"):
                return k
    return None


def pasos_de(n, maximo=6):
    """Pasos de una guía: cada <h2> con la primera idea del párrafo que lo sigue."""
    b = n.get("body", "")
    out = []
    for m in re.finditer(r"<h2[^>]*>(.*?)</h2>\s*(?:<p[^>]*>(.*?)</p>)?", b, re.S):
        tit = re.sub(r"^\s*\d+[.)]\s*", "", limpio(m.group(1)))
        if not m.group(2) or re.search(r"para seguir|relacionad|sigue leyendo", tit, re.I):
            continue
        txt = limpio(m.group(2))
        frases = re.split(r"(?<=[.!?])\s+", txt)
        corto = frases[0]
        if len(corto) < 110 and len(frases) > 1:
            corto += " " + frases[1]
        if len(corto) > 260:
            corto = corto[:257].rsplit(" ", 1)[0] + "…"
        out.append({"titulo": tit, "texto": corto})
        if len(out) >= maximo:
            break
    return out


def desde_nota_artistas(n):
    """Guía para artistas en carrusel: portada + un paso por lámina + cierre para guardar."""
    aj = {}
    pa = os.path.join(RAIZ, "redes", "reel", n["id"] + ".json")
    if os.path.exists(pa):
        aj = json.load(open(pa, encoding="utf-8"))
    cov = n.get("cov") or {}
    pasos = pasos_de(n)
    lam = [{"tipo": "portada", "tema": "negro", "chip": "Guía", "etiqueta": "PARA ARTISTAS",
            "grande": aj.get("hero", limpio(cov.get("f", "")) or "GUÍA"), "alto_grande": 400,
            "titulo": aj.get("titular", limpio(n["title"])), "bajada": aj.get("bajada", f"{len(pasos)} pasos. Guárdalo." if pasos else "")}]
    lam += [{"tipo": "paso", "num": i, "titulo": p["titulo"], "texto": p["texto"]} for i, p in enumerate(pasos, 1)]
    lam.append({"tipo": "cierre", "tema": "rojo", "lineas": ["GUÁRDALO PARA TU", "PRÓXIMO LANZAMIENTO."]})
    return {"id": n["id"], "tema": "negro", "fuente": "", "laminas": lam}


def desde_nota(n, portada="rojo"):
    """Serie estándar de una nota: portada (con foto de prensa si el artista está en el banco) + lo esencial + cierre."""
    if n.get("sec") == "artistas":
        return desde_nota_artistas(n)
    aj = {}
    pa = os.path.join(RAIZ, "redes", "reel", n["id"] + ".json")
    if os.path.exists(pa):
        aj = json.load(open(pa, encoding="utf-8"))
    titulo = limpio(n["title"])
    tit, baj = titulo, ""
    if ";" in titulo:
        tit, baj = [x.strip() for x in titulo.split(";", 1)]
    elif ":" in titulo and len(titulo.split(":")[0]) <= 42:
        tit, baj = [x.strip() for x in titulo.split(":", 1)]
    if baj:
        baj = baj[0].upper() + baj[1:] + ("" if baj.endswith(".") else ".")
    cov = n.get("cov") or {}
    fuentes = ", ".join(dict.fromkeys(re.split(r"\s+[—–-]\s+|:\s", s[0])[0].strip() for s in (n.get("src") or [])))
    primeras = [x.strip() for x in fuentes.split(",") if x.strip()]
    corto = ", ".join(primeras[:2]) if len(", ".join(primeras[:2])) <= 26 else (primeras[0][:22] if primeras else "")
    if len(primeras) > 2 or (primeras and corto == primeras[0][:22] and len(primeras) > 1):
        corto += " y otros"
    puntos = [limpio(b) for b in (n.get("brief") or [])][:4] or [limpio(n.get("dek", ""))]
    slug = foto_de_banco(n) if os.environ.get("SIN_FOTO") != "1" else None
    if slug:  # las noticias con foto del artista se ven y se comparten más: la foto va primero
        tapa = {"tipo": "foto", "foto": f"redes/fotos/{slug}.jpg", "foco_y": 0.15, "chip": n.get("tag", ""),
                "etiqueta": ETIQUETAS.get(n["sec"], "NOTICIA"), "titulo": aj.get("titular", tit), "bajada": aj.get("bajada", baj)}
    else:
        tapa = {"tipo": "portada", "tema": portada, "chip": n.get("tag", ""), "etiqueta": ETIQUETAS.get(n["sec"], "NOTICIA"),
                "grande": aj.get("hero", limpio(cov.get("f", "")) or n.get("tag", "")), "alto_grande": 430,
                "titulo": aj.get("titular", tit), "bajada": aj.get("bajada", baj)}
    return {"id": n["id"], "tema": "rojo", "fuente": "" if n.get("propia") else corto, "laminas": [
        tapa,
        {"tipo": "esencial", "sub": (n.get("tag") or "").upper(), "puntos": puntos},
        {"tipo": "cierre", "lineas": ["LA NOTA COMPLETA,", "EN LA WEB."]},
    ]}


def historia(portada_img, salida):
    """Historia 9:16: la portada sobre fondo negro y el botón."""
    im = Image.new("RGB", (1080, 1920), INK)
    p = portada_img.resize((960, 1200), Image.LANCZOS)
    im.paste(p, (60, 230))
    d = ImageDraw.Draw(im)
    bw, bh, by = 600, 100, 1530
    bx = (1080 - bw) // 2
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=50, fill=RED)
    t = "LEE LA NOTA · LINK EN LA BIO"
    f = F(IN, 30, 800)
    d.text((bx + (bw - d.textlength(t, font=f)) / 2, by + 34), t, font=f, fill=WHITE)
    esp(d, (540, 1680), "ELCOROMAGAZINE.COM", F(MO, 28), WHITE, 0.25, centro=True)
    im.save(salida, quality=92, optimize=True)


def generar(S, out):
    os.makedirs(out, exist_ok=True)
    total = len(S["laminas"])
    hechos = []
    for i, L in enumerate(S["laminas"], 1):
        T = TEMAS[L.get("tema", S.get("tema", "rojo"))]
        fn = TIPOS.get(L["tipo"]) or TIPOS_EXTRA.get(L["tipo"]) or globals()["TIPOS_EXTRA_FOTO"][L["tipo"]]
        im = fn(L, T, i, total, S)
        p = os.path.join(out, f"{S['id']}-s{i}.jpg")
        im.save(p, quality=92, optimize=True)
        hechos.append(p)
    return hechos


def l_foto(L, T, n, total, S):
    """Portada con foto (solo fotos con permiso: prensa oficial o licencia). Foto arriba, degradado a negro, titular abajo."""
    im = Image.new("RGB", (W, H), INK)
    foto = Image.open(os.path.join(RAIZ, L["foto"])).convert("RGB")
    fw, fh = foto.size
    alto = 900
    esc = max(W / fw, alto / fh)
    foto = foto.resize((int(fw * esc), int(fh * esc)), Image.LANCZOS)
    fx = (foto.width - W) // 2
    fy = int((foto.height - alto) * L.get("foco_y", 0.2))
    im.paste(foto.crop((fx, fy, fx + W, fy + alto)), (0, 0))
    grad = Image.new("L", (1, 360))
    for y in range(360):
        grad.putpixel((0, y), int(255 * (y / 359) ** 1.4))
    grad = grad.resize((W, 360))
    im.paste(Image.new("RGB", (W, 360), INK), (0, alto - 360), grad)
    d = ImageDraw.Draw(im)
    lk = ajustar(lockup(M, FD, 220, WHITE), 240, 62)
    im.paste(lk, (X0, 56), lk)
    if L.get("chip"):
        f = F(MO, 26)
        w = tl(d, L["chip"].upper(), f, 0.18) + 40
        d.rectangle([X1 - w, 62, X1, 114], fill=RED)
        esp(d, (X1 - w + 20, 74), L["chip"].upper(), f, WHITE, 0.18)
    fe = F(BS, 76, 900)
    et = L["etiqueta"].upper()
    eb = d.textbbox((0, 0), et, font=fe)
    y = 760
    d.rectangle([X0, y, X0 + eb[2] - eb[0] + 32, y + eb[3] - eb[1] + 28], fill=RED)
    d.text((X0 + 16 - eb[0], y + 14 - eb[1]), et, font=fe, fill=WHITE)
    y += eb[3] - eb[1] + 52
    f, ls, lh = cabe(d, L["titulo"].upper(), BS, 800, X1 - X0, 260, 116, 60, 0.98, 3)
    for l in ls:
        d.text((X0, y), l, font=f, fill=WHITE)
        y += lh
    if L.get("bajada"):
        fb = F(IN, 34, 500)
        y += 10
        for l in wrap(d, L["bajada"], fb, X1 - X0)[:2]:
            d.text((X0, y), l, font=fb, fill=(220, 220, 220))
            y += 44
    if L.get("credito"):
        fc = F(MO, 18)
        t = ("FOTO: " + L["credito"]).upper()
        capa = Image.new("RGBA", (int(tl(d, t, fc, 0.1)) + 10, 30), (0, 0, 0, 0))
        esp(ImageDraw.Draw(capa), (0, 4), t, fc, (235, 235, 235), 0.1)
        capa = capa.rotate(90, expand=True)
        im.paste(capa, (X1 + 22, 140), capa)
    yb = H - 110
    d.rectangle([X0, yb, X1, yb + 3], fill=RED)
    esp(d, (X0, yb + 28), "DESLIZA →", F(MO, 26), WHITE, 0.3)
    esp(d, (X1, yb + 28), "ELCOROMAGAZINE.COM", F(MO, 26), WHITE, 0.2, derecha=True)
    return im


TIPOS_EXTRA_FOTO = dict(foto=l_foto)


if __name__ == "__main__":
    S = json.load(open(sys.argv[1], encoding="utf-8"))
    print(json.dumps(generar(S, sys.argv[2])))
