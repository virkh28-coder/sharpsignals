# Model v0 Specification

## Goal

Produce **positive Closing Line Value (CLV)** consistently across all 5 sports. CLV — not short-term W/L — is what we optimize for. It's the only metric that correlates with long-term profit, and the only honest one for a transparent brand.

## North-star metric: CLV

**Closing Line Value** = difference between the odds we picked at vs. the odds at market close.

Example: We pick Lakers +6 at -110. Market closes Lakers +5 at -110. We got the line 1 point better → positive CLV.

If we consistently beat closing lines, our picks are +EV. If we don't, our model is bad regardless of short-term wins. Published weekly, this stat is our credibility anchor.

## Pick selection criterion

Only publish a pick when our model's fair-odds imply **≥3% edge** over market odds.

```python
fair_probability = model.predict(game)
market_implied = 1 / decimal_odds
edge = fair_probability - market_implied
if edge >= 0.03:
    publish()
```

Edge < 3% = noise. Edge 3–7% = realistic sweet spot. Edge > 10% = probably bad data.

## Bet sizing: Quarter-Kelly, capped

```python
kelly = (fair_prob * decimal_odds - 1) / (decimal_odds - 1)
units = min(kelly * 0.25, 2.0)
```

Quarter-Kelly because full Kelly is too volatile for a public track record. Hard cap at 2u — never use "max unit" / "lock" language.

## v0 models per sport

### NBA — Elo + pace/efficiency adjustments
- Base: Elo (K=20), tuned on historical
- Adjustments: home court (~+100 Elo), rest days, B2B flag, pace (for totals)
- Output: win prob + expected margin → ML, spread, totals
- Priors: last 20% of previous season

### NHL — Elo + xG shrinkage
- Base: Elo on W/L
- Enhancement: shrink recent form to xG differential (MoneyPuck data)
- Goalie adjustment: starter xGA vs league avg
- Output: ML, puck line, totals

### MLB — Pitcher-adjusted win probability
- Base: team run-scoring + run-prevention rates
- Key: starting pitcher FIP/xFIP (dominant signal)
- Bullpen adjustment, park factors (Coors, Fenway, etc.)
- Output: ML, run line, totals

### Soccer — Dixon-Coles Poisson
- Base: attack/defense strengths via Dixon-Coles
- Enhancement: recent xG-for and xG-against (10 matches, exp decay)
- Home advantage: ~0.3 goals (EPL historical baseline; tune per league)
- Output: 1X2, over/under, BTTS
- Initial coverage: EPL; expandable to La Liga, Bundesliga, Serie A, Ligue 1, Champions League

### Cricket — format-specific
- T20: batting impact + bowling impact + venue + DLS-aware
- ODI/Test: heavier weight on recent first-class form
- Key signals: toss outcome + pitch report
- Output: ML for limited-overs; session/innings for Test

## Confidence tiers (display only, not selection)

| Tier     | Edge    | Display            |
| -------- | ------- | ------------------ |
| Standard | 3–5%    | "Model pick"       |
| Strong   | 5–8%    | "Higher-conviction"|
| Rare     | 8%+     | "Premium signal"   |

Never: "lock", "guaranteed", "sure thing", "insider", "fixed".

## What gets logged per pick (before publishing)

```json
{
  "pick_id": "2026-04-24-NBA-LAL-GSW-ML-LAL",
  "timestamp_utc": "2026-04-24T18:45:00Z",
  "sport": "NBA",
  "event": "Lakers vs Warriors",
  "market": "moneyline",
  "selection": "Lakers",
  "odds_american": -115,
  "odds_decimal": 1.87,
  "sportsbook_source": "DraftKings",
  "model_fair_odds_decimal": 1.72,
  "model_fair_probability": 0.581,
  "market_implied_probability": 0.535,
  "edge_percent": 4.6,
  "kelly_fraction": 0.0425,
  "bet_size_units": 1.0,
  "confidence_tier": "standard",
  "result": null,
  "closing_odds_american": null,
  "clv_percent": null
}
```

After the game: `result`, `closing_odds_*`, `clv_percent` are filled in and the public log updates.

## Pipeline

```
cron (daily 9am ET)
  → scrapers/<sport>.py     (games + odds)
  → models/<sport>.py       (predictions)
  → agents/pick_agent       (filter edge≥3%, Kelly-size)
  → agents/track_record     (log + push to public Google Sheet)
  → agents/content_agent    (Claude API → caption + graphic)
  → compliance_check        (disclaimer, language audit)
  → agents/scheduler_agent  (IG + Telegram post)

cron (daily 10am next day)
  → after_result_hook       (fill result + CLV)
```

## Backtesting gate

Before ANY picks go live publicly:
1. Run each sport's model on 2 full prior seasons
2. Verify: hit rate > 52.4% (break-even at -110) **AND** avg CLV > 0
3. CLV positive + hit rate below break-even → still ship (variance acceptable)
4. CLV negative → **do not ship** — iterate model first

## v1 roadmap (post-launch)

- Replace Elo with gradient-boosted trees (xgboost) where data supports it
- Live/in-play models for top leagues
- Player prop models (NBA + NFL v2 addition)
- Ensemble methods combining multiple sub-models per sport
