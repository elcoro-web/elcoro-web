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
        if gb[2] - gb[0] <= X1 - X0 and gb[3] - gb[1] <= 470:
            break
        size -= 8
    d.text((X0 - gb[0], 420 - gb[1]), g, font=fg, fill=c)
    y = 420 + (gb[3] - gb[1]) + 50
    f, ls, lh = cabe(d, L["titulo"].upper(), BS, 800, X1 - X0, 230, 92, 54, 1.0, 3)
    for l in ls:
        d.text((X0, y), l, font=f, fill=c)
        y += lh
    if L.get("bajada"):
        d.text((X0, y + 18), L["bajada"], font=F(IN, 34, 500), fill=c)
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

if __name__ == "__main__":
    S = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]
    os.makedirs(out, exist_ok=True)
    total = len(S["laminas"])
    hechos = []
    for i, L in enumerate(S["laminas"], 1):
        T = TEMAS[L.get("tema", S.get("tema", "rojo"))]
        im = TIPOS[L["tipo"]](L, T, i, total, S)
        p = os.path.join(out, f"{S['id']}-s{i}.jpg")
        im.save(p, quality=92, optimize=True)
        hechos.append(p)
    print(json.dumps(hechos))
