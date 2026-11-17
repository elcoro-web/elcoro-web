# Redes de El Coro: guía de publicación automática

> **PAUSA (17 nov 2026): no se programa nada en redes hasta que Rilo lo autorice.** El perfil se está relanzando con el concepto negro y rojo. Si lees esto en una ejecución automática, termina sin publicar y dilo en una línea.

Las redes llevan gente a la web. Cada publicación presenta una nota ya publicada en elcoromagazine.com, con la identidad de El Coro, y manda a leerla completa.

## Regla que no se rompe: solo las cuentas de El Coro
- En Metricool hay varias marcas. **Solo se publica en la marca de El Coro**, la que tiene conectado el Instagram **elcoromagazine**. Antes de programar cualquier cosa, llama a `getBrandSettings` y comprueba en `networksData` que `instagramData` sea `elcoromagazine`.
- **Nunca se publica en la marca "Rilo"** (blogId 7886435, Instagram `rilo`, TikTok `rilomusica`) ni en ninguna otra cuenta personal o de artista de Rilo, aunque sea la única marca disponible.
- Si no existe la marca de El Coro, no se publica nada. Termina y dilo en el resumen.
- Se publica solo en las redes conectadas a esa marca, entre instagram, facebook, threads y tiktok. Si una red no está conectada, se omite.

## Qué sale
- Cada nota sale una sola vez, con su propio contenido. `redes/publicadas.json` lleva el registro y nunca se borra.
- `python3 herramientas/redes.py pendientes` ordena las notas de las últimas 36 horas que aún no salieron: primero la noticia grande (peso 3), luego las de "Hoy en un minuto" y las piezas propias, y después las más recientes.
- Usa tu criterio con esa lista. Elige la nota que más le interesa al público de Instagram (grandes artistas, latinos, premios, estrenos, giras con fechas en EE. UU. o Latinoamérica, consejos útiles para artistas). Sáltate las notas que ya perdieron vigencia, como la previa de un evento que ya pasó.
- **Ritmo:**
  - máximo 3 publicaciones de feed por día en Instagram (carruseles y reels cuentan igual), separadas al menos 3 horas de cualquier otra publicación de feed ya programada ese día, antes o después;
  - historias solo para la noticia grande del día (peso 3), máximo 2 por día;
  - `python3 herramientas/redes.py hoy` muestra lo ya programado hoy, y `getScheduledPosts` lo confirma en Metricool.
- Nunca nada sobre la música de Rilo ni sobre bares o coctelería.

## Carrusel o reel
- **Reel resumen** ("3 noticias que tienes que saber"): una vez al día, en la primera publicación del día, junta 3 notas pendientes de temas distintos: `python3 herramientas/redes.py video <id1> <id2> <id3>`. Las 3 se anotan con `instagram-reel`.
- **Reel de una nota** para la noticia grande (peso 3) y los momentos (`"tag": "Momento"`): `python3 herramientas/redes.py video <id>`.
- **Carrusel** para lo demás. Carruseles y reels cuentan igual en el tope de 3 publicaciones de feed al día.
- Diseño de los reels: cifra o palabra grande, titular corto en mayúsculas, bajada, línea en inglés y pie "1 / 3". Si el titular de la nota es largo, crea `redes/reel/<id>.json` con `titular` (máximo unas 7 palabras), `bajada`, y si la nota da fechas o cifras comparables, `datos` (hasta 3 cajas `[grande, chico]`, con `destacar` = la caja más importante) o `barra` `[parte, total]`. Todo tiene que salir de la nota: no se inventan datos.
- Antes de subirlo, saca un cuadro de cada pantalla y míralos con Read para comprobar que nada se corte ni se monte: `ffmpeg -v error -ss <segundo> -i redes/video/<archivo>.mp4 -frames:v 1 /tmp/cuadro-<segundo>.png`. En un resumen de 3, los segundos 7, 13 y 20; en un reel de una nota, el 5.
- El video lleva una base rítmica original generada por la herramienta (sin canciones de terceros).

## Series con concepto (listas y nominados)
Además de la nota suelta, El Coro tiene formatos fijos que se reconocen en el feed. Se arman con `python3 herramientas/series.py redes/series/<id>.json redes/img` a partir de un JSON con los datos de una nota publicada (ver los ejemplos en `redes/series/`):
- **TOP 10** (`lista`): cada semana, cuando salga la nota del Billboard 200 o del Hot 100, un carrusel portada + 1-5 + 6-10 + cierre, con chips como "DEBUT" o "5 SEMANAS EN EL NO. 1".
- **NOMINADOS** (`nominados`): en temporada de premios, una lámina por categoría con las casillas tipográficas de cada obra.
- **LOS MÁS** (`barras`): rankings con barras (más nominados, más semanas, más reproducciones).
- Identidad de las series: **negro y rojo** (tema `rojo`: banda roja, fondo negro). Es la firma de El Coro en el feed; otros temas solo como excepción.
- Sin fotos de artistas ni portadas de discos: las casillas son tipográficas.
- Cuentan como una publicación de feed. Úsalas cuando la nota lo permita; al menos una serie por semana.

## Cómo se arma cada publicación
1. `python3 herramientas/redes.py preparar <id>` crea las imágenes en `redes/img/`:
   - `-1`: portada del carrusel, 4:5;
   - `-2`: Lo esencial, 4:5;
   - `-story`: historia, 9:16.

   Si toca reel, crea también el video (ver "Carrusel o reel").

   También devuelve los textos y los enlaces públicos de las imágenes.
2. **Sube las imágenes a GitHub antes de programar**, porque Metricool las descarga de esos enlaces: `git add redes/ && git commit -m "Redes: <id>" && git push origin main`. Si el push es rechazado, haz `git pull --rebase origin main` y vuelve a empujar.
3. Programa en Metricool con `createScheduledPost` (blogId de El Coro, zona horaria America/New_York):
   - **Instagram reel:** en el texto de un resumen, una línea por nota (1️⃣ 2️⃣ 3️⃣) con su titular; `media` con el `video`, `videoThumbnailUrl` con `portada_video`, `texto_ig` e `instagramData` `{"type":"REEL","showReelOnFeed":true,"isAiGenerated":false}`.
   - **Instagram carrusel:** carrusel de feed con `carrusel` (las dos imágenes), `texto_ig`, `mediaAltText` con `alt` e `instagramData` `{"type":"POST"}`.
   - **Historia (solo peso 3):** otra publicación con `historia`, sin texto y `instagramData` `{"type":"STORY"}`.
   - **Facebook:** publicación aparte con `carrusel`, `texto_link` (lleva el enlace a la nota) y `facebookData` `{"type":"POST"}`.
   - **Threads:** publicación aparte con la imagen `-1` y `texto_corto`.
   - **TikTok (si está conectado):** si hay reel, publicación aparte con el `video`; si no, con `carrusel`; `texto_ig` y `tiktokData` con `title` = `titulo_90`.
   - **Hora:**
     - consulta `getBestTimeToPostByNetwork` (instagram, el día de hoy) y usa la mejor franja de las próximas 3 horas, al menos 20 minutos en el futuro;
     - si la hora buena ya pasó, usa la siguiente franja buena;
     - nunca programes para la madrugada (entre 00:00 y 07:00).
4. Anota la publicación con `python3 herramientas/redes.py marcar <id> instagram,facebook,... <fecha ISO programada> <plannerUrl>`; si salió como reel, usa `instagram-reel` en vez de `instagram`. Luego `git add redes/ && git commit -m "Redes: programada <id>" && git push origin main`.

## Textos
- Usa los textos que da `preparar`. Puedes ajustar la redacción para que suene natural en redes, pero sin agregar datos que no estén en la nota y sin cambiar cifras, nombres ni fechas.
- Se citan las fuentes. No se inventan citas ni declaraciones.
- Hashtags: 3 a 5 y relevantes. Si el texto los trae, no agregues más.
- **Etiquetas de cuentas:** solo si estás seguro de que el usuario existe y es la cuenta oficial (verificada o enlazada desde la web oficial del artista). Ante la duda, no etiquetes.
- `isAiGenerated` en false: las imágenes son diseños tipográficos de El Coro, no fotos ni imágenes generadas.

## Si algo falla
- Si Metricool rechaza una publicación, no reintentes con el mismo contenido más de una vez. Anota el error en el resumen y sigue con las demás redes.
- Si una red pide algo que no tenemos, como un video para un reel, se omite esa red.
