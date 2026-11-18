// Constructor del sitio estático: convierte web_fuente.html (plantilla) en un sitio de varias páginas, con la marca de marca.json.
// Usage: node build.js <source.html> <outdir>
const fs = require("fs"), path = require("path");
const { JSDOM, VirtualConsole } = require("jsdom");

const SRC = process.argv[2] || "src.html";
const OUT = process.argv[3] || "site";
const M = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "marca.json"), "utf8"));
const LOGO = M.logo_pre ? `<i style="font-style:italic;font-size:.4em;letter-spacing:-.01em;margin-right:.07em">${M.logo_pre}</i>${M.logo || M.nombre}` : (M.logo || M.nombre);
const TOK = s => s.replace(/\{\{LOGO\}\}/g, LOGO).replace(/\{\{NOMBRE_LARGO\}\}/g, M.nombre_largo).replace(/\{\{NOMBRE\}\}/g, M.nombre).replace(/\{\{DOMINIO\}\}/g, M.dominio).replace(/\{\{EMAIL\}\}/g, M.email_prensa).replace(/\{\{IG\}\}/g, M.instagram.replace(/^@/, "")).replace(/\{\{SLUG\}\}/g, M.slug);
const SITE = "https://" + M.dominio;
const raw = TOK(fs.readFileSync(SRC, "utf8"));

// ---- split source ----
const style = raw.match(/<style>([\s\S]*?)<\/style>/)[1];
const markup = raw.slice(raw.indexOf("</style>") + 8, raw.indexOf("<script>")).trim();
let script = raw.slice(raw.indexOf("<script>") + 8, raw.lastIndexOf("</script>"));
const fontsLink = raw.match(/<link rel="stylesheet" href="https:\/\/fonts[^>]+>/)[0];
// fuentes sin bloquear la página: se ve con letra del sistema y cambia apenas llega la fuente
const fontsHref = fontsLink.match(/href="([^"]+)"/)[1];
const fontsAsync = `<link rel="preload" as="style" href="${fontsHref}"><link rel="stylesheet" href="${fontsHref}" media="print" onload="this.media='all'"><noscript>${fontsLink}</noscript>`;

// ---- pass 1: extract data ----
const vc = new VirtualConsole(); // silence "not implemented" noise
const probe = new JSDOM(`<!DOCTYPE html><body>${markup}<script>${script}</script></body>`, { url: SITE + "/", runScripts: "dangerously", virtualConsole: vc });
const W = probe.window;
const A = W.eval("A"), PAGES = W.eval("PAGES"), T = W.eval("T");
const slug = W.eval("slug");
const tags = [...new Set(A.map(a => a.tag))];
// per-article share images (og/<id>.jpg next to the source file)
const OGDIR = path.join(path.dirname(path.resolve(SRC)), "og");
const OGMAP = {};
for (const a of A) if (fs.existsSync(path.join(OGDIR, a.id + ".jpg"))) OGMAP[a.id] = "/assets/og/" + a.id + ".jpg";

// ---- routes ----
const ROUTE = { inicio: "/" };
for (const k of Object.keys(T.es.sections)) if (k !== "inicio" && k !== "manifiesto") ROUTE[k] = `/${k}/`;
const short = t => { let s = slug(t), o = ""; for (const w of s.split("-")) { if ((o + "-" + w).length > 72) break; o = o ? o + "-" + w : w; } return o.replace(/(-(de|del|la|las|los|el|y|en|a|con|al))+$/, ""); };
// Direcciones fijas: la primera dirección de cada nota queda guardada en web/rutas.json y no cambia aunque se pula el titular
// (cambiar una URL ya indexada le hace perder a Google lo ganado). Nunca se borra una entrada de ese archivo.
const RUTAS_F = path.join(__dirname, "rutas.json");
const RUTAS = fs.existsSync(RUTAS_F) ? JSON.parse(fs.readFileSync(RUTAS_F, "utf8")) : {};
const usadas = new Set(Object.values(RUTAS));
for (const a of A) {
  if (!RUTAS[a.id]) {
    let r = `/${a.sec}/${short(a.title)}/`, i = 2;
    while (usadas.has(r)) r = `/${a.sec}/${short(a.title)}-${i++}/`;
    RUTAS[a.id] = r; usadas.add(r);
  }
  ROUTE[a.id] = RUTAS[a.id];
}
fs.writeFileSync(RUTAS_F, JSON.stringify(Object.fromEntries(Object.entries(RUTAS).sort()), null, 1) + "\n");
for (const k of Object.keys(PAGES)) ROUTE[k] = `/${k}/`;
for (const tg of tags) ROUTE["t-" + slug(tg)] = `/tema/${slug(tg)}/`;

// ---- pass 2: patch app script ----
function rep(from, to, all) {
  if (!script.includes(from)) throw new Error("patch not found: " + from);
  script = all ? script.split(from).join(to) : script.replace(from, to);
}
rep(`const h=(location.hash||"#inicio").slice(1);`, `const h=CUR();`);
rep(`location.hash==="#"+k`, `CUR()===k`);
rep(`document.documentElement.lang=lang;scrollTo(0,0);`, `document.documentElement.lang=lang;fixLinks(document);if(window.__booted)scrollTo(0,0);window.__booted=1;`);
rep(`datePublished:a.date,`, `datePublished:a.date+"T"+(a.hora||"09:00")+":00-05:00",dateModified:MOD(a),url:SITE+ROUTE[a.id],mainEntityOfPage:SITE+ROUTE[a.id],image:[SITE+(FOTOS[a.id]?"/assets/fotos/"+a.id+".jpg":(OG[a.id]||"/assets/og-default.jpg"))],`);
rep(`publisher:{"@type":"NewsMediaOrganization",name:"${M.nombre_largo}"}`, `publisher:{"@type":"NewsMediaOrganization",name:"${M.nombre_largo}",url:SITE,logo:{"@type":"ImageObject",url:SITE+"/assets/icon-512.png"}}`);
rep(`riverShown=n;$("#count")`, `fixLinks($("#feed"));riverShown=n;$("#count")`);
rep(`addEventListener("hashchange",route);`, ``);
rep(`document.title=a?`, `if(window.__nt)document.title=a?`);
rep(`function setLang(){lang=`, `function setLang(){window.__nt=1;lang=`);

const shim = `const SITE=${JSON.stringify(SITE)};const OG=${JSON.stringify(OGMAP)};const ROUTE=${JSON.stringify(ROUTE)};
const CUR=()=>{const p=location.pathname.replace(/index\\.html$/,"");for(const k in ROUTE)if(ROUTE[k]===p)return k;return "inicio"};
const MOD=a=>{const p=a.date+"T"+(a.hora||"09:00")+":00-05:00";const c=(a.correcciones||[]).concat((a.ediciones||[]).filter(x=>x.tipo==="ampliacion")).map(x=>x.iso||(x.fecha?x.fecha.split(".").reverse().join("-")+"T12:00:00-05:00":"")).filter(Boolean).sort();return c.length&&c[c.length-1]>p?c[c.length-1]:p};
const fmtD=d=>{const [y,m,dd]=(d||"").split("-");return lang==="es"?dd+"."+m+"."+y:m+"/"+dd+"/"+y};
function fixLinks(r){r.querySelectorAll('a[href^="#"]').forEach(a=>{const k=a.getAttribute("href").slice(1);if(ROUTE[k])a.setAttribute("href",ROUTE[k])})}
document.addEventListener("click",e=>{const a=e.target.closest('a[href^="#"]');if(!a)return;const k=a.getAttribute("href").slice(1);if(ROUTE[k]){e.preventDefault();location.href=ROUTE[k]}},true);
`;
const app = shim + script;
fs.mkdirSync(path.join(OUT, "assets/og"), { recursive: true });
for (const id in OGMAP) fs.copyFileSync(path.join(OGDIR, id + ".jpg"), path.join(OUT, "assets/og", id + ".jpg"));
fs.writeFileSync(path.join(OUT, "assets/estilo.css"), style.trim() + "\n");
// app.js lleva solo el índice liviano de las notas; el texto completo va en la página de cada nota (window.__NOTA)
const LITE = ["id", "date", "hora", "sec", "tag", "min", "title", "titleEn", "dek", "peso", "minuto", "propia"];
const jsonSafe = o => JSON.stringify(o).replace(/</g, "\\u003c");
const ia = app.indexOf("/*@@A*/"), ja = app.indexOf("/*A@@*/");
if (ia < 0 || ja < 0) throw new Error("faltan los marcadores de notas en la plantilla");
const appLite = app.slice(0, ia) + jsonSafe(A.map(a => Object.fromEntries(LITE.filter(k => a[k] !== undefined).map(k => [k, a[k]])))) + app.slice(ja + 7);
fs.writeFileSync(path.join(OUT, "assets/app.js"), appLite);
const VER = require("crypto").createHash("sha1").update(appLite + style).digest("hex").slice(0, 10);
const tagCount = {}; for (const a of A) tagCount[a.tag] = (tagCount[a.tag] || 0) + 1;
const thinTag = key => { const tg = key.startsWith("t-") ? tags.find(x => "t-" + slug(x) === key) : null; return !!tg && tagCount[tg] < 3; };

// ---- fechas de publicación y de última actualización ----
const PUB = a => `${a.date}T${a.hora || "09:00"}:00-05:00`;
const MODN = a => { const c = (a.correcciones || []).concat((a.ediciones || []).filter(x => x.tipo === "ampliacion")).map(x => x.iso || (x.fecha ? x.fecha.split(".").reverse().join("-") + "T12:00:00-05:00" : "")).filter(Boolean).sort(); return c.length && c[c.length - 1] > PUB(a) ? c[c.length - 1] : PUB(a); };
// descripciones propias de cada sección (Google muestra este texto en los resultados)
const SEC_DESC = {
  noticias: "Noticias de música de hoy: anuncios de artistas, giras, conciertos y lo que pasa en la música latina y del mundo, con fuentes verificadas.",
  premios: "Grammy, Latin Grammy, Billboard, Premios Lo Nuestro y más: nominados, ganadores, fechas y dónde ver las ceremonias, con contexto.",
  listas: "Billboard Hot 100, Billboard 200, Hot Latin Songs y Spotify: los No. 1, los récords y lo que dicen las cifras de cada semana.",
  lanzamientos: "Estrenos de la semana: discos y canciones nuevas de la música latina y del mundo, cada viernes, con lo esencial de cada uno.",
  critica: "Reseñas y lecturas de discos de El Coro: qué funciona, qué no y dónde queda cada álbum en la carrera del artista.",
  industria: "El negocio de la música: streaming, sellos, derechos, regalías, cifras de la RIAA y la IFPI y las personas detrás de los éxitos.",
  artistas: "Consejos prácticos para artistas independientes: lanzar música, distribución, regalías, derechos, pitch a playlists y prensa, paso a paso.",
};
const crumbs = list => ({ "@context": "https://schema.org", "@type": "BreadcrumbList", itemListElement: list.map(([name, url], i) => ({ "@type": "ListItem", position: i + 1, name, item: SITE + url })) });

// ---- page meta ----
const esc = s => String(s).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
const strip = s => String(s).replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
const DEF_DESC = `${M.nombre_largo}: noticias de música del mundo en tiempo real, en español e inglés. Premios, lanzamientos, listas, crítica e industria, con fuentes verificadas.`;
function metaFor(key) {
  const a = A.find(x => x.id === key);
  const pg = PAGES[key];
  const tg = key.startsWith("t-") ? tags.find(x => "t-" + slug(x) === key) : null;
  const sec = T.es.sections[key];
  let title = `${M.nombre_largo} — La música del mundo, en tiempo real`, desc = DEF_DESC, type = "website", extra = "", robots = "index,follow,max-image-preview:large";
  if (a) {
    title = strip(a.title).length > 58 ? strip(a.title) : `${strip(a.title)} | ${M.nombre}`; desc = a.dek; type = "article"; // Google corta cerca de 60 caracteres: el titular va primero y la marca solo si cabe
    extra = `<meta property="article:published_time" content="${PUB(a)}">\n<meta property="article:modified_time" content="${MODN(a)}">\n<meta property="article:section" content="${esc(T.es.sections[a.sec])}">\n<meta property="article:tag" content="${esc(a.tag)}">`;
  } else if (pg) { title = `${pg.t.es} | ${M.nombre_largo}`; desc = strip(pg.body.es).slice(0, 155); }
  else if (tg) { title = `Tema: ${tg} | ${M.nombre_largo}`; desc = `Todas las notas de ${M.nombre} sobre ${tg}.`; if (thinTag(key)) robots = "noindex,follow"; }
  else if (sec && key !== "inicio") {
    title = `${sec} | ${M.nombre_largo}`; desc = SEC_DESC[key] || `${sec}: lo último en ${M.nombre_largo}, la música del mundo en tiempo real.`;
    if (["envivo", "cultura"].includes(key)) robots = "noindex,follow";
  }
  const url = SITE + ROUTE[key];
  return `<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>${esc(title)}</title>
<meta name="description" content="${esc(desc)}">
<meta name="robots" content="${robots}">
<link rel="canonical" href="${url}">
<meta property="og:site_name" content="${M.nombre_largo}">
<meta property="og:locale" content="es_US">
<meta property="og:type" content="${type}">
<meta property="og:title" content="${esc(a ? strip(a.title) : title.replace(" | " + M.nombre_largo, ""))}">
<meta property="og:description" content="${esc(desc)}">
<meta property="og:url" content="${url}">
<meta property="og:image" content="${SITE}${(a && OGMAP[a.id]) || "/assets/og-default.jpg"}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
${extra}
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/assets/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="alternate" type="application/rss+xml" title="${M.nombre_largo}" href="/feed.xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
${fontsAsync}
<link rel="stylesheet" href="/assets/estilo.css?v=${VER}">`;
}

// ---- render every route ----
function render(key, file) {
  const head = metaFor(key);
  const html = `<!DOCTYPE html><html lang="es"><head>${head}</head><body>${markup}<script id="__app">${app}</script></body></html>`;
  const dom = new JSDOM(html, { url: SITE + ROUTE[key], runScripts: "dangerously", virtualConsole: vc });
  const d = dom.window.document;
  // the app sets <title>; keep our SEO title instead
  d.title = d.head.querySelector("title").textContent;
  const s = d.getElementById("__app"); const ext = d.createElement("script"); ext.src = "/assets/app.js?v=" + VER; s.replaceWith(ext);
  const nota = A.find(x => x.id === key);
  if (nota) { const inl = d.createElement("script"); inl.textContent = "window.__NOTA=" + jsonSafe(nota) + ";"; ext.before(inl); }
  // move JSON-LD into head for crawlers (app updates it by id)
  const ld = d.getElementById("ld"); if (ld) d.head.appendChild(ld);
  const addLD = o => { const e = d.createElement("script"); e.setAttribute("type", "application/ld+json"); e.textContent = JSON.stringify(o); d.head.appendChild(e); };
  if (nota) addLD(crumbs([["Portada", "/"], [T.es.sections[nota.sec], ROUTE[nota.sec]], [nota.title, ROUTE[nota.id]]]));
  else if (T.es.sections[key] && key !== "inicio" && ROUTE[key]) addLD(crumbs([["Portada", "/"], [T.es.sections[key], ROUTE[key]]]));
  if (key === "inicio" && !file) addLD({ "@context": "https://schema.org", "@type": "WebSite", name: M.nombre_largo, alternateName: [M.nombre, M.dominio], url: SITE + "/", inLanguage: "es" });
  // la foto principal empieza a bajar junto con el estilo, sin esperar al resto
  const hero = d.querySelector('img[fetchpriority="high"]');
  if (hero) {
    const pl = d.createElement("link");
    pl.setAttribute("rel", "preload"); pl.setAttribute("as", "image"); pl.setAttribute("fetchpriority", "high");
    pl.setAttribute("href", hero.getAttribute("src"));
    if (hero.getAttribute("srcset")) { pl.setAttribute("imagesrcset", hero.getAttribute("srcset")); pl.setAttribute("imagesizes", hero.getAttribute("sizes") || "100vw"); }
    const css = d.head.querySelector('link[href^="/assets/estilo.css"]');
    d.head.insertBefore(pl, css || null);
  }
  let out = "<!DOCTYPE html>\n" + d.documentElement.outerHTML;
  out = out.replace(/href="#([^"]+)"/g, (m, k) => ROUTE[k] ? `href="${ROUTE[k]}"` : m);
  const fp = path.join(OUT, file || (ROUTE[key] + "index.html"));
  fs.mkdirSync(path.dirname(fp), { recursive: true });
  fs.writeFileSync(fp, out);
  dom.window.close();
}
for (const k of Object.keys(ROUTE)) render(k);
render("inicio", "404.html");
{ const f404 = path.join(OUT, "404.html"); fs.writeFileSync(f404, fs.readFileSync(f404, "utf8").replace('content="index,follow,max-image-preview:large"', 'content="noindex,follow"').replace(/<link rel="canonical"[^>]*>/, "")); }

// ---- sitemap, news sitemap, rss, robots, manifest ----
const lastmod = A.reduce((m, a) => a.date > m ? a.date : m, "");
const sitemapKeys = Object.keys(ROUTE).filter(k => !["envivo", "cultura"].includes(k) && !thinTag(k));
fs.writeFileSync(path.join(OUT, "sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n` +
  sitemapKeys.map(k => {
    const a = A.find(x => x.id === k);
    const img = a && W.eval("FOTOS")[a.id] ? `<image:image><image:loc>${SITE}/assets/fotos/${a.id}.jpg</image:loc></image:image>` : (a && OGMAP[a.id] ? `<image:image><image:loc>${SITE}${OGMAP[a.id]}</image:loc></image:image>` : "");
    return `  <url><loc>${SITE}${ROUTE[k]}</loc><lastmod>${a ? MODN(a) : lastmod}</lastmod>${img}</url>`;
  }).join("\n") + `\n</urlset>\n`);
const x = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const byDate = A.slice().sort((a, b) => (b.date + (b.hora || "")).localeCompare(a.date + (a.hora || "")));
const lim = new Date(new Date(lastmod + "T12:00:00Z").getTime() - 2 * 864e5).toISOString().slice(0, 10);
const recientes = byDate.filter(a => a.date >= lim); // Google News solo quiere las últimas 48 horas
fs.writeFileSync(path.join(OUT, "news-sitemap.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">\n` +
  recientes.map(a => `  <url><loc>${SITE}${ROUTE[a.id]}</loc><news:news><news:publication><news:name>${M.nombre_largo}</news:name><news:language>es</news:language></news:publication><news:publication_date>${a.date}T${a.hora || "09:00"}:00-05:00</news:publication_date><news:title>${x(a.title)}</news:title></news:news></url>`).join("\n") + `\n</urlset>\n`);
const rfc = a => new Date(PUB(a)).toUTCString();
fs.writeFileSync(path.join(OUT, "feed.xml"),
  `<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>\n<title>${M.nombre_largo}</title><link>${SITE}/</link><description>La música del mundo, en tiempo real.</description><language>es</language>\n<atom:link href="${SITE}/feed.xml" rel="self" type="application/rss+xml"/>\n` +
  byDate.map(a => `<item><title>${x(a.title)}</title><link>${SITE}${ROUTE[a.id]}</link><guid>${SITE}${ROUTE[a.id]}</guid><pubDate>${rfc(a)}</pubDate><category>${x(T.es.sections[a.sec])}</category><description>${x(a.dek)}</description></item>`).join("\n") + `\n</channel></rss>\n`);
fs.writeFileSync(path.join(OUT, "robots.txt"), `User-agent: *\nAllow: /\n\nSitemap: ${SITE}/sitemap.xml\nSitemap: ${SITE}/news-sitemap.xml\n`);
fs.writeFileSync(path.join(OUT, "site.webmanifest"), JSON.stringify({ name: M.nombre_largo, short_name: M.nombre, start_url: "/", display: "browser", background_color: "#ffffff", theme_color: "#e3120b", icons: [{ src: "/assets/icon-192.png", sizes: "192x192", type: "image/png" }, { src: "/assets/icon-512.png", sizes: "512x512", type: "image/png" }] }, null, 1));
// archivos del hosting (Namecheap / Apache): .htaccess y boletín en PHP
for (const f of [".htaccess", "suscribir.php"]) { const hp = path.join(__dirname, "hosting", f); if (fs.existsSync(hp)) fs.writeFileSync(path.join(OUT, f), TOK(fs.readFileSync(hp, "utf8"))); }
console.log("routes:", Object.keys(ROUTE).length, "articles:", A.length);
