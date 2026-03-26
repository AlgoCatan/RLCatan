from catanatron.action_space import (
    LEGACY_PPO_ACTIONS_ARRAY,
    LEGACY_PPO_ACTION_SPACE_SIZE,
    from_action_space,
    to_action_space,
)
from catanatron.models.board import get_edges
from catanatron.models.enums import Action, ActionType
from catanatron.models.player import Color


def test_roll_actions_share_one_action_space_slot():
    action = Action(Color.BLUE, ActionType.ROLL, (3, 4))

    assert to_action_space(action) == 0


def test_from_action_space_returns_matching_playable_action():
    road = Action(Color.BLUE, ActionType.BUILD_ROAD, get_edges()[0])
    playable_actions = [
        Action(Color.BLUE, ActionType.ROLL, (1, 1)),
        road,
    ]

    assert from_action_space(to_action_space(road), playable_actions) == road


def test_legacy_ppo_action_space_collapses_discards():
    discard = Action(Color.BLUE, ActionType.DISCARD, "WOOD")

    index = to_action_space(discard, LEGACY_PPO_ACTIONS_ARRAY)

    assert LEGACY_PPO_ACTION_SPACE_SIZE == 290
    assert LEGACY_PPO_ACTIONS_ARRAY[index] == (ActionType.DISCARD, None)


def test_legacy_ppo_action_space_keeps_end_turn_in_range():
    assert LEGACY_PPO_ACTIONS_ARRAY[-1] == (ActionType.END_TURN, None)
    assert len(LEGACY_PPO_ACTIONS_ARRAY) == LEGACY_PPO_ACTION_SPACE_SIZE
