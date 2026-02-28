"""结构化对局数据的序列化辅助函数。"""

from __future__ import annotations

from four_in_a_row.core.models import GameState, Move, RuleSet, board_to_matrix


def serialize_move(move: Move | None) -> dict[str, object] | None:
    # 允许传入 None，便于直接处理“上一手为空”的初始场景。
    if move is None:
        return None
    return move.as_dict()


def serialize_ruleset(rule_set: RuleSet) -> dict[str, object]:
    # 规则配置单独展开，方便日志和摘要文件直接消费。
    return {
        "rows": rule_set.rows,
        "cols": rule_set.cols,
        "connect_n": rule_set.connect_n,
        "first_player": rule_set.first_player.value,
        "gravity": rule_set.gravity,
    }


def serialize_state(state: GameState) -> dict[str, object]:
    # 状态导出保持扁平结构，便于落盘、前端读取和后续分析。
    return {
        "board_matrix": board_to_matrix(state.board),
        "next_player": state.next_player.value,
        "move_count": state.move_count,
        "status": state.status.value,
        "winner": state.winner.value if state.winner is not None else None,
        "last_move": serialize_move(state.last_move),
    }
