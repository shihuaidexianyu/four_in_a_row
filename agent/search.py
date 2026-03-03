"""按旧 C++ `bfs` + `heuristic` 语义复现搜索流程。"""

from __future__ import annotations

from random import Random

from agent.base import (
    BLACK_WINS,
    WHITE_WINS,
    BitBoard,
    ScoredAction,
    SearchNode,
    SearchParams,
    SearchResult,
    bitmask_to_move,
    validate_cpp_rules,
)
from agent.evaluation import evaluate_board, get_pruned_moves, sample_kept_patterns
from game_base.core.models import GameState, PlayerColor, RuleSet


def decide_move(
    state: GameState,
    rule_set: RuleSet,
    params: SearchParams,
    rng: Random,
) -> SearchResult:
    """按旧 C++ `heuristic::makemove_bfs` 选择动作。"""

    validate_cpp_rules(rule_set)
    board = BitBoard.from_state(state, rule_set)
    root = SearchNode(
        board=board,
        val=evaluate_board(board, params),
        player=state.next_player,
        depth=1,
    )

    legal_moves = tuple(
        ScoredAction(
            move=bitmask_to_move(bitmask, state.next_player, rule_set),
            value=0.0,
            bitmask=bitmask,
        )
        for bitmask in _legal_bitmasks(board)
    )
    if not legal_moves:
        raise RuntimeError("No legal actions available.")

    if rng.random() < params.lapse_rate:
        chosen = legal_moves[int(rng.random() * len(legal_moves))]
        return SearchResult(
            move=chosen.move,
            root_value=root.val,
            iterations=0,
            stability_hits=0,
            used_lapse=True,
            dropped_feature_count=0,
            scored_actions=legal_moves,
        )

    kept_patterns = sample_kept_patterns(params, rng)
    dropped_feature_count = 731 - len(kept_patterns)
    self_player = state.next_player

    current = root
    stability_hits = 0
    previous_best = 0
    iterations = 0

    while (
        iterations < params.max_iterations
        and stability_hits < params.stopping_thresh
        and not root.determined()
    ):
        candidates = get_pruned_moves(
            board=current.board,
            player=current.player,
            self_player=self_player,
            rule_set=rule_set,
            params=params,
            rng=rng,
            kept_patterns=kept_patterns,
        )
        current = expand_node(current, candidates)
        current = select_node(root)
        best = best_move(root)
        current_best = best.move_bitmask
        if current_best == previous_best:
            stability_hits += 1
        else:
            stability_hits = 0
        previous_best = current_best
        iterations += 1

    chosen = best_move(root)
    scored_actions = tuple(
        ScoredAction(move=child.move, value=child.val, bitmask=child.move_bitmask)
        for child in root.children
        if child.move is not None
    )
    if chosen.move is None:
        raise RuntimeError("Best root move is missing.")

    return SearchResult(
        move=chosen.move,
        root_value=root.val,
        iterations=iterations,
        stability_hits=stability_hits,
        used_lapse=False,
        dropped_feature_count=dropped_feature_count,
        scored_actions=scored_actions if scored_actions else legal_moves,
    )


def expand_node(node: SearchNode, candidates: list[ScoredAction]) -> SearchNode:
    """按旧 C++ `node::expand` 展开一个叶节点。"""

    if node.children:
        return node

    for candidate in candidates:
        if node.player is PlayerColor.BLACK:
            child_value = node.val + candidate.value
        else:
            child_value = node.val - candidate.value
        child = SearchNode(
            board=node.board.add(candidate.bitmask, node.player),
            val=child_value,
            player=node.player.other(),
            depth=node.depth + 1,
            move_bitmask=candidate.bitmask,
            move=candidate.move,
            parent=node,
        )
        node.children.append(child)

    if node.children:
        recompute_opt(node)
        recompute_pess(node)
        recompute_val(node)
        if node.determined():
            set_best_determined(node)
        if node.best is not None and node.best.determined():
            # `get_val()` 里可能把 best 指向确定子树。为保持与 C++ 类似，
            # 这里不额外改写，直接走正常回传。
            pass
        if node.parent is None:
            return node
        backpropagate(node.parent, node)
    return node


def backpropagate(node: SearchNode, changed: SearchNode) -> None:
    """按旧 C++ `node::backpropagate` 更新祖先链。"""

    if not update_opt(node, changed):
        recompute_opt(node)
    if not update_pess(node, changed):
        recompute_pess(node)
    if not changed.determined() and update_val(node, changed):
        node.best = changed
    else:
        recompute_val(node)
    if node.parent is not None:
        backpropagate(node.parent, node)


def select_node(node: SearchNode) -> SearchNode:
    """按旧 C++ `node::select` 沿 principal variation 下探。"""

    current = node
    while current.best is not None:
        current = current.best
    return current


def best_move(node: SearchNode) -> SearchNode:
    """按旧 C++ `node::bestmove` 返回根节点最佳子节点。"""

    if not node.children:
        raise RuntimeError("Cannot choose a best move from an unexpanded root.")
    if node.determined():
        set_best_determined(node)
        if node.best is None:
            raise RuntimeError("Determined node has no best child.")
        return node.best

    best_child = None
    best_value = -20_000.0 if node.player is PlayerColor.BLACK else 20_000.0
    for child in node.children:
        if node.player is PlayerColor.BLACK:
            if child.val > best_value:
                best_value = child.val
                best_child = child
        else:
            if child.val < best_value:
                best_value = child.val
                best_child = child
    if best_child is None:
        raise RuntimeError("Failed to locate best child.")
    return best_child


def recompute_opt(node: SearchNode) -> None:
    node.opt = WHITE_WINS if node.player is PlayerColor.BLACK else BLACK_WINS
    for child in node.children:
        update_opt(node, child)


def recompute_pess(node: SearchNode) -> None:
    node.pess = WHITE_WINS if node.player is PlayerColor.BLACK else BLACK_WINS
    for child in node.children:
        update_pess(node, child)


def recompute_val(node: SearchNode) -> None:
    node.val = -20_000.0 if node.player is PlayerColor.BLACK else 20_000.0
    node.best = None
    for child in node.children:
        if not child.determined() and update_val(node, child):
            node.best = child
    for child in node.children:
        if child.determined():
            update_val(node, child)


def set_best_determined(node: SearchNode) -> None:
    """按旧 C++ `get_best_determined` 在已确定子树里选一条最优线。"""

    if node.player is PlayerColor.BLACK:
        candidates = [child for child in node.children if child.pess == node.pess]
    else:
        candidates = [child for child in node.children if child.opt == node.opt]
    node.best = candidates[0] if candidates else None


def update_val(node: SearchNode, child: SearchNode) -> bool:
    if node.player is PlayerColor.BLACK and child.val > node.val:
        node.val = child.val
        return True
    if node.player is PlayerColor.WHITE and child.val < node.val:
        node.val = child.val
        return True
    return False


def update_opt(node: SearchNode, child: SearchNode) -> bool:
    if node.player is PlayerColor.BLACK and child.opt > node.opt:
        node.opt = child.opt
        return True
    if node.player is PlayerColor.WHITE and child.opt < node.opt:
        node.opt = child.opt
        return True
    return False


def update_pess(node: SearchNode, child: SearchNode) -> bool:
    if node.player is PlayerColor.BLACK and child.pess > node.pess:
        node.pess = child.pess
        return True
    if node.player is PlayerColor.WHITE and child.pess < node.pess:
        node.pess = child.pess
        return True
    return False


def _legal_bitmasks(board: BitBoard) -> tuple[int, ...]:
    occupied = board.black | board.white
    masks: list[int] = []
    current = 1
    while current < (1 << 36):
        if (occupied & current) == 0:
            masks.append(current)
        current <<= 1
    return tuple(masks)
