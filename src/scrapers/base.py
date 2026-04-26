"""
Base scraper interface — all sport-specific scrapers inherit from this.
Guarantees a consistent output shape for the pick_agent to consume.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional


@dataclass
class GameOdds:
    """Normalized odds for one market at one sportsbook."""

    sportsbook: str  # "DraftKings", "FanDuel", "bet365", etc.
    market: str      # "moneyline", "spread", "total", "1x2", etc.
    selection: str   # e.g. "Lakers", "over 228.5", "draw"
    line: Optional[float]         # point spread or total; None for ML
    odds_american: int
    odds_decimal: float
    fetched_at_utc: datetime


@dataclass
class Game:
    """Normalized game/event + all markets/books we found."""

    sport: str               # "NBA", "NHL", "MLB", "EPL", "CRICKET"
    event_id: str            # stable id from source API where possible
    home_team: str
    away_team: str
    commence_time_utc: datetime
    odds: list[GameOdds]
    raw: dict                # the original API payload for debugging

    def to_dict(self) -> dict:
        d = asdict(self)
        d["commence_time_utc"] = self.commence_time_utc.isoformat()
        for o in d["odds"]:
            o["fetched_at_utc"] = o["fetched_at_utc"].isoformat() if isinstance(
                o["fetched_at_utc"], datetime
            ) else o["fetched_at_utc"]
        return d


class BaseScraper(ABC):
    """All scrapers follow the same interface."""

    sport: str = "UNKNOWN"

    @abstractmethod
    def fetch_today(self) -> list[Game]:
        """Pull all of today's games + available odds. Returns list of Game."""
        ...

    @abstractmethod
    def fetch_closing_odds(self, event_id: str) -> list[GameOdds]:
        """Pull closing odds for a completed game (for CLV calc). Called day after."""
        ...
