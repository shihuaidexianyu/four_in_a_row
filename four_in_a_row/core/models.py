"""Domain models for game rules and state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias


class PlayerColor(StrEnum):
    """Color identifiers used both on the board and in logs."""

    BLACK = "B"
    WHITE = "W"

    def other(self) -> "PlayerColor":
        return PlayerColor.WHITE if self is PlayerColor.BLACK else PlayerColor.BLACK


class GameStatus(StrEnum):
    """Lifecycle states for a match."""

    ONGOING = "ongoing"
    BLACK_WIN = "black_win"
    WHITE_WIN = "white_win"
    DRAW = "draw"


BoardCell: TypeAlias = PlayerColor | None
Board: TypeAlias = tuple[tuple[BoardCell, ...], ...]


@dataclass(frozen=True, slots=True)
class Position:
    row: int
    col: int


@dataclass(frozen=True, slots=True)
class Move:
    """A move can be column-based (gravity) or coordinate-based."""

    player: PlayerColor
    column: int | None = None
    position: Position | None = None

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"player": self.player.value}
        if self.column is not None:
            payload["column"] = self.column
        if self.position is not None:
            payload["position"] = {"row": self.position.row, "col": self.position.col}
        return payload


@dataclass(frozen=True, slots=True)
class RuleSet:
    rows: int = 4
    cols: int = 9
    connect_n: int = 4
    first_player: PlayerColor = PlayerColor.BLACK
    gravity: bool = True

    def __post_init__(self) -> None:
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("Board dimensions must be positive.")
        if self.connect_n <= 1:
            raise ValueError("connect_n must be at least 2.")
        if self.connect_n > max(self.rows, self.cols):
            raise ValueError("connect_n cannot exceed the board dimensions.")


@dataclass(frozen=True, slots=True)
class GameState:
    board: Board
    next_player: PlayerColor
    move_count: int
    status: GameStatus = GameStatus.ONGOING
    winner: PlayerColor | None = None
    last_move: Move | None = None


def empty_board(rows: int, cols: int) -> Board:
    return tuple(tuple(None for _ in range(cols)) for _ in range(rows))


def board_to_matrix(board: Board) -> list[list[str | None]]:
    return [[cell.value if cell is not None else None for cell in row] for row in board]


def board_to_pretty(board: Board) -> str:
    rendered_rows = []
    for row in board:
        rendered_rows.append(
            " ".join(cell.value if cell is not None else "." for cell in row)
        )
    footer = " ".join(str(index) for index in range(len(board[0]) if board else 0))
    if footer:
        rendered_rows.append(footer)
    return "\n".join(rendered_rows)
