"""
Train the NBA Elo model on cached historical games and save it.

Run from project root, inside venv:
  python scripts/train_nba_model.py

What it does:
  1. Reads data/raw/nba_historical.csv (built by nba_historical_loader.py)
  2. Replays every game through the Elo updater (with 538-style MoV multiplier)
  3. Saves the trained model to data/models/nba_elo.pkl
  4. Prints the top 10 + bottom 5 ratings as a sanity check —
     if the rankings look obviously wrong (e.g. Hornets at #1), the
     training is broken and we shouldn't ship picks.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Allow running as `python scripts/train_nba_model.py` from project root —
# without this, sys.path includes scripts/ but not the project root, so
# `from src...` would fail.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.nba_historical_loader import load_from_csv
from src.models.nba_model import NBAModel, save


def main() -> None:
    csv_path = Path("data/raw/nba_historical.csv")
    if not csv_path.exists():
        raise SystemExit(
            f"No historical data at {csv_path}. "
            "Run `python -m src.models.nba_historical_loader` first."
        )

    games = load_from_csv(csv_path)
    print(f"Loaded {len(games)} games")

    model = NBAModel()
    model.train_from_games(games)

    sorted_teams = sorted(model.elo.ratings.items(), key=lambda kv: -kv[1])
    print("\n--- top 10 by Elo ---")
    for team, rating in sorted_teams[:10]:
        print(f"  {team:5}  {rating:7.1f}")

    print("\n--- bottom 5 by Elo ---")
    for team, rating in sorted_teams[-5:]:
        print(f"  {team:5}  {rating:7.1f}")

    out = save(model)
    print(f"\nSaved model → {out}")


if __name__ == "__main__":
    main()
