"""Player protocol definitions."""

from __future__ import annotations

from typing import Protocol

from four_in_a_row.core.models import Move, PlayerColor
from four_in_a_row.interface.views import Observation


class Player(Protocol):
    """Player 协议定义了玩家需要实现的接口，支持人类玩家和 AI 智能体的多样化实现。"""

    player_id: str
    color: PlayerColor

    def choose_move(self, observation: Observation) -> Move:
        """Return the next move for the player."""
