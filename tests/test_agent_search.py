from __future__ import annotations

from random import Random

from agent.base import SearchParams
from agent.evaluation import load_patterns
from agent.flow import HeuristicSearchAgent
from agent.search import decide_move
from game_base.core.models import Move, PlayerColor, Position, RuleSet
from game_base.core.rules import apply_move, new_game
from game_base.interface.views import build_observation


def test_feature_table_matches_cpp_count() -> None:
    assert len(load_patterns()) == 731


def test_search_prefers_immediate_winning_move_on_cpp_board() -> None:
    rule_set = RuleSet(rows=4, cols=9, connect_n=4)
    state = new_game(rule_set)
    scripted_moves = (
        Move(player=PlayerColor.BLACK, position=Position(row=0, col=0)),
        Move(player=PlayerColor.WHITE, position=Position(row=1, col=0)),
        Move(player=PlayerColor.BLACK, position=Position(row=0, col=1)),
        Move(player=PlayerColor.WHITE, position=Position(row=1, col=1)),
        Move(player=PlayerColor.BLACK, position=Position(row=0, col=2)),
        Move(player=PlayerColor.WHITE, position=Position(row=1, col=2)),
    )
    for move in scripted_moves:
        state = apply_move(state, move, rule_set)

    result = decide_move(
        state=state,
        rule_set=rule_set,
        params=SearchParams(gamma=1.0, lapse_rate=0.0, noise_std=0.0),
        rng=Random(7),
    )

    assert result.move.position == Position(row=0, col=3)
    assert result.used_lapse is False
    assert result.iterations >= 1


def test_agent_implements_player_protocol_for_cpp_rules() -> None:
    rule_set = RuleSet(rows=4, cols=9, connect_n=4)
    state = new_game(rule_set)
    scripted_moves = (
        Move(player=PlayerColor.BLACK, position=Position(row=0, col=0)),
        Move(player=PlayerColor.WHITE, position=Position(row=1, col=0)),
        Move(player=PlayerColor.BLACK, position=Position(row=0, col=1)),
        Move(player=PlayerColor.WHITE, position=Position(row=1, col=1)),
        Move(player=PlayerColor.BLACK, position=Position(row=0, col=2)),
        Move(player=PlayerColor.WHITE, position=Position(row=1, col=2)),
    )
    for move in scripted_moves:
        state = apply_move(state, move, rule_set)

    agent = HeuristicSearchAgent(
        player_id="cpp-search-black",
        color=PlayerColor.BLACK,
        rule_set=rule_set,
        params=SearchParams(gamma=1.0, lapse_rate=0.0, noise_std=0.0),
        seed=11,
    )
    observation = build_observation(state, rule_set)
    move = agent.choose_move(observation)

    assert move.position == Position(row=0, col=3)
    assert agent.last_result is not None
