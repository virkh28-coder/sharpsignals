"""
Render the SharpSignals first-post hero graphic for Instagram.

Different from a daily pick: this is a brand-intro card meant to be the
first thing a new follower sees. No odds, no edge — just positioning.

Output: data/processed/intro_post.png (1080×1350 IG portrait)
"""

from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw

from agents.content_agent.post_generator import (
    BG_DEEP, BG_ELEV, BORDER, TEXT_PRIMARY, TEXT_MUTED,
    ACCENT_BLUE, POS_GREEN,
    _load_fonts, _rounded_rect,
)


def render() -> Path:
    W, H = 1080, 1350
    PAD = 60

    img = Image.new("RGB", (W, H), color=BG_DEEP)

    # Soft glow bottom-right for depth
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for r, alpha in ((640, 6), (440, 9), (280, 14), (160, 18)):
        d.ellipse((W - r, H - r, W + r, H + r), fill=(*ACCENT_BLUE, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")

    # Faded line-chart watermark, large, bottom-left
    layer2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(layer2)
    cx, cy = int(W * 0.25), int(H * 0.62)
    pts = [
        (cx - 220, cy + 180),
        (cx - 80,  cy + 80),
        (cx + 60,  cy + 130),
        (cx + 220, cy - 80),
        (cx + 360, cy - 220),
    ]
    d2.line(pts, fill=(*ACCENT_BLUE, 18), width=22)
    d2.ellipse((pts[-1][0] - 22, pts[-1][1] - 22,
                pts[-1][0] + 22, pts[-1][1] + 22),
               fill=(*ACCENT_BLUE, 24))
    img = Image.alpha_composite(img.convert("RGBA"), layer2).convert("RGB")

    draw = ImageDraw.Draw(img)
    fonts = _load_fonts()

    # Wordmark top-left
    draw.text((PAD, PAD), "SHARPSIGNALS",
              fill=ACCENT_BLUE, font=fonts["wordmark"])

    # Eyebrow pill (top-right) — "FOLLOW THE ALGORITHM"
    eyebrow = "FOLLOW THE ALGORITHM"
    bbox = draw.textbbox((0, 0), eyebrow, font=fonts["pill"])
    pw = bbox[2] - bbox[0]
    pad_x, pad_y = 18, 8
    px2 = W - PAD
    px1 = px2 - pw - pad_x * 2
    py1 = PAD - 4
    py2 = py1 + 44
    _rounded_rect(draw, (px1, py1, px2, py2),
                  radius=22, fill=BG_ELEV, outline=ACCENT_BLUE, width=2)
    draw.text((px1 + pad_x, py1 + pad_y - 2),
              eyebrow, fill=ACCENT_BLUE, font=fonts["pill"])

    # Hairline under header
    draw.line([(PAD, PAD + 80), (W - PAD, PAD + 80)],
              fill=BORDER, width=1)

    # Hero headline — split for emphasis
    headline_y = 360
    draw.text((PAD, headline_y), "Every pick",
              fill=TEXT_PRIMARY, font=fonts["pick_big"])
    draw.text((PAD, headline_y + 110), "logged.",
              fill=TEXT_PRIMARY, font=fonts["pick_big"])
    draw.text((PAD, headline_y + 250), "Every loss",
              fill=ACCENT_BLUE, font=fonts["pick_big"])
    draw.text((PAD, headline_y + 360), "shown.",
              fill=ACCENT_BLUE, font=fonts["pick_big"])

    # Sub-line: sports covered
    sub_y = headline_y + 510
    draw.text((PAD, sub_y),
              "NBA · NHL · MLB · SOCCER · CRICKET",
              fill=TEXT_MUTED, font=fonts["row_label"])

    # CTA pill — bottom of card
    cta_y = H - 290
    cta_card = (PAD, cta_y, W - PAD, cta_y + 100)
    _rounded_rect(draw, cta_card, radius=14,
                  fill=BG_ELEV, outline=BORDER, width=2)
    draw.text((PAD + 28, cta_y + 22),
              "PUBLIC TRACK RECORD", fill=POS_GREEN, font=fonts["label"])
    draw.text((PAD + 28, cta_y + 50),
              "sharpsignals.org",
              fill=ACCENT_BLUE, font=fonts["url"])

    # Footer hairline
    draw.line([(PAD, H - 145), (W - PAD, H - 145)],
              fill=BORDER, width=1)

    draw.text((PAD, H - 60),
              "18+ · Analytical content, not betting advice · ConnexOntario 1-866-531-2600",
              fill=TEXT_MUTED, font=fonts["footer"])

    out = Path("data/processed/intro_post.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    return out


if __name__ == "__main__":
    p = render()
    print(f"Wrote {p}")
