"""暴露给人类和 AI 的只读视图。"""

from __future__ import annotations

from dataclasses import dataclass

from four_in_a_row.core.models import (
    Board,
    GameState,
    GameStatus,
    Move,
    PlayerColor,
    RuleSet,
)
from four_in_a_row.core.rules import legal_actions


@dataclass(frozen=True, slots=True)
class Observation:
    """玩家每回合拿到的统一输入。"""

    board: Board
    next_player: PlayerColor
    legal_actions: tuple[Move, ...]
    move_count: int
    last_move: Move | None
    status: GameStatus


def build_observation(state: GameState, rule_set: RuleSet) -> Observation:
    # 观察对象是状态快照，不应该让玩家直接改动底层 GameState。
    return Observation(
        board=state.board,
        next_player=state.next_player,
        legal_actions=tuple(legal_actions(state, rule_set)),
        move_count=state.move_count,
        last_move=state.last_move,
        status=state.status,
    )
