#!/usr/bin/env bash
# Render every brand SVG to PNG at the right size for its destination.
#
# Why this exists:
#   IG / Meta Graph / favicon caches all want raster images. We keep the
#   sources as SVG (one-pixel-perfect file per asset), and re-render
#   whenever brand identity changes.
#
# Renderer preference:
#   1. rsvg-convert  (librsvg) — cleanest text antialiasing, install via brew
#   2. qlmanage                — built-in macOS, works without install but text
#                                rendering is slightly softer
#
# Usage:
#   bash scripts/render_assets.sh
#
# Add new assets at the bottom, in the ASSETS array.

set -euo pipefail

cd "$(dirname "$0")/.."

if command -v rsvg-convert >/dev/null 2>&1; then
  RENDERER="rsvg-convert"
elif command -v qlmanage >/dev/null 2>&1; then
  RENDERER="qlmanage"
else
  echo "ERROR: need rsvg-convert (brew install librsvg) or macOS qlmanage"
  exit 1
fi
echo "Using $RENDERER"

# format: "<src.svg>:<dst.png>:<width>:<height>"
ASSETS=(
  "brand/profile_picture.svg:brand/profile_picture.png:1080:1080"
  "web/assets/social/og-card.svg:web/assets/social/og-card.png:1200:630"
  "web/favicon.svg:web/favicon.png:256:256"
)

render() {
  local src="$1" dst="$2" w="$3" h="$4"
  mkdir -p "$(dirname "$dst")"
  case "$RENDERER" in
    rsvg-convert)
      rsvg-convert -w "$w" -h "$h" "$src" -o "$dst"
      ;;
    qlmanage)
      # qlmanage takes the longest side via -s and writes <basename>.png
      local longest=$(( w > h ? w : h ))
      local tmp; tmp=$(mktemp -d)
      qlmanage -t -s "$longest" -o "$tmp" "$src" >/dev/null 2>&1
      mv "$tmp/$(basename "$src").png" "$dst"
      rm -rf "$tmp"
      ;;
  esac
  echo "  $src → $dst ($w×$h, $(stat -f%z "$dst") bytes)"
}

for entry in "${ASSETS[@]}"; do
  IFS=':' read -r src dst w h <<<"$entry"
  if [[ ! -f "$src" ]]; then
    echo "  SKIP (missing): $src"
    continue
  fi
  render "$src" "$dst" "$w" "$h"
done

echo "Done."
