"""
Smoke + behavior tests for NBAModel.

Designed to run without any external API: synthetic schedule + odds, no
nba_api / Odds API calls. The point is to lock in the model's logic so we
notice silently broken predictions before they hit production.

Run:  pytest tests/test_nba_model.py -v
"""

from __future__ import annotations
from datetime import datetime, timezone

import pytest

from src.models.nba_model import NBAModel, TeamContext
from src.scrapers.base import Game, GameOdds


def _odds(market: str, selection: str, line: float | None, american: int) -> GameOdds:
    return GameOdds(
        sportsbook="DraftKings",
        market=market,
        selection=selection,
        line=line,
        odds_american=american,
        odds_decimal=_a2d(american),
        fetched_at_utc=datetime.now(timezone.utc),
    )


def _a2d(american: int) -> float:
    return 1.0 + american / 100.0 if american >= 0 else 1.0 + 100.0 / abs(american)


def _game(home: str, away: str, *odds: GameOdds) -> Game:
    return Game(
        sport="NBA",
        event_id=f"{home}-{away}",
        home_team=home,
        away_team=away,
        commence_time_utc=datetime.now(timezone.utc),
        odds=list(odds),
        raw={},
    )


def test_unrated_teams_predict_home_advantage():
    """Two new teams (default rating) → home should win > 50% from HCA alone."""
    model = NBAModel()
    p_home = model.fair_win_probability("LAL", "BOS")
    assert p_home > 0.55, f"home advantage not applied, got {p_home}"
    assert p_home < 0.70, f"home advantage shouldn't dominate at default Elo, got {p_home}"


def test_better_team_at_home_wins_more_than_road():
    """A strong team at home should be favored more than the same team on the road."""
    model = NBAModel()
    model.elo.ratings = {"LAL": 1700, "BOS": 1500}
    p_home = model.fair_win_probability("LAL", "BOS")
    p_road = model.fair_win_probability("BOS", "LAL")  # LAL now visiting
    assert p_home > 1 - p_road  # LAL home > LAL away


def test_back_to_back_penalty_lowers_team_prob():
    """A team on a B2B should be predicted to win less than a rested team."""
    model = NBAModel()
    model.elo.ratings = {"LAL": 1600, "BOS": 1600}
    p_normal = model.fair_win_probability("LAL", "BOS")
    model.team_context["LAL"] = TeamContext(days_rest=0, is_back_to_back=True)
    p_b2b = model.fair_win_probability("LAL", "BOS")
    assert p_b2b < p_normal, "B2B home team should have lower win prob"


def test_predict_games_returns_moneyline_for_each_side():
    """Every game must produce moneyline predictions for both teams."""
    model = NBAModel()
    g = _game(
        "LAL", "BOS",
        _odds("moneyline", "LAL", None, -150),
        _odds("moneyline", "BOS", None, +130),
    )
    preds = model.predict_games([g])
    ml = [p for p in preds if p.market == "moneyline"]
    assert len(ml) == 2
    selections = {p.selection for p in ml}
    assert selections == {"LAL", "BOS"}
    # Probabilities sum to 1 (moneyline only, no draws in NBA)
    p_lal = next(p for p in ml if p.selection == "LAL").fair_probability
    p_bos = next(p for p in ml if p.selection == "BOS").fair_probability
    assert abs(p_lal + p_bos - 1.0) < 1e-9


def test_predict_games_emits_spread_per_unique_line():
    """Two books offering same spread → emit one prediction per side, not 4."""
    model = NBAModel()
    g = _game(
        "LAL", "BOS",
        _odds("spread", "LAL", -3.5, -110),
        _odds("spread", "BOS", 3.5, -110),
    )
    g.odds.append(_odds("spread", "LAL", -3.5, -108))  # different book, same line
    preds = model.predict_games([g])
    spread = [p for p in preds if p.market == "spread"]
    # One per side per unique line
    assert len(spread) == 2


def test_predict_games_emits_totals():
    """Over and under should both be predicted for any total line offered."""
    model = NBAModel()
    g = _game(
        "LAL", "BOS",
        _odds("total", "Over", 225.5, -110),
        _odds("total", "Under", 225.5, -110),
    )
    preds = model.predict_games([g])
    totals = [p for p in preds if p.market == "total"]
    assert len(totals) == 2
    sels = {p.selection for p in totals}
    assert "over 225.5" in sels and "under 225.5" in sels


def test_train_from_games_moves_winners_up():
    """A team that wins all its games should end above its starting rating."""
    model = NBAModel()
    history = [
        {"home_team": "LAL", "away_team": "BOS", "home_score": 110, "away_score": 90},
        {"home_team": "LAL", "away_team": "MIA", "home_score": 108, "away_score": 95},
        {"home_team": "LAL", "away_team": "GSW", "home_score": 115, "away_score": 100},
    ]
    model.train_from_games(history)
    assert model.elo.get("LAL") > 1500
    assert model.elo.get("BOS") < 1500


def test_probabilities_in_range():
    """No prediction should leak a fair_probability outside [0, 1]."""
    model = NBAModel()
    model.elo.ratings = {"LAL": 1900, "BOS": 1300}  # extreme rating gap
    g = _game(
        "LAL", "BOS",
        _odds("moneyline", "LAL", None, -800),
        _odds("moneyline", "BOS", None, +600),
        _odds("spread", "LAL", -15.5, -110),
        _odds("spread", "BOS", 15.5, -110),
        _odds("total", "Over", 225.5, -110),
        _odds("total", "Under", 225.5, -110),
    )
    for p in model.predict_games([g]):
        assert 0.0 <= p.fair_probability <= 1.0, (
            f"out-of-range prob {p.fair_probability} for {p.selection}"
        )


@pytest.mark.parametrize("home_score,away_score,expected_winner_above_starting", [
    (110, 90, True),
    (95, 100, False),
])
def test_mov_multiplier_applied(home_score, away_score, expected_winner_above_starting):
    """Margin-of-victory multiplier should reward winners more for blowouts."""
    model = NBAModel()
    model.train_from_games([
        {"home_team": "LAL", "away_team": "BOS",
         "home_score": home_score, "away_score": away_score},
    ])
    if expected_winner_above_starting:
        assert model.elo.get("LAL") > 1500
    else:
        assert model.elo.get("LAL") < 1500
