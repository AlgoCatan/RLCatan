import json


def _format_action_value(facts: dict) -> str:
    """Converts the action value into something more readable."""
    action_type = facts["chosen_type"]
    value = facts["chosen_value"]

    if action_type in {"BUILD_SETTLEMENT", "BUILD_CITY"} and value is not None:
        return f"node {value}"

    if action_type == "BUILD_ROAD" and value is not None:
        return f"edge {tuple(value)}"

    if action_type == "MOVE_ROBBER" and isinstance(value, list):
        coord = value[0] if len(value) > 0 else None
        target = value[1] if len(value) > 1 else None
        return f"move robber to {coord}" + (f", target {target}" if target else "")

    return str(value)


def build_llm_prompt(det_explanation: dict, action_index: int) -> str:
    """Generate a grounded prompt for a single action explanation."""
    facts = det_explanation["facts_used"]

    base_prompt = f"""
Explain why this Catan bot likely chose its move.

Rules:
- Use only the information provided below.
- Do not claim certainty about hidden motives.
- Write 1 short paragraph followed by 2-4 bullet points of key factors.
- Mention tradeoffs or uncertainty where appropriate.
- Focus on why this move may have been preferred over the legal alternatives.
- Avoid directly referencing internal node/tile IDs in your response, or any other info a human wouldn't know from the game state.
- The given considerations are generated via a deterministic explainer. As such, it is likely not all info is relevant to a given
  decision, especially in rare/edge cases such as initial settlement placements. If a fact appears to add no useful info,
  do not mention it in your response.

Chosen move:
- action type: {facts["chosen_type"]}
- action value: {_format_action_value(facts)}

Important considerations:
{chr(10).join(f"- {reason}" for reason in det_explanation["explanation"])}
    """

    det_json = json.dumps(det_explanation, ensure_ascii=True, sort_keys=True, default=str)
    return (
        "You are explaining exactly one Catan action.\n"
        f"Action index: {action_index}\n"
        "Grounding rules:\n"
        "- Use only facts from DETERMINISTIC_FACTS and BASE_PROMPT.\n"
        "- Do not mention future or past turns other than Action index above.\n"
        "- If a detail is missing, say 'unknown from provided data'.\n"
        "- Keep the explanation concise and factual.\n\n"
        f"DETERMINISTIC_FACTS:\n{det_json}\n\n"
        f"BASE_PROMPT:\n{base_prompt}\n"
    )
