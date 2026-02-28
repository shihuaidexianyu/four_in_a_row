"""Serialization helpers for structured match data."""

from __future__ import annotations

from four_in_a_row.core.models import GameState, Move, RuleSet, board_to_matrix


def serialize_move(move: Move | None) -> dict[str, object] | None:
    if move is None:
        return None
    return move.as_dict()


def serialize_ruleset(rule_set: RuleSet) -> dict[str, object]:
    return {
        "rows": rule_set.rows,
        "cols": rule_set.cols,
        "connect_n": rule_set.connect_n,
        "first_player": rule_set.first_player.value,
        "gravity": rule_set.gravity,
    }


def serialize_state(state: GameState) -> dict[str, object]:
    return {
        "board_matrix": board_to_matrix(state.board),
        "next_player": state.next_player.value,
        "move_count": state.move_count,
        "status": state.status.value,
        "winner": state.winner.value if state.winner is not None else None,
        "last_move": serialize_move(state.last_move),
    }
