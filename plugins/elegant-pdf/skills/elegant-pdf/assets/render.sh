#!/usr/bin/env bash
# elegant-pdf renderer — HTML -> PDF (clickable links preserved) or a crisp 2x JPEG.
# Uses headless Chrome/Chromium/Edge; no other dependencies.
#
#   render.sh pdf   input.html output.pdf
#   render.sh jpeg  input.html output.jpeg [WIDTH] [HEIGHT]   (defaults 1080x1500)
#
# The input HTML must be able to load its assets (theme.css, images): keep it in
# the same folder as theme.css, or inline the stylesheet. Chrome loads file://
# directly, so no local server is needed.
set -euo pipefail

MODE="${1:-}"; IN="${2:-}"; OUT="${3:-}"
[ -n "$MODE" ] && [ -n "$IN" ] && [ -n "$OUT" ] || { echo "usage: render.sh pdf|jpeg input.html output [W] [H]"; exit 2; }
[ -f "$IN" ] || { echo "input not found: $IN"; exit 1; }

# absolute file:// url (Chrome needs a real path for relative assets)
ABS="$(cd "$(dirname "$IN")" && pwd)/$(basename "$IN")"
URL="file://$ABS"

find_chrome() {
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "$(command -v google-chrome 2>/dev/null || true)" \
    "$(command -v chromium 2>/dev/null || true)" \
    "$(command -v chromium-browser 2>/dev/null || true)"; do
    [ -n "$c" ] && [ -x "$c" ] && { echo "$c"; return 0; }
  done
  echo ""; return 1
}
CHROME="$(find_chrome)"
[ -n "$CHROME" ] || { echo "No Chrome/Chromium/Edge found. Install one, or render another way."; exit 1; }

case "$MODE" in
  pdf)
    "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer \
      --print-to-pdf="$OUT" "$URL"
    echo "wrote $OUT"
    ;;
  jpeg|jpg)
    W="${4:-1080}"; H="${5:-1500}"
    TMP="$(mktemp -d)/shot.png"
    # 2x device scale => a WxH sheet renders at (2W)x(2H) pixels.
    "$CHROME" --headless=new --disable-gpu --hide-scrollbars \
      --force-device-scale-factor=2 --window-size="${W},${H}" \
      --screenshot="$TMP" "$URL"
    if command -v sips >/dev/null 2>&1; then
      sips -s format jpeg -s formatOptions 92 "$TMP" --out "$OUT" >/dev/null
    elif command -v magick >/dev/null 2>&1; then
      magick "$TMP" -quality 92 "$OUT"
    else
      echo "PNG written (no sips/magick to make jpeg): $TMP"; exit 0
    fi
    echo "wrote $OUT ($((2*W))x$((2*H)))"
    ;;
  *) echo "unknown mode: $MODE (use pdf or jpeg)"; exit 2 ;;
esac
