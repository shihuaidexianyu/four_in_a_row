from __future__ import annotations

from pathlib import Path

from four_in_a_row.adapters.cli_player import CLIPlayer
from four_in_a_row.adapters.random_agent import RandomAgent
from four_in_a_row.core.engine import run_match
from four_in_a_row.core.models import PlayerColor, RuleSet, board_to_pretty
from four_in_a_row.recording.recorder import JsonlRecorder


def main() -> None:
    rule_set = RuleSet()
    recorder = JsonlRecorder(Path("match_logs"))
    black_player = CLIPlayer(
        player_id="human-black",
        color=PlayerColor.BLACK,
        rule_set=rule_set,
    )
    white_player = RandomAgent(
        player_id="random-white",
        color=PlayerColor.WHITE,
        seed=7,
    )

    result = run_match(
        black_player=black_player,
        white_player=white_player,
        rule_set=rule_set,
        recorder=recorder,
    )

    print()
    print("Final board:")
    print(board_to_pretty(result.final_state.board))
    print(f"Result: {result.final_state.status.value}")
    print(
        f"Winner: {result.final_state.winner.value if result.final_state.winner else 'None'}"
    )
    print(f"Events: {result.event_log_path}")
    print(f"Summary: {result.summary_path}")


if __name__ == "__main__":
    main()
