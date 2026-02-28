"""基于 JSONL 的对局记录器。"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from four_in_a_row.core.models import GameState, Move, RuleSet
from four_in_a_row.interface.views import Observation
from four_in_a_row.recording import events
from four_in_a_row.recording.schema import (
    serialize_move,
    serialize_ruleset,
    serialize_state,
)


class JsonlRecorder:
    """追加写入事件流，并在结束时输出一份摘要。"""

    def __init__(self, output_dir: str | Path) -> None:
        # 每盘对局生成独立文件，便于后续批量分析和回放。
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.match_id = uuid4().hex
        self.events_path = self.output_dir / f"{self.match_id}.events.jsonl"
        self.summary_path = self.output_dir / f"{self.match_id}.summary.json"
        self._event_index = 0
        self._started_at: str | None = None

    def record_match_started(
        self, rule_set: RuleSet, players: dict, initial_state: GameState
    ) -> None:
        # 开局事件记录规则、玩家信息和初始棋盘。
        timestamp = _timestamp()
        self._started_at = timestamp
        self._emit(
            events.MATCH_STARTED,
            {
                "ruleset": serialize_ruleset(rule_set),
                "players": {
                    color.value: {
                        "player_id": player.player_id,
                        "color": player.color.value,
                    }
                    for color, player in players.items()
                },
                "initial_state": serialize_state(initial_state),
            },
            timestamp=timestamp,
            turn_index=0,
        )

    def record_turn_started(
        self, turn_index: int, player, observation: Observation
    ) -> None:
        # 回合开始时记录观察信息，方便分析当时的可选动作空间。
        self._emit(
            events.TURN_STARTED,
            {
                "observation": {
                    "move_count": observation.move_count,
                    "legal_actions": [
                        serialize_move(move) for move in observation.legal_actions
                    ],
                    "last_move": serialize_move(observation.last_move),
                    "status": observation.status.value,
                }
            },
            turn_index=turn_index,
            player=player,
        )

    def record_move_submitted(
        self,
        turn_index: int,
        player,
        move: Move,
        think_time_ms: int,
    ) -> None:
        # 先记录“玩家提交了什么”，再记录“引擎实际接受了什么”。
        self._emit(
            events.MOVE_SUBMITTED,
            {
                "proposed_move": serialize_move(move),
                "think_time_ms": think_time_ms,
            },
            turn_index=turn_index,
            player=player,
        )

    def record_move_applied(
        self,
        turn_index: int,
        player,
        move: Move | None,
        previous_state: GameState,
        new_state: GameState,
        observation: Observation,
    ) -> None:
        self._emit(
            events.MOVE_APPLIED,
            {
                "accepted_move": serialize_move(move),
                # 保留落子前后两份棋盘快照，单步分析时不必整盘回放。
                "board_before": serialize_state(previous_state)["board_matrix"],
                "board_after": serialize_state(new_state)["board_matrix"],
                "legal_actions_before": [
                    serialize_move(action) for action in observation.legal_actions
                ],
                "status_after": new_state.status.value,
                "winner": new_state.winner.value
                if new_state.winner is not None
                else None,
            },
            turn_index=turn_index,
            player=player,
        )

    def record_match_finished(self, final_state: GameState, turn_index: int) -> None:
        # 结束时同时写事件流终点和摘要文件，兼顾完整性与检索效率。
        finished_at = _timestamp()
        self._emit(
            events.MATCH_FINISHED,
            {
                "result": final_state.status.value,
                "winner": final_state.winner.value
                if final_state.winner is not None
                else None,
                "total_moves": final_state.move_count,
                "final_state": serialize_state(final_state),
            },
            timestamp=finished_at,
            turn_index=turn_index,
        )
        summary = {
            "match_id": self.match_id,
            "started_at": self._started_at,
            "ended_at": finished_at,
            "winner": final_state.winner.value
            if final_state.winner is not None
            else None,
            "result": final_state.status.value,
            "total_moves": final_state.move_count,
            "final_board": serialize_state(final_state)["board_matrix"],
            "event_log_path": str(self.events_path),
        }
        self.summary_path.write_text(
            json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8"
        )

    def _emit(
        self,
        event_type: str,
        payload: dict[str, object],
        *,
        timestamp: str | None = None,
        turn_index: int | None = None,
        player=None,
    ) -> None:
        # 所有事件先拼成统一公共字段，再附加各事件自己的载荷。
        event = {
            "event_id": self._event_index,
            "event_type": event_type,
            "match_id": self.match_id,
            "timestamp": timestamp or _timestamp(),
            "turn_index": turn_index,
            "player_id": player.player_id if player is not None else None,
            "player_color": player.color.value if player is not None else None,
        }
        event.update(payload)
        # JSONL 适合流式追加，也很方便直接喂给 pandas、DuckDB 等工具。
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=True))
            handle.write("\n")
        self._event_index += 1


def _timestamp() -> str:
    # 统一使用 UTC 时间，避免后续跨时区分析时混乱。
    return datetime.now(UTC).isoformat()
