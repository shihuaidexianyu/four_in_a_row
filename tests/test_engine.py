"""Tests for match orchestration and shared player interface."""

from __future__ import annotations

import unittest
from dataclasses import dataclass, field

from four_in_a_row.core.engine import run_match
from four_in_a_row.core.models import GameStatus, Move, PlayerColor, Position, RuleSet
from four_in_a_row.interface.views import Observation


@dataclass
class ScriptedPlayer:
    player_id: str
    color: PlayerColor
    moves: list[Move]
    seen_observations: list[Observation] = field(default_factory=list)

    def choose_move(self, observation: Observation) -> Move:
        self.seen_observations.append(observation)
        return self.moves.pop(0)


class EngineTestCase(unittest.TestCase):
    def test_run_match_uses_shared_player_protocol(self) -> None:
        rule_set = RuleSet(gravity=False)
        black = ScriptedPlayer(
            player_id="black-script",
            color=PlayerColor.BLACK,
            moves=[
                Move(PlayerColor.BLACK, position=Position(0, 0)),
                Move(PlayerColor.BLACK, position=Position(0, 1)),
                Move(PlayerColor.BLACK, position=Position(0, 2)),
                Move(PlayerColor.BLACK, position=Position(0, 3)),
            ],
        )
        white = ScriptedPlayer(
            player_id="white-script",
            color=PlayerColor.WHITE,
            moves=[
                Move(PlayerColor.WHITE, position=Position(1, 0)),
                Move(PlayerColor.WHITE, position=Position(1, 1)),
                Move(PlayerColor.WHITE, position=Position(1, 2)),
            ],
        )

        result = run_match(black, white, rule_set)

        self.assertEqual(result.final_state.status, GameStatus.BLACK_WIN)
        self.assertEqual(len(black.seen_observations), 4)
        self.assertEqual(len(white.seen_observations), 3)
        self.assertEqual(black.seen_observations[0].next_player, PlayerColor.BLACK)


if __name__ == "__main__":
    unittest.main()
