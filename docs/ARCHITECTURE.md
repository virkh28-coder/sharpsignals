# Architecture

## Stack

- **Language**: Python 3.11+
- **Storage**: SQLite for MVP (scales to 100K+ picks easily), Postgres later
- **Scheduling**: `cron` on VPS OR GitHub Actions (free tier, 2000 min/mo)
- **Content gen**: Anthropic Claude API (Sonnet 4.6)
- **Image gen**: PIL (Pillow) with custom bet-slip template
- **Publishing**:
  - Instagram: Meta Graph API (requires IG Business account linked to FB Page)
  - Telegram: Bot API (free, no approval needed)
  - Newsletter: Substack API or manual paste
- **Track record**: Google Sheets API (public view-only sheet for social proof)

## Data flow

```
┌──────────────┐      ┌──────────────┐
│  Scrapers    │─────▶│  data/raw/   │
│  (per sport) │      └──────┬───────┘
└──────────────┘             │
                             ▼
                      ┌──────────────┐
                      │   Models     │
                      │  (per sport) │
                      └──────┬───────┘
                             │ predictions
                             ▼
                      ┌──────────────┐
                      │  pick_agent  │  filter edge≥3%, Kelly-size
                      └──────┬───────┘
                             │
                ┌────────────┼────────────┐
                ▼            ▼            ▼
        ┌─────────────┐ ┌──────────┐ ┌──────────┐
        │ pick_logger │ │ content_ │ │compliance│
        │ (SQLite +   │ │  agent   │ │  check   │
        │  G-Sheet)   │ │ (Claude) │ └────┬─────┘
        └─────────────┘ └────┬─────┘      │
                             │            │
                             └────┬───────┘
                                  ▼
                          ┌──────────────┐
                          │  scheduler_  │
                          │    agent     │
                          └──────┬───────┘
                                 │
                   ┌─────────────┼─────────────┐
                   ▼             ▼             ▼
                 ┌────┐       ┌─────┐       ┌────────┐
                 │ IG │       │ TG  │       │TikTok/X│
                 └────┘       └─────┘       └────────┘
```

## Agent responsibilities

### `agents/pick_agent/`
- Pulls today's games from scraper outputs
- Runs sport-specific model
- Filters: edge ≥ 3%, confidence tier assignment
- Calculates Kelly sizing (capped 2u)
- Passes to pick_logger + content_agent

### `agents/content_agent/`
- Input: pick dict
- Calls Claude API with structured prompt (see `agents/content_agent/prompts.md`)
- Generates:
  - IG caption (≤2,200 chars, no banned language)
  - Telegram message (markdown)
  - Bet-slip graphic via PIL (1080×1350 IG portrait)
- Returns content bundle

### `agents/track_record_agent/`
- Appends pick to `data/picks_log/picks.jsonl` AND `data/picks_log/picks.sqlite`
- Pushes row to public Google Sheet via sheets API
- Next day: runs `update_results.py` to fill in result + closing odds + CLV

### `agents/scheduler_agent/`
- Cron-triggered 9am ET daily
- Orchestrates: pick_agent → content_agent → compliance_check → platform posters
- Handles retries, logs failures, alerts on errors (Discord webhook or email)

## Compliance check (automatic, every post)

`src/utils/compliance.py` scans generated caption + graphic text for:

- Banned words: `lock`, `guaranteed`, `sure thing`, `inside info`, `fixed`, `rigged`, `can't lose`
- Required: `18+` disclaimer string
- Required: `ConnexOntario` OR `1-866-531-2600` string

If any check fails → post is blocked, logged to review queue, Discord ping sent.

## Why SQLite + JSONL

- SQLite: fast queries for dashboards ("show me MLB CLV last 30 days")
- JSONL: append-only, human-readable, git-committable as audit trail
- Both written on every pick → redundancy + auditability

## Secrets management

All keys in `.env` (gitignored). Template in `config/.env.example`. Never committed:

- `ANTHROPIC_API_KEY`
- `THE_ODDS_API_KEY`
- `SPORTMONKS_API_KEY`
- `META_GRAPH_ACCESS_TOKEN`
- `IG_BUSINESS_ACCOUNT_ID`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHANNEL_ID`
- `GOOGLE_SHEETS_CREDENTIALS_PATH`
- `GOOGLE_SHEET_ID`
- `DISCORD_WEBHOOK_URL`

## Deployment

**MVP (months 1–3):** single Hetzner CX11 VPS ($5/mo), Ubuntu 24.04, cron jobs, SQLite on disk.

**Growth (month 4+):** same VPS, add lightweight FastAPI for public dashboard at `sharpsignals.com/record`, migrate SQLite → Postgres.

## Failure modes to anticipate

1. **Scraper breaks** (API change) → fallback: log error, skip sport for day, Discord ping
2. **Model produces no picks** → that's fine; only post when edge exists
3. **Meta Graph API rate limit** → exponential backoff, retry next hour
4. **Compliance check fails** → hold post for manual review, never auto-override
5. **CLV goes negative for a sport over 50+ picks** → auto-pause that sport, alert owner, iterate model
