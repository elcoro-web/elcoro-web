#!/usr/bin/env python3
"""Lista las notas publicadas que más necesitan trabajo (calidad y SEO). No cambia nada.
Uso: python3 herramientas/revisar.py [cuántas]   (por defecto 10; 0 = todas)
"""
import json, os, re, sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
N = json.load(open(os.path.join(R, "contenido", "notas.json"), encoding="utf-8"))
ids = {n["id"] for n in N}
RELLENO = ("increíble", "épico", "impresionante", "sin duda", "cabe destacar", "cabe mencionar", "no cabe duda",
           "en este sentido", "es importante mencionar", "vale la pena mencionar", "a nivel de", "de cara a",
           "rompe el silencio", "explota", "polémica", "no vas a creer")


def texto(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()


def problemas(n):
    p = []
    body = n.get("body", "")
    w = len(texto(body).split())
    minimo = 350 if n.get("propia") else 250
    if w < minimo:
        p.append((3, f"corta: {w} palabras (meta {minimo}+)"))
    if "<h2" not in body:
        p.append((3, "sin subtítulo <h2>"))
    enlaces = set(re.findall(r'href="#([a-z0-9-]+)"', body))
    if not enlaces & ids:
        p.append((2, "sin enlaces a otras notas de El Coro"))
    rotos = enlaces - ids
    if rotos:
        p.append((3, "enlaces internos rotos: " + ", ".join(sorted(rotos))))
    t = texto(n.get("title"))
    if len(t) > 75:
        p.append((1, f"titular largo para Google ({len(t)} caracteres; ideal ≤ 70)"))
    d = texto(n.get("dek"))
    if len(d) > 170:
        p.append((1, f"entradilla larga para la descripción de Google ({len(d)}; ideal 110-160)"))
    if len(d) < 70:
        p.append((1, f"entradilla corta ({len(d)} caracteres)"))
    bajo = (t + " " + d + " " + texto(body)).lower()
    malas = [x for x in RELLENO if x in bajo] + (["signo de exclamación en el titular"] if "!" in t else [])
    if malas:
        p.append((1, "frases de relleno o sensacionalistas: " + ", ".join(malas)))
    if len(n.get("src") or []) < (1 if n.get("propia") else 2):
        p.append((3, "menos fuentes de las necesarias"))
    return p


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    filas = [(sum(x[0] for x in problemas(n)), n, problemas(n)) for n in N]
    filas = [f for f in filas if f[0]]
    filas.sort(key=lambda f: -f[0])
    for puntos, n, ps in (filas if k == 0 else filas[:k]):
        print(f"[{puntos}] {n['id']} · {n['sec']} · {n['date']}")
        for _, m in ps:
            print("    - " + m)
    print(f"{len(filas)} de {len(N)} notas con algo por mejorar")


if __name__ == "__main__":
    main()
