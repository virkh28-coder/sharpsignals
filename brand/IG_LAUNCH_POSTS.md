# Instagram launch sequence — first 7 posts

These get manually posted in order, ~1 per day. Goal: by post 7, the brand voice and methodology are established, and the algorithmic pick automation can take over without anyone wondering "wait, who is this account?"

Every caption below is **already compliance-checked** — banned words avoided, 18+ + ConnexOntario lines included. Copy-paste straight to IG.

---

## Post 1 — Intro / why this account exists

**Image**: Plain branded card. Background `#0D1117`, headline in Inter Bold `#79C0FF`:
> Every pick logged.
> Every loss shown.

Subline (smaller, `#8B949E`): `algorithmic sports analytics — sharpsignals.org`

**Caption**:

```
SharpSignals.

An algorithm — not a guru — produces our picks across NBA, NHL, MLB, EPL, and cricket. Every pick lands in a public Google Sheet at the same time it goes here. Wins and losses go in the same column.

The metric we actually care about is Closing Line Value. If our picks consistently get a better number than the market closes at, we're sharp. If they don't, we don't deserve your follow — and the public sheet will show that.

What this account will never do:
— Lock you into a "VIP" paywall for picks
— Use words like "guaranteed", "lock", "fixed", or "inside info"
— Hide losses or quietly delete bad picks
— Sell you a $300/week subscription

What it will do:
— Drop 1–3 model picks per day across 5 sports, openly
— Show the math behind each one: edge %, model fair odds, units
— Publish weekly transparency reports

Track record link in bio.

📊 Methodology over hype.

—
18+ · Analytical content, not betting advice · ConnexOntario 1-866-531-2600
```

---

## Post 2 — What is Closing Line Value?

**Image**: Carousel, 3 slides, all `#0D1117` background.
- **Slide 1 (title)**: "What is Closing Line Value?" — Inter Bold, `#E6EDF3`
- **Slide 2 (definition)**: Mono text:
  ```
  CLV = (your_odds / closing_odds) - 1

  Bet at +130
  Closes at +110
  CLV = +9.5%
  ```
  Side note in `#8B949E`: "You got a better number than the market did."
- **Slide 3 (why it matters)**: "Why we publish CLV instead of W/L" — bullets:
  - W/L is variance over short samples
  - CLV correlates with long-term profit
  - You can't fake CLV — it's what books actually closed at

**Caption**:

```
Closing Line Value (CLV) is the only metric that actually correlates with long-term betting profit.

Most accounts post W/L records. The problem: a 5-3 record this week tells you nothing — it could be lucky, unlucky, or noise. CLV is the closing odds versus the odds we got.

If we picked Lakers +6 at -110 and the line closes at Lakers +4.5 at -110, our pick beat the close by 1.5 points. That's positive CLV. Over a thousand picks, accounts with positive average CLV make money. Accounts with negative average CLV don't, no matter how often they post green wins.

Every pick we publish is timestamped before tip-off. Every closing line gets logged the next morning. Math is shown.

—
18+ · Analytical content, not betting advice · ConnexOntario 1-866-531-2600
```

---

## Post 3 — Why we only pick when edge ≥ 3%

**Image**: Single card. Centered headline (large, `#79C0FF`):
> Most days,
> 0–2 picks total.

Subhead (`#8B949E`): "If the edge isn't ≥ 3%, the pick doesn't ship."

**Caption**:

```
Most days, this account will post 0–2 picks. Some days, zero.

Why: the model only emits a pick when its fair probability beats the market's implied probability by at least 3 percentage points. Below that threshold, the "edge" is indistinguishable from noise — and we'd rather post nothing than fake conviction on a coin flip.

Accounts that post 8 picks every day aren't running models. They're filling content slots and hoping enough hit to look smart in screenshots.

We'd rather have credibility for 30 quiet days than a viral hot streak we can't repeat.

—
18+ · Analytical content, not betting advice · ConnexOntario 1-866-531-2600
```

---

## Post 4 — Bankroll & Kelly (educational)

**Image**: Carousel, 3 slides.
- **Slide 1**: "Bet sizing isn't a feeling." — large `#E6EDF3` headline.
- **Slide 2 (formula)**:
  ```
  Kelly fraction =
  (fair_prob × odds - 1) / (odds - 1)

  We bet quarter-Kelly.
  Capped at 2 units.
  ```
- **Slide 3 (why)**: "Full Kelly is theoretically optimal — and impossibly volatile in real life. Quarter-Kelly cuts variance by 75% with ~70% of the long-run growth. The 2u cap exists because models are wrong sometimes and we'd rather not learn that lesson on a 4u play."

**Caption**:

```
Bet sizing isn't a feeling.

Every pick we post comes with a unit size — and that size isn't an emotion. It's a quarter-Kelly fraction of bankroll, hard-capped at 2 units.

Why quarter-Kelly: full Kelly is mathematically optimal in theory, but in real markets where your "true" probability is itself uncertain, full Kelly gets brutalized by variance. Quarter-Kelly keeps ~70% of the long-run growth at ~25% of the volatility. That trade is worth it for anyone who plans to bet for more than a quarter.

Why the 2u cap: even when the model says "huge edge", the model can be wrong. The cap exists so a single bad pick doesn't damage a serious bankroll.

You'll never see "max play" or "lock of the day" copy on this account. Those are the words of accounts hoping you don't ask about variance.

—
18+ · Analytical content, not betting advice · ConnexOntario 1-866-531-2600
```

---

## Post 5 — Why a 52% win rate can still lose money

**Image**: Single card. Big number `52.4%` in `#79C0FF`, label "the break-even rate at -110" beneath in `#8B949E`. Then table:
```
HIT RATE   WIN/LOSS @ -110
50.0%      LOSING
52.4%      BREAK EVEN
55.0%      PROFITABLE
60.0%      ELITE
```

**Caption**:

```
Hit rate doesn't tell you what most accounts pretend it does.

At standard -110 vig, you need to win 52.4% of your bets just to break even. So a "55% win rate" that sounds amazing in a screenshot is barely above water once you account for the juice.

This is why we publish CLV instead of bragging about W/L: a 53% hitter with strong CLV is profitable; a 53% hitter with negative CLV is bleeding slowly.

Anyone selling you "60% sustained ATS hit rate" doesn't have a track record long enough to make that claim, or is using selective windows. Real edges in mature markets are 2–5 percentage points above break-even on the bets that qualify — and most days, no bet qualifies.

—
18+ · Analytical content, not betting advice · ConnexOntario 1-866-531-2600
```

---

## Post 6 — How a pick gets made (methodology walkthrough)

**Image**: Carousel, 5 slides — match the steps in `web/index.html` "Methodology" section.
- Slide 1: "How one pick is made" — title
- Slide 2: "01 · Scrape today's games + market odds across multiple books"
- Slide 3: "02 · Run the sport's model. NBA: Elo + rest + pace."
- Slide 4: "03 · Filter by edge ≥ 3%. Most predictions don't qualify."
- Slide 5: "04 · Quarter-Kelly sizing, 2u cap. Log first, post second."

**Caption**:

```
The full pipeline behind every pick this account posts:

1. Pull today's slate of games + live odds from The Odds API (covers DraftKings, FanDuel, bet365, etc.) — multiple books so we can shop the best price.

2. Run the sport's model. For NBA, that's an Elo rating system with adjustments for: home court (~+100 Elo), rest day differential (±15 Elo per day), back-to-back penalty (-25), and pace for totals.

3. Compare model fair probability to market implied probability. If edge ≥ 3%, it qualifies.

4. Quarter-Kelly bet sizing, capped at 2 units. Confidence tier assigned: standard (3–5%), strong (5–8%), or rare (8%+).

5. The pick lands in the public sheet — with timestamp, odds, edge, units — BEFORE it gets posted here. Sheet timestamp is the proof.

The model's not magic. It's transparent math. The edge isn't huge — most days, no game qualifies — and that's the point.

—
18+ · Analytical content, not betting advice · ConnexOntario 1-866-531-2600
```

---

## Post 7 — The scamdicapper playbook (what we won't do)

**Image**: Single card. Headline in `#F85149`:
> The 6 things this account
> will never do.

Below, six lines, each with a red ✕:
- ✕ Charge $300/week for "VIP locks"
- ✕ Hide or delete losing picks
- ✕ Post fake DM screenshots
- ✕ Use "guaranteed" / "fixed" / "lock"
- ✕ Sell locked picks behind a paywall
- ✕ Promote unlicensed sportsbooks

**Caption**:

```
A field guide to the scamdicapper playbook — and a list of things this account refuses to do.

What you'll see from most "betting expert" accounts:
- "VIP" channels at $300/week with "guaranteed locks"
- Cherry-picked screenshots of wins; losses quietly deleted
- Fake DM screenshots of customers thanking them
- Comparisons of "today's lock" priced like financial advice
- Affiliate links to whatever sportsbook pays the most, regardless of whether it's licensed

What this account does instead:
- Public Google Sheet of every pick — wins AND losses, no edits
- One pricing tier ever, no "VIP locks"
- Timestamps that prove picks were posted before games started
- Affiliate links only to AGCO-licensed sportsbooks (Ontario's regulated operators)
- Plain math: model probability, market probability, edge percent, units

Trust the receipts, not the screenshots.

Track record in bio.

—
18+ · Analytical content, not betting advice · ConnexOntario 1-866-531-2600
```

---

## Posting cadence

| Day | Post | Why this slot |
| --- | ---- | ------------- |
| Mon | 1 — Intro | Sets the brand on the most visible day |
| Tue | 2 — CLV explainer | Educational hook for the new audience |
| Wed | 3 — Edge ≥ 3% rule | Manages expectations on volume |
| Thu | 4 — Bankroll / Kelly | Ties the math to bettor practice |
| Fri | 5 — 52% break-even | High-engagement / shareable |
| Sat | 6 — Methodology walkthrough | Saturday browsing, longer carousel |
| Sun | 7 — Scamdicapper playbook | Strongest positioning piece |

After post 7, the algorithmic pipeline can ship daily picks without the audience wondering who you are.

## Hashtag strategy

Append the same 5–7 tags to each post (don't over-tag — IG penalizes spam-tagging):

```
#sportsbetting #sportsanalytics #betting #nba #closinglinevalue #bettingtwitter #algorithmictrading
```

Swap in `#nhl`, `#mlb`, `#epl`, `#ipl` when the relevant sport is featured.
