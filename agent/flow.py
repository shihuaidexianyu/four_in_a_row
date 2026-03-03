"""把 C++ 风格搜索包装成兼容当前 Player 协议的智能体。"""

from __future__ import annotations

from dataclasses import dataclass, field
from random import Random

from agent.base import SearchParams, SearchResult, winner_from_status
from agent.search import decide_move
from game_base.core.models import GameState, Move, PlayerColor, RuleSet
from game_base.interface.views import Observation


@dataclass(slots=True)
class HeuristicSearchAgent:
    """按旧 C++ 启发式模型工作的搜索玩家。"""

    player_id: str
    color: PlayerColor
    rule_set: RuleSet
    params: SearchParams = field(default_factory=SearchParams)
    seed: int | None = None
    _rng: Random = field(init=False, repr=False)
    _last_result: SearchResult | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = Random(self.seed)

    @property
    def last_result(self) -> SearchResult | None:
        return self._last_result

    def choose_move(self, observation: Observation) -> Move:
        if observation.next_player is not self.color:
            raise RuntimeError("It is not this agent's turn.")
        state = GameState(
            board=observation.board,
            next_player=observation.next_player,
            move_count=observation.move_count,
            status=observation.status,
            winner=winner_from_status(observation.status),
            last_move=observation.last_move,
        )
        self._last_result = decide_move(
            state=state,
            rule_set=self.rule_set,
            params=self.params,
            rng=self._rng,
        )
        return self._last_result.move
