"""
Walk-forward NBA backtest.

We don't have paid historical odds, so we can't compute true CLV. What we
*can* compute, and what actually matters for a model going to production:

  1. Hit rate on the moneyline (raw and at confidence buckets)
  2. Brier score (squared-error loss on probabilities)
  3. Calibration table: of the games where we said "65% home win",
     what fraction actually had the home team win?
  4. -110 break-even: of the games where the model expressed a strong
     enough opinion to clear the standard juice, how often was it right?

If the model is well-calibrated and beats the -110 break-even line, the
methodology has predictive value and shipping picks publicly is justified.
If not, we don't ship — the public sheet would expose it.

Walk-forward = no look-ahead bias. For each historical game we predict
using only the Elo state built from games BEFORE it, then update.

Run:
  python scripts/backtest_nba.py
"""

from __future__ import annotations
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.models.nba_historical_loader import load_from_csv
from src.models.nba_model import NBAModel


# Per docs/MODEL_V0_SPEC.md: 52.4% is moneyline break-even at -110.
BREAK_EVEN = 0.524


def main() -> None:
    games = load_from_csv(Path("data/raw/nba_historical.csv"))
    print(f"Loaded {len(games)} games (chronological)")

    # Burn-in: train on the first N games to give Elo a sane starting point
    # without using those games as "predictions". Common practice = ~20% of data.
    burn_in = max(200, len(games) // 5)
    model = NBAModel()

    print(f"Burn-in: training on first {burn_in} games (no eval)")
    for g in games[:burn_in]:
        _train_step(model, g)

    eval_games = games[burn_in:]
    print(f"Evaluating walk-forward on {len(eval_games)} games\n")

    records: list[dict] = []
    for g in eval_games:
        # Predict BEFORE updating — this is the no-look-ahead invariant.
        p_home = model.fair_win_probability(g["home_team"], g["away_team"])
        actual_home_win = g["home_score"] > g["away_score"]

        records.append({
            "p_home": p_home,
            "home_won": actual_home_win,
            "margin": g["home_score"] - g["away_score"],
        })

        _train_step(model, g)

    _report(records)


def _train_step(model: NBAModel, g: dict) -> None:
    """Update Elo with a single game's outcome."""
    model.train_from_games([g])


def _report(records: list[dict]) -> None:
    n = len(records)
    if n == 0:
        print("No eval games — increase data or shrink burn-in")
        return

    # ---- Raw hit rate ----
    correct = sum(
        1 for r in records
        if (r["p_home"] >= 0.5) == r["home_won"]
    )
    raw_hit = correct / n
    print(f"Total games:    {n}")
    print(f"Raw hit rate:   {raw_hit:.3%}  (predicted favorite won)")
    print()

    # ---- Brier score ----
    brier = sum((r["p_home"] - (1.0 if r["home_won"] else 0.0)) ** 2 for r in records) / n
    print(f"Brier score:    {brier:.4f}  (lower = better; 0.25 = always 50%)")

    # ---- Log loss ----
    eps = 1e-9
    log_loss = -sum(
        math.log(r["p_home"] + eps if r["home_won"] else (1 - r["p_home"]) + eps)
        for r in records
    ) / n
    print(f"Log loss:       {log_loss:.4f}  (lower = better; 0.6931 = always 50%)")
    print()

    # ---- Calibration table ----
    print("Calibration (does P(predicted) match P(actual)?):")
    print(f"  {'bucket':>14}  {'n':>5}  {'avg p':>7}  {'actual':>7}  {'gap':>6}")
    bucket_edges = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 1.00]
    for lo, hi in zip(bucket_edges, bucket_edges[1:]):
        bucket = [r for r in records if lo <= max(r["p_home"], 1 - r["p_home"]) < hi]
        if not bucket:
            continue
        avg_p = sum(max(r["p_home"], 1 - r["p_home"]) for r in bucket) / len(bucket)
        actual = sum(
            1 for r in bucket
            if (r["p_home"] >= 0.5) == r["home_won"]
        ) / len(bucket)
        gap = actual - avg_p
        flag = "✓" if abs(gap) < 0.03 else ("⚠" if abs(gap) < 0.06 else "✗")
        print(f"  [{lo:.2f}, {hi:.2f})  {len(bucket):>5}  "
              f"{avg_p:.3f}  {actual:.3f}  {gap:+.3f} {flag}")
    print()

    # ---- -110 break-even check ----
    confident = [r for r in records if max(r["p_home"], 1 - r["p_home"]) >= BREAK_EVEN]
    if confident:
        c_hit = sum(
            1 for r in confident
            if (r["p_home"] >= 0.5) == r["home_won"]
        ) / len(confident)
        units_pl = _units_pl(confident, juice_decimal=1.909)  # -110
        print(f"-110 break-even gate (model conviction ≥ 52.4%):")
        print(f"  picks evaluated:  {len(confident)}")
        print(f"  hit rate:         {c_hit:.3%}")
        print(f"  units P&L (1u flat, -110): {units_pl:+.2f}u")
        verdict = "✓ ship" if units_pl > 0 else "✗ DO NOT ship"
        print(f"  verdict:          {verdict}")
    else:
        print("No games at >= 52.4% conviction — model is too uncertain")


def _units_pl(records: list[dict], juice_decimal: float = 1.909) -> float:
    """Simulate flat 1-unit bets at given decimal odds, betting the model favorite."""
    pl = 0.0
    for r in records:
        favored_home = r["p_home"] >= 0.5
        won = (favored_home and r["home_won"]) or (not favored_home and not r["home_won"])
        pl += (juice_decimal - 1.0) if won else -1.0
    return pl


if __name__ == "__main__":
    main()
