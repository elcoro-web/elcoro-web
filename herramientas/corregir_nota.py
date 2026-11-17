#!/usr/bin/env python3
"""Corrige una nota publicada sin borrarla y deja la corrección visible al final de la nota.
Uso: python3 herramientas/corregir_nota.py <id> <cambios.json> "Texto para el lector" [actualizacion]
Sin el último argumento queda como "Corrección"; con "actualizacion" queda como "Actualización" (para guías con datos nuevos).
cambios.json: un objeto con los campos que cambian (por ejemplo {"body": "...", "brief": [...]}).
"""
import json, os, sys, time

R = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NOTAS = os.path.join(R, "contenido", "notas.json")

if len(sys.argv) not in (4, 5) or (len(sys.argv) == 5 and sys.argv[4] != "actualizacion"):
    sys.exit(__doc__)
nid, cambios, texto = sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8")), sys.argv[3]
tipo = "actualizacion" if len(sys.argv) == 5 else "correccion"
N = json.load(open(NOTAS, encoding="utf-8"))
nota = next((n for n in N if n["id"] == nid), None)
if not nota:
    sys.exit(f"no existe la nota {nid}")
if "id" in cambios:
    sys.exit("el id no se cambia: la dirección de la nota debe seguir funcionando")
nota.update(cambios)
nota.setdefault("correcciones", []).append({"fecha": time.strftime("%d.%m.%Y"), "nota": texto, "tipo": tipo})
json.dump(N, open(NOTAS, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("actualizada:" if tipo == "actualizacion" else "corregida:", nid)
