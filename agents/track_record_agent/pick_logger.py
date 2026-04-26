"""
Track-record logger.

Writes every pick to:
  1. data/picks_log/picks.jsonl  (append-only, git-committable audit trail)
  2. data/picks_log/picks.sqlite  (for fast queries / dashboards)
  3. Public Google Sheet          (social proof — what customers see)

Run AFTER pick_agent produces picks, BEFORE content_agent posts publicly.
Order matters: log first so the public record is the source of truth.
"""

from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from typing import Iterable

from agents.pick_agent.pick_generator import Pick

DATA_DIR = Path(os.environ.get("DATA_DIR", "./data"))
PICKS_DIR = DATA_DIR / "picks_log"
JSONL_PATH = PICKS_DIR / "picks.jsonl"
SQLITE_PATH = PICKS_DIR / "picks.sqlite"


SCHEMA = """
CREATE TABLE IF NOT EXISTS picks (
    pick_id TEXT PRIMARY KEY,
    timestamp_utc TEXT NOT NULL,
    sport TEXT NOT NULL,
    event_id TEXT NOT NULL,
    event_label TEXT NOT NULL,
    market TEXT NOT NULL,
    selection TEXT NOT NULL,
    odds_american INTEGER NOT NULL,
    odds_decimal REAL NOT NULL,
    sportsbook_source TEXT NOT NULL,
    model_fair_probability REAL NOT NULL,
    market_implied_probability REAL NOT NULL,
    edge_percent REAL NOT NULL,
    kelly_fraction REAL NOT NULL,
    bet_size_units REAL NOT NULL,
    confidence_tier TEXT NOT NULL,
    result TEXT,
    closing_odds_american INTEGER,
    closing_odds_decimal REAL,
    clv_percent REAL
);
CREATE INDEX IF NOT EXISTS idx_picks_sport ON picks(sport);
CREATE INDEX IF NOT EXISTS idx_picks_timestamp ON picks(timestamp_utc);
"""


def _ensure_paths() -> None:
    PICKS_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(SQLITE_PATH) as db:
        db.executescript(SCHEMA)


def log_picks(picks: Iterable[Pick]) -> int:
    """Log picks locally. Returns count written. Idempotent on pick_id."""
    _ensure_paths()
    picks = list(picks)
    if not picks:
        return 0

    with open(JSONL_PATH, "a") as f:
        for p in picks:
            f.write(json.dumps(p.to_dict()) + "\n")

    with sqlite3.connect(SQLITE_PATH) as db:
        for p in picks:
            d = p.to_dict()
            cols = ", ".join(d.keys())
            placeholders = ", ".join("?" * len(d))
            db.execute(
                f"INSERT OR IGNORE INTO picks ({cols}) VALUES ({placeholders})",
                tuple(d.values()),
            )

    return len(picks)


def push_to_google_sheet(picks: Iterable[Pick]) -> None:
    """Append picks to the public Google Sheet (social proof).

    Requires:
      GOOGLE_SHEETS_CREDENTIALS_PATH — path to service account JSON
      GOOGLE_SHEET_ID                — the sheet id (from its URL)
    """
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError:
        print("google-api-python-client not installed — skipping sheet push")
        return

    creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID")
    if not creds_path or not sheet_id:
        print("Google Sheets env not set — skipping push (picks still logged locally)")
        return

    creds = service_account.Credentials.from_service_account_file(
        creds_path, scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    service = build("sheets", "v4", credentials=creds)

    rows = [
        [
            p.timestamp_utc, p.sport, p.event_label, p.market, p.selection,
            p.odds_american, p.sportsbook_source, p.edge_percent,
            p.bet_size_units, p.confidence_tier,
            p.result or "", p.clv_percent or "",
        ]
        for p in picks
    ]
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range="Picks!A:L",
        valueInputOption="RAW",
        insertDataOption="INSERT_ROWS",
        body={"values": rows},
    ).execute()
