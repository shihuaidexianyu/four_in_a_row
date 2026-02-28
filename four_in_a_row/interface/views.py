"""Read-only state views exposed to human and AI players."""

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
    board: Board
    next_player: PlayerColor
    legal_actions: tuple[Move, ...]
    move_count: int
    last_move: Move | None
    status: GameStatus


def build_observation(state: GameState, rule_set: RuleSet) -> Observation:
    return Observation(
        board=state.board,
        next_player=state.next_player,
        legal_actions=tuple(legal_actions(state, rule_set)),
        move_count=state.move_count,
        last_move=state.last_move,
        status=state.status,
    )
