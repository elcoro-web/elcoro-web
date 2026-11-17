# El Coro · elcoromagazine.com

Revista de música hecha en Nueva York, en español y con resumen en inglés.

## Cómo funciona
- `contenido/notas.json`: todas las notas. **Nunca se borran**; solo se agregan con `herramientas/nueva_nota.py` o se corrigen con `herramientas/corregir_nota.py`. Las correcciones quedan visibles en la nota.
- `web/plantilla.html`: diseño y lógica de la web. La portada se arma sola con las notas más nuevas.
- `herramientas/construir.py`: genera el sitio completo en `public/`, con las imágenes para compartir, el sitemap, Google News y el RSS.
- `public/`: el sitio listo. El hosting (Namecheap) revisa `public/version.txt` cada 15 minutos y copia lo nuevo con `servidor/actualizar_web.sh`.
- `REDACCION.md`: guía editorial que sigue la redacción automática.
- `marca.json`: nombre, dominio, Instagram y correo.

## Publicar a mano
```bash
python3 herramientas/nueva_nota.py mi-nota.json
python3 herramientas/construir.py
git add -A && git commit -m "Nota: ..." && git push
```
