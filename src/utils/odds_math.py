"""
Odds math utilities: American ↔ decimal ↔ implied probability,
edge calculation, Kelly sizing, CLV calculation.

All the core math the pick_agent and track_record_agent depend on.
"""

from __future__ import annotations


def american_to_decimal(american: int) -> float:
    """Convert American odds to decimal.

    >>> american_to_decimal(-110)
    1.909...
    >>> american_to_decimal(+200)
    3.0
    """
    if american >= 0:
        return 1.0 + american / 100.0
    return 1.0 + 100.0 / abs(american)


def decimal_to_american(decimal: float) -> int:
    """Convert decimal odds to American.

    >>> decimal_to_american(2.0)
    100
    >>> decimal_to_american(1.5)
    -200
    """
    if decimal >= 2.0:
        return int(round((decimal - 1.0) * 100))
    return int(round(-100.0 / (decimal - 1.0)))


def decimal_to_implied_prob(decimal: float) -> float:
    """Decimal odds → implied probability (with vig)."""
    return 1.0 / decimal


def implied_prob_to_decimal(prob: float) -> float:
    """Implied probability → decimal odds (zero-vig)."""
    if prob <= 0 or prob >= 1:
        raise ValueError(f"Probability must be in (0, 1), got {prob}")
    return 1.0 / prob


def edge(fair_prob: float, market_decimal: float) -> float:
    """Our edge = fair probability - market implied probability.

    Positive edge means the market is offering odds that imply a lower
    probability than our model believes is true. Publish if >= 0.03.
    """
    market_implied = decimal_to_implied_prob(market_decimal)
    return fair_prob - market_implied


def kelly_fraction(fair_prob: float, decimal_odds: float) -> float:
    """Full-Kelly fraction of bankroll to bet.

    f* = (p * b - q) / b
    where b = decimal_odds - 1, p = fair_prob, q = 1 - p.

    Returns 0 if no edge (never bet negative-EV).
    """
    b = decimal_odds - 1.0
    q = 1.0 - fair_prob
    f = (fair_prob * b - q) / b
    return max(0.0, f)


def quarter_kelly_units(
    fair_prob: float,
    decimal_odds: float,
    max_units: float = 2.0,
) -> float:
    """Quarter-Kelly sizing in units, capped.

    v0 policy: quarter-Kelly × 100 (so 1 unit = 1% of bankroll), capped at 2u.
    Returns 0.0 if no edge.
    """
    f = kelly_fraction(fair_prob, decimal_odds)
    if f <= 0:
        return 0.0
    units = f * 0.25 * 100.0  # quarter-Kelly, expressed as units
    return round(min(units, max_units), 2)


def clv_percent(
    pick_odds_decimal: float,
    closing_odds_decimal: float,
) -> float:
    """Closing Line Value as a percentage.

    CLV% = (pick_decimal / closing_decimal) - 1, expressed as %.
    Positive CLV = we got a better line than the market closed at.

    Example: we pick at 2.00, market closes at 1.90 → CLV = +5.26%.
    """
    return round(((pick_odds_decimal / closing_odds_decimal) - 1.0) * 100.0, 2)


def remove_vig_two_way(odds_a_decimal: float, odds_b_decimal: float) -> tuple[float, float]:
    """Remove the vig from a two-outcome market (ML, over/under).

    Returns (fair_prob_a, fair_prob_b).
    """
    p_a = decimal_to_implied_prob(odds_a_decimal)
    p_b = decimal_to_implied_prob(odds_b_decimal)
    total = p_a + p_b
    return p_a / total, p_b / total


def remove_vig_three_way(
    odds_a_decimal: float,
    odds_draw_decimal: float,
    odds_b_decimal: float,
) -> tuple[float, float, float]:
    """Remove vig from 3-way market (1X2 soccer). Returns (p_a, p_draw, p_b)."""
    p_a = decimal_to_implied_prob(odds_a_decimal)
    p_d = decimal_to_implied_prob(odds_draw_decimal)
    p_b = decimal_to_implied_prob(odds_b_decimal)
    total = p_a + p_d + p_b
    return p_a / total, p_d / total, p_b / total


if __name__ == "__main__":
    # Quick sanity check
    print("Lakers -115 ML, model says fair prob = 0.581")
    dec = american_to_decimal(-115)
    print(f"  Decimal: {dec:.3f}")
    print(f"  Market implied: {decimal_to_implied_prob(dec):.3f}")
    e = edge(0.581, dec)
    print(f"  Edge: {e*100:.2f}%")
    print(f"  Units: {quarter_kelly_units(0.581, dec)}")
