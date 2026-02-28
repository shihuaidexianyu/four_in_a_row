"""Tests for pure rule evaluation."""

from __future__ import annotations

import unittest

from four_in_a_row.core.errors import InvalidMoveError
from four_in_a_row.core.models import GameStatus, Move, PlayerColor, Position, RuleSet
from four_in_a_row.core.rules import apply_move, legal_actions, new_game


class RulesTestCase(unittest.TestCase):
    def test_horizontal_win_in_coordinate_mode(self) -> None:
        rule_set = RuleSet(gravity=False)
        state = new_game(rule_set)
        moves = [
            Move(PlayerColor.BLACK, position=Position(0, 0)),
            Move(PlayerColor.WHITE, position=Position(1, 0)),
            Move(PlayerColor.BLACK, position=Position(0, 1)),
            Move(PlayerColor.WHITE, position=Position(1, 1)),
            Move(PlayerColor.BLACK, position=Position(0, 2)),
            Move(PlayerColor.WHITE, position=Position(1, 2)),
            Move(PlayerColor.BLACK, position=Position(0, 3)),
        ]

        for move in moves:
            state = apply_move(state, move, rule_set)

        self.assertEqual(state.status, GameStatus.BLACK_WIN)
        self.assertEqual(state.winner, PlayerColor.BLACK)

    def test_vertical_win_in_gravity_mode(self) -> None:
        rule_set = RuleSet(gravity=True)
        state = new_game(rule_set)
        moves = [
            Move(PlayerColor.BLACK, column=0),
            Move(PlayerColor.WHITE, column=1),
            Move(PlayerColor.BLACK, column=0),
            Move(PlayerColor.WHITE, column=1),
            Move(PlayerColor.BLACK, column=0),
            Move(PlayerColor.WHITE, column=1),
            Move(PlayerColor.BLACK, column=0),
        ]

        for move in moves:
            state = apply_move(state, move, rule_set)

        self.assertEqual(state.status, GameStatus.BLACK_WIN)
        self.assertEqual(state.winner, PlayerColor.BLACK)

    def test_main_diagonal_win(self) -> None:
        rule_set = RuleSet(gravity=False)
        state = new_game(rule_set)
        moves = [
            Move(PlayerColor.BLACK, position=Position(0, 0)),
            Move(PlayerColor.WHITE, position=Position(0, 1)),
            Move(PlayerColor.BLACK, position=Position(1, 1)),
            Move(PlayerColor.WHITE, position=Position(0, 2)),
            Move(PlayerColor.BLACK, position=Position(2, 2)),
            Move(PlayerColor.WHITE, position=Position(0, 3)),
            Move(PlayerColor.BLACK, position=Position(3, 3)),
        ]

        for move in moves:
            state = apply_move(state, move, rule_set)

        self.assertEqual(state.status, GameStatus.BLACK_WIN)

    def test_anti_diagonal_win(self) -> None:
        rule_set = RuleSet(gravity=False)
        state = new_game(rule_set)
        moves = [
            Move(PlayerColor.BLACK, position=Position(0, 3)),
            Move(PlayerColor.WHITE, position=Position(0, 0)),
            Move(PlayerColor.BLACK, position=Position(1, 2)),
            Move(PlayerColor.WHITE, position=Position(1, 0)),
            Move(PlayerColor.BLACK, position=Position(2, 1)),
            Move(PlayerColor.WHITE, position=Position(2, 0)),
            Move(PlayerColor.BLACK, position=Position(3, 0)),
        ]

        for move in moves:
            state = apply_move(state, move, rule_set)

        self.assertEqual(state.status, GameStatus.BLACK_WIN)

    def test_draw_when_board_is_full(self) -> None:
        rule_set = RuleSet(rows=2, cols=3, connect_n=3, gravity=False)
        state = new_game(rule_set)
        moves = [
            Move(PlayerColor.BLACK, position=Position(0, 0)),
            Move(PlayerColor.WHITE, position=Position(0, 1)),
            Move(PlayerColor.BLACK, position=Position(0, 2)),
            Move(PlayerColor.WHITE, position=Position(1, 1)),
            Move(PlayerColor.BLACK, position=Position(1, 0)),
            Move(PlayerColor.WHITE, position=Position(1, 2)),
        ]

        for move in moves:
            state = apply_move(state, move, rule_set)

        self.assertEqual(state.status, GameStatus.DRAW)

    def test_invalid_out_of_bounds_move(self) -> None:
        rule_set = RuleSet(gravity=False)
        state = new_game(rule_set)

        with self.assertRaises(InvalidMoveError):
            apply_move(
                state, Move(PlayerColor.BLACK, position=Position(10, 0)), rule_set
            )

    def test_invalid_move_on_occupied_space(self) -> None:
        rule_set = RuleSet(gravity=False)
        state = new_game(rule_set)
        state = apply_move(
            state, Move(PlayerColor.BLACK, position=Position(0, 0)), rule_set
        )

        with self.assertRaises(InvalidMoveError):
            apply_move(
                state, Move(PlayerColor.WHITE, position=Position(0, 0)), rule_set
            )

    def test_invalid_move_for_wrong_player(self) -> None:
        rule_set = RuleSet(gravity=False)
        state = new_game(rule_set)

        with self.assertRaises(InvalidMoveError):
            apply_move(
                state, Move(PlayerColor.WHITE, position=Position(0, 0)), rule_set
            )

    def test_invalid_move_after_terminal_state(self) -> None:
        rule_set = RuleSet(rows=1, cols=2, connect_n=2, gravity=False)
        state = new_game(rule_set)
        state = apply_move(
            state, Move(PlayerColor.BLACK, position=Position(0, 0)), rule_set
        )
        state = apply_move(
            state, Move(PlayerColor.WHITE, position=Position(0, 1)), rule_set
        )

        with self.assertRaises(InvalidMoveError):
            apply_move(
                state, Move(PlayerColor.BLACK, position=Position(0, 0)), rule_set
            )

    def test_gravity_and_coordinate_modes_expose_different_actions(self) -> None:
        gravity_state = new_game(RuleSet(gravity=True))
        coordinate_state = new_game(RuleSet(gravity=False))

        gravity_actions = legal_actions(gravity_state, RuleSet(gravity=True))
        coordinate_actions = legal_actions(coordinate_state, RuleSet(gravity=False))

        self.assertTrue(all(move.column is not None for move in gravity_actions))
        self.assertTrue(all(move.position is not None for move in coordinate_actions))


if __name__ == "__main__":
    unittest.main()
