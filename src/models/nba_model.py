"""
NBA model — Elo with pace, rest, and home-court adjustments.

Spec: docs/MODEL_V0_SPEC.md → NBA section.

Pipeline:
  1. Train Elo from historical games (load_history) — produces team ratings
  2. predict_games(games_today) → list[ModelPrediction] for moneyline + spread + total
  3. pick_agent filters edge ≥ 3% and Kelly-sizes

Adjustments on top of base Elo:
  - Home advantage:        +100 Elo to home team pre-match (FiveThirtyEight default)
  - Rest days:             ±15 Elo per day differential, capped at ±45
  - Back-to-back penalty:  -25 Elo to a team playing on zero days rest
  - Pace adjustment:       used for totals (over/under), not ML

Why Elo and not gradient boosting for v0:
  Elo gets us 95% of the signal with 5% of the moving parts. We can backtest
  it cleanly, the failure modes are obvious, and "team rating moved from 1610
  to 1622 because they beat a 1580 team" is a sentence we can put in a caption.
  We replace with xgboost in v1 once we have a track record proving the
  methodology works.
"""

from __future__ import annotations
import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from agents.pick_agent.pick_generator import ModelPrediction
from src.models.elo import EloModel, mov_multiplier_538
from src.scrapers.base import Game

log = logging.getLogger(__name__)


# League-average pace (possessions per 48 min). Used as the baseline for the
# totals model. Updated annually from nba_api stats.
LEAGUE_AVG_PACE = 99.5
# Points per possession (league avg). Used to convert pace differential → points.
LEAGUE_PPP = 1.14


@dataclass
class TeamContext:
    """Per-team state used at prediction time. Filled from recent schedule."""

    days_rest: int = 2          # default if we can't compute
    is_back_to_back: bool = False
    pace_estimate: float = LEAGUE_AVG_PACE
    off_rating: float = LEAGUE_PPP * 100  # per 100 possessions
    def_rating: float = LEAGUE_PPP * 100


@dataclass
class NBAModel:
    """NBA Elo with NBA-specific adjustments."""

    elo: EloModel = field(
        default_factory=lambda: EloModel(scale=400.0, k=20.0, home_advantage=100.0)
    )
    rest_advantage_per_day: float = 15.0
    rest_advantage_cap: float = 45.0
    b2b_penalty: float = 25.0
    team_context: dict[str, TeamContext] = field(default_factory=dict)

    # ---------- training ----------

    def train_from_games(self, historical: list[dict]) -> None:
        """Replay historical games to build Elo ratings.

        Each entry needs: home_team, away_team, home_score, away_score.
        We use 538-style margin-of-victory multiplier so blowouts move ratings
        more, but autocorrelated with rating gap to prevent runaway.
        """
        for g in historical:
            home_won = g["home_score"] > g["away_score"]
            point_diff = g["home_score"] - g["away_score"]
            elo_diff = (
                self.elo.get(g["home_team"]) + self.elo.home_advantage
                - self.elo.get(g["away_team"])
            )
            mov = mov_multiplier_538(point_diff, elo_diff if home_won else -elo_diff)
            self.elo.update(
                team_a=g["home_team"],
                team_b=g["away_team"],
                result_a=1.0 if home_won else 0.0,
                a_is_home=True,
                mov_multiplier=mov,
            )
        log.info(f"NBA Elo trained on {len(historical)} games")

    # ---------- prediction ----------

    def fair_win_probability(self, home: str, away: str) -> float:
        """Probability the HOME team wins, with all adjustments applied."""
        rating_home = self.elo.get(home) + self.elo.home_advantage
        rating_away = self.elo.get(away)

        # Rest adjustment
        ctx_home = self.team_context.get(home, TeamContext())
        ctx_away = self.team_context.get(away, TeamContext())
        rest_delta = self._rest_adjustment(ctx_home, ctx_away)
        rating_home += rest_delta

        return 1.0 / (1.0 + 10 ** ((rating_away - rating_home) / self.elo.scale))

    def expected_total(self, home: str, away: str) -> float:
        """Estimated combined points (for totals market).

        E[total] = pace_avg(home, away) * (off_avg + def_avg) / 100
        Where off_avg/def_avg are the two teams' offensive/defensive ratings.
        Falls back to league averages if context not loaded.
        """
        ctx_h = self.team_context.get(home, TeamContext())
        ctx_a = self.team_context.get(away, TeamContext())
        pace = (ctx_h.pace_estimate + ctx_a.pace_estimate) / 2.0
        # Each team's expected scoring = its off_rating vs opponent's def_rating
        team_a_score = pace * (ctx_h.off_rating + ctx_a.def_rating) / 200.0
        team_b_score = pace * (ctx_a.off_rating + ctx_h.def_rating) / 200.0
        return team_a_score + team_b_score

    def predict_games(self, games: list[Game]) -> list[ModelPrediction]:
        """Convert today's games into model predictions across all 3 markets.

        For every game, emit predictions for:
          - moneyline (both sides)
          - spread (matching spreads we have odds for, both sides)
          - total (over/under, matching the line)
        The pick_agent then filters by edge ≥ 3%.
        """
        out: list[ModelPrediction] = []
        for game in games:
            if game.sport != "NBA":
                continue

            p_home = self.fair_win_probability(game.home_team, game.away_team)
            p_away = 1.0 - p_home

            out.extend(self._moneyline_predictions(game, p_home, p_away))
            out.extend(self._spread_predictions(game, p_home))
            out.extend(self._total_predictions(game))

        return out

    # ---------- internals ----------

    def _rest_adjustment(self, home: TeamContext, away: TeamContext) -> float:
        """Elo points to add to home team for rest differential."""
        diff = home.days_rest - away.days_rest
        delta = diff * self.rest_advantage_per_day
        delta = max(-self.rest_advantage_cap, min(self.rest_advantage_cap, delta))
        if home.is_back_to_back:
            delta -= self.b2b_penalty
        if away.is_back_to_back:
            delta += self.b2b_penalty
        return delta

    def _moneyline_predictions(
        self, game: Game, p_home: float, p_away: float
    ) -> list[ModelPrediction]:
        return [
            ModelPrediction(
                sport="NBA",
                event_id=game.event_id,
                event_label=f"{game.away_team} @ {game.home_team}",
                market="moneyline",
                selection=game.home_team,
                fair_probability=p_home,
            ),
            ModelPrediction(
                sport="NBA",
                event_id=game.event_id,
                event_label=f"{game.away_team} @ {game.home_team}",
                market="moneyline",
                selection=game.away_team,
                fair_probability=p_away,
            ),
        ]

    def _spread_predictions(self, game: Game, p_home: float) -> list[ModelPrediction]:
        """For each unique spread line offered, emit both sides.

        Approximation: convert win prob → expected margin via Elo→margin
        regression (NBA-specific: each Elo point ≈ 0.034 points). Then assume
        margin ~ Normal(expected, sigma=12 points) and integrate over each line.
        Sigma=12 is roughly the historical NBA stdev of point margin.
        """
        SIGMA = 12.0
        # Elo → expected margin (home pov). Coefficient calibrated from historical.
        rating_diff = (
            self.elo.get(game.home_team) + self.elo.home_advantage
            - self.elo.get(game.away_team)
        )
        expected_margin_home = rating_diff * 0.034

        seen_lines: set[float] = set()
        out: list[ModelPrediction] = []
        for o in game.odds:
            if o.market != "spread" or o.line is None:
                continue
            if o.line in seen_lines:
                continue
            seen_lines.add(o.line)

            # If the line is +3, the home team needs to win by more than +3
            # for the home -3 side to cash. We compute P(home_margin > -line_for_home)
            # for the home side, and 1 - that for the away side.
            # The line stored is from the side's perspective; we infer side by team.
            if o.selection == game.home_team:
                p_cover = _p_normal_above(-o.line, expected_margin_home, SIGMA)
                team = game.home_team
            else:
                p_cover = 1.0 - _p_normal_above(-(-o.line), expected_margin_home, SIGMA)
                team = game.away_team
            out.append(
                ModelPrediction(
                    sport="NBA",
                    event_id=game.event_id,
                    event_label=f"{game.away_team} @ {game.home_team}",
                    market="spread",
                    selection=team,
                    fair_probability=p_cover,
                )
            )
        return out

    def _total_predictions(self, game: Game) -> list[ModelPrediction]:
        """Over/under predictions for each unique total line offered.

        Approximation: total ~ Normal(expected_total, sigma=18). Sigma=18
        comes from historical NBA combined-points stdev.
        """
        SIGMA = 18.0
        expected = self.expected_total(game.home_team, game.away_team)

        seen_lines: set[float] = set()
        out: list[ModelPrediction] = []
        for o in game.odds:
            if o.market != "total" or o.line is None:
                continue
            if o.line in seen_lines:
                continue
            seen_lines.add(o.line)

            p_over = _p_normal_above(o.line, expected, SIGMA)
            label = f"over {o.line}" if o.selection.lower().startswith("over") else f"under {o.line}"
            # Emit whichever side this odds row represents.
            if o.selection.lower().startswith("over"):
                p = p_over
                label = f"over {o.line}"
            else:
                p = 1.0 - p_over
                label = f"under {o.line}"
            out.append(
                ModelPrediction(
                    sport="NBA",
                    event_id=game.event_id,
                    event_label=f"{game.away_team} @ {game.home_team}",
                    market="total",
                    selection=label,
                    fair_probability=p,
                )
            )
        return out


def _p_normal_above(threshold: float, mean: float, sigma: float) -> float:
    """P(X > threshold) for X ~ Normal(mean, sigma). No scipy dep."""
    z = (threshold - mean) / sigma
    return 1.0 - _phi(z)


def _phi(z: float) -> float:
    """Standard-normal CDF via erf — accurate to ~1e-7."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def load_or_train(model_path: Optional[Path] = None) -> NBAModel:
    """Load a pickled NBAModel from disk, or train a fresh one if missing.

    Training requires `historical` data — pulled by historical_loader. Keeping
    this lazy means a clean clone can scrape today's games without the full
    training set yet (predictions will be uninformative until trained).
    """
    import pickle

    model_path = model_path or Path("data/models/nba_elo.pkl")
    if model_path.exists():
        with open(model_path, "rb") as f:
            log.info(f"Loaded NBA model from {model_path}")
            return pickle.load(f)
    log.warning(f"No model at {model_path} — returning untrained NBAModel")
    return NBAModel()


def save(model: NBAModel, model_path: Optional[Path] = None) -> Path:
    import pickle

    model_path = model_path or Path("data/models/nba_elo.pkl")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    log.info(f"Saved NBA model to {model_path}")
    return model_path
