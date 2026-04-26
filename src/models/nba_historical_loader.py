"""
Historical-game loader for the NBA Elo model.

Uses nba_api's LeagueGameLog to pull every regular-season + playoff game for
a given season. The output is the dict shape that NBAModel.train_from_games
expects:
  {home_team, away_team, home_score, away_score, game_date}

Why not store the raw payloads:
  We re-process them every retrain anyway. Keeping a thin extractor here means
  upstream API changes break in one place.
"""

from __future__ import annotations
import logging
from datetime import date
from pathlib import Path
from typing import Iterable

log = logging.getLogger(__name__)


SEASON_TYPES = ("Regular Season", "Playoffs")


def fetch_season(season: str) -> list[dict]:
    """Pull every game from a season. `season` format: "2024-25".

    Each game appears twice in the LeagueGameLog (home row + away row); we
    deduplicate on GAME_ID and pivot home/away from MATCHUP.
    """
    try:
        from nba_api.stats.endpoints import leaguegamelog
    except ImportError as e:
        raise RuntimeError("nba_api not installed — run: pip install nba_api") from e

    out: dict[str, dict] = {}
    for season_type in SEASON_TYPES:
        log.info(f"  fetching {season} {season_type}")
        df = leaguegamelog.LeagueGameLog(
            season=season,
            season_type_all_star=season_type,
        ).get_data_frames()[0]

        for row in df.itertuples():
            game_id = row.GAME_ID
            is_home = " vs. " in row.MATCHUP  # "LAL vs. GSW" home, "LAL @ GSW" away
            entry = out.setdefault(
                game_id,
                {"game_id": game_id, "game_date": row.GAME_DATE},
            )
            if is_home:
                entry["home_team"] = row.TEAM_ABBREVIATION
                entry["home_score"] = int(row.PTS)
            else:
                entry["away_team"] = row.TEAM_ABBREVIATION
                entry["away_score"] = int(row.PTS)

    games = [g for g in out.values() if all(k in g for k in
             ("home_team", "away_team", "home_score", "away_score"))]
    games.sort(key=lambda g: g["game_date"])
    log.info(f"  {season}: {len(games)} games")
    return games


def fetch_seasons(seasons: Iterable[str]) -> list[dict]:
    """Pull and concatenate multiple seasons in chronological order."""
    all_games: list[dict] = []
    for s in seasons:
        all_games.extend(fetch_season(s))
    return all_games


def cache_to_csv(games: list[dict], path: Path) -> None:
    """Persist for fast retrains. CSV beats pickle here for diffability."""
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    if not games:
        return
    fields = list(games[0].keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(games)
    log.info(f"  cached {len(games)} games → {path}")


def load_from_csv(path: Path) -> list[dict]:
    import csv

    with open(path) as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    for r in rows:
        r["home_score"] = int(r["home_score"])
        r["away_score"] = int(r["away_score"])
    return rows


def main() -> None:
    """CLI entry: fetch last 2 seasons + current and cache to data/raw/."""
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--seasons", nargs="+", default=_default_seasons())
    parser.add_argument("--out", default="data/raw/nba_historical.csv")
    args = parser.parse_args()

    games = fetch_seasons(args.seasons)
    cache_to_csv(games, Path(args.out))


def _default_seasons() -> list[str]:
    """Last 2 completed + current. NBA seasons are labeled by their start year."""
    today = date.today()
    start_year = today.year - 1 if today.month < 10 else today.year
    return [
        f"{start_year - 2}-{str(start_year - 1)[-2:]}",
        f"{start_year - 1}-{str(start_year)[-2:]}",
        f"{start_year}-{str(start_year + 1)[-2:]}",
    ]


if __name__ == "__main__":
    main()
