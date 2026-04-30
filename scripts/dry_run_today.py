"""
Dry run: scrape today's NBA games + odds, run predictions, show qualifying picks.

This bypasses the scheduler's posting/Telegram/IG flow entirely so we can
review what the model would publish before it actually goes anywhere public.

Output:
  - Number of games scraped
  - Number of predictions generated
  - Every qualifying pick (edge ≥ 3%) printed in detail
  - The same picks dumped to data/processed/dry_run_picks.json for inspection

With the --with-content flag, we ALSO call the content_agent on each pick:
  - Generates the IG caption via Claude (~$0.02 per pick)
  - Renders the bet-slip graphic PNG
  - Generates the Telegram-formatted message
  - Runs compliance check
Outputs land in data/processed/ — caption .txt, graphic .png — ready for
manual review or eventual auto-posting.

Run from project root, inside venv:
  python scripts/dry_run_today.py
  python scripts/dry_run_today.py --with-content
"""

from __future__ import annotations
import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from agents.pick_agent.pick_generator import generate_picks
from agents.scheduler_agent.daily_run import _build_odds_lookup
from src.models.nba_model import load_or_train
from src.scrapers.nba import NBAScraper

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("dry-run")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--with-content",
        action="store_true",
        help="Also call the content agent (Claude caption + bet-slip graphic + TG message). "
             "Costs ~$0.02 per pick. Outputs to data/processed/.",
    )
    args = parser.parse_args()

    log.info("--- scraping today's NBA games ---")
    scraper = NBAScraper()
    games = scraper.fetch_today()
    log.info(f"Found {len(games)} NBA games today")
    for g in games:
        log.info(f"  {g.away_team} @ {g.home_team} — {len(g.odds)} odds rows across books")
    if not games:
        log.warning("No games today (off-day or end of season). Re-run on a game day.")
        return

    log.info("\n--- running NBA model ---")
    model = load_or_train()
    if not model.elo.ratings:
        raise SystemExit("Model has no ratings — did you run scripts/train_nba_model.py?")
    predictions = model.predict_games(games)
    log.info(f"Generated {len(predictions)} raw predictions across all markets")

    log.info("\n--- filtering to edge ≥ 3% picks ---")
    odds_lookup = _build_odds_lookup(games)
    picks = generate_picks(predictions, odds_lookup)
    log.info(f"Qualifying picks: {len(picks)}")

    if not picks:
        log.info("No picks today — model didn't find any edge ≥ 3% in available markets.")
        log.info("This is normal on quiet days. Re-run tomorrow.")
        return

    log.info("\n--- detailed pick review ---")
    out = []
    for p in picks:
        d = p.to_dict()
        out.append(d)
        print()
        print(f"  {p.event_label}")
        print(f"  market:  {p.market}")
        print(f"  pick:    {p.selection}")
        print(f"  odds:    {p.odds_american:+d}  @  {p.sportsbook_source}")
        print(f"  model:   {p.model_fair_probability * 100:.1f}% fair")
        print(f"  market:  {p.market_implied_probability * 100:.1f}% implied")
        print(f"  edge:    +{p.edge_percent:.2f}%")
        print(f"  units:   {p.bet_size_units:.2f}u  ({p.confidence_tier})")

    out_path = Path("data/processed/dry_run_picks.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    log.info(f"\nSaved picks → {out_path}")

    if args.with_content:
        _generate_content_for(picks)
    else:
        log.info("\nRun again with --with-content to also generate captions + graphics.")
    log.info("\nNothing was posted. Inspect the outputs, then we decide what to ship.")


def _generate_content_for(picks) -> None:
    """Call the content agent for each pick. Writes caption .txt + .png to disk."""
    from agents.content_agent.post_generator import generate as generate_content

    log.info("\n--- generating content (Claude captions + bet-slip graphics) ---")
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    for p in picks:
        log.info(f"  generating for {p.pick_id} ({p.event_label}, {p.selection})")
        try:
            content = generate_content(p, output_dir=output_dir)
        except Exception as e:
            log.error(f"    failed: {e}")
            continue

        caption_path = output_dir / f"{p.pick_id}.caption.txt"
        tg_path = output_dir / f"{p.pick_id}.telegram.txt"
        caption_path.write_text(content.caption)
        tg_path.write_text(content.telegram_message)
        status = "✓ pass" if content.compliance_passed else f"✗ {content.compliance_notes}"
        log.info(f"    compliance:  {status}")
        log.info(f"    caption:     {caption_path}")
        log.info(f"    telegram:    {tg_path}")
        if content.graphic_path:
            log.info(f"    graphic:     {content.graphic_path}")


if __name__ == "__main__":
    main()
