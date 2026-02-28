"""Player protocol definitions."""

from __future__ import annotations

from typing import Protocol

from four_in_a_row.core.models import Move, PlayerColor
from four_in_a_row.interface.views import Observation


class Player(Protocol):
    player_id: str
    color: PlayerColor

    def choose_move(self, observation: Observation) -> Move:
        """Return the next move for the player."""
