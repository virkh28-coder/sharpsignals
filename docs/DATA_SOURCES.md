# Data Source Audit

## Summary

All 5 sports covered with **~$100–160/mo combined** (~$1,200–1,920/year), fitting the <$2K budget.

| Sport   | Stats (free)                          | Odds          | Monthly cost |
| ------- | ------------------------------------- | ------------- | ------------ |
| NBA     | stats.nba.com (via `nba_api`)         | The Odds API  | $0 + shared  |
| NHL     | api-web.nhle.com + MoneyPuck          | The Odds API  | $0 + shared  |
| MLB     | statsapi.mlb.com + pybaseball         | The Odds API  | $0 + shared  |
| Soccer  | football-data.org + Understat (xG)    | The Odds API  | $0 + shared  |
| Cricket | Sportmonks / CricketData + Cricinfo   | The Odds API  | $20–40       |

Shared: **The Odds API $30/mo** + **Claude API $50–100/mo**.

---

## NBA

**Stats: `nba_api` wrapper around stats.nba.com**
- Install: `pip install nba_api`
- Cost: free, no key
- Rate limit: ~1 req/sec — set User-Agent header
- Coverage: box scores, advanced (pace, ORtg, DRtg), lineups, injuries

**Odds: The Odds API** — https://the-odds-api.com
- Free tier: 500 req/mo · Paid: $30/mo for 20K reqs
- Coverage: ML, spreads, totals, props from 30+ books (DK, FD, bet365)

Season: Oct–Apr, ~10 games/day.

---

## NHL

**Stats: api-web.nhle.com (official, free, no key)**
- `https://api-web.nhle.com/v1/`
- Coverage: schedule, standings, stats, play-by-play
- Reference: https://github.com/Zmalski/NHL-API-Reference

**Enhancement: MoneyPuck** — https://moneypuck.com
- Free CSV downloads daily
- Expected goals, Corsi, Fenwick

Season: Oct–Apr, ~8–12 games/day.

---

## MLB

**Stats: statsapi.mlb.com (official, free, no key)**
- `https://statsapi.mlb.com/api/v1/`
- Python wrapper: `pip install MLB-StatsAPI`
- Coverage: schedule, starting pitchers, live state, full history

**Enhancement: pybaseball** (FanGraphs + Statcast)
- `pip install pybaseball`
- Coverage: wOBA, FIP, park factors, pitch-level Statcast

Season: Apr–Oct, ~15 games/day = massive content volume.

---

## Soccer (EPL + top European leagues)

**Stats: football-data.org**
- `https://api.football-data.org/v4/`
- Free tier: 10 req/min, covers EPL + top 5 + Champions League
- Paid: €12/mo if we scale

**Enhancement: Understat** (xG)
- https://understat.com
- `pip install understat`
- Coverage: EPL, La Liga, Bundesliga, Serie A, Ligue 1 with shot maps

Season: Aug–May, ~10 matches per gameweek.

---

## Cricket

Hardest free-data sport. Biggest underserved market (India).

**Option A: Sportmonks Cricket** — https://www.sportmonks.com/cricket-api/
- Paid plans from $19/mo
- Coverage: IPL, international, BBL, PSL, CPL, county, ball-by-ball

**Option B: CricketData.org**
- Free tier, paid ~$10/mo
- Coverage: schedules, scorecards, player stats

**Enhancement: ESPNCricinfo** (scrape Statsguru respectfully)
- Historical back to 1800s
- TOS-ambiguous — rate limit + no bulk downloads

**Odds for cricket**: The Odds API covers IPL, T20 WC, Ashes. Smaller tournaments may need Betfair Exchange API (UK/EU account + £0.70 one-time key).

Season: IPL Mar–May (highest betting volume globally), international year-round — **no off-season**.

---

## Claude API (content generation)

- https://www.anthropic.com/api
- Claude Sonnet 4.6 pricing: ~$3/M input tokens, ~$15/M output
- Est. volume: 5 picks/day × 5 sports × 30 days ≈ 750 picks/mo × ~2K tokens ≈ $40–60/mo
- Plus newsletter long-form ~$30/mo
- **Total: $50–100/mo**

---

## Monthly data stack total

| Service             | $/mo         |
| ------------------- | ------------ |
| The Odds API        | $30          |
| Sportmonks Cricket  | $19–29       |
| Claude API          | $50–100      |
| **Total**           | **$100–160** |

Annual: **$1,200–1,920** — leaves room for domain (~$12/yr) + VPS (~$60–120/yr) + buffer.

---

## Build order

1. **NBA** — cleanest API, high game volume, best US affiliate economics
2. **MLB** — similar free data, high game volume during summer
3. **NHL** — official API, manageable
4. **Soccer** — xG enrichment adds complexity (start with EPL)
5. **Cricket** — most complex stack, save for last (and it's IPL-ready for March launch)
