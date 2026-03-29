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
            "AUDIENCE: Experienced Catan player.\n"
            "STYLE: Deep strategic analysis with game theory, probability, settlement clusters, production chains.\n"
            "TONE: Technical. Explain move optimality for competitive play."
        )
    elif familiarity == "LOW":
        return (
            "AUDIENCE: New to Catan, unfamiliar with mechanics.\n"
            "STYLE: Simple, beginner-friendly, no jargon.\n"
            "MUST: Define resources, settlements, cities, roads. Explain basic reasoning and immediate benefit."
        )
    else:  # MEDIUM
        return (
            "AUDIENCE: Knows basic Catan rules, not expert.\n"
            "STYLE: Balanced. Intermediate concepts like resource scarcity and position value.\n"
            "TONE: Clear, no heavy jargon."
        )


def build_llm_prompt(det_explanation: dict, familiarity: str = "MEDIUM") -> str:
    """Generates a prompt for LLM move explanation based on familiarity level."""
    facts = det_explanation["facts_used"]
    familiarity_instruction = _get_familiarity_instruction(familiarity)

    # Use numbered format instead of markdown bullets for considerations
    considerations = "\n".join(
        f"{i+1}. {reason}"
        for i, reason in enumerate(det_explanation["explanation"])
    )

    return f"""EXPLAIN WHY THIS CATAN BOT CHOSE ITS MOVE

AUDIENCE AND STYLE:
{familiarity_instruction}

OUTPUT FORMAT (REQUIRED):
- Write exactly one paragraph of 3-5 sentences
- Use PLAIN TEXT ONLY: no asterisks, no dashes for bullets, no markdown formatting
- Reference the move and its 2-3 most important factors from below
- Write naturally as flowing prose

MOVE DETAILS:
Action: {facts["chosen_type"]}
Target: {_format_action_value(facts)}

KEY FACTORS TO ANALYZE:
{considerations}

GUIDELINES:
- Use ONLY information provided above
- If a factor seems irrelevant, skip it
- Do NOT reference internal node IDs, tile numbers, or player names
- Do NOT claim certainty about hidden bot intentions
- Mention tradeoffs or uncertainty if relevant
- Be conversational and clear for your audience"""
