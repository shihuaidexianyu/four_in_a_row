"""C++ 四子棋启发式模型的基础数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt

from game_base.core.models import GameState, GameStatus, Move, PlayerColor, Position, RuleSet

BOARD_ROWS = 4
BOARD_WIDTH = 9
BOARD_CELLS = BOARD_ROWS * BOARD_WIDTH
BOARD_END = 1 << BOARD_CELLS
FULL_MASK = BOARD_END - 1
NWEIGHTS = 17

# 旧 C++ `bfs::node` 的终局界限值，保留原语义。
BLACK_WINS = BOARD_CELLS
WHITE_WINS = -BOARD_CELLS

# 旧 C++ 在节点值里对终局使用更大的固定分值。
BLACK_WIN_VALUE = 10_000.0
WHITE_WIN_VALUE = -10_000.0
DRAW_VALUE = 0.0

BitMask = int


@dataclass(frozen=True, slots=True)
class SearchParams:
    """按旧 C++ `heuristic` 的参数布局定义。"""

    stopping_thresh: int = 7
    pruning_thresh: float = 5.0
    gamma: float = 0.01
    lapse_rate: float = 0.01
    opp_scale: float = 1.0
    exploration_constant: float = 1.0
    center_weight: float = 1.0
    w_act: tuple[float, ...] = (
        0.8,
        0.2,
        3.5,
        6.0,
        0.8,
        0.2,
        3.5,
        6.0,
        0.8,
        0.2,
        3.5,
        6.0,
        0.8,
        0.2,
        3.5,
        6.0,
        0.0,
    )
    w_pass: tuple[float, ...] = (
        0.8,
        0.2,
        3.5,
        6.0,
        0.8,
        0.2,
        3.5,
        6.0,
        0.8,
        0.2,
        3.5,
        6.0,
        0.8,
        0.2,
        3.5,
        6.0,
        0.0,
    )
    delta: tuple[float, ...] = (
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
        0.2,
    )
    noise_std: float = 1.0

    def __post_init__(self) -> None:
        if self.stopping_thresh < 0:
            raise ValueError("stopping_thresh must be non-negative.")
        if self.pruning_thresh < 0:
            raise ValueError("pruning_thresh must be non-negative.")
        if not 0 < self.gamma <= 1:
            raise ValueError("gamma must be in (0, 1].")
        if not 0 <= self.lapse_rate <= 1:
            raise ValueError("lapse_rate must be in [0, 1].")
        if self.opp_scale < 0:
            raise ValueError("opp_scale must be non-negative.")
        if self.noise_std < 0:
            raise ValueError("noise_std must be non-negative.")
        if len(self.w_act) != NWEIGHTS:
            raise ValueError(f"w_act must contain {NWEIGHTS} values.")
        if len(self.w_pass) != NWEIGHTS:
            raise ValueError(f"w_pass must contain {NWEIGHTS} values.")
        if len(self.delta) != NWEIGHTS:
            raise ValueError(f"delta must contain {NWEIGHTS} values.")
        for drop_rate in self.delta:
            if not 0 <= drop_rate <= 1:
                raise ValueError("All delta values must be in [0, 1].")

    @property
    def c_self(self) -> float:
        return 2.0 * self.opp_scale / (1.0 + self.opp_scale)

    @property
    def c_opp(self) -> float:
        return 2.0 / (1.0 + self.opp_scale)

    @property
    def max_iterations(self) -> int:
        # 对齐 `heuristic.cpp` 当前主实现：用固定迭代上限，而不是几何分布抽样。
        return int(1.0 / self.gamma) + 1


@dataclass(frozen=True, slots=True)
class Pattern:
    """与旧 C++ `pattern` 对应的单个模式实例。"""

    pieces: BitMask
    pieces_empty: BitMask
    n: int
    weight_index: int


@dataclass(frozen=True, slots=True)
class ScoredAction:
    """一次候选动作的即时启发式增量。"""

    move: Move
    value: float
    bitmask: BitMask


@dataclass(frozen=True, slots=True)
class SearchResult:
    """一次搜索决策的完整输出。"""

    move: Move
    root_value: float
    iterations: int
    stability_hits: int
    used_lapse: bool
    dropped_feature_count: int
    scored_actions: tuple[ScoredAction, ...]


@dataclass(frozen=True, slots=True)
class BitBoard:
    """4x9 无重力棋盘的位板表示，和旧 C++ `board` 对齐。"""

    black: BitMask = 0
    white: BitMask = 0

    @classmethod
    def from_state(cls, state: GameState, rule_set: RuleSet) -> "BitBoard":
        validate_cpp_rules(rule_set)
        black = 0
        white = 0
        for row_index, row in enumerate(state.board):
            for col_index, cell in enumerate(row):
                if cell is None:
                    continue
                bitmask = position_to_bitmask(row_index, col_index)
                if cell is PlayerColor.BLACK:
                    black |= bitmask
                else:
                    white |= bitmask
        return cls(black=black, white=white)

    def contains(self, bitmask: BitMask, player: PlayerColor) -> bool:
        player_bits = self.black if player is PlayerColor.BLACK else self.white
        return (bitmask & ~player_bits) == 0

    def isempty(self, bitmask: BitMask = FULL_MASK) -> bool:
        return (bitmask & self.black) == 0 and (bitmask & self.white) == 0

    def nempty(self, bitmask: BitMask) -> int:
        occupied = self.black | self.white
        return (bitmask & ~occupied).bit_count()

    def num_pieces(self) -> int:
        return (self.black | self.white).bit_count()

    def active_player(self) -> PlayerColor:
        return PlayerColor.WHITE if self.num_pieces() % 2 else PlayerColor.BLACK

    def is_full(self) -> bool:
        return (self.black | self.white) == FULL_MASK

    def black_has_won(self) -> bool:
        return is_win(self.black)

    def white_has_won(self) -> bool:
        return is_win(self.white)

    def player_has_won(self, player: PlayerColor) -> bool:
        return self.black_has_won() if player is PlayerColor.BLACK else self.white_has_won()

    def game_has_ended(self) -> bool:
        return self.black_has_won() or self.white_has_won() or self.is_full()

    def add(self, bitmask: BitMask, player: PlayerColor) -> "BitBoard":
        if not self.isempty(bitmask):
            raise ValueError("Bitmask is already occupied.")
        if player is PlayerColor.BLACK:
            return BitBoard(black=self.black | bitmask, white=self.white)
        return BitBoard(black=self.black, white=self.white | bitmask)


@dataclass(slots=True)
class SearchNode:
    """按旧 C++ `bfs::node` 语义保存搜索树节点。"""

    board: BitBoard
    val: float
    player: PlayerColor
    depth: int
    move_bitmask: BitMask = 0
    move: Move | None = None
    parent: "SearchNode | None" = None
    children: list["SearchNode"] = field(default_factory=list)
    best: "SearchNode | None" = None
    opt: int = field(init=False)
    pess: int = field(init=False)

    def __post_init__(self) -> None:
        if self.board.black_has_won():
            terminal = BLACK_WINS - self.depth
            self.opt = terminal
            self.pess = terminal
            self.val = BLACK_WIN_VALUE
            return
        if self.board.white_has_won():
            terminal = WHITE_WINS + self.depth
            self.opt = terminal
            self.pess = terminal
            self.val = WHITE_WIN_VALUE
            return
        if self.board.is_full():
            self.opt = 0
            self.pess = 0
            self.val = DRAW_VALUE
            return
        self.pess = WHITE_WINS + self.depth + 1
        self.opt = BLACK_WINS - self.depth - 1

    def determined(self) -> bool:
        return self.opt == self.pess


def validate_cpp_rules(rule_set: RuleSet) -> None:
    """旧 C++ 模型只支持 4x9、四连。"""

    if rule_set.rows != BOARD_ROWS or rule_set.cols != BOARD_WIDTH:
        raise ValueError("C++ heuristic replication requires a 4x9 board.")
    if rule_set.connect_n != 4:
        raise ValueError("C++ heuristic replication requires connect_n=4.")


def bitmask_to_move(bitmask: BitMask, player: PlayerColor, rule_set: RuleSet) -> Move:
    validate_cpp_rules(rule_set)
    if bitmask <= 0 or bitmask >= BOARD_END or bitmask.bit_count() != 1:
        raise ValueError("bitmask_to_move requires a single in-range bit.")
    bit_index = bitmask.bit_length() - 1
    row = bit_index // BOARD_WIDTH
    col = bit_index % BOARD_WIDTH
    return Move(player=player, position=Position(row=row, col=col))


def position_to_bitmask(row: int, col: int) -> BitMask:
    if not (0 <= row < BOARD_ROWS and 0 <= col < BOARD_WIDTH):
        raise ValueError("Position is out of range for the 4x9 C++ board.")
    return 1 << (row * BOARD_WIDTH + col)


def iter_single_bit_masks(mask: BitMask) -> tuple[BitMask, ...]:
    """按位展开一个掩码，顺序与 C++ `for(m=1; m!=boardend; m<<=1)` 一致。"""

    bits: list[BitMask] = []
    current = 1
    while current != BOARD_END:
        if mask & current:
            bits.append(current)
        current <<= 1
    return tuple(bits)


def center_value_for_bit(bitmask: BitMask) -> float:
    """复现旧 C++ 的中心距离加权。"""

    if bitmask <= 0 or bitmask >= BOARD_END or bitmask.bit_count() != 1:
        raise ValueError("center_value_for_bit requires a single in-range bit.")
    bit_index = bitmask.bit_length() - 1
    row = bit_index // BOARD_WIDTH
    col = bit_index % BOARD_WIDTH
    return 1.0 / sqrt((row - 1.5) ** 2 + (col - 4.0) ** 2)


def winner_from_status(status: GameStatus) -> PlayerColor | None:
    if status is GameStatus.BLACK_WIN:
        return PlayerColor.BLACK
    if status is GameStatus.WHITE_WIN:
        return PlayerColor.WHITE
    return None


def is_win(pieces: BitMask) -> bool:
    """按旧 C++ 的位运算方式判断四连。"""

    return bool(
        pieces
        & (pieces >> BOARD_WIDTH)
        & (pieces >> (2 * BOARD_WIDTH))
        & (pieces >> (3 * BOARD_WIDTH))
    ) or bool(
        pieces
        & (pieces >> (BOARD_WIDTH + 1))
        & (pieces >> (2 * BOARD_WIDTH + 2))
        & (pieces >> (3 * BOARD_WIDTH + 3))
    ) or bool(
        pieces
        & (pieces >> (BOARD_WIDTH - 1))
        & (pieces >> (2 * BOARD_WIDTH - 2))
        & (pieces >> (3 * BOARD_WIDTH - 3))
        & 0x0000000000001F8
    ) or bool(
        pieces
        & (pieces >> 1)
        & (pieces >> 2)
        & (pieces >> 3)
        & 0x0000001F8FC7E3F
    )
