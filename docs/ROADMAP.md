# SharpSignals — 30 / 60 / 90 Day Roadmap

## Day 0 (today) — you handle

- [ ] Verify `sharpsignals.com` (or `.bet` / `.co`) + `@sharpsignals` on IG/TG/TikTok are available
- [ ] Register domain (~$12/year on Porkbun)
- [ ] Create IG Business account, Telegram channel, TikTok, X/Twitter — all `@sharpsignals` (or nearest available)
- [ ] Create Meta Developer App (free) → generate access tokens for IG Graph API
- [ ] Create Anthropic API account → save key to `.env`
- [ ] Create The Odds API account → save key to `.env`
- [ ] Create public Google Sheet titled "SharpSignals — Public Pick Log" → share as view-only link

---

## Week 1 (Days 1–7) — Claude Code handles

**Goal: NBA scraper + Elo model + one manual end-to-end pick posted to IG.**

- [ ] `src/scrapers/nba.py` — pulls today's games + odds from nba_api + The Odds API
- [ ] `src/models/elo.py` — Elo base class
- [ ] `src/models/nba_model.py` — NBA-specific Elo with pace/home adjustments
- [ ] `src/utils/odds_math.py` — american↔decimal↔implied, Kelly, CLV
- [ ] Backtest NBA model on 2023–24 and 2024–25 seasons → verify CLV > 0
- [ ] `agents/pick_agent/pick_generator.py` — runs model, filters edge≥3%, sizes bets
- [ ] `agents/track_record_agent/pick_logger.py` — writes to data/picks_log + pushes to Google Sheet
- [ ] `agents/content_agent/post_generator.py` — Claude API → caption + bet-slip graphic (PIL)
- [ ] `agents/scheduler_agent/ig_scheduler.py` — post via Meta Graph API
- [ ] **Manually review + post first 3 picks before any automation goes live**

---

## Week 2 — scale to 3 sports

- [ ] Add MLB scraper + model
- [ ] Add NHL scraper + model
- [ ] Publish daily across NBA + MLB + NHL (2–4 picks/day total)
- [ ] Reach out to 3 AGCO-licensed sportsbooks for affiliate programs (DraftKings Ontario, FanDuel Ontario, bet365)
- [ ] Start engaging in r/sportsbook, r/SportsBettingAnalytics organically (no self-promotion yet)

---

## Week 3 — add Soccer + start newsletter

- [ ] Add Soccer scraper + Dixon-Coles model (EPL focus initially, expandable to top 5 leagues)
- [ ] Set up Substack at `sharpsignals.substack.com`
- [ ] First newsletter: "What We Learned From Week 1 of Public Picks" (CLV breakdown)
- [ ] Free tier: weekly recap. Paid tier ($19/mo): deeper weekly methodology + unit-level breakdowns
- [ ] Affiliate integrations live (links tracked per platform)

---

## Week 4 — add cricket + launch push

- [ ] Add cricket scraper + T20 model (IPL-ready)
- [ ] First month transparency report: public total units won/lost, blended CLV, win rate per sport
- [ ] Launch paid Substack ($19/mo)
- [ ] First paid-ad test: $50 on Meta targeting sports betting readers of legit publications (The Action Network, Covers) — Ontario-only audience, AGCO-compliant landing

---

## Month 2 — optimize, don't add

- Goal: one full month of daily picks across all 5 sports
- Iterate models based on first-month CLV data
- Post weekly transparency report on IG (track-record screenshots)
- Grow IG to 2K–5K organic (realistic with daily value content)
- Aim: 50 newsletter subs at $19/mo = $950/mo MRR floor

---

## Month 3 — expand content types

- Add short-form video (Reels/TikTok/Shorts): model explainers, "why we didn't pick this game", CLV deep-dives
- Add YouTube: weekly 15-min recap with visualizations
- Podcast feed (even just audio of YouTube) via Transistor/Buzzsprout
- Goal: 200 paid subs = $3,800 MRR + ~10 NGC affiliate conversions/mo (~$2,500) = $6K+/mo run rate

---

## Month 4–6 targets

- 500–1,000 paid subs ($9,500–$19,000 MRR)
- 50+ NGC affiliate conversions/month ($10K–25K/mo)
- $20K–40K MRR blended = legitimate long-term brand trajectory

---

## What "done" looks like by Day 90

A daily-updating feed across 5 sports, a public Google Sheet track record with >500 picks logged, a paid newsletter with ~200 subs, 3+ sportsbook affiliate partnerships, all on a budget under $1,500 total first-quarter spend.
