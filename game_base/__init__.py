"""项目对外暴露的核心入口。"""

from game_base.core.engine import MatchResult, run_match
from game_base.core.models import GameState, Move, PlayerColor, Position, RuleSet
from game_base.core.rules import apply_move, legal_actions, new_game
from game_base.recording.recorder import JsonlRecorder

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
