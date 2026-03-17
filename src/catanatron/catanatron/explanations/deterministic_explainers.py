def extract_common_facts(packet: dict) -> dict:
    """
    Extracts common facts from a bot decision packet for use in deterministic explanations.
    These are facts every bot will have available at decision time and are not specific to any one bot's internal logic.
    """
    chosen = packet["chosen_action"]
    playable = packet.get("playable_actions", [])
    summary = packet.get("player_summary", {})

    return {
        "bot_class": packet.get("bot_class"),
        "prompt": packet.get("prompt"),
        "chosen_type": chosen.get("action_type"),
        "chosen_value": chosen.get("value"),
        "num_legal_actions": len(playable),
        "is_forced": len(playable) == 1,
        "vp": summary.get("actual_victory_points"),
        "settlements": summary.get("settlements"),
        "cities": summary.get("cities"),
        "has_longest_road": summary.get("has_longest_road"),
        "has_largest_army": summary.get("has_largest_army"),
        "dev_cards_in_hand": summary.get("dev_cards_in_hand"),
    }


def explain_common(packet: dict, facts: dict) -> list[str]:
    reasons = []

    if facts["is_forced"]:
        reasons.append("This was the only legal action available.")

    prompt = facts["prompt"]
    action_type = facts["chosen_type"]

    if prompt == "BUILD_INITIAL_SETTLEMENT":
        reasons.append("This was an opening placement decision, so early board position and future resource access matter most.")
    elif prompt == "PLAY_TURN":
        reasons.append("This was a normal turn decision, so the bot was choosing among its currently legal tactical options.")

        if action_type == "BUILD_CITY":
            reasons.append("Upgrading to a city usually strengthens resource production at an already valuable location.")
        elif action_type == "BUILD_SETTLEMENT":
            reasons.append("Building a settlement usually improves expansion, resource access, and victory point progress.")
        elif action_type == "BUILD_ROAD":
            reasons.append("Building a road usually supports expansion, connectivity, or longest road pressure.")
        elif action_type == "BUY_DEVELOPMENT_CARD":
            reasons.append("Buying a development card usually trades immediate certainty for future tactical flexibility.")
        elif action_type == "END_TURN":
            reasons.append("Ending the turn suggests the bot judged that no available action was worth taking immediately.")

    elif prompt == "MOVE_ROBBER":
        reasons.append("This was a robber decision, so disruption and denial are likely important.")
    elif prompt == "DISCARD":
        reasons.append("This was a discard decision, so the bot was minimizing what it gave up while staying flexible.")

    if facts["vp"] is not None:
        reasons.append(f"The acting player currently has {facts['vp']} visible victory points.")

        if facts["vp"] >= 8:
            reasons.append("The bot was close to winning, so it likely prioritized high-impact actions that could secure victory.")
        elif facts["vp"] <= 2:
            reasons.append("The bot was far from winning, so it likely focused on building up resources and infrastructure.")
        else:
            reasons.append("The bot had some progress towards victory, so it likely balanced building up resources with making strategic plays.")

    return reasons


def explain_bot_specific(packet: dict, facts: dict) -> list[str]:
    """Explains the bot's decision based on its specific class and any additional metadata it provided about the decision."""
    reasons = []
    bot_class = facts["bot_class"]

    if bot_class == "SimplePlayer":
        reasons.append("This bot follows a simple rule-based policy and picks the first legal action in the list.")
    elif bot_class == "RandomPlayer":
        reasons.append("This bot chooses randomly from the legal actions, so the move is not based on strategic evaluation.")
    elif bot_class == "PPOPlayer":
        reasons.append("This bot uses a PPO policy, which evaluates the game state and legal actions to assign probabilities to each action based on expected value.")

        chosen_index = packet.get("chosen_index")
        filtered_indices = packet.get("filtered_indices")
        deterministic = packet.get("deterministic")

        if deterministic:
            reasons.append("The PPO policy was queried in deterministic mode, so it selected its highest-preference legal action rather than sampling.")
        else:
            reasons.append("The PPO policy was queried in stochastic mode, so some randomness may have influenced the final choice.")

        if chosen_index is not None:
            reasons.append(f"The chosen action corresponded to policy action index {chosen_index}.")

        if filtered_indices is not None:
            reasons.append(f"{len(filtered_indices)} legal policy actions remained after action filtering.")

    return reasons


def explain_packet(packet: dict) -> dict:
    """Generate a deterministic explanation for a bot decision based on the information in the packet."""
    facts = extract_common_facts(packet)

    reasons = []
    reasons.extend(explain_common(packet, facts))
    reasons.extend(explain_bot_specific(packet, facts))

    confidence_basis = "generic"

    if packet.get("bot_class") in {"SimplePlayer", "RandomPlayer"}:
        confidence_basis = "rule-based"

    if packet.get("chosen_index") is not None or packet.get("filtered_indices") is not None:
        confidence_basis = "policy-metadata"

    summary = reasons[0] if reasons else "The bot selected one of the currently legal actions."

    return {
        "summary": summary,
        "reasoning_mode": "deterministic",
        "confidence_basis": confidence_basis,
        "details": reasons,
        "facts_used": facts,
    }