#!/bin/bash
# El Coro: copia la web desde GitHub cuando hay una versión nueva. Lo ejecuta el cron de cPanel cada 15 minutos.
# Nunca borra archivos del sitio: solo agrega y actualiza.
GH_USUARIO="elcoro-web"
REPO="elcoro-web"
DEST="$HOME/elcoromagazine.com"
TMP="$HOME/.elcoro_tmp"
LOG="$HOME/elcoro_actualizaciones.log"
umask 022
remota=$(curl -fsS -m 30 "https://raw.githubusercontent.com/$GH_USUARIO/$REPO/main/public/version.txt") || exit 0
actual=$(cat "$DEST/version.txt" 2>/dev/null)
[ -n "$remota" ] && [ "$remota" = "$actual" ] && exit 0
rm -rf "$TMP" && mkdir -p "$TMP" || exit 1
if curl -fsSL -m 120 "https://codeload.github.com/$GH_USUARIO/$REPO/tar.gz/refs/heads/main" | tar -xz -C "$TMP" --strip-components=2 "$REPO-main/public" \
   && [ -f "$TMP/index.html" ] && [ -f "$TMP/version.txt" ]; then
  cp -R "$TMP"/. "$DEST"/
  find "$DEST" \( -path "$DEST/cgi-bin" -o -path "$DEST/.well-known" \) -prune -o -type d -exec chmod 755 {} + -o -type f -exec chmod 644 {} +
  echo "$(date -u +%FT%TZ) actualizado a $(cat "$TMP/version.txt")" >> "$LOG"
else
  echo "$(date -u +%FT%TZ) ERROR al descargar" >> "$LOG"
fi
rm -rf "$TMP"
