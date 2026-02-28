"""Domain-specific errors for the game engine."""


class GameError(Exception):
    """Base class for game-related failures."""


class InvalidMoveError(GameError):
    """Raised when a move cannot be applied to the current state."""
