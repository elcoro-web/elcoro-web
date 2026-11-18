#!/usr/bin/env python3
"""Redes de El Coro: qué nota sale, con qué imágenes y con qué texto. Nunca borra el registro.

  python3 herramientas/redes.py pendientes [horas]      notas recientes que aún no salieron en redes, de más a menos importante
  python3 herramientas/redes.py preparar <id>           crea las imágenes en redes/img/ y muestra textos y enlaces (JSON)
  python3 herramientas/redes.py marcar <id> <redes> <fecha_programada> [enlace_metricool]
                                                        anota la publicación en redes/publicadas.json (redes separadas por coma)
  python3 herramientas/redes.py video <id> [id2 id3]    crea el reel (video 9:16, 1 a 3 notas) en redes/video/ y muestra el enlace (JSON)
  python3 herramientas/redes.py cancelar <id> [motivo]   la publicación no salió: la nota vuelve a quedar pendiente
  python3 herramientas/redes.py hoy                     publicaciones programadas hoy (hora de Nueva York)
  python3 herramientas/redes.py puedo [fecha_iso]       ¿se puede programar una publicación de feed a esa hora? (pausa, tope diario, 3 h de separación)

El ritmo está blindado aquí y no en la memoria de nadie: `marcar` se niega a anotar una publicación de feed que rompa las reglas.
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
# --- Ritmo seguro para Instagram (cuenta nueva: Instagram castiga las ráfagas) ---
PAUSA_HASTA = datetime(2026, 11, 19, 16, 0, tzinfo=NY)       # restricción de Instagram del 17 nov 2026
RAMPA = {"2026-11-19": 1, "2026-11-20": 2}                   # vuelta gradual después de la pausa
TOPE_FEED_DIA = 3                                             # ritmo normal: máximo 3 publicaciones de feed al día
SEPARACION = timedelta(hours=3)                               # entre dos publicaciones de feed
FEED = {"instagram", "instagram-reel", "instagram-carrusel"}  # las historias no cuentan como feed

HASH_SEC = {"noticias": "#NoticiasMusicales", "premios": "#PremiosMusicales", "listas": "#ListasMusicales",
            "lanzamientos": "#NuevaMúsica", "critica": "#CríticaMusical", "industria": "#IndustriaMusical",
            "artistas": "#ArtistasIndependientes"}


def notas():
    return json.load(open(P("contenido", "notas.json"), encoding="utf-8"))


def registro():
    return json.load(open(REG, encoding="utf-8")) if os.path.exists(REG) else []


def limpio(t):
    t = (t or "").replace("{{NOMBRE_LARGO}}", "El Coro Magazine").replace("{{NOMBRE}}", "El Coro")
    t = re.sub(r"<[^>]+>", "", t)
    for k, v in (("&amp;", "&"), ("&nbsp;", " "), ("&quot;", '"'), ("&#39;", "'")):
        t = t.replace(k, v)
    return re.sub(r"\s+", " ", t).strip()


TAG_HASH = {"Agenda": "#Conciertos", "Momento": "#ÚltimaHora", "Lista": "#Listas", "Análisis": "#MúsicaLatina"}


def etiqueta(t):
    if t in TAG_HASH:
        return TAG_HASH[t]
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
    """Notas que aún no salieron en redes, de más a menos interesantes para Instagram.
    Noticias: las de las últimas `horas`. Guías para artistas: cualquiera (no caducan)."""
    ya = hechas()
    ahora = datetime.now(NY)
    sys.path.insert(0, P("herramientas"))
    import series
    c = [n for n in notas() if n["id"] not in ya and (n["sec"] == "artistas" or ahora - cuando(n) <= timedelta(hours=horas))]

    def puntos(n):
        p = {3: 6, 2: 3}.get(n.get("peso"), 0)
        p += 5 if n.get("tag") == "Momento" else 0          # lo que se comenta hoy
        p += 3 if series.foto_de_banco(n) else 0             # con foto del artista se ve y se comparte más
        p += 2 if n.get("minuto") else 0
        p += 2 if n["sec"] in ("premios", "listas") else 0
        p -= 3 if n["sec"] == "industria" else 0             # interesa menos en Instagram que en la web
        horas_ = (ahora - cuando(n)).total_seconds() / 3600
        p -= horas_ / 8 if n["sec"] != "artistas" else 0     # las noticias pierden interés con las horas
        return p
    for n in sorted(c, key=puntos, reverse=True):
        d = {k: n.get(k) for k in ("id", "date", "hora", "sec", "tag", "peso", "title")}
        d.update(pilar="artistas" if n["sec"] == "artistas" else "noticia", con_foto=bool(series.foto_de_banco(n)), puntos=round(puntos(n), 1))
        print(json.dumps(d, ensure_ascii=False))
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
    serie = series.desde_nota(n, portada)
    for viejo in glob.glob(os.path.join(IMG, id_ + "-s*.jpg")):
        os.remove(viejo)  # imágenes de un intento anterior de esta misma nota (no son registro: se regeneran)
    hechos = series.generar(serie, IMG)
    series.historia(Image.open(hechos[0]), os.path.join(IMG, id_ + "-story.jpg"))
    titulo, dek = limpio(n["title"]), limpio(n.get("dek"))
    aj = {}
    pa = P("redes", "reel", id_ + ".json")
    if os.path.exists(pa):
        aj = json.load(open(pa, encoding="utf-8"))
    puntos = [limpio(b) for b in (n.get("brief") or [])][:4]
    fuentes = ", ".join(dict.fromkeys(re.split(r"\s+[—–-]\s+|:\s", s[0])[0].strip() for s in (n.get("src") or [])))
    tags = [t for t in dict.fromkeys(["#ElCoroMagazine", HASH_SEC.get(n["sec"], ""), etiqueta(n.get("tag", "")), "#Música"]) if len(t) > 2]
    if n["sec"] == "artistas":
        tags = ["#ElCoroMagazine", "#ArtistasIndependientes", "#MúsicaIndependiente", "#ConsejosParaArtistas"]
    url = url_nota(id_)
    gancho = aj.get("gancho") or titulo
    pregunta = aj.get("pregunta") or pregunta_de(n)
    if n["sec"] == "artistas":
        pasos = [p["titulo"] for p in series.pasos_de(n)]
        lista = "\n".join(f"{i}. {p}" for i, p in enumerate(pasos, 1))
        cuerpo = f"{EMOJI['artistas']} {gancho}\n\n{dek}" + (f"\n\nEn el carrusel:\n{lista}" if pasos else "") + f"\n\n{pregunta}"
        cierre_ig, pie_fuentes = "\n\n📰 La guía completa: link en la bio · elcoromagazine.com", ""
    else:
        cuerpo = f"{EMOJI.get(n['sec'], '🎵')} {gancho}\n\n{dek}\n\n" + "\n".join("→ " + p for p in puntos) + f"\n\n{pregunta}"
        cierre_ig = "\n\n📰 Nota completa: link en la bio · elcoromagazine.com"
        pie_fuentes = f"\nFuentes: {fuentes}." if fuentes and not n.get("propia") else ""
    texto_ig = cuerpo + cierre_ig + pie_fuentes + "\n\n" + " ".join(tags)
    texto_link = cuerpo + pie_fuentes + f"\n\n📰 Nota completa: {url}"
    corto = f"{gancho}\n\n{url}"
    if len(corto) > 280:
        corto = gancho[: 280 - len(url) - 4].rstrip() + "…\n\n" + url
    lam = [os.path.basename(h) for h in hechos]
    print(json.dumps({
        "id": id_, "url": url, "pilar": "artistas" if n["sec"] == "artistas" else "noticia",
        "con_foto": any(L.get("tipo") == "foto" for L in serie["laminas"]),
        "carrusel": [RAW + x for x in lam],
        "historia": RAW + id_ + "-story.jpg",
        "alt": [f"El Coro: {titulo}"] + [f"Lámina {i} de {len(lam)}: {titulo}" for i in range(2, len(lam))] + ["La nota completa en elcoromagazine.com."],
        "texto_ig": texto_ig, "texto_link": texto_link, "texto_corto": corto,
        "titulo_90": gancho[:90],
        "archivos": [os.path.relpath(h, R) for h in hechos] + [os.path.relpath(os.path.join(IMG, id_ + "-story.jpg"), R)],
    }, ensure_ascii=False, indent=1))


EMOJI = {"noticias": "🎤", "premios": "🏆", "listas": "📈", "lanzamientos": "💿", "critica": "🎧", "industria": "💼", "artistas": "🎯"}


def pregunta_de(n):
    """Cierre del texto que invita a comentar, guardar o compartir (sin pedir 'me gusta')."""
    sec, tag = n["sec"], n.get("tag", "")
    if sec == "artistas":
        return "📌 Guárdalo para tu próximo lanzamiento y compártelo con tu productor o tu manager."
    if tag == "Agenda" or "gira" in limpio(n.get("title", "")).lower():
        return "¿Vas? Etiqueta a la persona con la que irías 👇"
    return {"premios": "¿Quién crees que se lo lleva? 👇", "listas": "¿Ya la tienes en tu playlist? 👇",
            "lanzamientos": "¿Cuál escuchas primero? 👇", "industria": "¿Cómo crees que esto cambia la música? 👇",
            "critica": "¿Estás de acuerdo con la crítica? 👇"}.get(sec, "¿Qué opinas? Te leemos 👇")


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


def feed_vigente():
    """Fechas (NY) de las publicaciones de feed anotadas y no canceladas después."""
    canc, out = {}, []
    reg = registro()
    for x in reg:
        if x.get("cancelada"):
            canc.setdefault(x["id"], []).append(x["registrada"])
    for x in reg:
        if x.get("cancelada") or not FEED & set(x.get("redes") or []):
            continue
        if any(c >= x["registrada"] for c in canc.get(x["id"], [])):
            continue
        try:
            f = datetime.fromisoformat(x["programada"].replace("Z", "+00:00"))
        except ValueError:
            continue
        out.append(f.astimezone(NY) if f.tzinfo else f.replace(tzinfo=NY))
    return out


def motivo_no(fecha):
    """None si se puede programar una publicación de feed en `fecha`; si no, el motivo."""
    ahora = datetime.now(NY)
    if ahora < PAUSA_HASTA or fecha < PAUSA_HASTA:
        return f"pausa por restricción de Instagram hasta {PAUSA_HASTA:%d/%m %H:%M} (Nueva York)"
    if fecha < ahora + timedelta(minutes=15):
        return "la hora tiene que estar al menos 15 minutos en el futuro"
    if fecha.hour < 7:
        return "nada de madrugada (00:00 a 07:00)"
    dia = fecha.strftime("%Y-%m-%d")
    tope = RAMPA.get(dia, TOPE_FEED_DIA)
    otras = feed_vigente()
    del_dia = [f for f in otras if f.strftime("%Y-%m-%d") == dia]
    if len(del_dia) >= tope:
        return f"ese día ya tiene {len(del_dia)} publicaciones de feed (tope {tope})"
    cerca = [f for f in otras if abs(f - fecha) < SEPARACION]
    if cerca:
        return f"hay otra publicación de feed a menos de 3 horas ({min(cerca, key=lambda f: abs(f - fecha)):%d/%m %H:%M})"
    return None


def puedo(fecha_txt=None):
    fecha = datetime.fromisoformat(fecha_txt) if fecha_txt else datetime.now(NY) + timedelta(minutes=30)
    fecha = fecha.astimezone(NY) if fecha.tzinfo else fecha.replace(tzinfo=NY)
    m = motivo_no(fecha)
    if m:
        print(f"NO: {m}")
        sys.exit(1)
    print(f"SÍ: se puede programar una publicación de feed el {fecha:%d/%m %H:%M} (Nueva York)")


def marcar(id_, redes, fecha, enlace=""):
    if not any(x["id"] == id_ for x in notas()):
        sys.exit(f"no existe la nota {id_}")
    if FEED & {x.strip() for x in redes.split(",")}:
        f = datetime.fromisoformat(fecha.replace("Z", "+00:00"))
        f = f.astimezone(NY) if f.tzinfo else f.replace(tzinfo=NY)
        m = motivo_no(f)
        if m:
            sys.exit(f"✗ no se anota: {m}. Borra esa publicación de Metricool (o reprográmala) y vuelve a intentarlo")
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
    elif a[0] == "puedo" and len(a) in (1, 2):
        puedo(*a[1:])
    else:
        sys.exit(__doc__)
