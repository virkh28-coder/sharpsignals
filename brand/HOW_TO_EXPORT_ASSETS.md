# How to turn the SVG assets into PNGs (for IG / Meta / etc.)

Instagram doesn't accept SVG profile pictures. Meta's Open Graph crawler also wants PNG/JPG. So we need to render the SVG sources into PNGs once.

## Two options, no design software needed

### Option 1 — In your browser (zero install)

1. Open the SVG file in Chrome/Safari (drag the file into a browser tab)
2. Take a screenshot of just the rendered SVG:
   - **macOS**: `Cmd + Shift + 4`, drag a box around the SVG, save
3. Result is a PNG — slightly imperfect but fine for IG profile pic at 320×320

This is good enough for the IG profile pic. For Open Graph cards (where pixel quality matters more), use option 2.

### Option 2 — Use rsvg-convert (best quality, one-time install)

```bash
brew install librsvg
```

Then in the project root:

```bash
# IG profile picture (1080×1080 — IG max)
rsvg-convert -w 1080 -h 1080 brand/profile_picture.svg \
  -o brand/profile_picture.png

# Open Graph card for social link previews (1200×630 — Twitter/Meta standard)
rsvg-convert -w 1200 -h 630 web/assets/social/og-card.svg \
  -o web/assets/social/og-card.png
```

## Where each PNG goes

| File | Where to upload |
| ---- | --------------- |
| `brand/profile_picture.png` | Instagram → Edit profile → Change profile photo. Also set as Telegram channel avatar. |
| `web/assets/social/og-card.png` | Lives at `https://sharpsignals.org/assets/social/og-card.png` after Cloudflare Pages auto-deploys. The landing page already references it via the `og:image` meta tag. |

## Verify the OG card works

After pushing the PNG and Cloudflare Pages re-deploys (~30 seconds):

1. Go to https://www.opengraph.xyz/
2. Paste `https://sharpsignals.org`
3. The preview should show the dark card with "Every pick logged. Every loss shown."

If it shows a blank/broken image, the PNG isn't reachable yet — wait 1 minute and try again, or check the Pages deployment log.

## When to redo these

- **Profile pic**: only if you change the brand mark
- **OG card**: anytime you change the headline / positioning copy. Re-render and push — Meta caches OG images for ~24h, force a refresh by appending `?v=2` to the meta-tag URL.
