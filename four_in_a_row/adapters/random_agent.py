"""最简单的基线智能体：从合法动作里随机选一步。"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random

from four_in_a_row.core.models import Move, PlayerColor
from four_in_a_row.interface.views import Observation


@dataclass(slots=True)
class RandomAgent:
    """用于联调和冒烟测试的占位 AI。"""

    player_id: str
    color: PlayerColor
    seed: int | None = None
    _rng: Random = field(init=False, repr=False)

    def __post_init__(self) -> None:
        # 固定 seed 时可以得到可复现的对局序列。
        self._rng = Random(self.seed)

    def choose_move(self, observation: Observation) -> Move:
        if not observation.legal_actions:
            raise RuntimeError("No legal actions available.")
        # 主动依赖 observation.legal_actions，保证它和其他玩家走同一接口。
        return self._rng.choice(list(observation.legal_actions))
