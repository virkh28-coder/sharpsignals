# SharpSignals — Visual & Voice Identity

Single source of truth. Landing page, bet-slip graphics, IG profile, future Reels — all reference these tokens.

## Positioning (one line)

> An algorithm shows its work. Every pick logged publicly — wins and losses.

## Voice

- **Confident, not cocky.** "Model gives Lakers 58.1% — implied market 53.5%. We bet at +4.6% edge." Never "this one's a banger".
- **Honest about uncertainty.** "Models produce probabilities, not predictions." Always frame outcomes as distributions.
- **No hype emojis.** Max one tasteful emoji per post. 📊 acceptable. 🔥💸💯 forbidden.
- **Educational by default.** Every post should leave the reader smarter about betting math, not more excited about a parlay.

## Color tokens

| Token         | Hex       | RGB             | Usage                                    |
| ------------- | --------- | --------------- | ---------------------------------------- |
| `bg-deep`     | `#0D1117` | (13, 17, 23)    | Page/graphic background (GitHub-dark)    |
| `bg-elev`     | `#161B22` | (22, 27, 34)    | Cards, panels, raised surfaces           |
| `border`      | `#30363D` | (48, 54, 61)    | Hairlines, dividers                      |
| `text-primary`| `#E6EDF3` | (230, 237, 243) | Headlines, body                          |
| `text-muted`  | `#8B949E` | (139, 148, 158) | Captions, secondary labels               |
| `accent-blue` | `#79C0FF` | (121, 192, 255) | Brand primary — wordmark, links, numbers |
| `accent-cyan` | `#56D4DD` | ( 86, 212, 221) | Hover, highlight                         |
| `pos-green`   | `#56D364` | ( 86, 211, 100) | Positive edge, wins, +CLV                |
| `neg-red`     | `#F85149` | (248,  81,  73) | Losses, –CLV, alert                      |
| `warn-yellow` | `#E3B341` | (227, 179,  65) | Holds, push, review queue                |

The palette intentionally borrows GitHub's dark theme — it's instantly readable to the technical bettor segment we want and signals "data tool", not "VIP tipster".

## Typography

| Role     | Font (web)                | Fallback                       | Notes                                |
| -------- | ------------------------- | ------------------------------ | ------------------------------------ |
| Display  | `Inter` 700               | system-ui, -apple-system       | Wordmark, hero headline              |
| Body     | `Inter` 400/500           | system-ui, -apple-system       | Most copy                            |
| Mono     | `JetBrains Mono` 500      | ui-monospace, SF Mono, Menlo   | Odds, percentages, numerics, code    |

Numbers always in mono — odds and percentages stay column-aligned and feel quantitative.

## Logo / wordmark

v0 is wordmark-only: `SHARPSIGNALS` in Inter 700, all caps, letter-spacing 0.05em, in `accent-blue` over `bg-deep`. No icon yet. Adding an icon before there's a real brand to put it on is premature.

Optional future mark: a stylized line chart suggesting a "sharper" angle than market consensus — but not before month 2 when we have track record screenshots that benefit from one.

## Image assets we generate

### Bet-slip graphic (1080×1350, IG portrait)

Single template, four sections top-to-bottom:
1. **Header** — wordmark + sport tag pill (right-aligned)
2. **Matchup** — `Away @ Home`, large, center
3. **The pick** — selection + market in `accent-blue`, odds in mono
4. **Edge breakdown** — model fair %, market implied %, edge %, units (mono table)
5. **Footer** — 18+ · Analytical content · ConnexOntario 1-866-531-2600

### Carousel template (Stories, multi-slide)

For "weekly transparency report" posts:
- Slide 1 — Title + week number + units record
- Slides 2..N — One pick per slide with result + CLV
- Final slide — Cumulative CLV + sample size disclaimer

## What we never do (visual)

- ❌ Bright green/red flashing "BIG WIN" / "LOCK" badges
- ❌ Stock photos of money / cars / yachts
- ❌ Fake screenshots of payouts or DM testimonials
- ❌ Comparison images vs. competitor accounts
- ❌ Faces of athletes used commercially (rights issue)
- ❌ Mascots, gambling iconography (dice, cards, chips)

## IG bio (initial)

```
SharpSignals · Algorithmic sports analytics
Every pick logged. Every loss shown.
NBA · NHL · MLB · Soccer · Cricket
sharpsignals.org · 18+ · ConnexOntario
```

Link in bio → `sharpsignals.org` → has Telegram, public track record sheet, newsletter signup.

## File-naming for assets we ship to public CDN

```
assets/
  picks/         # bet-slip pngs, named {pick_id}.png
  reports/       # weekly/monthly transparency carousels, named YYYY-MM-DD-report-N.png
  social/        # static social profile assets (avatars, OG image)
```

The `picks/` dir is what `GRAPHIC_PUBLIC_BASE_URL` points to so Meta's IG Graph API can fetch images by URL.
