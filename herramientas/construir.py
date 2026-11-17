#!/usr/bin/env python3
"""Construye la web completa de El Coro en public/ a partir de:
   contenido/notas.json (todas las notas; nunca se borran), web/plantilla.html, marca.json.
Uso: python3 herramientas/construir.py
Necesita: python3 con Pillow y numpy; node con jsdom (se instala solo en web/node_modules si falta).
"""
import hashlib, json, os, re, shutil, subprocess, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
P = lambda *a: os.path.join(R, *a)


def paso(t):
    print("·", t, flush=True)


def secciones(plantilla):
    m = re.search(r"sections:\{(.*?)\}", plantilla)
    return dict(re.findall(r'(\w+):"([^"]*)"', m.group(1)))


def main():
    M = json.load(open(P("marca.json"), encoding="utf-8"))
    N = json.load(open(P("contenido", "notas.json"), encoding="utf-8"))
    plantilla = open(P("web", "plantilla.html"), encoding="utf-8").read()
    SEC = secciones(plantilla)

    paso(f"{len(N)} notas")
    ids = [n["id"] for n in N]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        sys.exit(f"ids repetidos: {dup}")
    for n in N:
        if n["sec"] not in SEC:
            sys.exit(f"{n['id']}: sección desconocida {n['sec']}")

    # 1. plantilla + datos
    A = [{k: v for k, v in n.items() if k != "cov"} for n in N]
    COV = {n["id"]: n["cov"] for n in N if n.get("cov")}
    js = lambda o: json.dumps(o, ensure_ascii=False).replace("</", "<\\/")
    # fotos de prensa con crédito: web/fotos/<id>.jpg + web/fotos/<id>.json (alt, credito, pie, pos)
    FOT = {}
    if os.path.isdir(P("web", "fotos")):
        from PIL import Image
        for f in sorted(os.listdir(P("web", "fotos"))):
            fid = f[:-5] if f.endswith(".json") else None
            if fid and fid in ids:
                meta = json.load(open(P("web", "fotos", f), encoding="utf-8"))
                img = P("web", "fotos", fid + ".jpg")
                if not os.path.exists(img):
                    sys.exit(f"falta la foto web/fotos/{fid}.jpg")
                if not meta.get("credito") or not meta.get("alt"):
                    sys.exit(f"{fid}: la foto necesita 'credito' y 'alt'")
                meta["w"], meta["h"] = Image.open(img).size
                FOT[fid] = meta
        if FOT:
            paso(f"fotos con crédito: {len(FOT)}")
    completo = (plantilla.replace("/*@@NOTAS@@*/[]", "/*@@A*/" + js(A) + "/*A@@*/").replace("/*@@PORTADAS@@*/{}", js(COV))
                .replace("/*@@FOTOS@@*/{}", js(FOT)))
    open(P("web", "_completo.html"), "w", encoding="utf-8").write(completo)

    # 2. imágenes para compartir: solo las que faltan
    faltan = [n for n in N if not os.path.exists(P("web", "og", n["id"] + ".jpg"))]
    if faltan:
        paso(f"imágenes para compartir nuevas: {len(faltan)}")
        a_json = P("web", "_og.json")
        json.dump([{"id": n["id"], "title": n["title"], "titleEn": n["titleEn"], "date": n["date"], "sec": SEC[n["sec"]],
                    "tag": n["tag"], "cov": n.get("cov"), "dek": n["dek"], "brief": n["brief"], "en": n["en"], "src": n["src"]}
                   for n in faltan], open(a_json, "w", encoding="utf-8"), ensure_ascii=False)
        subprocess.run([sys.executable, P("herramientas", "og.py"), a_json, P("marca", "fuentes"), P("web", "og"), P("marca.json")], check=True)
        os.remove(a_json)

    # 3. páginas
    if not os.path.isdir(P("web", "node_modules", "jsdom")):
        paso("instalando jsdom")
        subprocess.run(["npm", "install", "--silent", "--no-audit", "--no-fund", "jsdom@24"], cwd=P("web"), check=True)
    tmp = P("_public_tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    subprocess.run(["node", P("web", "build.js"), P("web", "_completo.html"), tmp], check=True,
                   env=dict(os.environ, NODE_PATH=P("web", "node_modules")))
    # archivos que van tal cual en la raíz del sitio (verificación de Google, ads.txt, etc.)
    if os.path.isdir(P("web", "raiz")):
        for f in os.listdir(P("web", "raiz")):
            if not f.startswith(".") and f != "LEEME.txt":
                shutil.copy(P("web", "raiz", f), os.path.join(tmp, f))
    if FOT:
        os.makedirs(os.path.join(tmp, "assets", "fotos"), exist_ok=True)
        for fid in FOT:
            shutil.copy(P("web", "fotos", fid + ".jpg"), os.path.join(tmp, "assets", "fotos", fid + ".jpg"))
    for f in os.listdir(P("marca", "iconos")):
        shutil.copy(P("marca", "iconos", f), os.path.join(tmp, "favicon.ico" if f == "favicon.ico" else os.path.join("assets", f)))

    # 4. versión (el hosting la compara para saber si hay algo nuevo)
    h = hashlib.sha1()
    for d, _, fs in sorted(os.walk(tmp)):
        for f in sorted(fs):
            h.update(os.path.relpath(os.path.join(d, f), tmp).encode()); h.update(open(os.path.join(d, f), "rb").read())
    version = time.strftime("%Y%m%d-%H%M%S", time.gmtime()) + "-" + h.hexdigest()[:10]
    open(os.path.join(tmp, "version.txt"), "w").write(version + "\n")

    shutil.rmtree(P("public"), ignore_errors=True)
    os.rename(tmp, P("public"))
    os.remove(P("web", "_completo.html"))
    paginas = sum(1 for d, _, fs in os.walk(P("public")) for f in fs if f == "index.html")
    paso(f"listo: {paginas} páginas en public/ · versión {version}")


if __name__ == "__main__":
    main()
