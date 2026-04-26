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
BORDER = (48, 54, 61)
TEXT_PRIMARY = (230, 237, 243)
TEXT_MUTED = (139, 148, 158)
ACCENT_BLUE = (121, 192, 255)
POS_GREEN = (86, 211, 100)
WARN_YELLOW = (227, 179, 65)


def _render_graphic(pick: Pick, output_dir: Path) -> Optional[Path]:
    """Render a 1080×1350 branded bet-slip graphic via PIL.

    Layout (top → bottom, see brand/IDENTITY.md):
      1. Header — wordmark + sport pill (right-aligned)
      2. Matchup — large
      3. The pick — selection + market in accent-blue, odds in mono
      4. Edge breakdown table
      5. Footer — compliance copy
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow not installed — skipping graphic")
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{pick.pick_id}.png"

    W, H = 1080, 1350
    PAD = 72

    img = Image.new("RGB", (W, H), color=BG_DEEP)
    draw = ImageDraw.Draw(img)

    fonts = _load_fonts()

    # ---- Header ----
    draw.text((PAD, PAD), "SHARPSIGNALS", fill=ACCENT_BLUE, font=fonts["wordmark"])
    _pill(draw, pick.sport, (W - PAD - 220, PAD - 4), fonts["pill"])

    # Hairline under header
    draw.line([(PAD, PAD + 90), (W - PAD, PAD + 90)], fill=BORDER, width=2)

    # ---- Matchup ----
    matchup_y = PAD + 130
    draw.text((PAD, matchup_y), "MATCHUP", fill=TEXT_MUTED, font=fonts["label"])
    draw.text(
        (PAD, matchup_y + 38),
        pick.event_label,
        fill=TEXT_PRIMARY,
        font=fonts["matchup"],
    )

    # ---- The Pick (raised card) ----
    card_y = matchup_y + 170
    card = (PAD, card_y, W - PAD, card_y + 320)
    _rounded_rect(draw, card, radius=18, fill=BG_ELEV, outline=BORDER, width=2)

    inner_x = PAD + 36
    draw.text((inner_x, card_y + 28), "THE PICK", fill=TEXT_MUTED, font=fonts["label"])
    draw.text(
        (inner_x, card_y + 70),
        pick.selection,
        fill=ACCENT_BLUE,
        font=fonts["pick_big"],
    )
    draw.text(
        (inner_x, card_y + 160),
        pick.market.upper(),
        fill=TEXT_MUTED,
        font=fonts["label"],
    )

    odds_text = f"{_format_american(pick.odds_american)}  @  {pick.sportsbook_source}"
    draw.text(
        (inner_x, card_y + 215),
        odds_text,
        fill=TEXT_PRIMARY,
        font=fonts["odds"],
    )

    # ---- Edge breakdown ----
    table_y = card_y + 360
    rows = [
        ("Model fair %", f"{pick.model_fair_probability * 100:.1f}%", TEXT_PRIMARY),
        ("Market implied %", f"{pick.market_implied_probability * 100:.1f}%", TEXT_PRIMARY),
        ("Edge", f"+{pick.edge_percent:.2f}%", POS_GREEN),
        ("Units", f"{pick.bet_size_units:.2f}u  ({pick.confidence_tier})", _tier_color(pick.confidence_tier)),
    ]
    for i, (label, value, value_color) in enumerate(rows):
        row_y = table_y + i * 70
        draw.text((PAD, row_y), label, fill=TEXT_MUTED, font=fonts["row_label"])
        # Right-align values
        bbox = draw.textbbox((0, 0), value, font=fonts["row_value"])
        value_w = bbox[2] - bbox[0]
        draw.text((W - PAD - value_w, row_y), value, fill=value_color, font=fonts["row_value"])
        if i < len(rows) - 1:
            sep_y = row_y + 56
            draw.line([(PAD, sep_y), (W - PAD, sep_y)], fill=BORDER, width=1)

    # ---- Footer ----
    draw.line([(PAD, H - 150), (W - PAD, H - 150)], fill=BORDER, width=2)
    draw.text(
        (PAD, H - 120),
        "18+ · Analytical content, not betting advice",
        fill=TEXT_MUTED,
        font=fonts["footer"],
    )
    draw.text(
        (PAD, H - 80),
        "ConnexOntario 1-866-531-2600 · sharpsignals.org",
        fill=TEXT_MUTED,
        font=fonts["footer"],
    )

    img.save(path, "PNG", optimize=True)
    return path


def _load_fonts() -> dict:
    """Try Inter + JetBrains Mono if installed; gracefully fall back to DejaVu.

    On a fresh system, only DejaVu (Pillow's default) is guaranteed. Anyone
    deploying this should install Inter + JetBrains Mono via fonts.google.com
    or the OS package manager for the intended look.
    """
    from PIL import ImageFont

    candidates = {
        "wordmark":  [("Inter-Bold.ttf", 56), ("DejaVuSans-Bold.ttf", 56)],
        "pill":      [("Inter-Medium.ttf", 28), ("DejaVuSans-Bold.ttf", 28)],
        "label":     [("JetBrainsMono-Medium.ttf", 24), ("DejaVuSansMono-Bold.ttf", 24)],
        "matchup":   [("Inter-Bold.ttf", 64), ("DejaVuSans-Bold.ttf", 64)],
        "pick_big":  [("Inter-Bold.ttf", 76), ("DejaVuSans-Bold.ttf", 76)],
        "odds":      [("JetBrainsMono-Medium.ttf", 44), ("DejaVuSansMono-Bold.ttf", 44)],
        "row_label": [("Inter-Medium.ttf", 32), ("DejaVuSans.ttf", 32)],
        "row_value": [("JetBrainsMono-Medium.ttf", 36), ("DejaVuSansMono-Bold.ttf", 36)],
        "footer":    [("Inter-Medium.ttf", 22), ("DejaVuSans.ttf", 22)],
    }
    out: dict = {}
    for role, options in candidates.items():
        font = None
        for name, size in options:
            try:
                font = ImageFont.truetype(name, size)
                break
            except OSError:
                continue
        out[role] = font or ImageFont.load_default()
    return out


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
