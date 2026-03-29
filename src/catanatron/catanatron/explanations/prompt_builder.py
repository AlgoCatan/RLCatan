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


def _get_familiarity_instruction(familiarity: str) -> str:
    """Return instruction for LLM based on familiarity level."""
    if familiarity == "HIGH":
        return (
            "Assume the reader is an experienced Catan player. Provide deep strategic analysis, "
            "including game theory concepts, probabilistic reasoning, settlement cluster analysis, "
            "production chains, and sophisticated trading strategies. Use technical terminology. "
            "Explain why this move is optimal in the context of competitive play."
        )
    elif familiarity == "LOW":
        return (
            "Assume the reader is new to Catan and doesn't deeply understand game mechanics. "
            "Explain concepts simply without jargon. Define what resources, settlements, cities, and roads do. "
            "Explain the basic reasoning without advanced strategy. Focus on immediate benefit. "
            "Keep language friendly and accessible."
        )
    else:  # MEDIUM
        return (
            "Assume the reader knows basic Catan rules but isn't an expert. Balance strategic depth with clarity. "
            "Explain intermediate concepts like resource scarcity and position value without heavy jargon."
        )


def build_llm_prompt(det_explanation: dict, familiarity: str = "MEDIUM") -> str:
    """Generates a prompt for LLM move explanation based on familiarity level."""
    facts = det_explanation["facts_used"]

    familiarity_instruction = _get_familiarity_instruction(familiarity)

    return f"""
Explain why this Catan bot likely chose its move.

Familiarity level: {familiarity}
{familiarity_instruction}
        
Rules:
- Respond in plain text, not markdown.
- Use only the information provided below.
- Do not claim certainty about hidden motives.
- Write 1 short paragraph followed by 2-4 bullet points of key factors.
- Mention tradeoffs or uncertainty where appropriate.
- Focus on why this move may have been preferred over the legal alternatives.
- Do not directly reference internal node/tile IDs in your response, or any other info a human wouldn't know from the game state.
- The given considerations are generated via a deterministic explainer. As such, it is likely not all info is relevant to a given
  decision, especially in rare/edge cases such as initial settlement placements. If a fact appears to add no useful info,
  do not mention it in your response.
        
Chosen move:
- action type: {facts["chosen_type"]}
- action value: {_format_action_value(facts)}
        
Important considerations:
{chr(10).join(f"- {reason}" for reason in det_explanation["explanation"])}
    """
