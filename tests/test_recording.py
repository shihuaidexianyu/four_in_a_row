"""Tests for structured match recording."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from four_in_a_row.core.engine import run_match
from four_in_a_row.core.models import Move, PlayerColor, Position, RuleSet
from four_in_a_row.recording.recorder import JsonlRecorder


@dataclass
class ScriptedPlayer:
    player_id: str
    color: PlayerColor
    moves: list[Move]

    def choose_move(self, observation) -> Move:
        return self.moves.pop(0)


class RecordingTestCase(unittest.TestCase):
    def test_jsonl_recorder_writes_events_and_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            recorder = JsonlRecorder(tmp_dir)
            rule_set = RuleSet(gravity=False)
            black = ScriptedPlayer(
                player_id="black",
                color=PlayerColor.BLACK,
                moves=[
                    Move(PlayerColor.BLACK, position=Position(0, 0)),
                    Move(PlayerColor.BLACK, position=Position(0, 1)),
                    Move(PlayerColor.BLACK, position=Position(0, 2)),
                    Move(PlayerColor.BLACK, position=Position(0, 3)),
                ],
            )
            white = ScriptedPlayer(
                player_id="white",
                color=PlayerColor.WHITE,
                moves=[
                    Move(PlayerColor.WHITE, position=Position(1, 0)),
                    Move(PlayerColor.WHITE, position=Position(1, 1)),
                    Move(PlayerColor.WHITE, position=Position(1, 2)),
                ],
            )

            result = run_match(black, white, rule_set, recorder=recorder)

            event_lines = (
                Path(result.event_log_path).read_text(encoding="utf-8").splitlines()
            )
            summary = json.loads(Path(result.summary_path).read_text(encoding="utf-8"))

            self.assertGreaterEqual(len(event_lines), 1)
            event_types = [json.loads(line)["event_type"] for line in event_lines]
            self.assertIn("match_started", event_types)
            self.assertIn("move_applied", event_types)
            self.assertEqual(event_types[-1], "match_finished")
            self.assertEqual(summary["winner"], PlayerColor.BLACK.value)
            self.assertEqual(summary["total_moves"], 7)


if __name__ == "__main__":
    unittest.main()
