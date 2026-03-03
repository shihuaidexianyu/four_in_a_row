"""纯规则层：负责合法动作、状态迁移和胜负判定。"""

from __future__ import annotations

from game_base.core.errors import InvalidMoveError
from game_base.core.models import (
    Board,
    GameState,
    GameStatus,
    Move,
    PlayerColor,
    Position,
    RuleSet,
    empty_board,
)


def new_game(rule_set: RuleSet) -> GameState:
    # 对局初始化只依赖规则配置，不掺杂任何输入输出逻辑。
    return GameState(
        board=empty_board(rule_set.rows, rule_set.cols),
        next_player=rule_set.first_player,
        move_count=0,
    )


def legal_actions(state: GameState, rule_set: RuleSet) -> list[Move]:
    if state.status is not GameStatus.ONGOING:
        return []

    # 当前项目只支持无重力规则：所有空格都直接是合法动作。
    actions: list[Move] = []
    for row_index, row in enumerate(state.board):
        for col_index, cell in enumerate(row):
            if cell is None:
                actions.append(
                    Move(
                        player=state.next_player,
                        position=Position(row=row_index, col=col_index),
                    )
                )
    return actions


def validate_move(state: GameState, move: Move, rule_set: RuleSet) -> None:
    # 先判断对局阶段和轮次，再判断动作本身是否合法。
    if state.status is not GameStatus.ONGOING:
        raise InvalidMoveError("Cannot play after the match has ended.")
    if move.player is not state.next_player:
        raise InvalidMoveError("It is not this player's turn.")

    if (
        not 0 <= move.position.row < rule_set.rows
        or not 0 <= move.position.col < rule_set.cols
    ):
        raise InvalidMoveError("Position is out of bounds.")
    if state.board[move.position.row][move.position.col] is not None:
        raise InvalidMoveError("Selected position is already occupied.")


def apply_move(state: GameState, move: Move, rule_set: RuleSet) -> GameState:
    validate_move(state, move, rule_set)
    updated_board = _place_piece(state.board, move.position, move.player)

    # 新落下的这一子是唯一可能改变胜负的因素，因此只围绕它检查即可。
    winner = (
        move.player
        if _has_connection(updated_board, move.position, move.player, rule_set.connect_n)
        else None
    )
    if winner is PlayerColor.BLACK:
        status = GameStatus.BLACK_WIN
    elif winner is PlayerColor.WHITE:
        status = GameStatus.WHITE_WIN
    elif _is_full(updated_board):
        status = GameStatus.DRAW
    else:
        status = GameStatus.ONGOING

    return GameState(
        board=updated_board,
        next_player=state.next_player.other(),
        move_count=state.move_count + 1,
        status=status,
        winner=winner,
        last_move=move,
    )


def is_terminal(state: GameState) -> bool:
    return state.status is not GameStatus.ONGOING


def _place_piece(board: Board, position: Position, player: PlayerColor) -> Board:
    # 复制一份棋盘再写入，保持 GameState 不可变。
    board_rows = [list(row) for row in board]
    board_rows[position.row][position.col] = player
    return tuple(tuple(row) for row in board_rows)


def _has_connection(
    board: Board,
    position: Position,
    player: PlayerColor,
    connect_n: int,
) -> bool:
    # 以最后一步为中心，分别检查横、竖、两条对角线。
    directions = ((0, 1), (1, 0), (1, 1), (1, -1))
    for delta_row, delta_col in directions:
        count = 1
        count += _count_direction(board, position, player, delta_row, delta_col)
        count += _count_direction(board, position, player, -delta_row, -delta_col)
        if count >= connect_n:
            return True
    return False


def _count_direction(
    board: Board,
    position: Position,
    player: PlayerColor,
    delta_row: int,
    delta_col: int,
) -> int:
    row = position.row + delta_row
    col = position.col + delta_col
    count = 0
    max_rows = len(board)
    max_cols = len(board[0]) if board else 0

    # 沿着一个方向持续统计同色连续棋子数量，直到越界或颜色中断。
    while 0 <= row < max_rows and 0 <= col < max_cols and board[row][col] is player:
        count += 1
        row += delta_row
        col += delta_col
    return count


def _is_full(board: Board) -> bool:
    # 无空位且无人获胜时即为平局。
    return all(cell is not None for row in board for cell in row)
