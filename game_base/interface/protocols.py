"""玩家协议定义。"""

from __future__ import annotations

from typing import Protocol

from game_base.core.models import Move, PlayerColor
from game_base.interface.views import Observation


class Player(Protocol):
    """统一玩家接口，供人类适配器和 AI 共用。"""

    player_id: str
    color: PlayerColor

    def choose_move(self, observation: Observation) -> Move:
        """根据当前观察返回下一步动作。"""
