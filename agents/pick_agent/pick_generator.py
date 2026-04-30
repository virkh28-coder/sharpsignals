"""
Pick Agent — takes scraper output + model predictions, filters for edge ≥ 3%,
Kelly-sizes, and emits publishable Pick records.

Flow:
  scraper → Game[] with odds
  model  → fair_prob per selection
  pick_agent → Pick[] (edge≥3%, Kelly units, confidence tier)
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
import uuid

from src.utils.odds_math import (
    decimal_to_implied_prob,
    edge as calc_edge,
    quarter_kelly_units,
)

EDGE_THRESHOLD = 0.03   # 3% minimum edge to publish
EDGE_CEILING = 0.10     # 10% — above this, "edge" is almost always model error,
                        # not market error. We filter these out rather than ship,
                        # because mis-calibrated picks ship a single bad public
                        # pick that costs us more credibility than the bet ever
                        # could win us. See docs/MODEL_V0_SPEC.md.

# Markets temporarily disabled for live shipping. Updated 2026-04-29 after the
# walk-forward backtest revealed the NBA model is systematically overconfident
# above 65% conviction. Spreads + totals use different math (Normal distribution
# on margin/total) and aren't affected, so we restrict to those until we add
# probability calibration (Platt or isotonic) and re-backtest. Re-enable by
# removing 'moneyline' from this set and re-running scripts/backtest_nba.py
# to confirm the calibration gap has closed.
DISABLED_MARKETS: frozenset[str] = frozenset({"moneyline"})


@dataclass
class ModelPrediction:
    """Model output for a single selection."""

    sport: str
    event_id: str
    event_label: str  # e.g. "Lakers vs Warriors"
    market: str
    selection: str
    fair_probability: float


@dataclass
class Pick:
    pick_id: str
    timestamp_utc: str
    sport: str
    event_id: str
    event_label: str
    market: str
    selection: str
    odds_american: int
    odds_decimal: float
    sportsbook_source: str
    model_fair_probability: float
    market_implied_probability: float
    edge_percent: float
    kelly_fraction: float
    bet_size_units: float
    confidence_tier: str
    # Filled in later by update_results.py:
    result: Optional[str] = None
    closing_odds_american: Optional[int] = None
    closing_odds_decimal: Optional[float] = None
    clv_percent: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _confidence_tier(edge: float) -> str:
    if edge >= 0.08:
        return "rare"
    if edge >= 0.05:
        return "strong"
    return "standard"


def generate_picks(
    predictions: list[ModelPrediction],
    games_odds_lookup: dict,  # {(event_id, market, selection): list[GameOdds]}
    edge_threshold: float = EDGE_THRESHOLD,
    edge_ceiling: float = EDGE_CEILING,
    max_units: float = 2.0,
) -> list[Pick]:
    """For each prediction, find best available odds, check edge, size bet.

    games_odds_lookup: map from (event_id, market, selection) to list of GameOdds
    across sportsbooks. We pick the BEST (highest decimal) odds available.

    Filters: edge in [edge_threshold, edge_ceiling]. Edges above ceiling are
    silently dropped — see EDGE_CEILING docstring for rationale.
    """
    picks: list[Pick] = []
    now = datetime.now(timezone.utc).isoformat()

    for pred in predictions:
        if pred.market in DISABLED_MARKETS:
            continue
        key = (pred.event_id, pred.market, pred.selection)
        available = games_odds_lookup.get(key, [])
        if not available:
            continue

        # Take the best (highest decimal) odds across books
        best = max(available, key=lambda o: o.odds_decimal)

        edge_val = calc_edge(pred.fair_probability, best.odds_decimal)
        if edge_val < edge_threshold or edge_val > edge_ceiling:
            continue

        units = quarter_kelly_units(
            pred.fair_probability, best.odds_decimal, max_units=max_units
        )
        if units <= 0:
            continue

        from src.utils.odds_math import kelly_fraction as _kelly

        pick = Pick(
            pick_id=f"{datetime.now(timezone.utc).strftime('%Y%m%d')}-{pred.sport}-{uuid.uuid4().hex[:6]}",
            timestamp_utc=now,
            sport=pred.sport,
            event_id=pred.event_id,
            event_label=pred.event_label,
            market=pred.market,
            selection=pred.selection,
            odds_american=best.odds_american,
            odds_decimal=best.odds_decimal,
            sportsbook_source=best.sportsbook,
            model_fair_probability=round(pred.fair_probability, 4),
            market_implied_probability=round(
                decimal_to_implied_prob(best.odds_decimal), 4
            ),
            edge_percent=round(edge_val * 100, 2),
            kelly_fraction=round(_kelly(pred.fair_probability, best.odds_decimal), 4),
            bet_size_units=units,
            confidence_tier=_confidence_tier(edge_val),
        )
        picks.append(pick)

    # Dedup: at most one pick per (event, market, side). Different books and
    # different lines for the same side of the same game are correlated bets —
    # if our model is wrong, all of them lose together. We keep the single
    # highest-edge one to avoid over-exposure on a single game.
    return _dedupe_by_side(picks)


def _side_key(pick: Pick) -> tuple[str, str, str]:
    """Identify the (event, market, side) of a pick, ignoring line/book."""
    sel = pick.selection
    if pick.market == "total":
        # Selection looks like "over 225.0" / "under 225.0"
        side = "over" if sel.lower().startswith("over") else "under"
    elif pick.market == "spread":
        # Selection looks like "Los Angeles Lakers -3.5" — strip trailing line
        parts = sel.rsplit(" ", 1)
        side = parts[0] if len(parts) == 2 else sel
    else:
        # moneyline: selection is the team name
        side = sel
    return (pick.event_id, pick.market, side)


def _dedupe_by_side(picks: list[Pick]) -> list[Pick]:
    """Keep the single highest-edge pick per (event, market, side)."""
    best_per_side: dict[tuple[str, str, str], Pick] = {}
    for p in picks:
        key = _side_key(p)
        if key not in best_per_side or p.edge_percent > best_per_side[key].edge_percent:
            best_per_side[key] = p
    return list(best_per_side.values())
