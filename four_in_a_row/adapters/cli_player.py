"""Interactive CLI player."""

from __future__ import annotations

from dataclasses import dataclass

from four_in_a_row.core.models import (
    Move,
    PlayerColor,
    Position,
    RuleSet,
    board_to_pretty,
)
from four_in_a_row.interface.views import Observation


@dataclass(slots=True)
class CLIPlayer:
    player_id: str
    color: PlayerColor
    rule_set: RuleSet

    def choose_move(self, observation: Observation) -> Move:
        print()
        print(f"{self.player_id} ({self.color.value}) to move")
        print(board_to_pretty(observation.board))
        if observation.last_move is not None:
            print(f"Last move: {observation.last_move.as_dict()}")

        while True:
            try:
                if self.rule_set.gravity:
                    # Classic mode only needs a column; the engine computes the drop row.
                    raw_value = input("Choose a column: ").strip()
                    return Move(player=self.color, column=int(raw_value))

                # Coordinate mode supports rule variants without gravity.
                raw_value = input("Choose row,col: ").strip()
                row_text, col_text = (
                    part.strip() for part in raw_value.split(",", maxsplit=1)
                )
                return Move(
                    player=self.color,
                    position=Position(row=int(row_text), col=int(col_text)),
                )
            except (ValueError, IndexError):
                print("Invalid input format. Try again.")
