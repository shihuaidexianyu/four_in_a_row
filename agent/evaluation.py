"""按旧 C++ `heuristic.cpp` 复现特征解析、评估与候选动作打分。"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from random import Random

from agent.base import (
    BOARD_END,
    FULL_MASK,
    BitBoard,
    BitMask,
    Pattern,
    PlayerColor,
    ScoredAction,
    SearchParams,
    bitmask_to_move,
    center_value_for_bit,
    iter_single_bit_masks,
)
from game_base.core.models import RuleSet

_PATTERN_RE = re.compile(
    r"\{(0x[0-9A-Fa-f]+)ULL,(0x[0-9A-Fa-f]+)ULL,(\d+),w_act,w_pass,delta,(\d+)\}"
)


def evaluate_board(board: BitBoard, params: SearchParams) -> float:
    """按旧 C++ `heuristic::evaluate(board)` 计算黑方视角分值。"""

    player = board.active_player()
    total = 0.0
    center_lookup = center_value_lookup()

    current = 1
    while current != BOARD_END:
        if board.contains(current, player):
            total += params.center_weight * center_lookup[current]
        if board.contains(current, player.other()):
            total -= params.center_weight * center_lookup[current]
        current <<= 1

    for pattern in load_patterns():
        if not pattern_is_active(pattern, board):
            continue
        if pattern_contained(pattern, board, player):
            total += params.w_act[pattern.weight_index]
        elif pattern_contained(pattern, board, player.other()):
            total -= params.w_pass[pattern.weight_index]

    return total if player is PlayerColor.BLACK else -total


def get_pruned_moves(
    board: BitBoard,
    player: PlayerColor,
    self_player: PlayerColor,
    rule_set: RuleSet,
    params: SearchParams,
    rng: Random,
    kept_patterns: tuple[Pattern, ...],
) -> list[ScoredAction]:
    """按旧 C++ `get_pruned_moves` 规则返回剪枝后的候选动作。"""

    candidates = get_moves(
        board=board,
        player=player,
        self_player=self_player,
        rule_set=rule_set,
        params=params,
        rng=rng,
        kept_patterns=kept_patterns,
    )
    if not candidates:
        return []

    cutoff = 1
    while cutoff < len(candidates):
        if abs(candidates[0].value - candidates[cutoff].value) >= params.pruning_thresh:
            break
        cutoff += 1
    return candidates[:cutoff]


def get_moves(
    board: BitBoard,
    player: PlayerColor,
    self_player: PlayerColor,
    rule_set: RuleSet,
    params: SearchParams,
    rng: Random,
    kept_patterns: tuple[Pattern, ...],
) -> list[ScoredAction]:
    """按旧 C++ `heuristic::get_moves` 计算所有合法动作的即时增量。"""

    legal_bitmasks = legal_bitmasks_for_board(board, rule_set)
    if not legal_bitmasks:
        return []

    center_lookup = center_value_lookup()
    c_act = params.c_self if player is self_player else params.c_opp
    c_pass = params.c_opp if player is self_player else params.c_self
    delta_l = 0.0

    for pattern in kept_patterns:
        if not pattern_is_active(pattern, board):
            continue
        if pattern_contained(pattern, board, player):
            delta_l -= c_pass * diff_act_pass(pattern, params)
        elif pattern_contained(pattern, board, player.other()):
            delta_l -= c_act * diff_act_pass(pattern, params)

    candidates: list[ScoredAction] = []
    lookup: dict[BitMask, int] = {}
    for bitmask in legal_bitmasks:
        value = delta_l + params.center_weight * center_lookup[bitmask]
        if params.noise_std > 0:
            value += rng.gauss(0.0, params.noise_std)
        lookup[bitmask] = len(candidates)
        candidates.append(
            ScoredAction(
                move=bitmask_to_move(bitmask, player, rule_set),
                value=value,
                bitmask=bitmask,
            )
        )

    for pattern in kept_patterns:
        if not pattern_is_active(pattern, board):
            continue

        missing_self = missing_pieces(pattern, board, player)
        missing_opp = missing_pieces(pattern, board, player.other())

        if (missing_self & missing_opp) and missing_self.bit_count() == 1:
            index = lookup.get(missing_self)
            if index is not None:
                candidates[index] = replace_scored_action(
                    candidates[index],
                    candidates[index].value + c_pass * params.w_pass[pattern.weight_index],
                )

        if missing_self == 0 and pattern_just_active(pattern, board):
            for bitmask in iter_single_bit_masks(pattern.pieces_empty):
                index = lookup.get(bitmask)
                if index is not None:
                    candidates[index] = replace_scored_action(
                        candidates[index],
                        candidates[index].value
                        - c_pass * params.w_pass[pattern.weight_index],
                    )

        if missing_opp == 0 and pattern_just_active(pattern, board):
            for bitmask in iter_single_bit_masks(pattern.pieces_empty):
                index = lookup.get(bitmask)
                if index is not None:
                    candidates[index] = replace_scored_action(
                        candidates[index],
                        candidates[index].value
                        + c_act * params.w_act[pattern.weight_index],
                    )

    candidates.sort(key=lambda candidate: candidate.value, reverse=True)
    return candidates


def sample_kept_patterns(params: SearchParams, rng: Random) -> tuple[Pattern, ...]:
    """按旧 C++ `remove_features` 逻辑，为整次搜索固定一次实例级 Dropout。"""

    kept: list[Pattern] = []
    for pattern in load_patterns():
        drop_rate = params.delta[pattern.weight_index]
        if rng.random() < drop_rate:
            continue
        kept.append(pattern)
    return tuple(kept)


def legal_bitmasks_for_board(board: BitBoard, rule_set: RuleSet) -> tuple[BitMask, ...]:
    """旧 C++ 模型把所有空格都视为合法手。"""

    return iter_single_bit_masks(FULL_MASK & ~(board.black | board.white))


def pattern_is_active(pattern: Pattern, board: BitBoard) -> bool:
    return board.nempty(pattern.pieces_empty) >= pattern.n


def pattern_just_active(pattern: Pattern, board: BitBoard) -> bool:
    return board.nempty(pattern.pieces_empty) == pattern.n


def pattern_contained(pattern: Pattern, board: BitBoard, player: PlayerColor) -> bool:
    return board.contains(pattern.pieces, player)


def missing_pieces(pattern: Pattern, board: BitBoard, player: PlayerColor) -> BitMask:
    player_bits = board.black if player is PlayerColor.BLACK else board.white
    return pattern.pieces & ~player_bits


def diff_act_pass(pattern: Pattern, params: SearchParams) -> float:
    return params.w_act[pattern.weight_index] - params.w_pass[pattern.weight_index]


def replace_scored_action(candidate: ScoredAction, value: float) -> ScoredAction:
    return ScoredAction(move=candidate.move, value=value, bitmask=candidate.bitmask)


@lru_cache(maxsize=1)
def center_value_lookup() -> dict[BitMask, float]:
    """预计算每个单格位的中心权重。"""

    lookup: dict[BitMask, float] = {}
    current = 1
    while current != BOARD_END:
        lookup[current] = center_value_for_bit(current)
        current <<= 1
    return lookup


@lru_cache(maxsize=1)
def load_patterns() -> tuple[Pattern, ...]:
    """直接解析旧 C++ `features_all.cpp`，避免手抄 731 个模式。"""

    features_path = (
        Path(__file__).resolve().parents[1]
        / "fourinarow"
        / "Model code"
        / "features_all.cpp"
    )
    if not features_path.exists():
        raise FileNotFoundError(f"Missing C++ feature table: {features_path}")

    source = features_path.read_text(encoding="utf-8")
    patterns = tuple(
        Pattern(
            pieces=int(pieces, 16),
            pieces_empty=int(pieces_empty, 16),
            n=int(required_empty),
            weight_index=int(weight_index),
        )
        for pieces, pieces_empty, required_empty, weight_index in _PATTERN_RE.findall(
            source
        )
    )
    if len(patterns) != 731:
        raise ValueError(f"Expected 731 patterns, found {len(patterns)}.")
    return patterns
