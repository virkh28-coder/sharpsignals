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

EDGE_THRESHOLD = 0.03  # 3% minimum edge to publish


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
    max_units: float = 2.0,
) -> list[Pick]:
    """For each prediction, find best available odds, check edge, size bet.

    games_odds_lookup: map from (event_id, market, selection) to list of GameOdds
    across sportsbooks. We pick the BEST (highest decimal) odds available.
    """
    picks: list[Pick] = []
    now = datetime.now(timezone.utc).isoformat()

    for pred in predictions:
        key = (pred.event_id, pred.market, pred.selection)
        available = games_odds_lookup.get(key, [])
        if not available:
            continue

        # Take the best (highest decimal) odds across books
        best = max(available, key=lambda o: o.odds_decimal)

        edge_val = calc_edge(pred.fair_probability, best.odds_decimal)
        if edge_val < edge_threshold:
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

    return picks
