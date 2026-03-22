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


def build_llm_prompt(det_explanation: dict) -> str:
    """Generates a prompt for LLM move explanation based on the deterministic explanation of a bot's move."""
    facts = det_explanation["facts_used"]

    return f"""
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