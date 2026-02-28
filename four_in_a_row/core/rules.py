"""Pure game rules and state transitions."""

from __future__ import annotations

from four_in_a_row.core.errors import InvalidMoveError
from four_in_a_row.core.models import (
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
    return GameState(
        board=empty_board(rule_set.rows, rule_set.cols),
        next_player=rule_set.first_player,
        move_count=0,
    )


def legal_actions(state: GameState, rule_set: RuleSet) -> list[Move]:
    if state.status is not GameStatus.ONGOING:
        return []

    actions: list[Move] = []
    if rule_set.gravity:
        # Gravity mode exposes columns as actions; the landing row is resolved later.
        for col in range(rule_set.cols):
            if _find_drop_row(state.board, col) is not None:
                actions.append(Move(player=state.next_player, column=col))
        return actions

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
    if state.status is not GameStatus.ONGOING:
        raise InvalidMoveError("Cannot play after the match has ended.")
    if move.player is not state.next_player:
        raise InvalidMoveError("It is not this player's turn.")

    if rule_set.gravity:
        if move.column is None or move.position is not None:
            raise InvalidMoveError("Gravity mode requires a column-based move.")
        if not 0 <= move.column < rule_set.cols:
            raise InvalidMoveError("Column is out of bounds.")
        if _find_drop_row(state.board, move.column) is None:
            raise InvalidMoveError("Selected column is full.")
        return

    if move.position is None or move.column is not None:
        raise InvalidMoveError("Coordinate mode requires an explicit board position.")
    if (
        not 0 <= move.position.row < rule_set.rows
        or not 0 <= move.position.col < rule_set.cols
    ):
        raise InvalidMoveError("Position is out of bounds.")
    if state.board[move.position.row][move.position.col] is not None:
        raise InvalidMoveError("Selected position is already occupied.")


def apply_move(state: GameState, move: Move, rule_set: RuleSet) -> GameState:
    validate_move(state, move, rule_set)
    target = _resolve_position(state.board, move, rule_set)
    updated_board = _place_piece(state.board, target, move.player)

    # Only the new stone can create a fresh line, so winner detection stays local.
    winner = (
        move.player
        if _has_connection(updated_board, target, move.player, rule_set.connect_n)
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

    resolved_move = Move(player=move.player, position=target, column=move.column)
    return GameState(
        board=updated_board,
        next_player=state.next_player.other(),
        move_count=state.move_count + 1,
        status=status,
        winner=winner,
        last_move=resolved_move,
    )


def is_terminal(state: GameState) -> bool:
    return state.status is not GameStatus.ONGOING


def _find_drop_row(board: Board, col: int) -> int | None:
    for row_index in range(len(board) - 1, -1, -1):
        if board[row_index][col] is None:
            return row_index
    return None


def _resolve_position(board: Board, move: Move, rule_set: RuleSet) -> Position:
    if rule_set.gravity:
        drop_row = _find_drop_row(board, move.column or 0)
        if drop_row is None:
            raise InvalidMoveError("Selected column is full.")
        return Position(row=drop_row, col=move.column or 0)
    if move.position is None:
        raise InvalidMoveError("Position is required for coordinate mode.")
    return move.position


def _place_piece(board: Board, position: Position, player: PlayerColor) -> Board:
    board_rows = [list(row) for row in board]
    board_rows[position.row][position.col] = player
    return tuple(tuple(row) for row in board_rows)


def _has_connection(
    board: Board,
    position: Position,
    player: PlayerColor,
    connect_n: int,
) -> bool:
    # Treat the latest move as the center and expand along each axis in both directions.
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

    while 0 <= row < max_rows and 0 <= col < max_cols and board[row][col] is player:
        count += 1
        row += delta_row
        col += delta_col
    return count


def _is_full(board: Board) -> bool:
    return all(cell is not None for row in board for cell in row)
