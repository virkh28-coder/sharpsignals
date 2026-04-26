"""
NBA scraper.

Combines:
  - nba_api (stats.nba.com)   → schedule, team stats, injuries
  - The Odds API              → current market odds across books

Install:
  pip install nba_api

Env:
  THE_ODDS_API_KEY   (from https://the-odds-api.com)

Usage:
  scraper = NBAScraper(odds_api_key=os.environ["THE_ODDS_API_KEY"])
  games = scraper.fetch_today()
"""

from __future__ import annotations
import os
from datetime import datetime, timezone
from typing import Optional
import httpx

from .base import BaseScraper, Game, GameOdds

THE_ODDS_API_BASE = "https://api.the-odds-api.com/v4"
NBA_SPORT_KEY = "basketball_nba"


class NBAScraper(BaseScraper):
    sport = "NBA"

    def __init__(self, odds_api_key: Optional[str] = None, timeout: float = 15.0):
        self.odds_api_key = odds_api_key or os.environ.get("THE_ODDS_API_KEY")
        if not self.odds_api_key:
            raise RuntimeError("THE_ODDS_API_KEY not set")
        self.client = httpx.Client(timeout=timeout)

    # ---------- public interface ----------

    def fetch_today(self) -> list[Game]:
        """Pull NBA games with current odds."""
        raw_events = self._fetch_odds_api_events()
        games: list[Game] = []
        for event in raw_events:
            games.append(self._event_to_game(event))
        return games

    def fetch_closing_odds(self, event_id: str) -> list[GameOdds]:
        """The Odds API historical endpoint (paid tier); used day-after for CLV."""
        url = f"{THE_ODDS_API_BASE}/historical/sports/{NBA_SPORT_KEY}/events/{event_id}/odds"
        params = {
            "apiKey": self.odds_api_key,
            "regions": "us,uk,eu",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
        }
        r = self.client.get(url, params=params)
        r.raise_for_status()
        payload = r.json()
        return self._extract_odds(payload)

    # ---------- internals ----------

    def _fetch_odds_api_events(self) -> list[dict]:
        url = f"{THE_ODDS_API_BASE}/sports/{NBA_SPORT_KEY}/odds"
        params = {
            "apiKey": self.odds_api_key,
            "regions": "us,uk",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american",
            "dateFormat": "iso",
        }
        r = self.client.get(url, params=params)
        r.raise_for_status()
        return r.json()

    def _event_to_game(self, event: dict) -> Game:
        odds = self._extract_odds(event)
        return Game(
            sport=self.sport,
            event_id=event["id"],
            home_team=event["home_team"],
            away_team=event["away_team"],
            commence_time_utc=datetime.fromisoformat(
                event["commence_time"].replace("Z", "+00:00")
            ),
            odds=odds,
            raw=event,
        )

    @staticmethod
    def _extract_odds(event: dict) -> list[GameOdds]:
        now = datetime.now(timezone.utc)
        out: list[GameOdds] = []
        for book in event.get("bookmakers", []):
            book_name = book["title"]
            for market in book.get("markets", []):
                mkey = market["key"]  # h2h / spreads / totals
                for outcome in market.get("outcomes", []):
                    american = int(outcome["price"])
                    out.append(
                        GameOdds(
                            sportsbook=book_name,
                            market=_market_label(mkey),
                            selection=outcome["name"],
                            line=outcome.get("point"),
                            odds_american=american,
                            odds_decimal=_american_to_decimal(american),
                            fetched_at_utc=now,
                        )
                    )
        return out


def _market_label(key: str) -> str:
    return {
        "h2h": "moneyline",
        "spreads": "spread",
        "totals": "total",
    }.get(key, key)


def _american_to_decimal(american: int) -> float:
    if american >= 0:
        return round(1.0 + american / 100.0, 4)
    return round(1.0 + 100.0 / abs(american), 4)


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    scraper = NBAScraper()
    games = scraper.fetch_today()
    print(f"Found {len(games)} NBA games today")
    for g in games[:3]:
        print(f"  {g.away_team} @ {g.home_team}  — {len(g.odds)} odds rows")
