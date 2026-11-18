#!/usr/bin/env python3
"""Pule notas publicadas sin borrarlas: titular, entradilla, resumen, enlaces internos o cuerpo ampliado.
Uso: python3 herramientas/pulir_nota.py cambios.json
cambios.json: {"<id>": {"title": "...", "dek": "...", "body": "...", "src_mas": [["Medio — Título", "https://..."]]}, ...}
(las fuentes solo se suman con src_mas; nunca se quitan)

- Solo para estilo, claridad, SEO y contexto ampliado. Un dato equivocado se arregla con corregir_nota.py,
  que deja la corrección visible para el lector.
- No cambia el id ni la dirección de la nota (web/rutas.json la fija).
- Si el cuerpo crece con contexto nuevo, la nota queda como actualizada (dateModified); los retoques de estilo no.
- Valida lo mismo que nueva_nota.py: largo mínimo, <h2>, HTML simple y enlaces internos que existan.
"""
import json, os, re, sys
from datetime import datetime
from zoneinfo import ZoneInfo

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NOTAS = os.path.join(R, "contenido", "notas.json")
PERMITIDOS = {"title", "titleEn", "dek", "brief", "en", "body", "minuto", "tag", "cov", "min", "src_mas", "critica"}


def palabras(h):
    return len(re.sub(r"<[^>]+>", " ", h or "").split())


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    cambios = json.load(open(sys.argv[1], encoding="utf-8"))
    N = json.load(open(NOTAS, encoding="utf-8"))
    por_id = {n["id"]: n for n in N}
    ahora = datetime.now(ZoneInfo("America/New_York")).isoformat(timespec="seconds")
    for nid, c in cambios.items():
        n = por_id.get(nid)
        if not n:
            sys.exit(f"✗ no existe la nota {nid}")
        raros = set(c) - PERMITIDOS
        if raros:
            sys.exit(f"✗ {nid}: no se cambian {sorted(raros)} con esta herramienta")
        if "body" in c:
            b = c["body"]
            if re.search(r"<\s*(script|iframe|img|style)", b, re.I) or "${" in b:
                sys.exit(f"✗ {nid}: body con HTML no permitido")
            if "<h2" not in b:
                sys.exit(f"✗ {nid}: falta al menos un <h2>")
            minimo = 350 if n.get("propia") else 200
            if palabras(b) < minimo:
                sys.exit(f"✗ {nid}: body muy corto ({palabras(b)} palabras; mínimo {minimo})")
            rotos = set(re.findall(r'href="#([a-z0-9-]+)"', b)) - set(por_id)
            if rotos:
                sys.exit(f"✗ {nid}: enlaces a notas que no existen: {sorted(rotos)}")
        if "brief" in c and (not isinstance(c["brief"], list) or not 2 <= len(c["brief"]) <= 4):
            sys.exit(f"✗ {nid}: brief debe tener de 2 a 4 frases")
        if "src_mas" in c:  # las fuentes solo se suman, nunca se quitan
            mas = c.pop("src_mas")
            if any(not (isinstance(x, list) and len(x) == 2 and x[1].startswith("http")) for x in mas):
                sys.exit(f"✗ {nid}: src_mas debe ser una lista de [nombre, url]")
            ya = {x[1] for x in n["src"]}
            n["src"] = n["src"] + [x for x in mas if x[1] not in ya]
        antes = palabras(n.get("body"))
        amplia = "body" in c and palabras(c["body"]) >= antes + 60
        n.update(c)
        n.setdefault("ediciones", []).append({"iso": ahora, "tipo": "ampliacion" if amplia else "estilo", "campos": sorted(c)})
        if amplia:
            n["min"] = max(1, round(palabras(n["body"]) / 200))
        print(f"✓ {nid}: {', '.join(sorted(c))}" + (f" · {antes} → {palabras(n['body'])} palabras" if "body" in c else ""))
    json.dump(N, open(NOTAS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
