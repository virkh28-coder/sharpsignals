"""
Content Agent.

Takes a Pick and produces a publishable caption + graphic.
Uses Claude Sonnet 4.6 via the Anthropic SDK.

Output contract:
  - caption (≤2,200 chars for IG)
  - telegram_message (Markdown)
  - graphic_path (PNG file written to disk for the scheduler to upload)

Every generated caption passes through compliance.check() before returning.
If compliance fails, we re-ask Claude up to 2 times, then escalate to manual review.
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from agents.pick_agent.pick_generator import Pick
from src.utils.compliance import check as compliance_check


MODEL = "claude-sonnet-4-6"  # latest Sonnet at time of writing; update if needed


SYSTEM_PROMPT = """\
You write Instagram captions for SharpSignals — a transparent, algorithmic
sports betting analytics brand. Your job: turn a structured pick record into
a caption that is honest, analytical, and legally safe.

HARD RULES (NEVER break):
1. Never use: "lock", "guaranteed", "sure thing", "can't lose", "fixed",
   "inside info", "insider", "rigged", "secret tip", "exclusive", "max play".
2. Always include: "18+", the ConnexOntario helpline "1-866-531-2600",
   and a variant of "analytical content, not betting advice".
3. Never claim a winning outcome is certain. Models produce probabilities.
4. Never cite a track record number unless provided in the input.
5. Keep caption under 2,100 characters (IG hard limit 2,200, buffer for safety).

TONE: confident but honest. Data-driven. No hype emojis. One or two tasteful
emojis maximum. Audience = bettors who respect methodology, not thrill-seekers.

STRUCTURE:
  Line 1: matchup + market + selection
  Lines 2–4: why (one sentence on the model signal, one on the edge %)
  Line 5: odds + units + sportsbook
  Final block: standard disclaimer footer
"""


USER_TEMPLATE = """\
Generate an Instagram caption for this pick:

Sport: {sport}
Event: {event_label}
Market: {market}
Selection: {selection}
Odds: {odds_american} ({sportsbook_source})
Model fair probability: {model_fair_probability:.1%}
Market implied probability: {market_implied_probability:.1%}
Edge: {edge_percent}%
Units: {bet_size_units}u ({confidence_tier})

Output ONLY the caption, no preamble.
"""


@dataclass
class GeneratedContent:
    caption: str
    telegram_message: str
    graphic_path: Optional[Path]
    compliance_passed: bool
    compliance_notes: str


def generate(pick: Pick, output_dir: Path = Path("./data/processed")) -> GeneratedContent:
    """Generate caption + TG message + graphic for a pick."""
    caption = _generate_caption(pick)
    tg_message = _caption_to_telegram(pick)
    graphic = _render_graphic(pick, output_dir)

    result = compliance_check(caption)
    return GeneratedContent(
        caption=caption,
        telegram_message=tg_message,
        graphic_path=graphic,
        compliance_passed=result.passed,
        compliance_notes=result.summary(),
    )


def _generate_caption(pick: Pick, max_retries: int = 2) -> str:
    """Call Claude until compliance passes or we exhaust retries."""
    try:
        from anthropic import Anthropic
    except ImportError:
        raise RuntimeError("anthropic SDK not installed — run: pip install anthropic")

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_msg = USER_TEMPLATE.format(**pick.to_dict())

    for attempt in range(max_retries + 1):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        caption = resp.content[0].text.strip()

        if compliance_check(caption).passed:
            return caption

        # retry with stricter instruction
        user_msg = (
            USER_TEMPLATE.format(**pick.to_dict())
            + "\n\nPREVIOUS ATTEMPT FAILED COMPLIANCE. "
              "Do not use banned words. Ensure 18+ and ConnexOntario 1-866-531-2600 appear."
        )

    # All retries failed → return last attempt; caller sees compliance_passed=False
    return caption


def _caption_to_telegram(pick: Pick) -> str:
    """Build a short Telegram message directly from the pick.

    We intentionally don't reuse the IG caption — IG runs long and emoji-light,
    Telegram wants ~6 lines of plain Markdown. Generating from `pick` directly
    keeps the TG channel deterministic and Claude-free.
    """
    lines = [
        f"*{pick.sport} — {pick.event_label}*",
        f"Pick: *{pick.selection}* ({pick.market})",
        f"Odds: {pick.odds_american} @ {pick.sportsbook_source}",
        f"Edge: {pick.edge_percent}% | Size: {pick.bet_size_units}u",
        "",
        "18+ · Analytical content, not advice · ConnexOntario 1-866-531-2600",
    ]
    return "\n".join(lines)


# Brand tokens — keep in sync with brand/IDENTITY.md
BG_DEEP = (13, 17, 23)
BG_ELEV = (22, 27, 34)
BG_ELEV_2 = (28, 33, 41)
BORDER = (48, 54, 61)
BORDER_BRIGHT = (72, 81, 92)
TEXT_PRIMARY = (230, 237, 243)
TEXT_MUTED = (139, 148, 158)
ACCENT_BLUE = (121, 192, 255)
ACCENT_CYAN = (86, 212, 221)
POS_GREEN = (86, 211, 100)
NEG_RED = (248, 81, 73)
WARN_YELLOW = (227, 179, 65)


def _render_graphic(pick: Pick, output_dir: Path) -> Optional[Path]:
    """Render a 1080×1350 branded bet-slip graphic via PIL.

    Visual hierarchy (top → bottom):
      1. Watermark line-chart mark behind everything (very faded brand cue)
      2. Header strip: wordmark + date + "MODEL PICK" pill
      3. Sport tag with basketball icon
      4. Matchup display with @ separator
      5. Hero pick card with confidence-tier badge floating top-right
      6. Visual edge bar (gradient fill, edge magnitude)
      7. 2×2 stats grid: fair / implied / edge / units
      8. Footer with sharpsignals.org CTA + compliance disclaimers
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow not installed — skipping graphic")
        return None

    from datetime import datetime, timezone

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{pick.pick_id}.png"

    W, H = 1080, 1350
    PAD = 60

    img = Image.new("RGB", (W, H), color=BG_DEEP)
    fonts = _load_fonts()

    # 1. WATERMARK — large faded line-chart mark behind content
    _draw_watermark(img, W, H)

    # 2. SUBTLE BLUE GLOW bottom-right for depth
    _draw_corner_glow(img, W, H)

    draw = ImageDraw.Draw(img)

    # 3. HEADER STRIP
    _draw_header_strip(draw, W, PAD, pick.timestamp_utc, fonts)

    # 4. SPORT TAG (with basketball icon for NBA)
    sport_y = PAD + 140
    _draw_sport_tag(draw, PAD, sport_y, pick.sport, fonts)

    # 5. MATCHUP — emphasized
    matchup_y = sport_y + 90
    _draw_matchup(draw, PAD, matchup_y, pick.event_label, fonts)

    # 6. HERO PICK CARD with confidence badge
    card_y = matchup_y + 180
    card_h = 310
    _draw_pick_card(draw, PAD, card_y, W, card_h, pick, fonts)

    # 7. VISUAL EDGE BAR
    bar_y = card_y + card_h + 50
    _draw_edge_bar(draw, PAD, bar_y, W, pick.edge_percent, fonts)

    # 8. STATS 2×2 GRID
    grid_y = bar_y + 110
    _draw_stats_grid(draw, PAD, grid_y, W, pick, fonts)

    # 9. FOOTER
    _draw_footer(draw, PAD, H, W, fonts)

    img.save(path, "PNG", optimize=True)
    return path


# ----------- drawing helpers -----------

def _draw_watermark(img, W: int, H: int) -> None:
    """Big faded line-chart mark behind everything. ~5% opacity brand cue."""
    from PIL import Image, ImageDraw

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # Stylized rising line chart, oversize, top-right anchored
    cx, cy = int(W * 0.7), int(H * 0.4)
    pts = [
        (cx - 380, cy + 200),
        (cx - 200, cy + 60),
        (cx - 80,  cy + 130),
        (cx + 110, cy - 90),
        (cx + 280, cy - 240),
    ]
    d.line(pts, fill=(*ACCENT_BLUE, 14), width=18)
    d.ellipse((pts[-1][0] - 18, pts[-1][1] - 18, pts[-1][0] + 18, pts[-1][1] + 18),
              fill=(*ACCENT_BLUE, 18))
    img.alpha_composite(layer) if img.mode == "RGBA" else img.paste(
        Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    )


def _draw_corner_glow(img, W: int, H: int) -> None:
    """Soft blue glow in the bottom-right for depth."""
    from PIL import Image, ImageDraw

    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for r, alpha in ((520, 5), (380, 8), (240, 12), (140, 16)):
        d.ellipse(
            (W - r, H - r, W + r, H + r),
            fill=(*ACCENT_BLUE, alpha),
        )
    composited = Image.alpha_composite(img.convert("RGBA"), layer).convert("RGB")
    img.paste(composited)


def _draw_header_strip(draw, W: int, PAD: int, timestamp_utc: str, fonts) -> None:
    """Top: wordmark on left, date in middle, MODEL PICK pill on right."""
    # Wordmark
    draw.text((PAD, PAD), "SHARPSIGNALS", fill=ACCENT_BLUE, font=fonts["wordmark"])

    # Date (e.g. "29 APR 2026") — derived from pick timestamp
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))
        date_str = dt.strftime("%d %b %Y").upper()
    except Exception:
        date_str = ""

    if date_str:
        bbox = draw.textbbox((0, 0), date_str, font=fonts["pill"])
        date_w = bbox[2] - bbox[0]
        date_x = (W - date_w) // 2
        draw.text((date_x, PAD + 4), date_str, fill=TEXT_MUTED, font=fonts["pill"])

    # "MODEL PICK" pill (right-aligned)
    label = "MODEL PICK"
    bbox = draw.textbbox((0, 0), label, font=fonts["pill"])
    text_w = bbox[2] - bbox[0]
    pad_x, pad_y = 18, 8
    pill_x2 = W - PAD
    pill_x1 = pill_x2 - text_w - pad_x * 2
    pill_y1 = PAD - 4
    pill_y2 = pill_y1 + 44
    _rounded_rect(draw, (pill_x1, pill_y1, pill_x2, pill_y2),
                  radius=22, fill=ACCENT_BLUE)
    draw.text((pill_x1 + pad_x, pill_y1 + pad_y - 2),
              label, fill=BG_DEEP, font=fonts["pill"])

    # Hairline under header
    draw.line([(PAD, PAD + 80), (W - PAD, PAD + 80)], fill=BORDER, width=1)


def _draw_sport_tag(draw, x: int, y: int, sport: str, fonts) -> None:
    """Sport pill with a sport icon. NBA gets a basketball circle."""
    icon_size = 36
    pad_x = 18
    label = sport
    bbox = draw.textbbox((0, 0), label, font=fonts["pill"])
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pill_h = icon_size + 12
    pill_w = icon_size + pad_x + text_w + pad_x
    rect = (x, y, x + pill_w, y + pill_h)
    _rounded_rect(draw, rect, radius=pill_h // 2,
                  fill=BG_ELEV, outline=BORDER, width=2)

    # Basketball icon (orange-ish circle with seams)
    cx, cy = x + 6 + icon_size // 2, y + pill_h // 2
    r = icon_size // 2
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(228, 116, 49))
    draw.line((cx - r, cy, cx + r, cy), fill=(28, 18, 12), width=2)
    draw.line((cx, cy - r, cx, cy + r), fill=(28, 18, 12), width=2)
    # curve hints
    draw.arc((cx - r, cy - r * 2, cx + r, cy), 0, 180, fill=(28, 18, 12), width=2)
    draw.arc((cx - r, cy, cx + r, cy + r * 2), 180, 360, fill=(28, 18, 12), width=2)

    # Label
    draw.text((x + 6 + icon_size + pad_x,
               y + (pill_h - text_h) // 2 - 4),
              label, fill=TEXT_PRIMARY, font=fonts["pill"])


def _draw_matchup(draw, PAD: int, y: int, event_label: str, fonts) -> None:
    """Big matchup with subtle decoration."""
    draw.text((PAD, y - 30), "MATCHUP", fill=TEXT_MUTED, font=fonts["label"])
    # Try to split on " @ " for emphasis treatment
    if " @ " in event_label:
        away, home = event_label.split(" @ ", 1)
        # Two lines for readability
        draw.text((PAD, y + 8), away, fill=TEXT_PRIMARY, font=fonts["matchup"])
        draw.text((PAD, y + 78), "@ " + home, fill=ACCENT_BLUE, font=fonts["matchup"])
    else:
        draw.text((PAD, y + 8), event_label, fill=TEXT_PRIMARY, font=fonts["matchup"])


def _draw_pick_card(draw, PAD: int, y: int, W: int, h: int, pick, fonts) -> None:
    """Hero card containing the pick + odds + confidence badge."""
    rect = (PAD, y, W - PAD, y + h)
    _rounded_rect(draw, rect, radius=20, fill=BG_ELEV, outline=BORDER_BRIGHT, width=2)

    # Top accent bar (thin colored stripe along top edge of card)
    draw.rectangle((PAD + 2, y + 2, W - PAD - 2, y + 8),
                   fill=ACCENT_BLUE)

    inner_x = PAD + 36
    # "THE PICK" small label
    draw.text((inner_x, y + 32), "THE PICK", fill=TEXT_MUTED, font=fonts["label"])

    # Confidence tier badge (top-right of card)
    tier = pick.confidence_tier
    tier_color = _tier_color(tier)
    tier_label = tier.upper()
    bbox = draw.textbbox((0, 0), tier_label, font=fonts["pill"])
    tw = bbox[2] - bbox[0]
    badge_pad_x, badge_pad_y = 16, 8
    badge_x2 = W - PAD - 24
    badge_x1 = badge_x2 - tw - badge_pad_x * 2
    badge_y1 = y + 30
    badge_y2 = badge_y1 + 40
    _rounded_rect(draw, (badge_x1, badge_y1, badge_x2, badge_y2),
                  radius=20, fill=BG_ELEV_2, outline=tier_color, width=2)
    draw.text((badge_x1 + badge_pad_x, badge_y1 + badge_pad_y - 2),
              tier_label, fill=tier_color, font=fonts["pill"])

    # Big pick selection
    draw.text((inner_x, y + 80), pick.selection,
              fill=ACCENT_BLUE, font=fonts["pick_big"])

    # Bottom row: market label + odds
    draw.text((inner_x, y + h - 100), pick.market.upper(),
              fill=TEXT_MUTED, font=fonts["label"])
    odds_text = f"{_format_american(pick.odds_american)}  ·  {pick.sportsbook_source}"
    draw.text((inner_x, y + h - 60), odds_text,
              fill=TEXT_PRIMARY, font=fonts["odds"])


def _draw_edge_bar(draw, PAD: int, y: int, W: int, edge_percent: float, fonts) -> None:
    """Horizontal progress bar showing edge magnitude with gradient fill."""
    label = f"EDGE  +{edge_percent:.2f}%"
    draw.text((PAD, y - 28), label, fill=POS_GREEN, font=fonts["label"])

    bar_x1, bar_x2 = PAD, W - PAD
    bar_y1, bar_y2 = y, y + 20
    bar_w = bar_x2 - bar_x1

    # Track
    _rounded_rect(draw, (bar_x1, bar_y1, bar_x2, bar_y2),
                  radius=10, fill=BG_ELEV)

    # Fill — proportional to edge_percent capped at 10% (our ceiling)
    pct = max(0.0, min(edge_percent / 10.0, 1.0))
    fill_w = int(bar_w * pct)
    if fill_w >= 4:
        # gradient by drawing slim segments from blue → green
        for i in range(fill_w):
            t = i / max(fill_w, 1)
            r = int(ACCENT_BLUE[0] + (POS_GREEN[0] - ACCENT_BLUE[0]) * t)
            g = int(ACCENT_BLUE[1] + (POS_GREEN[1] - ACCENT_BLUE[1]) * t)
            b = int(ACCENT_BLUE[2] + (POS_GREEN[2] - ACCENT_BLUE[2]) * t)
            draw.line([(bar_x1 + i, bar_y1 + 4), (bar_x1 + i, bar_y2 - 4)],
                      fill=(r, g, b))

    # Tick marks (3% threshold, 10% ceiling)
    threshold_x = bar_x1 + int(bar_w * 0.3)
    ceiling_x = bar_x1 + int(bar_w * 1.0)
    for tx in (threshold_x, ceiling_x):
        draw.line([(tx, bar_y1 - 4), (tx, bar_y2 + 4)], fill=TEXT_MUTED, width=1)
    draw.text((threshold_x - 14, bar_y2 + 8), "3%",
              fill=TEXT_MUTED, font=fonts["mini"])
    draw.text((ceiling_x - 22, bar_y2 + 8), "10%",
              fill=TEXT_MUTED, font=fonts["mini"])


def _draw_stats_grid(draw, PAD: int, y: int, W: int, pick, fonts) -> None:
    """2×2 grid: model fair / market implied / kelly / units."""
    cell_w = (W - PAD * 2 - 20) // 2
    cell_h = 110
    gap = 20

    cells = [
        ("MODEL FAIR",
         f"{pick.model_fair_probability * 100:.1f}%",
         TEXT_PRIMARY),
        ("MARKET IMPLIED",
         f"{pick.market_implied_probability * 100:.1f}%",
         TEXT_PRIMARY),
        ("KELLY",
         f"{pick.kelly_fraction * 100:.2f}%",
         TEXT_PRIMARY),
        ("UNITS",
         f"{pick.bet_size_units:.2f}u",
         _tier_color(pick.confidence_tier)),
    ]
    positions = [
        (PAD, y),
        (PAD + cell_w + gap, y),
        (PAD, y + cell_h + gap),
        (PAD + cell_w + gap, y + cell_h + gap),
    ]
    for (cx, cy), (label, value, val_color) in zip(positions, cells):
        rect = (cx, cy, cx + cell_w, cy + cell_h)
        _rounded_rect(draw, rect, radius=12,
                      fill=BG_ELEV, outline=BORDER, width=1)
        draw.text((cx + 22, cy + 18), label, fill=TEXT_MUTED, font=fonts["mini"])
        draw.text((cx + 22, cy + 48), value,
                  fill=val_color, font=fonts["stat_value"])


def _draw_footer(draw, PAD: int, H: int, W: int, fonts) -> None:
    """Footer with sharpsignals.org CTA + compliance line."""
    # Top hairline
    draw.line([(PAD, H - 145), (W - PAD, H - 145)], fill=BORDER, width=1)

    # Big URL
    url = "sharpsignals.org"
    draw.text((PAD, H - 122), url, fill=ACCENT_BLUE, font=fonts["url"])

    # CTA
    cta = "TRACK RECORD →"
    bbox = draw.textbbox((0, 0), cta, font=fonts["pill"])
    cta_w = bbox[2] - bbox[0]
    draw.text((W - PAD - cta_w, H - 110), cta,
              fill=ACCENT_BLUE, font=fonts["pill"])

    # Compliance
    draw.text((PAD, H - 60),
              "18+ · Analytical content, not betting advice · ConnexOntario 1-866-531-2600",
              fill=TEXT_MUTED, font=fonts["footer"])


def _load_fonts() -> dict:
    """Resolve font instances per role.

    Path-based resolution (most reliable):
      1. Inter / JetBrains Mono if user has them installed at known paths
      2. macOS system fonts (Helvetica, SF Pro, Menlo) via absolute path
      3. Pillow's bundled DejaVuSans.ttf (no Bold variant ships, so we use
         BoldOblique as an emergency fallback rather than the bitmap default)

    The bitmap default that ImageFont.load_default() returns is fixed-size
    and looks like a debug printout — never use it for production graphics.
    """
    from PIL import ImageFont

    # Bold sans-serif (headlines, wordmark, pick text)
    BOLD_SANS = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Inter-Bold.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ]
    # Regular sans-serif (body, footer)
    SANS = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Inter-Regular.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
    ]
    # Medium-weight sans (pills, captions)
    MEDIUM_SANS = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/Library/Fonts/Inter-Medium.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    # Mono (numerics, labels)
    MONO_BOLD = [
        "/System/Library/Fonts/Menlo.ttc",  # Bold via index=1
        "/Library/Fonts/JetBrainsMono-Bold.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]
    MONO = [
        "/System/Library/Fonts/Menlo.ttc",  # Regular index=0
        "/Library/Fonts/JetBrainsMono-Regular.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]

    spec = {
        "wordmark":    (BOLD_SANS, 44),
        "pill":        (MEDIUM_SANS, 24),
        "label":       (MONO_BOLD, 22),
        "matchup":     (BOLD_SANS, 56),
        "pick_big":    (BOLD_SANS, 100),
        "odds":        (MONO_BOLD, 40),
        "row_label":   (MEDIUM_SANS, 28),
        "row_value":   (MONO_BOLD, 32),
        "stat_value":  (MONO_BOLD, 44),
        "url":         (BOLD_SANS, 36),
        "mini":        (MONO, 18),
        "footer":      (SANS, 18),
    }
    out: dict = {}
    for role, (paths, size) in spec.items():
        out[role] = _try_paths(paths, size, ImageFont)
    return out


def _try_paths(paths: list, size: int, ImageFont) -> object:
    """Try each path; for .ttc collections also try index 1 (typically Bold)."""
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
        if p.endswith(".ttc"):
            for idx in (1, 2, 3):
                try:
                    return ImageFont.truetype(p, size, index=idx)
                except OSError:
                    pass
    # Last resort: DejaVu BoldOblique ships with matplotlib in the venv
    try:
        return ImageFont.truetype("DejaVuSans-BoldOblique.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _format_american(american: int) -> str:
    return f"+{american}" if american >= 0 else f"{american}"


def _tier_color(tier: str) -> tuple[int, int, int]:
    if tier == "rare":
        return WARN_YELLOW
    if tier == "strong":
        return POS_GREEN
    return TEXT_PRIMARY


def _pill(draw, label: str, top_left: tuple[int, int], font) -> None:
    """Draw a sport tag pill: rounded rect with label inside."""
    pad_x, pad_y = 18, 8
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x, y = top_left
    rect = (x, y, x + text_w + pad_x * 2, y + text_h + pad_y * 2)
    _rounded_rect(draw, rect, radius=(rect[3] - rect[1]) // 2,
                  fill=BG_ELEV, outline=BORDER, width=2)
    draw.text((x + pad_x, y + pad_y - 2), label, fill=ACCENT_BLUE, font=font)


def _rounded_rect(draw, xy, radius, fill, outline=None, width=1) -> None:
    """PIL's rounded_rectangle with a stable signature across versions."""
    try:
        draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
    except AttributeError:
        # Older Pillow — fall back to a plain rectangle.
        draw.rectangle(xy, fill=fill, outline=outline, width=width)
