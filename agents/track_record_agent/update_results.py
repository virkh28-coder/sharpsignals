"""
Update results — runs the day after picks were posted.

For each unresolved pick:
  1. Fetch the game's final result from the sport's scraper
  2. Fetch closing odds (the line right before tip-off)
  3. Compute win/loss/push and CLV%
  4. Update SQLite, append to JSONL log, push the update to Google Sheets

Run nightly (cron 8:00 ET ≈ 12:00 UTC):
  0 12 * * * cd /path/to/sharpsignals && /path/to/venv/bin/python -m \
      agents.track_record_agent.update_results
"""

from __future__ import annotations
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.utils.odds_math import clv_percent

from .pick_logger import JSONL_PATH, SQLITE_PATH, _ensure_paths

log = logging.getLogger(__name__)


def update_pending_results() -> int:
    """Walk the SQLite log for picks with result IS NULL and try to grade them.

    Returns the number of picks updated. Picks for events that haven't
    finished yet stay pending and will be picked up tomorrow.
    """
    _ensure_paths()
    pending = _load_pending()
    if not pending:
        log.info("No pending picks to grade.")
        return 0

    updated = 0
    for pick in pending:
        try:
            graded = _grade_pick(pick)
        except Exception as e:
            log.error(f"  {pick['pick_id']}: grade failed: {e}")
            continue
        if graded is None:
            continue  # event not final yet
        _persist(graded)
        _append_jsonl_update(graded)
        updated += 1
        log.info(
            f"  {pick['pick_id']}: {graded['result']} "
            f"(CLV {graded.get('clv_percent')}%)"
        )
    return updated


def _load_pending() -> list[dict]:
    with sqlite3.connect(SQLITE_PATH) as db:
        db.row_factory = sqlite3.Row
        rows = db.execute(
            "SELECT * FROM picks WHERE result IS NULL ORDER BY timestamp_utc"
        ).fetchall()
    return [dict(r) for r in rows]


def _grade_pick(pick: dict) -> Optional[dict]:
    """Call the right scraper for closing odds + final score.

    Returns None if the event isn't graded yet (try again tomorrow).
    Returns the picked dict augmented with result + CLV when graded.
    """
    sport = pick["sport"]
    final = _fetch_final(sport, pick["event_id"])
    if final is None:
        return None  # not final yet

    closing = _fetch_closing_odds(sport, pick["event_id"], pick["market"], pick["selection"])
    result = _outcome(pick, final)
    out = dict(pick)
    out["result"] = result
    if closing is not None:
        out["closing_odds_american"] = closing["odds_american"]
        out["closing_odds_decimal"] = closing["odds_decimal"]
        out["clv_percent"] = clv_percent(pick["odds_decimal"], closing["odds_decimal"])
    return out


def _fetch_final(sport: str, event_id: str) -> Optional[dict]:
    """Return {'home_score', 'away_score', 'home_team', 'away_team'} or None."""
    if sport == "NBA":
        from src.scrapers.nba import NBAScraper
        # NBAScraper does not expose a final-score helper yet — graceful skip.
        # TODO: implement NBAScraper.fetch_final(event_id) using nba_api scoreboard.
        log.warning(f"  {sport} fetch_final not implemented — skipping {event_id}")
        return None
    raise NotImplementedError(f"No final-score lookup for {sport} yet")


def _fetch_closing_odds(
    sport: str, event_id: str, market: str, selection: str
) -> Optional[dict]:
    if sport == "NBA":
        from src.scrapers.nba import NBAScraper
        try:
            rows = NBAScraper().fetch_closing_odds(event_id)
        except Exception as e:
            log.warning(f"  closing odds lookup failed for {event_id}: {e}")
            return None
        candidates = [
            r for r in rows
            if r.market == market and r.selection == selection
        ]
        if not candidates:
            return None
        # Take the median across books for a stable closing line.
        candidates.sort(key=lambda r: r.odds_decimal)
        mid = candidates[len(candidates) // 2]
        return {
            "odds_american": mid.odds_american,
            "odds_decimal": mid.odds_decimal,
        }
    return None


def _outcome(pick: dict, final: dict) -> str:
    """Return 'win' / 'loss' / 'push' / 'void' for the pick.

    Currently handles NBA moneyline only — extend per market as we add sports.
    """
    market = pick["market"]
    sel = pick["selection"]

    if market == "moneyline":
        winner = final["home_team"] if final["home_score"] > final["away_score"] else final["away_team"]
        return "win" if sel == winner else "loss"

    log.warning(f"grading not implemented for market={market}; marking void")
    return "void"


def _persist(updated: dict) -> None:
    """Update SQLite and re-push to Google Sheet."""
    with sqlite3.connect(SQLITE_PATH) as db:
        db.execute(
            """
            UPDATE picks
            SET result = ?,
                closing_odds_american = ?,
                closing_odds_decimal = ?,
                clv_percent = ?
            WHERE pick_id = ?
            """,
            (
                updated.get("result"),
                updated.get("closing_odds_american"),
                updated.get("closing_odds_decimal"),
                updated.get("clv_percent"),
                updated["pick_id"],
            ),
        )
    _push_sheet_update(updated)


def _append_jsonl_update(updated: dict) -> None:
    """Append a delta record to the JSONL audit trail.

    We append rather than rewrite so the log stays append-only and
    git-committable as historical proof of when results were filled in.
    """
    delta = {
        "pick_id": updated["pick_id"],
        "graded_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": updated.get("result"),
        "closing_odds_american": updated.get("closing_odds_american"),
        "clv_percent": updated.get("clv_percent"),
    }
    with open(JSONL_PATH.parent / "results.jsonl", "a") as f:
        f.write(json.dumps(delta) + "\n")


def _push_sheet_update(updated: dict) -> None:
    """Update the matching row in the public Google Sheet by pick_id.

    For v0 we just append a delta row — full row-update by ID is a
    nice-to-have. The sheet's first audit pass is "join on pick_id".
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        return
    creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not creds_path or not sheet_id:
        return
    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=creds)
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="Results!A:E",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": [[
            updated["pick_id"],
            datetime.now(timezone.utc).isoformat(),
            updated.get("result", ""),
            updated.get("closing_odds_american", ""),
            updated.get("clv_percent", ""),
        ]]},
    ).execute()


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    n = update_pending_results()
    log.info(f"=== graded {n} picks ===")


if __name__ == "__main__":
    main()
