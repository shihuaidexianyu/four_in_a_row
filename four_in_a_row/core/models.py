"""游戏规则和状态使用的数据模型。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias


class PlayerColor(StrEnum):
    """棋盘和日志里共用的执子标识。"""

    BLACK = "B"
    WHITE = "W"

    def other(self) -> "PlayerColor":
        return PlayerColor.WHITE if self is PlayerColor.BLACK else PlayerColor.BLACK


class GameStatus(StrEnum):
    """一盘对局在生命周期中的状态。"""

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
    """一步落子动作，兼容重力模式和坐标模式。"""

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
    """规则配置。默认值对应 README 里的 4x9 四子棋。"""

    rows: int = 4
    cols: int = 9
    connect_n: int = 4
    first_player: PlayerColor = PlayerColor.BLACK
    gravity: bool = True

    def __post_init__(self) -> None:
        # 在初始化时尽早做约束检查，避免后续运行阶段才发现规则非法。
        if self.rows <= 0 or self.cols <= 0:
            raise ValueError("Board dimensions must be positive.")
        if self.connect_n <= 1:
            raise ValueError("connect_n must be at least 2.")
        if self.connect_n > max(self.rows, self.cols):
            raise ValueError("connect_n cannot exceed the board dimensions.")


@dataclass(frozen=True, slots=True)
class GameState:
    """不可变对局状态，便于测试、回放和日志记录。"""

    board: Board
    next_player: PlayerColor
    move_count: int
    status: GameStatus = GameStatus.ONGOING
    winner: PlayerColor | None = None
    last_move: Move | None = None


def empty_board(rows: int, cols: int) -> Board:
    # 用 tuple 嵌套 tuple 表示棋盘，天然不可变，适合做状态快照。
    return tuple(tuple(None for _ in range(cols)) for _ in range(rows))


def board_to_matrix(board: Board) -> list[list[str | None]]:
    # 导出为普通列表，便于 JSON 序列化和前端消费。
    return [[cell.value if cell is not None else None for cell in row] for row in board]


def board_to_pretty(board: Board) -> str:
    # 终端展示时用 "." 表示空位，底部补一行列号方便输入。
    rendered_rows = []
    for row in board:
        rendered_rows.append(
            " ".join(cell.value if cell is not None else "." for cell in row)
        )
    footer = " ".join(str(index) for index in range(len(board[0]) if board else 0))
    if footer:
        rendered_rows.append(footer)
    return "\n".join(rendered_rows)
