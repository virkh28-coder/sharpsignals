"""
Scheduler Agent — orchestrates the daily pipeline.

Cron setup (runs daily at 14:00 UTC = 10:00 ET):
  0 14 * * * cd /path/to/sharpsignals && /path/to/venv/bin/python -m agents.scheduler_agent.daily_run

What it does:
  1. For each active sport, run the scraper
  2. Run the sport's model against today's games
  3. Call pick_agent to generate Pick objects (edge≥3%, Kelly-sized)
  4. Log all picks (JSONL + SQLite + Google Sheet)
  5. For each pick, generate caption + graphic via content_agent
  6. Run compliance_check — if fail, route to review queue
  7. Post to IG + Telegram via platform posters

Errors are caught per-sport so one broken scraper doesn't kill the run.
"""

from __future__ import annotations
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from agents.content_agent.post_generator import generate as generate_content
from agents.pick_agent.pick_generator import generate_picks
from agents.track_record_agent.pick_logger import log_picks, push_to_google_sheet

load_dotenv()
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("scheduler")


ACTIVE_SPORTS = ["NBA"]  # add MLB, NHL, EPL, CRICKET as they come online


def run_sport(sport: str) -> int:
    """Run the pipeline for one sport. Returns picks posted."""
    log.info(f"--- {sport} ---")

    # 1. scrape
    try:
        games = _scrape(sport)
        log.info(f"  scraped {len(games)} games")
    except Exception as e:
        log.error(f"  scrape failed: {e}")
        return 0

    # 2. predict
    try:
        predictions = _predict(sport, games)
        log.info(f"  predictions: {len(predictions)}")
    except Exception as e:
        log.error(f"  model failed: {e}")
        return 0

    # 3. odds lookup for pick_agent
    odds_lookup = _build_odds_lookup(games)

    # 4. filter to picks
    picks = generate_picks(predictions, odds_lookup)
    log.info(f"  qualifying picks (edge≥3%): {len(picks)}")
    if not picks:
        return 0

    # 5. log first, post second
    n = log_picks(picks)
    log.info(f"  logged {n} picks locally")
    try:
        push_to_google_sheet(picks)
    except Exception as e:
        log.warning(f"  sheet push failed: {e}")

    # 6 + 7. content + post
    posted = 0
    for pick in picks:
        content = generate_content(pick, output_dir=Path("./data/processed"))
        if not content.compliance_passed:
            log.warning(f"  {pick.pick_id}: compliance FAIL → review queue")
            _route_to_review(pick, content)
            continue
        try:
            _post_everywhere(pick, content)
            posted += 1
        except Exception as e:
            log.error(f"  {pick.pick_id}: post failed: {e}")

    return posted


def _scrape(sport: str):
    if sport == "NBA":
        from src.scrapers.nba import NBAScraper
        return NBAScraper().fetch_today()
    raise NotImplementedError(f"No scraper for {sport} yet")


def _predict(sport: str, games):
    """Return list[ModelPrediction] for the day's games."""
    if sport == "NBA":
        from src.models.nba_model import load_or_train

        model = load_or_train()
        return model.predict_games(games)
    log.warning(f"  {sport} model not wired yet — returning empty predictions")
    return []


def _build_odds_lookup(games) -> dict:
    lookup = {}
    for g in games:
        for o in g.odds:
            lookup.setdefault((g.event_id, o.market, o.selection), []).append(o)
    return lookup


def _route_to_review(pick, content) -> None:
    review_dir = Path("./data/processed/review_queue")
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / f"{pick.pick_id}.txt").write_text(
        f"PICK: {pick.to_dict()}\n\nCAPTION:\n{content.caption}\n\nCOMPLIANCE:\n{content.compliance_notes}"
    )


def _post_everywhere(pick, content) -> None:
    """Push to Telegram first (cheap, instant), then IG (slower, async).

    Each platform is wrapped so one failing doesn't block the other — we'd
    rather get out on TG than skip the day because IG's container was slow.
    """
    from agents.scheduler_agent import ig_poster, telegram_poster

    try:
        telegram_poster.post(content.telegram_message, photo_path=content.graphic_path)
        log.info(f"  {pick.pick_id}: posted to Telegram")
    except Exception as e:
        log.error(f"  {pick.pick_id}: Telegram post failed: {e}")

    if not content.graphic_path:
        log.warning(f"  {pick.pick_id}: no graphic — skipping IG (IG requires image)")
        return

    try:
        ig_poster.post(content.caption, content.graphic_path)
        log.info(f"  {pick.pick_id}: posted to Instagram")
    except Exception as e:
        log.error(f"  {pick.pick_id}: IG post failed: {e}")


def main() -> None:
    total = 0
    for sport in ACTIVE_SPORTS:
        try:
            total += run_sport(sport)
        except Exception as e:
            log.exception(f"{sport} pipeline crashed: {e}")
    log.info(f"=== done. Total posts: {total} ===")


if __name__ == "__main__":
    main()
