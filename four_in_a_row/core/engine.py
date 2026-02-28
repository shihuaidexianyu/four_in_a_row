"""对局调度层：把玩家、规则和记录器串起来。"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter_ns

from four_in_a_row.core.models import GameState, PlayerColor, RuleSet
from four_in_a_row.core.rules import apply_move, is_terminal, new_game
from four_in_a_row.interface.views import Observation, build_observation
from four_in_a_row.recording.recorder import JsonlRecorder


@dataclass(frozen=True, slots=True)
class MatchResult:
    """一次对局运行后的返回结果。"""

    final_state: GameState
    event_log_path: str | None = None
    summary_path: str | None = None


def run_match(
    black_player,
    white_player,
    rule_set: RuleSet,
    recorder: JsonlRecorder | None = None,
) -> MatchResult:
    # 调度层负责流程控制，不直接实现任何规则细节。
    state = new_game(rule_set)
    players = {
        PlayerColor.BLACK: black_player,
        PlayerColor.WHITE: white_player,
    }

    if recorder is not None:
        recorder.record_match_started(
            rule_set=rule_set,
            players=players,
            initial_state=state,
        )

    turn_index = 0
    while not is_terminal(state):
        current_player = players[state.next_player]
        # 不管是人类玩家还是 AI，看到的都是同一份只读观察。
        observation = build_observation(state, rule_set)
        if recorder is not None:
            recorder.record_turn_started(
                turn_index=turn_index, player=current_player, observation=observation
            )

        # 在调度层统计思考时长，后续可以直接用于行为分析。
        turn_start_ns = perf_counter_ns()
        move = current_player.choose_move(observation)
        think_time_ms = (perf_counter_ns() - turn_start_ns) // 1_000_000

        if recorder is not None:
            recorder.record_move_submitted(
                turn_index=turn_index,
                player=current_player,
                move=move,
                think_time_ms=think_time_ms,
            )

        # 保留旧状态，记录器才能输出完整的前后状态变化。
        previous_state = state
        state = apply_move(state, move, rule_set)

        if recorder is not None:
            recorder.record_move_applied(
                turn_index=turn_index,
                player=current_player,
                move=state.last_move,
                previous_state=previous_state,
                new_state=state,
                observation=observation,
            )

        turn_index += 1

    if recorder is not None:
        recorder.record_match_finished(final_state=state, turn_index=turn_index)

    # 返回最终状态和日志路径，方便上层继续展示、回放或分析。
    return MatchResult(
        final_state=state,
        event_log_path=str(recorder.events_path) if recorder is not None else None,
        summary_path=str(recorder.summary_path) if recorder is not None else None,
    )
