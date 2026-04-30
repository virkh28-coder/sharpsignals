# CLAUDE.md — Project Context

## What this business is

A **transparent, algorithm-driven sports analytics brand** covering NBA, NHL, MLB, soccer, and cricket.

**It is explicitly NOT:**
- A tipster account pretending to be a human expert
- A VIP picks funnel with hidden track record
- A scraped/cloned copy of another account
- Selling "guaranteed" or "locked" picks at scam-tier pricing ($300/week etc.)

## Core positioning

> "An algorithm shows its work. Every pick logged publicly — wins and losses. No fake experts, no hidden results."

Transparency is the **moat**. Every competitor in this niche hides losses. We don't. That's defensible long-term.

## Revenue model

1. **Primary: Sportsbook affiliate** — $150–500 per NGC (new gambling customer) via AGCO-licensed operators (DraftKings Ontario, FanDuel Ontario, bet365 Ontario, PROLINE+)
2. **Secondary: Paid newsletter** at $19–29/mo on Substack/Ghost — sells **analysis, methodology, education**, NOT locked picks (critical legal distinction)
3. **Future: Data/API licensing** to other creators

## Sports covered (v1)

| Sport   | Data source                            | Model approach                    |
| ------- | -------------------------------------- | --------------------------------- |
| NBA     | nba_api + The Odds API                 | Elo + pace/efficiency             |
| NHL     | api-web.nhle.com + MoneyPuck           | Elo + expected goals              |
| MLB     | statsapi.mlb.com + pybaseball          | Pitcher-adjusted win probability  |
| Soccer  | football-data.org + Understat (xG)     | Poisson goals model (EPL focus)   |
| Cricket | Sportmonks or CricketData + Cricinfo   | Format-specific (T20 / ODI / Test)|

## Model philosophy (v0)

**North-star metric: Closing Line Value (CLV)**, not short-term W/L. If we consistently beat closing lines, we're +EV regardless of variance.

Every pick published with:
- Timestamp (IG post time = timestamp proof)
- Odds at time of pick
- Our fair-odds estimate
- Expected value %
- Bet size in units (Kelly-based, capped at 2u)

## Folder map

- `agents/` — autonomous pipeline modules (pick, content, scheduler, track record)
- `src/scrapers/` — one file per sport
- `src/models/` — Elo base + sport-specific
- `src/utils/` — odds math, Kelly, CLV calc
- `src/content/` — caption + graphic generators
- `data/picks_log/` — PUBLIC track record (every pick, wins + losses)
- `compliance/` — Ontario-specific legal
- `docs/` — roadmap, calendar, architecture, budget
- `brand/` — name, voice, visual identity

## Hard constraints

- Total first-year spend **<$2,000** (see `docs/BUDGET.md`)
- All public posts carry **18+** + **ConnexOntario 1-866-531-2600** disclaimers
- No "guaranteed" / "lock" / "fixed" / "sure thing" / "inside info" language ever
- Affiliate links ONLY to AGCO-licensed sportsbooks for Ontario-facing content
- Track record is PUBLIC — every loss shown
- No locked "VIP" picks behind a paywall (subscription sells analysis/education)

## Claude Code build order (v0 MVP)

1. Pick brand name → register domain + IG + Telegram + TikTok handles
2. Build NBA scraper (`src/scrapers/nba.py`) — cleanest data to start
3. Build Elo model (`src/models/elo.py`)
4. Build pick_agent → pick_logger → public Google Sheet
5. Build content_agent using Claude API (Sonnet 4.6) for captions
6. Build graphic generator (PIL → branded bet-slip image)
7. Build scheduler_agent for IG via Meta Graph API
8. Replicate 2–6 for MLB → NHL → Soccer → cricket
9. Launch Substack newsletter
10. Apply to sportsbook affiliate programs

See `docs/ROADMAP.md` for full timeline.

## Compliance check before any post goes live

```
[ ] 18+ disclaimer present
[ ] ConnexOntario helpline visible
[ ] No guaranteed/lock/fixed language
[ ] Odds at time of pick recorded
[ ] Fair-odds estimate recorded
[ ] Pick entered in public log BEFORE posting
[ ] Kelly sizing capped at 2u
[ ] Affiliate link (if any) is AGCO-licensed operator
```

## When extending this project

Before adding new sport/source/monetization, check:
1. Does it break transparency principle? (Reject.)
2. Does it require a license we don't have? (Reject or acquire.)
3. Ontario AGCO compliant? (Verify.)
4. Fits <$2K first-year budget? (Verify.)
