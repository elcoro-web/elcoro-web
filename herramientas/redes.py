#!/usr/bin/env python3
"""Redes de El Coro: qué nota sale, con qué imágenes y con qué texto. Nunca borra el registro.

  python3 herramientas/redes.py pendientes [horas]      notas recientes que aún no salieron en redes, de más a menos importante
  python3 herramientas/redes.py preparar <id>           crea las imágenes en redes/img/ y muestra textos y enlaces (JSON)
  python3 herramientas/redes.py marcar <id> <redes> <fecha_programada> [enlace_metricool]
                                                        anota la publicación en redes/publicadas.json (redes separadas por coma)
  python3 herramientas/redes.py video <id> [id2 id3]    crea el reel (video 9:16, 1 a 3 notas) en redes/video/ y muestra el enlace (JSON)
  python3 herramientas/redes.py cancelar <id> [motivo]   la publicación no salió: la nota vuelve a quedar pendiente
  python3 herramientas/redes.py hoy                     publicaciones programadas hoy (hora de Nueva York)
"""
import glob, json, os, re, subprocess, sys, unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *x: os.path.join(R, *x)
NY = ZoneInfo("America/New_York")
REG = P("redes", "publicadas.json")
IMG = P("redes", "img")
RAW = "https://raw.githubusercontent.com/elcoro-web/elcoro-web/main/redes/img/"
VID = P("redes", "video")
RAWV = "https://raw.githubusercontent.com/elcoro-web/elcoro-web/main/redes/video/"
DOM = "https://elcoromagazine.com"
HASH_SEC = {"noticias": "#NoticiasMusicales", "premios": "#PremiosMusicales", "listas": "#ListasMusicales",
            "lanzamientos": "#NuevaMúsica", "critica": "#CríticaMusical", "industria": "#IndustriaMusical",
            "artistas": "#ArtistasIndependientes"}


def notas():
    return json.load(open(P("contenido", "notas.json"), encoding="utf-8"))


def registro():
    return json.load(open(REG, encoding="utf-8")) if os.path.exists(REG) else []


def limpio(t):
    t = re.sub(r"<[^>]+>", "", t or "")
    for k, v in (("&amp;", "&"), ("&nbsp;", " "), ("&quot;", '"'), ("&#39;", "'")):
        t = t.replace(k, v)
    return re.sub(r"\s+", " ", t).strip()


def etiqueta(t):
    t = "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")
    t = re.sub(r"[^A-Za-z0-9 ]", " ", t)
    return "#" + "".join(w[:1].upper() + w[1:] for w in t.split())


def cuando(n):
    return datetime.strptime(n["date"] + " " + (n.get("hora") or "00:00"), "%Y-%m-%d %H:%M").replace(tzinfo=NY)


def url_nota(id_):
    for f in glob.glob(P("public", "*", "*", "index.html")):
        with open(f, encoding="utf-8") as h:
            if f'window.__NOTA={{"id":"{id_}"' in h.read():
                return DOM + "/" + os.path.relpath(os.path.dirname(f), P("public")).replace(os.sep, "/") + "/"
    return DOM + "/"


def pendientes(horas=36):
    ya = hechas()
    ahora = datetime.now(NY)
    c = [n for n in notas() if n["id"] not in ya and ahora - cuando(n) <= timedelta(hours=horas)]
    prio = lambda n: (-(n.get("peso") or 1), -int(n.get("tag") == "Momento"), -int(bool(n.get("minuto"))), -int(bool(n.get("propia"))), -cuando(n).timestamp())
    for n in sorted(c, key=prio):
        print(json.dumps({k: n.get(k) for k in ("id", "date", "hora", "sec", "tag", "peso", "propia", "title")}, ensure_ascii=False))
    if not c:
        print("(no hay notas pendientes para redes)")


def preparar(id_):
    n = next((x for x in notas() if x["id"] == id_), None)
    if not n:
        sys.exit(f"no existe la nota {id_}")
    os.makedirs(IMG, exist_ok=True)
    sys.path.insert(0, P("herramientas"))
    import series
    from PIL import Image
    portada = os.environ.get("PORTADA") or ("negro" if len(hechas()) % 2 else "rojo")
    hechos = series.generar(series.desde_nota(n, portada), IMG)
    series.historia(Image.open(hechos[0]), os.path.join(IMG, id_ + "-story.jpg"))
    titulo, dek = limpio(n["title"]), limpio(n.get("dek"))
    puntos = [limpio(b) for b in (n.get("brief") or [])][:4]
    fuentes = ", ".join(dict.fromkeys(re.split(r"\s+[—–-]\s+|:\s", s[0])[0].strip() for s in (n.get("src") or [])))
    tags = [t for t in dict.fromkeys(["#ElCoroMagazine", HASH_SEC.get(n["sec"], ""), etiqueta(n.get("tag", "")), "#Música"]) if len(t) > 2]
    url = url_nota(id_)
    cuerpo = f"{titulo}\n\n{dek}\n\n📌 Lo esencial\n" + "\n".join("→ " + p for p in puntos)
    pie_fuentes = f"\n\nFuentes: {fuentes}." if fuentes and not n.get("propia") else ""
    texto_ig = cuerpo + pie_fuentes + "\n\n📰 Nota completa: link en la bio · elcoromagazine.com\n\n" + " ".join(tags)
    texto_link = cuerpo + pie_fuentes + f"\n\n📰 Nota completa: {url}"
    corto = f"{titulo}\n\n{url}"
    if len(corto) > 280:
        corto = titulo[: 280 - len(url) - 4].rstrip() + "…\n\n" + url
    print(json.dumps({
        "id": id_, "url": url,
        "carrusel": [RAW + id_ + f"-s{i}.jpg" for i in (1, 2, 3)],
        "historia": RAW + id_ + "-story.jpg",
        "alt": [f"Portada de El Coro: {titulo}", "Lo esencial: " + " ".join(puntos), "La nota completa en elcoromagazine.com."],
        "texto_ig": texto_ig, "texto_link": texto_link, "texto_corto": corto,
        "titulo_90": titulo[:90],
        "archivos": [os.path.relpath(os.path.join(IMG, id_ + s), R) for s in ("-s1.jpg", "-s2.jpg", "-s3.jpg", "-story.jpg")],
    }, ensure_ascii=False, indent=1))


def video(ids):
    """Reel con 1 a 3 notas (herramientas/reel.py)."""
    todas = notas()
    ns = []
    for id_ in ids[:3]:
        n = next((x for x in todas if x["id"] == id_), None)
        if not n:
            sys.exit(f"no existe la nota {id_}")
        ns.append(n)
    os.makedirs(VID, exist_ok=True)
    nombre = ids[0] if len(ids) == 1 else "resumen-" + datetime.now(NY).strftime("%Y%m%d-%H%M")
    tmps = []
    for i, n in enumerate(ns):
        tmp = P("redes", f"_nota{i}.json")
        json.dump(n, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        tmps.append(tmp)
    salida = os.path.join(VID, nombre + "-reel.mp4")
    try:
        subprocess.run([sys.executable, P("herramientas", "reel.py"), salida, P("marca.json"), P("marca", "fuentes"), *tmps],
                       check=True, stdout=subprocess.DEVNULL)
    finally:
        for t in tmps:
            os.remove(t)
    print(json.dumps({"ids": ids[:3], "video": RAWV + nombre + "-reel.mp4", "portada_video": RAWV + nombre + "-reel.jpg",
                      "titulo_90": (limpio(ns[0]["title"]) if len(ns) == 1 else f"{len(ns)} noticias de música que tienes que saber hoy")[:90],
                      "archivos": [os.path.relpath(os.path.join(VID, nombre + s), R) for s in ("-reel.mp4", "-reel.jpg")]},
                     ensure_ascii=False, indent=1))


def marcar(id_, redes, fecha, enlace=""):
    if not any(x["id"] == id_ for x in notas()):
        sys.exit(f"no existe la nota {id_}")
    r = registro()
    r.append({"id": id_, "redes": [x.strip() for x in redes.split(",") if x.strip()], "programada": fecha,
              "metricool": enlace, "registrada": datetime.now(NY).strftime("%Y-%m-%d %H:%M")})
    os.makedirs(os.path.dirname(REG), exist_ok=True)
    json.dump(r, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"anotada: {id_} → {redes} ({fecha}) · total {len(r)}")


def cancelar(id_, motivo=""):
    """Anota que una publicación programada se canceló antes de salir: la nota vuelve a estar pendiente."""
    r = registro()
    r.append({"id": id_, "cancelada": True, "motivo": motivo, "registrada": datetime.now(NY).strftime("%Y-%m-%d %H:%M")})
    json.dump(r, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"cancelada: {id_}")


def hechas():
    est = {}
    for x in registro():
        est[x["id"]] = not x.get("cancelada")
    return {k for k, v in est.items() if v}


def hoy():
    d = datetime.now(NY).strftime("%Y-%m-%d")
    canc = {}
    for x in registro():
        if x.get("cancelada"):
            canc[x["id"]] = x["registrada"]
    h = [x for x in registro() if not x.get("cancelada") and x["programada"].startswith(d)
         and not (x["id"] in canc and canc[x["id"]] >= x["registrada"])]
    for x in h:
        print(json.dumps(x, ensure_ascii=False))
    print(f"{len(h)} publicaciones programadas hoy ({d})")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    if a[0] == "pendientes":
        pendientes(int(a[1]) if len(a) > 1 else 36)
    elif a[0] == "preparar" and len(a) == 2:
        preparar(a[1])
    elif a[0] == "marcar" and len(a) in (4, 5):
        marcar(*a[1:])
    elif a[0] == "video" and 2 <= len(a) <= 4:
        video(a[1:])
    elif a[0] == "cancelar" and len(a) in (2, 3):
        cancelar(*a[1:])
    elif a[0] == "hoy":
        hoy()
    else:
        sys.exit(__doc__)
