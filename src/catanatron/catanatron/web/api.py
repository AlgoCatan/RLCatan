"""
Module: 8. Backend API Server
Author: Forked, modified by Sunny Yao
Date: 2026-03-19
Purpose: Exposes the backend HTTP API for game creation, gameplay actions,
analysis requests, bot discovery, and explanation-related endpoints.
"""

import os
import json
import logging
import traceback
from typing import List
from functools import lru_cache
from pathlib import Path

from flask import Response, Blueprint, jsonify, abort, request

from catanatron.cli.accumulators import ExplanationAccumulator
from catanatron.explanations.explanation_service import (
    ExplanationService,
    GeminiLLM,
    LLMQuotaExceededError,
)
from catanatron.web.models import db, upsert_game_state, get_game_state, UserStart
from catanatron.web.audit import log_game_start
from catanatron.web.mcts_analysis import GameAnalyzer
from catanatron.json import GameEncoder, action_from_json
from catanatron.models.player import Color, Player, RandomPlayer
from catanatron.models.map import build_map
from catanatron.game import Game

from catanatron.players.minimax_placement import AlphaBetaPlacementPlayer
from catanatron.players.value import ValueFunctionPlayer
from catanatron.players.minimax import AlphaBetaPlayer, SameTurnAlphaBetaPlayer
from catanatron.players.search import VictoryPointPlayer
from catanatron.players.mcts import MCTSPlayer
from catanatron.players.playouts import GreedyPlayoutsPlayer
from catanatron.players.weighted_random import WeightedRandomPlayer
from catanatron.players.placement import PlacementPlayer
from werkzeug.exceptions import HTTPException

bp = Blueprint("api", __name__, url_prefix="/api")
VALID_MAP_TEMPLATES = {"BASE", "MINI", "TOURNAMENT"}

# Per-game explanation state (keyed by game_id) to support concurrent users
# Limit to 100 games in memory to prevent memory leaks from long-running servers
EXPLANATION_STATE = {}  # {game_id: {"accumulator": ..., "service": ...}}
MAX_EXPLANATION_STATES = 100


@lru_cache(maxsize=1)
def _load_league_bots_by_name() -> dict[str, dict]:
    """
    Loads the league json once and returns a mapping:
      bot_name -> bot_record
    """
    bots_path = os.environ.get("BOTS_JSON_PATH")
    if not bots_path:
        return {}

    data = json.loads(Path(bots_path).read_text(encoding="utf-8"))
    return {b["name"]: b for b in data}


def _resolve_model_path(raw_path: str) -> Path:
    p = Path(raw_path)

    # If this is an HPC absolute path (e.g., /nfs/.../rlcatan/...), remap into the container
    if p.is_absolute() and "rlcatan" in p.parts:
        idx = p.parts.index("rlcatan")
        p = Path("/app").joinpath(*p.parts[idx:])

    # If path is relative, treat it as relative to /app
    if not p.is_absolute():
        p = Path("/app") / p

    return p


def _prune_explanation_state():
    """Remove oldest explanation states if count exceeds limit."""
    if len(EXPLANATION_STATE) > MAX_EXPLANATION_STATES:
        # Keep the MAX_EXPLANATION_STATES most recent by removing oldest
        to_remove = len(EXPLANATION_STATE) - MAX_EXPLANATION_STATES
        for _ in range(to_remove):
            oldest_key = next(iter(EXPLANATION_STATE))
            del EXPLANATION_STATE[oldest_key]


def player_factory(player_key):
    key, color = player_key

    player = None
    if player_key[0] == "CATANATRON":
        player = AlphaBetaPlayer(color, 2, True)

    elif player_key[0] == "FINAL_BOSS":
        player = AlphaBetaPlacementPlayer(color, 3, True)

    elif player_key[0] == "VALUE_FUNCTION":
        player = ValueFunctionPlayer(color, is_bot=True)

    elif player_key[0] == "MCTS_PLAYER":
        player = MCTSPlayer(color, num_simulations=100)

    elif player_key[0] == "GREEDY_PLAYER":
        player = GreedyPlayoutsPlayer(color, num_playouts=50)

    elif player_key[0] == "VP_PLAYER":
        player = VictoryPointPlayer(color)

    elif player_key[0] == "PLACEMENT_PLAYER":
        player = PlacementPlayer(color)

    elif player_key[0] in {"WEIGHTED_RANDOM", "WEIGHTED_RANDOM_PLAYER"}:
        player = WeightedRandomPlayer(color)

    elif player_key[0] == "RANDOM":
        player = RandomPlayer(color)

    elif player_key[0] == "HUMAN":
        player = ValueFunctionPlayer(color, is_bot=False)

    elif player_key[0] in {"PPO_PLAYER", "PPOP"}:
        from catanatron.players.ppo_player import PPOPlayer

        player = PPOPlayer(color=color, device="cpu", deterministic=True)

    # load bots by name from league.json (Their keys are expected to be in the format "BOT:bot_name")
    elif isinstance(key, str) and key.startswith("BOT:"):
        from catanatron.players.ppo_player import PPOPlayer

        bot_name = key.split(":", 1)[1]
        bots = _load_league_bots_by_name()
        bot = bots.get(bot_name)

        if bot is None:
            abort(400, description=f"Unknown bot '{bot_name}'")

        raw_path = bot.get("path")

        if not raw_path:
            abort(400, description=f"Bot '{bot_name}' has no model path")

        model_path = _resolve_model_path(raw_path)

        player = PPOPlayer(
            color=color, model_path=str(model_path), device="cpu", deterministic=True
        )

    if player is None:
        raise ValueError(f"Invalid player key: {key}")

    player.bot_name = key
    return player


@bp.route("/games", methods=("POST",))
def post_game_endpoint():
    global EXPLANATION_STATE

    if not request.is_json or request.json is None or "players" not in request.json:
        abort(400, description="Missing or invalid JSON body: 'players' key required")

    player_keys = request.json["players"]
    if not isinstance(player_keys, list) or not 2 <= len(player_keys) <= 4:
        abort(400, description="'players' must be a list with 2 to 4 entries")

    map_template = request.json.get("map_template", "BASE")
    if map_template not in VALID_MAP_TEMPLATES:
        abort(
            400,
            description="'map_template' must be one of BASE, MINI, or TOURNAMENT",
        )

    discard_limit = request.json.get("discard_limit", 7)
    if not isinstance(discard_limit, int) or not 5 <= discard_limit <= 20:
        abort(400, description="'discard_limit' must be an integer between 5 and 20")

    vps_to_win = request.json.get("vps_to_win", 10)
    if not isinstance(vps_to_win, int) or not 3 <= vps_to_win <= 20:
        abort(400, description="'vps_to_win' must be an integer between 3 and 20")

    friendly_robber = request.json.get("friendly_robber", False)
    if not isinstance(friendly_robber, bool):
        abort(400, description="'friendly_robber' must be a boolean")

    familiarity = request.json.get("familiarity", "MEDIUM")
    if familiarity not in {"HIGH", "MEDIUM", "LOW"}:
        abort(400, description="'familiarity' must be one of HIGH, MEDIUM, or LOW")

    players = list(map(player_factory, zip(player_keys, Color)))
    catan_map = build_map(map_template)

    game = Game(
        players=players,
        discard_limit=discard_limit,
        friendly_robber=friendly_robber,
        vps_to_win=vps_to_win,
        catan_map=catan_map,
    )
    # Create explanation state for this game
    _prune_explanation_state()
    accumulator = ExplanationAccumulator(recent_action_count=5)
    service = ExplanationService(accumulator, GeminiLLM(), familiarity)
    EXPLANATION_STATE[game.id] = {
        "accumulator": accumulator,
        "service": service,
        "familiarity": familiarity,
    }
    upsert_game_state(game)
    return jsonify({"game_id": game.id})


@bp.route("/analytics/start", methods=("POST",))
def post_start_analytics_endpoint():
    logged = log_game_start(request)
    return jsonify({"logged": logged}), (200 if logged else 500)


@bp.route("/admin/user-starts", methods=("GET",))
def get_user_starts_endpoint():
    try:
        limit = int(request.args.get("limit", 50))
    except ValueError:
        abort(400, description="'limit' must be an integer")

    limit = max(1, min(limit, 200))
    rows = (
        db.session.query(UserStart)
        .order_by(UserStart.timestamp.desc())
        .limit(limit)
        .all()
    )
    payload = [
        {
            "id": row.id,
            "ip": row.ip,
            "timestamp": row.timestamp.isoformat(),
        }
        for row in rows
    ]
    return jsonify(payload)


@bp.route("/games/<string:game_id>/states/<string:state_index>", methods=("GET",))
def get_game_endpoint(game_id, state_index):
    parsed_state_index = _parse_state_index(state_index)
    game = get_game_state(game_id, parsed_state_index)
    if game is None:
        abort(404, description="Resource not found")

    payload = json.dumps(game, cls=GameEncoder)
    return Response(
        response=payload,
        status=200,
        mimetype="application/json",
    )


@bp.route("/games/<string:game_id>/actions", methods=["POST"])
def post_action_endpoint(game_id):
    game = get_game_state(game_id)
    if game is None:
        abort(404, description="Resource not found")

    if game.winning_color() is not None:
        return Response(
            response=json.dumps(game, cls=GameEncoder),
            status=200,
            mimetype="application/json",
        )

    # TODO: remove `or body_is_empty` when fully implement actions in FE
    body_is_empty = (not request.data) or request.json is None or request.json == {}
    if game.state.current_player().is_bot or body_is_empty:
        state = EXPLANATION_STATE.get(game_id)
        if state:
            game.play_tick(accumulators=[state["accumulator"]])
        else:
            logging.warning(
                f"No explanation state for game {game_id}; skipping explanation recording"
            )
            game.play_tick(accumulators=[])
        upsert_game_state(game)
    else:
        action = action_from_json(request.json)
        game_before_action = game.copy()

        # For human players, we need to build the decision_info before calling step()
        # This is normally done in decide_with_context(), but human moves come from HTTP
        player = game_before_action.state.current_player()
        playable_actions = list(game_before_action.state.playable_actions)
        player.last_decision_info = player.build_decision_info(
            game_before_action, playable_actions, action
        )

        game.execute(action)
        state = EXPLANATION_STATE.get(game_id)
        if state:
            state["accumulator"].step(game_before_action, action)
        upsert_game_state(game)

    return Response(
        response=json.dumps(game, cls=GameEncoder),
        status=200,
        mimetype="application/json",
    )


@bp.route("/stress-test", methods=["GET"])
def stress_test_endpoint():
    players = [
        AlphaBetaPlayer(Color.RED, 2, True),
        AlphaBetaPlayer(Color.BLUE, 2, True),
        AlphaBetaPlayer(Color.ORANGE, 2, True),
        AlphaBetaPlayer(Color.WHITE, 2, True),
    ]
    game = Game(players=players)
    game.play_tick()
    return Response(
        response=json.dumps(game, cls=GameEncoder),
        status=200,
        mimetype="application/json",
    )


@bp.route(
    "/games/<string:game_id>/states/<string:state_index>/mcts-analysis", methods=["GET"]
)
def mcts_analysis_endpoint(game_id, state_index):
    """Get MCTS analysis for specific game state."""
    logging.info(f"MCTS analysis request for game {game_id} at state {state_index}")

    # Convert 'latest' to None for consistency with get_game_state
    parsed_state_index = _parse_state_index(state_index)
    try:
        game = get_game_state(game_id, parsed_state_index)
        if game is None:
            logging.error(
                f"Game/state not found: {game_id}/{state_index}"
            )  # Use original state_index for logging
            abort(404, description="Game state not found")

        analyzer = GameAnalyzer(num_simulations=100)
        probabilities = analyzer.analyze_win_probabilities(game)

        logging.info(f"Analysis successful. Probabilities: {probabilities}")
        return Response(
            response=json.dumps(
                {
                    "success": True,
                    "probabilities": probabilities,
                    "state_index": (
                        parsed_state_index
                        if parsed_state_index is not None
                        else len(game.state.actions)
                    ),
                }
            ),
            status=200,
            mimetype="application/json",
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in MCTS analysis endpoint: {str(e)}")
        logging.error(traceback.format_exc())
        return Response(
            response=json.dumps(
                {"success": False, "error": str(e), "trace": traceback.format_exc()}
            ),
            status=500,
            mimetype="application/json",
        )


@bp.route("/games/<string:game_id>/explain/<int:move_index>", methods=["GET"])
def explain_move_endpoint(game_id, move_index):
    """Explain a move using LLM."""
    state = EXPLANATION_STATE.get(game_id)
    if not state:
        abort(404, description="No explanation packets available for that game")

    # UI sends global action index, while accumulator keeps only recent packets.
    action_count = len(get_game_state(game_id).state.actions)
    packet_count = len(state["accumulator"].packets)
    packet_start_index = action_count - packet_count

    if move_index < packet_start_index or move_index >= action_count:
        abort(
            400,
            description=(
                f"Move {move_index} is outside explainable range "
                f"[{packet_start_index}, {action_count - 1}]"
            ),
        )

    packet_index = move_index - packet_start_index

    try:
        explanation = state["service"].explain_action(packet_index)
    except LLMQuotaExceededError as exc:
        abort(429, description=str(exc))
    except IndexError as exc:
        abort(400, description=str(exc))
    except ValueError as exc:
        abort(409, description=str(exc))

    return jsonify(
        {
            "move_index": move_index,
            "explanation": explanation,
        }
    )


def _parse_state_index(state_index_str: str):
    """Helper function to parse and validate state_index."""
    if state_index_str == "latest":
        return None
    try:
        return int(state_index_str)
    except ValueError:
        abort(
            400,
            description="Invalid state_index format. state_index must be an integer or 'latest'.",
        )


def _load_bots():
    """
    Temporary bot source:
    - If BOTS_JSON_PATH is set and points to a JSON file, load it.
    - Otherwise return a small stub list so the UI works.
    """

    def _normalize_bot(raw):
        bot_id = raw.get("id") or raw.get("name")
        name = raw.get("name") or bot_id
        elo = raw.get("elo", 0)

        # Key is what /api/games expects in its "players" array
        key = raw.get("key")
        if not key:
            if bot_id == "random":
                key = "RANDOM"
            else:
                key = f"BOT:{bot_id}"

        return {
            "id": bot_id,
            "name": name,
            "elo": elo,
            "key": key,
            "path": raw.get("path"),
            "games": raw.get("games"),
        }

    default_bots = [
        {
            "id": "catanatron_ab_2",
            "name": "Catanatron",
            "elo": 1500,
            "key": "CATANATRON",
        },
        {
            "id": "final_boss",
            "name": "Final Boss",
            "elo": 1600,
            "key": "FINAL_BOSS",
        },
        {
            "id": "value_function",
            "name": "Value Function Bot",
            "elo": 1400,
            "key": "VALUE_FUNCTION",
        },
        {"id": "ppo_player", "name": "PPO Player", "elo": 1475, "key": "PPO_PLAYER"},
        {"id": "mcts", "name": "MCTS", "elo": 1450, "key": "MCTS_PLAYER"},
        {
            "id": "greedy",
            "name": "Greedy Playouts",
            "elo": 1300,
            "key": "GREEDY_PLAYER",
        },
        {
            "id": "vp_player",
            "name": "Victory Point Bot",
            "elo": 1200,
            "key": "VP_PLAYER",
        },
        {
            "id": "placement_player",
            "name": "Placement Only Bot",
            "elo": 1100,
            "key": "PLACEMENT_PLAYER",
        },
        {
            "id": "weighted_random",
            "name": "Weighted Random",
            "elo": 1050,
            "key": "WEIGHTED_RANDOM_PLAYER",
        },
        {"id": "random", "name": "Random", "elo": 1000, "key": "RANDOM"},
        {"id": "human", "name": "Human", "elo": None, "key": "HUMAN"},
    ]

    path = os.environ.get("BOTS_JSON_PATH")

    json_bots = []
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            json_bots = [_normalize_bot(x) for x in data]

    return default_bots + json_bots


@bp.route("/bots", methods=("GET",))
def get_bots_endpoint():
    return jsonify(_load_bots())


# ===== Debugging Routes
# @app.route(
#     "/games/<string:game_id>/players/<int:player_index>/features", methods=["GET"]
# )
# def get_game_feature_vector(game_id, player_index):
#     game = get_game_state(game_id)
#     if game is None:
#         abort(404, description="Resource not found")

#     return create_sample(game, game.state.colors[player_index])


# @app.route("/games/<string:game_id>/value-function", methods=["GET"])
# def get_game_value_function(game_id):
#     game = get_game_state(game_id)
#     if game is None:
#         abort(404, description="Resource not found")

#     # model = tf.keras.models.load_model("data/models/mcts-rep-a")
#     model2 = tf.keras.models.load_model("data/models/mcts-rep-b")
#     feature_ordering = get_feature_ordering()
#     indices = [feature_ordering.index(f) for f in NUMERIC_FEATURES]
#     data = {}
#     for color in game.state.colors:
#         sample = create_sample_vector(game, color)
#         # scores = model.call(tf.convert_to_tensor([sample]))

#         inputs1 = [create_board_tensor(game, color)]
#         inputs2 = [[float(sample[i]) for i in indices]]
#         scores2 = model2.call(
#             [tf.convert_to_tensor(inputs1), tf.convert_to_tensor(inputs2)]
#         )
#         data[color.value] = float(scores2.numpy()[0][0])

#     return data
