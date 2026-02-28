"""Core package exports for the four-in-a-row project."""

from four_in_a_row.core.engine import MatchResult, run_match
from four_in_a_row.core.models import GameState, Move, PlayerColor, Position, RuleSet
from four_in_a_row.core.rules import apply_move, legal_actions, new_game
from four_in_a_row.recording.recorder import JsonlRecorder

__all__ = [
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
