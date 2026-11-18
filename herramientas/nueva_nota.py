#!/usr/bin/env python3
"""Agrega una o varias notas nuevas al inicio de contenido/notas.json. Nunca borra ni reemplaza notas.
Uso: python3 herramientas/nueva_nota.py nota1.json [nota2.json ...]
Cada archivo trae una nota (objeto) o una lista de notas. El formato está en REDACCION.md.
"""
import collections, difflib, json, os, re, sys, unicodedata
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NOTAS = os.path.join(R, "contenido", "notas.json")
SECCIONES = {"noticias", "premios", "listas", "lanzamientos", "critica", "industria", "artistas"}
COLORES = {"#0a0a0a", "#0b0b0b", "#ffffff", "#fff", "#e3120b", "#ffd400", "#1d3ea0", "#0f6b3f", "#3fae6a", "#f0ece4",
           "#f3f3f3", "#2b2b2b", "#f2f2f2"}


TOPE_DIARIO = 10          # máximo de notas por día (hora de Nueva York): calidad antes que volumen. Una nota con peso 3 (la noticia grande) puede pasarlo
TOPE_TANDA = 2            # máximo de notas por ejecución (la redacción corre cada hora): ritmo parejo, sin ráfagas
TOPE_HORA = 2             # máximo de notas en las últimas 2 horas
PARECIDO_MAX = 0.80       # títulos más parecidos que esto a una nota reciente se bloquean por repetidos


def normal(t):
    t = unicodedata.normalize("NFD", t.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]+", " ", t).strip()


def error(n, msg):
    sys.exit(f"✗ {n.get('id', '?')}: {msg}")


def validar(n, existentes, recientes):
    for k in ("id", "date", "hora", "sec", "tag", "min", "title", "titleEn", "dek", "brief", "en", "body", "src", "cov"):
        if k not in n or n[k] in ("", None):
            error(n, f"falta el campo '{k}'")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", n["id"]) or len(n["id"]) > 60:
        error(n, "id: solo minúsculas, números y guiones (máx. 60)")
    if n["id"] in existentes:
        error(n, "ya existe una nota con ese id (no se reemplaza nada; usa corregir_nota.py)")
    if not re.fullmatch(r"20\d\d-\d\d-\d\d", n["date"]) or not re.fullmatch(r"\d\d:\d\d", n["hora"]):
        error(n, "date AAAA-MM-DD y hora HH:MM (hora de Nueva York)")
    if n["sec"] not in SECCIONES:
        error(n, f"sec debe ser una de {sorted(SECCIONES)}")
    if not isinstance(n["brief"], list) or not 2 <= len(n["brief"]) <= 4:
        error(n, "brief: lista de 2 a 4 frases")
    if not isinstance(n["src"], list) or any(not (isinstance(s, list) and len(s) == 2 and s[1].startswith("http")) for s in n["src"]):
        error(n, "src: lista de [nombre, url]")
    if len(n["src"]) < (1 if n.get("propia") else 2):
        error(n, "las noticias necesitan al menos 2 fuentes (las piezas propias, 1)")
    if re.search(r"<\s*(script|iframe|img|style)", n["body"], re.I) or "${" in n["body"]:
        error(n, "body: HTML simple sin script, iframe, img, style ni ${...}")
    c = n["cov"]
    for k in ("f", "bg", "fg", "c", "e"):
        if k not in c:
            error(n, f"cov.{k} falta")
    if c["bg"].lower() not in COLORES or c["fg"].lower() not in COLORES:
        error(n, "cov: usa colores de la paleta (ver REDACCION.md)")
    if "minuto" in n and (not isinstance(n["minuto"], list) or len(n["minuto"]) != 2):
        error(n, "minuto: [frase en español, English line]")
    if "peso" in n and n["peso"] not in (1, 2, 3):
        error(n, "peso: 1, 2 o 3")
    palabras = len(re.sub(r"<[^>]+>", " ", n["body"]).split())
    minimo = 350 if n.get("propia") else 200
    if palabras < minimo:
        error(n, f"body muy corto ({palabras} palabras; mínimo {minimo}). Agrega contexto propio, no relleno")
    if "<h2" not in n["body"]:
        error(n, "falta al menos un subtítulo <h2> de contexto (por ejemplo: Por qué importa, Contexto, Qué sigue)")
    for rid, rt in recientes:
        r = difflib.SequenceMatcher(None, normal(n["title"]), normal(rt)).ratio()
        if r >= PARECIDO_MAX:
            error(n, f"se parece demasiado a una nota ya publicada ({rid}: {rt}). Si hay un dato nuevo, actualiza esa nota con corregir_nota.py ... actualizacion")
    return palabras


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    N = json.load(open(NOTAS, encoding="utf-8"))
    existentes = {n["id"] for n in N}
    recientes = [(x["id"], x["title"]) for x in N[:300]]
    nuevas = []
    for f in sys.argv[1:]:
        d = json.load(open(f, encoding="utf-8"))
        for n in (d if isinstance(d, list) else [d]):
            p = validar(n, existentes | {x["id"] for x in nuevas}, recientes + [(x["id"], x["title"]) for x in nuevas])
            del_dia = sum(1 for x in N + nuevas if x["date"] == n["date"])
            if del_dia >= TOPE_DIARIO and n.get("peso") != 3 and not os.environ.get("ENCARGO_DIRECTOR"):  # encargo directo de Rilo
                error(n, f"tope diario alcanzado ({TOPE_DIARIO} notas el {n['date']}). Mejor pocas notas muy buenas: publica esta mañana o actualiza una existente")
            if len(nuevas) >= TOPE_TANDA and n.get("peso") != 3 and not os.environ.get("ENCARGO_DIRECTOR"):
                error(n, f"máximo {TOPE_TANDA} notas por tanda. Guarda esta para la próxima vuelta")
            hace2h = (datetime.now(NY) - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
            ultimas = sum(1 for x in N if f"{x['date']} {x['hora']}" >= hace2h)
            if ultimas + len(nuevas) >= TOPE_HORA and n.get("peso") != 3 and not os.environ.get("ENCARGO_DIRECTOR"):
                error(n, f"ya salieron {ultimas + len(nuevas)} notas en las últimas 2 horas (máximo {TOPE_HORA}). Publica en la próxima vuelta")
            nuevas.append(n)
            print(f"✓ {n['id']} · {n['sec']} · {p} palabras · {len(n['src'])} fuentes")
    nuevas.sort(key=lambda n: n["date"] + n["hora"], reverse=True)
    json.dump(nuevas + N, open(NOTAS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"notas en total: {len(nuevas) + len(N)} (+{len(nuevas)})")
    c = collections.Counter(x["sec"] for x in nuevas + N)
    print("por sección (prioriza las más flojas):", ", ".join(f"{k} {c.get(k, 0)}" for k in sorted(SECCIONES, key=lambda k: c.get(k, 0))))


if __name__ == "__main__":
    main()
