"""
Render the SharpSignals Open Graph card directly with Pillow.

We render at exact 1200×630 pixels (the Twitter / Meta / iMessage standard).
Pillow gives us pixel-perfect control without depending on an SVG renderer
that pads non-square viewBoxes.

Tokens here mirror brand/IDENTITY.md. Output: web/assets/social/og-card.png

Run:
  python3 scripts/render_og_card.py
"""

from __future__ import annotations
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# Brand tokens (sync with brand/IDENTITY.md)
BG_DEEP = (13, 17, 23)
BG_ELEV = (22, 27, 34)
BORDER = (48, 54, 61)
TEXT_PRIMARY = (230, 237, 243)
TEXT_MUTED = (139, 148, 158)
ACCENT_BLUE = (121, 192, 255)


W, H = 1200, 630
PAD = 64


def load_font(family: str, size: int, weight: str = "Regular") -> ImageFont.FreeTypeFont:
    """Try system fonts first (Inter / SF / Helvetica), then DejaVu fallback.

    macOS ships SF / Helvetica; Inter only if user installed it. We try a
    sensible chain so the OG card looks the same on any contributor's machine.
    """
    candidates = []
    if family == "sans":
        candidates = [
            (f"Inter-{weight}.ttf", size),
            ("HelveticaNeue.ttc", size),
            ("Helvetica.ttc", size),
            ("Arial.ttf", size),
            ("DejaVuSans-Bold.ttf" if weight == "Bold" else "DejaVuSans.ttf", size),
        ]
    elif family == "mono":
        candidates = [
            (f"JetBrainsMono-{weight}.ttf", size),
            ("SFMono-Regular.otf", size),
            ("Menlo.ttc", size),
            ("DejaVuSansMono-Bold.ttf" if weight == "Bold" else "DejaVuSansMono.ttf", size),
        ]
    for name, sz in candidates:
        try:
            return ImageFont.truetype(name, sz)
        except OSError:
            continue
    return ImageFont.load_default()


def render() -> Path:
    img = Image.new("RGB", (W, H), color=BG_DEEP)
    draw = ImageDraw.Draw(img)

    # Subtle blue glow bottom-right (radial-gradient approximation)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    for r, alpha in ((420, 6), (320, 10), (220, 14), (140, 18)):
        glow_draw.ellipse(
            (W - r, H - r, W + r, H + r),
            fill=(*ACCENT_BLUE, alpha),
        )
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Hairline frame
    draw.rounded_rectangle(
        (40, 40, W - 40, H - 40),
        radius=20,
        outline=BORDER,
        width=2,
    )

    # Wordmark
    wordmark_font = load_font("sans", 32, "Bold")
    draw.text((PAD + 16, PAD + 24), "SHARPSIGNALS", fill=ACCENT_BLUE, font=wordmark_font)

    # Hairline under wordmark
    draw.line([(PAD + 16, 130), (W - PAD - 16, 130)], fill=BORDER, width=2)

    # Eyebrow
    eyebrow_font = load_font("mono", 22, "Medium")
    draw.text((PAD + 16, 175), "ALGORITHMIC SPORTS ANALYTICS",
              fill=ACCENT_BLUE, font=eyebrow_font)

    # Headline (two lines)
    headline_font = load_font("sans", 78, "Bold")
    draw.text((PAD + 16, 230), "Every pick logged.", fill=TEXT_PRIMARY, font=headline_font)
    draw.text((PAD + 16, 320), "Every loss shown.", fill=ACCENT_BLUE, font=headline_font)

    # Sub
    sub_font = load_font("sans", 24, "Regular")
    draw.text((PAD + 16, 425),
              "NBA · NHL · MLB · Soccer · Cricket — public track record",
              fill=TEXT_MUTED, font=sub_font)

    # CTA pill (bottom-right)
    cta_text = "sharpsignals.org  >"
    cta_font = load_font("sans", 24, "Bold")
    bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pill_pad_x, pill_pad_y = 24, 14
    pill_x2 = W - PAD - 16
    pill_y2 = H - PAD - 50
    pill_x1 = pill_x2 - text_w - pill_pad_x * 2
    pill_y1 = pill_y2 - text_h - pill_pad_y * 2
    draw.rounded_rectangle(
        (pill_x1, pill_y1, pill_x2, pill_y2),
        radius=(pill_y2 - pill_y1) // 2,
        fill=ACCENT_BLUE,
    )
    draw.text((pill_x1 + pill_pad_x, pill_y1 + pill_pad_y - 3),
              cta_text, fill=BG_DEEP, font=cta_font)

    # Footer compliance
    footer_font = load_font("sans", 18, "Regular")
    draw.text((PAD + 16, H - PAD - 30),
              "18+ · Analytical content, not betting advice · ConnexOntario 1-866-531-2600",
              fill=TEXT_MUTED, font=footer_font)

    out = Path(__file__).resolve().parent.parent / "web" / "assets" / "social" / "og-card.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    return out


if __name__ == "__main__":
    path = render()
    size = os.path.getsize(path)
    img = Image.open(path)
    print(f"Wrote {path}")
    print(f"  dimensions: {img.size[0]}×{img.size[1]}")
    print(f"  size:       {size:,} bytes")
