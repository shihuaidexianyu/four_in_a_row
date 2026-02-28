"""项目对外暴露的核心入口。"""

from four_in_a_row.core.engine import MatchResult, run_match
from four_in_a_row.core.models import GameState, Move, PlayerColor, Position, RuleSet
from four_in_a_row.core.rules import apply_move, legal_actions, new_game
from four_in_a_row.recording.recorder import JsonlRecorder

__all__ = [
    # 这里列出对外公开的稳定 API。
    "GameState",
    "JsonlRecorder",
    "MatchResult",
    "Move",
    "PlayerColor",
    "Position",
    "RuleSet",
    "apply_move",
    "legal_actions",
    "new_game",
    "run_match",
]
