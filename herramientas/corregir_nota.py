#!/usr/bin/env python3
"""Corrige una nota publicada sin borrarla y deja la corrección visible al final de la nota.
Uso: python3 herramientas/corregir_nota.py <id> <cambios.json> "Texto de la corrección para el lector"
cambios.json: un objeto con los campos que cambian (por ejemplo {"body": "...", "brief": [...]}).
"""
import json, os, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NOTAS = os.path.join(R, "contenido", "notas.json")

if len(sys.argv) != 4:
    sys.exit(__doc__)
nid, cambios, texto = sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8")), sys.argv[3]
N = json.load(open(NOTAS, encoding="utf-8"))
nota = next((n for n in N if n["id"] == nid), None)
if not nota:
    sys.exit(f"no existe la nota {nid}")
if "id" in cambios:
    sys.exit("el id no se cambia: la dirección de la nota debe seguir funcionando")
nota.update(cambios)
nota.setdefault("correcciones", []).append({"fecha": time.strftime("%d.%m.%Y"), "nota": texto})
json.dump(N, open(NOTAS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("corregida:", nid)
