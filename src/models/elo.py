"""
Base Elo rating implementation. Used as foundation for NBA, NHL, and (with
sport-specific extensions) others.

Elo:
  expected_score(a, b) = 1 / (1 + 10 ** ((b - a) / scale))
  new_rating_a = a + K * (actual_a - expected_a)

Sport-specific subclasses override:
  - SCALE (400 standard; NBA may use 400, soccer ~480)
  - K (update aggressiveness; NBA ~20, NHL ~8, soccer ~20)
  - home_advantage (Elo points added to home team pre-match)
  - margin_of_victory_multiplier (optional: bigger wins move rating more)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EloModel:
    scale: float = 400.0
    k: float = 20.0
    home_advantage: float = 100.0  # Elo points given to home team pre-match
    initial_rating: float = 1500.0
    ratings: dict[str, float] = field(default_factory=dict)

    def get(self, team: str) -> float:
        return self.ratings.setdefault(team, self.initial_rating)

    def expected_score(
        self,
        team_a: str,
        team_b: str,
        a_is_home: bool = False,
    ) -> float:
        """Pre-match: probability team_a wins."""
        rating_a = self.get(team_a)
        rating_b = self.get(team_b)
        if a_is_home:
            rating_a += self.home_advantage
        else:
            rating_b += self.home_advantage
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / self.scale))

    def update(
        self,
        team_a: str,
        team_b: str,
        result_a: float,  # 1.0 win, 0.5 draw, 0.0 loss
        a_is_home: bool = False,
        mov_multiplier: float = 1.0,
    ) -> tuple[float, float]:
        """Update ratings after a game. Returns new (rating_a, rating_b)."""
        expected_a = self.expected_score(team_a, team_b, a_is_home)
        rating_a = self.get(team_a)
        rating_b = self.get(team_b)
        delta = self.k * mov_multiplier * (result_a - expected_a)
        self.ratings[team_a] = rating_a + delta
        self.ratings[team_b] = rating_b - delta
        return self.ratings[team_a], self.ratings[team_b]

    def load_history(self, games: list[dict]) -> None:
        """Replay a list of past games to build ratings from history.

        Each game dict needs: team_a, team_b, result_a, a_is_home, (optional) mov_multiplier.
        """
        for g in games:
            self.update(
                team_a=g["team_a"],
                team_b=g["team_b"],
                result_a=g["result_a"],
                a_is_home=g.get("a_is_home", False),
                mov_multiplier=g.get("mov_multiplier", 1.0),
            )


def mov_multiplier_538(
    point_diff: float,
    elo_diff: float,
    scaling: float = 2.2,
    shrink: float = 0.001,
) -> float:
    """FiveThirtyEight-style margin-of-victory multiplier (for NBA).

    Makes blowouts count more, but autocorrelates with rating gap so a good
    team thrashing a bad team doesn't runaway-boost ratings.
    """
    import math

    return math.log(abs(point_diff) + 1) * (scaling / ((elo_diff * shrink) + scaling))
