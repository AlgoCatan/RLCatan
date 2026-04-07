"""
Module: 9. Game State Manager
Author: Forked
Date: 2026-01-29
Purpose: Implements the action space module for the game state manager component, supporting simulation, state handling, utilities, or developer interaction with the game engine.
"""

from catanatron.models.board import get_edges
from catanatron.models.enums import RESOURCES, Action, ActionType
from catanatron.models.map import BASE_MAP_TEMPLATE, NUM_NODES, LandTile


def _build_actions_array(use_resource_specific_discard: bool):
    discard_entries = (
        [(ActionType.DISCARD, resource) for resource in RESOURCES]
        if use_resource_specific_discard
        else [(ActionType.DISCARD, None)]
    )

    return [
        (ActionType.ROLL, None),
        *[(ActionType.MOVE_ROBBER, tile) for tile in TILE_COORDINATES],
        *discard_entries,
        *[(ActionType.BUILD_ROAD, tuple(sorted(edge))) for edge in get_edges()],
        *[(ActionType.BUILD_SETTLEMENT, node_id) for node_id in range(NUM_NODES)],
        *[(ActionType.BUILD_CITY, node_id) for node_id in range(NUM_NODES)],
        (ActionType.BUY_DEVELOPMENT_CARD, None),
        (ActionType.PLAY_KNIGHT_CARD, None),
        *[
            (ActionType.PLAY_YEAR_OF_PLENTY, (first_card, RESOURCES[j]))
            for i, first_card in enumerate(RESOURCES)
            for j in range(i, len(RESOURCES))
        ],
        *[(ActionType.PLAY_YEAR_OF_PLENTY, (first_card,)) for first_card in RESOURCES],
        (ActionType.PLAY_ROAD_BUILDING, None),
        *[(ActionType.PLAY_MONOPOLY, r) for r in RESOURCES],
        *[
            (ActionType.MARITIME_TRADE, tuple(4 * [i] + [j]))
            for i in RESOURCES
            for j in RESOURCES
            if i != j
        ],
        *[
            (ActionType.MARITIME_TRADE, tuple(3 * [i] + [None, j]))  # type: ignore
            for i in RESOURCES
            for j in RESOURCES
            if i != j
        ],
        *[
            (ActionType.MARITIME_TRADE, tuple(2 * [i] + [None, None, j]))  # type: ignore
            for i in RESOURCES
            for j in RESOURCES
            if i != j
        ],
        (ActionType.END_TURN, None),
    ]


BASE_TOPOLOGY = BASE_MAP_TEMPLATE.topology
TILE_COORDINATES = [x for x, y in BASE_TOPOLOGY.items() if y == LandTile]
ACTIONS_ARRAY = _build_actions_array(use_resource_specific_discard=True)
LEGACY_PPO_ACTIONS_ARRAY = _build_actions_array(use_resource_specific_discard=False)
ACTION_SPACE_SIZE = len(ACTIONS_ARRAY)
LEGACY_PPO_ACTION_SPACE_SIZE = len(LEGACY_PPO_ACTIONS_ARRAY)
ACTION_TYPES = [i for i in ActionType]


def to_action_type_space(action):
    return ACTION_TYPES.index(action.action_type)


def normalize_action(action, *, use_resource_specific_discard: bool = True):
    normalized = action
    if normalized.action_type == ActionType.ROLL:
        return Action(action.color, action.action_type, None)
    if normalized.action_type == ActionType.MOVE_ROBBER:
        return Action(action.color, action.action_type, action.value[0])
    if normalized.action_type == ActionType.BUILD_ROAD:
        return Action(action.color, action.action_type, tuple(sorted(action.value)))
    if normalized.action_type == ActionType.BUY_DEVELOPMENT_CARD:
        return Action(action.color, action.action_type, None)
    if normalized.action_type == ActionType.DISCARD:
        if not use_resource_specific_discard:
            return Action(action.color, action.action_type, None)
        value = normalized.value
        if isinstance(value, (list, tuple)):
            value = value[0]
        return Action(action.color, action.action_type, value)
    return normalized


def _use_resource_specific_discard(action_array) -> bool:
    return len(action_array) != LEGACY_PPO_ACTION_SPACE_SIZE


def to_action_space(action, action_array=ACTIONS_ARRAY):
    normalized = normalize_action(
        action,
        use_resource_specific_discard=_use_resource_specific_discard(action_array),
    )
    return action_array.index((normalized.action_type, normalized.value))


def from_action_space(action_int, playable_actions, action_array=ACTIONS_ARRAY):
    action_type, value = action_array[action_int]
    catan_action = None
    for action in playable_actions:
        normalized = normalize_action(
            action,
            use_resource_specific_discard=_use_resource_specific_discard(action_array),
        )
        if normalized.action_type == action_type and normalized.value == value:
            catan_action = action
            break
    assert catan_action is not None
    return catan_action
