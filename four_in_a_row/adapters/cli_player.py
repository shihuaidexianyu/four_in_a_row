"""命令行交互玩家。"""

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
    """把终端输入适配成统一的 Move 协议。"""

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
                    # 经典模式只输入列号，最终落点由规则层决定。
                    raw_value = input("Choose a column: ").strip()
                    return Move(player=self.color, column=int(raw_value))

                # 无重力模式下，玩家直接输入 row,col。
                raw_value = input("Choose row,col: ").strip()
                row_text, col_text = (
                    part.strip() for part in raw_value.split(",", maxsplit=1)
                )
                return Move(
                    player=self.color,
                    position=Position(row=int(row_text), col=int(col_text)),
                )
            except (ValueError, IndexError):
                # 这里只兜底输入格式错误，真正的动作合法性由规则层判断。
                print("Invalid input format. Try again.")
