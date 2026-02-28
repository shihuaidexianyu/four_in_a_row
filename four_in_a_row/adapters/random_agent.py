"""Simple baseline agent that picks a legal move uniformly at random."""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random

from four_in_a_row.core.models import Move, PlayerColor
from four_in_a_row.interface.views import Observation


@dataclass(slots=True)
class RandomAgent:
    player_id: str
    color: PlayerColor
    seed: int | None = None
    _rng: Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = Random(self.seed)

    def choose_move(self, observation: Observation) -> Move:
        if not observation.legal_actions:
            raise RuntimeError("No legal actions available.")
        return self._rng.choice(list(observation.legal_actions))
