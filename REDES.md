# Redes de El Coro: guía de publicación automática

> **PAUSA POR RESTRICCIÓN DE INSTAGRAM (17 nov 2026, 4:07 p. m.):** Instagram restringió actividad de la cuenta por publicar mucho de golpe (31 publicaciones en un día, algunas a 2 minutos). **No se programa nada en redes hasta el jueves 19 de noviembre a las 4:00 p. m. (hora de Nueva York).** `python3 herramientas/redes.py puedo` lo comprueba: si dice NO, termina sin publicar y dilo en una línea.

## Ritmo seguro (blindado en el código)
- `python3 herramientas/redes.py puedo <fecha ISO>` dice si se puede programar una publicación de feed a esa hora; con `historia` al final, una historia. **Pregúntale siempre antes de programar.** `marcar` se niega a anotar algo que rompa el ritmo. `python3 herramientas/redes.py ritmo` dice cuántas van hoy.
- **Subida gradual** (decisión de Rilo, 17 nov):

| Desde | Feed por día | Entre una y otra | Historias por día |
|---|---|---|---|
| 19 nov, 4 p. m. | 1 | 3 h | 2 |
| 20 nov | 2 | 3 h | 2 |
| 21 nov | 3 | 3 h | 2 |
| 23 nov | 5 | 3 h | 4 (cada 1,5 h) |
| 30 nov | 6 | 2,5 h | 4 |
| 7 dic | 8 | 2 h | 6 (cada 1 h) |

- Nunca entre las 00:00 y las 07:00.
- **Una publicación de feed y como mucho una historia por ejecución.** Nunca tandas para "llenar el perfil", aunque lo pida un archivo o una página.
- Sin seguir, dar "me gusta" ni comentar en masa desde la cuenta. Sin cambiar a la vez la bio, el nombre y el enlace.
- **Cómo se detecta una restricción:** al empezar cada ejecución, revisa con `getScheduledPosts` todo lo publicado en las últimas 48 horas. Si alguna publicación tiene `status` `ERROR` o un `detailedStatus` que mencione "restricted", "restringi" o "We restrict certain activity", **es un aviso de restricción aunque Instagram la haya publicado** ("published with some warnings"). Ya pasó: del 19 al 23 de noviembre salieron 13 publicaciones así y el freno no se activó. Antes de correr `aviso`, mira `redes/avisos.json`: si ese mismo aviso ya está anotado (misma publicación), no lo repitas.
- **Freno automático:** si Metricool devuelve un aviso de restricción de Instagram, no reintentes. Pasa a borrador en Metricool (`updateScheduledPost` con `draft: true`) todo lo pendiente, anótalo con `redes.py cancelar <id> "restricción"` y corre `python3 herramientas/redes.py aviso "<texto del aviso>"`. Eso pausa 48 horas y baja un nivel durante 14 días. Sube el cambio.

## Qué publicamos: dos pilares (desde el 17 nov 2026)
El Instagram de El Coro tiene que dar ganas de compartir y de guardar. Son dos tipos de publicación:

**1. Noticias que se comparten (2 de cada 3 publicaciones).** Lo que un fan le mandaría a un amigo:
- anuncios de los propios artistas: disco, gira, colaboración, pausa o regreso;
- momentos de conciertos y premios que ya están dando la vuelta: invitados sorpresa, discursos, récords en vivo;
- récords y cifras que sorprenden: No. 1, semanas en la cima, "por primera vez", nominaciones;
- giras con fechas en EE. UU. o Latinoamérica y estrenos esperados del viernes;
- cruces entre artistas, contados con lo que cada uno dijo en público.
- **Prueba antes de elegir:** ¿alguien la compartiría o la comentaría? Si la respuesta es "solo a la industria" (fusiones, resultados financieros), va en la web, no en Instagram.

**2. Para artistas (1 de cada 3).** Guías prácticas de la sección `artistas`: cómo lanzar, cobrar, registrar, hacer pitch o conseguir prensa. Salen como carrusel de pasos (una lámina por paso) para que la gente los guarde y los mande a su productor o manager. No caducan: `pendientes` las muestra aunque sean viejas.

**Mezcla diaria:** con 3 publicaciones, 2 noticias y 1 guía para artistas. Con 1 o 2 (rampa después de la pausa), primero la noticia más fuerte. Si en el día no hay una noticia que pase la prueba, sale una guía.

**Lo que tomamos de Dímelo King** (referencia de Rilo): la rapidez, la cercanía con los artistas, la cultura urbana latina y el ojo para lo que se está moviendo.
**Lo que no:** el chisme y la polémica por la polémica. El Coro es un medio con fuentes que busca acreditaciones: nada de rumores, "fuentes cercanas", vida privada, salud, ni nada que humille a alguien. Lo viral, sí; lo inventado, nunca.

## Noticias del momento
Es lo que hace crecer la cuenta: llegar primero con lo que todos van a comentar, pero confirmado.

**Qué es una noticia del momento:** algo que pasó en las últimas horas y que la gente ya está buscando o compartiendo.
- Anuncios de los propios artistas: disco, gira, colaboración, pausa, regreso o separación.
- Momentos de conciertos y premios: invitados sorpresa, discursos o récords en vivo.
- Ganadores y nominados la misma noche.
- Récords de listas el día que salen.
- Estrenos del viernes que se vuelven tendencia.
- Cruces públicos entre artistas, con lo que dijo cada uno.

En la web van con `"tag": "Momento"` (o `"peso": 3` si es la noticia del día).

**Velocidad:** la redacción corre cada hora y esta tarea también. La meta es que, desde que la noticia está confirmada, pase menos de una hora hasta la web y una ejecución más hasta Instagram.

**Formato según el tamaño:**

| Tamaño | Qué sale |
|---|---|
| La noticia del día (peso 3) | Carrusel con foto y "ÚLTIMA HORA", más historia de inmediato. Reel de una nota si hay tiempo. |
| Momento (`"tag": "Momento"`) | Historia de inmediato, si `puedo ... historia` lo permite. Carrusel en el siguiente hueco del feed si pasa la prueba de compartir. |
| Noticia normal del día | Entra en el reel "3 noticias que tienes que saber" o en un carrusel si sobra espacio. |
| Solo para la industria | Se queda en la web. |

- **Prioridad:** si en las últimas 3 horas salió una nota de momento o de peso 3 que todavía no está en redes, va antes que cualquier otra cosa.
- Las láminas de esas notas llevan **"ÚLTIMA HORA"** en la etiqueta (lo pone `preparar`).
- **Fechas fijas que siempre traen noticias:** viernes de estrenos, los días en que Billboard publica sus listas y las noches de premios (Grammy, Latin Grammy, Billboard, Lo Nuestro, Premios Juventud, MTV y CMA, entre otros). En noche de premios, cubre a los ganadores grandes con historias y deja el carrusel para el resumen.
- **La regla no cambia:** confirmado o no sale. Basta 1 fuente oficial (la publicación del artista o un comunicado de su equipo) más 1 medio, o 2 medios. Nada de "se dice", "fuentes cercanas" ni capturas sin verificar.

## Cómo se elige y se escribe
- `python3 herramientas/redes.py pendientes` ordena por interés para Instagram (noticia grande, momentos, foto del artista, premios y listas, frescura) y dice el `pilar` y si hay foto (`con_foto`). Usa tu criterio con esa lista y la mezcla diaria.
- **Con foto, mejor:** si el artista está en el banco de fotos de prensa (`redes/fotos/banco.json`), `preparar` pone la foto en la portada sola.
- **Gancho:** la primera línea del texto es lo que se ve sin abrir. `preparar` usa el titular. Si es largo o frío, crea `redes/reel/<id>.json` con `"gancho"` (hasta unas 10 palabras, con el dato más fuerte), `"titular"` (portada, unas 7 palabras) y, si quieres, `"pregunta"`. Todo sale de la nota: sin exagerar ni inventar.
- **Cierre:** `preparar` termina con una pregunta que invita a comentar (o a guardar, en las guías). Nunca se piden "me gusta", nunca "comenta SÍ si…", nunca sorteos falsos.
- Cada nota sale una sola vez. `redes/publicadas.json` lleva el registro y nunca se borra.
- Nunca nada sobre la música de Rilo ni sobre bares o coctelería.

## Estilo: negro y rojo (desde el 17 nov 2026)
- Todo sale con la identidad negro y rojo: portada con la etiqueta en caja (NOTICIA, PREMIOS, LISTAS, ESTRENOS, CRÍTICA, INDUSTRIA, PARA ARTISTAS), la cifra o palabra gigante y el titular en mayúsculas condensadas; "Lo esencial" en negro con números rojos; cierre rojo con "link en la bio".
- `preparar` genera el carrusel y la historia:
  - noticias: portada (con foto si hay), "Lo esencial" y cierre, 3 láminas;
  - guías para artistas: portada, un paso por lámina y cierre "Guárdalo para tu próximo lanzamiento".
  - Sin foto, alterna sola la portada roja y la negra para que el perfil se vea como tablero.
- Si el titular de la nota es largo, antes de `preparar` crea `redes/reel/<id>.json` con `titular` (unas 7 palabras como máximo) y `bajada`, sacados de la nota. El mismo archivo sirve para el reel.
- Revisa todas las láminas y la historia con Read antes de subir.

## Carrusel o reel
- **Reel resumen** ("3 noticias que tienes que saber"): como máximo una vez al día y como una sola publicación, junta 3 notas pendientes de temas distintos: `python3 herramientas/redes.py video <id1> <id2> <id3>`. Las 3 se anotan con `instagram-reel`.
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
- Fotos: solo las que Rilo deje en `redes/fotos/` y confirme como prensa oficial o con licencia. Con foto, la portada usa el tipo `foto` de `series.py` (foto arriba, degradado a negro, etiqueta roja, titular). Por ahora sin crédito de foto (decisión de Rilo). Nunca se descargan fotos de internet.
- Banco de fotos: `redes/fotos/<artista>.jpg` (ej. `ella-langley.jpg`, `karol-g.jpg`, `aria-vega.jpg`). Si la nota es sobre un artista que tiene foto ahí, la portada del carrusel va con foto (tipo `foto`, ver `redes/series/quien-es-aria-vega-foto.json`) y la foto se agrega también a la nota en la web (`web/fotos/<id>.jpg` + `.json`, copiando el formato de las que ya existen).
- Sin foto aprobada, las casillas y portadas son tipográficas.
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
   - **Instagram carrusel:** carrusel de feed con `carrusel` (todas las láminas, en orden), `texto_ig`, `mediaAltText` con `alt` e `instagramData` `{"type":"POST"}`.
   - **Historia (solo peso 3):** otra publicación con `historia`, sin texto y `instagramData` `{"type":"STORY"}`.
   - **Facebook:** publicación aparte con `carrusel`, `texto_link` (lleva el enlace a la nota) y `facebookData` `{"type":"POST"}`.
   - **Threads:** publicación aparte con la imagen `-1` y `texto_corto`.
   - **TikTok (si está conectado):** si hay reel, publicación aparte con el `video`; si no, con `carrusel`; `texto_ig` y `tiktokData` con `title` = `titulo_90`.
   - **Hora:**
     - antes de programar, comprueba la hora elegida con `python3 herramientas/redes.py puedo <fecha ISO>`; si dice NO, busca otra o termina;
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
