"""
Module: 10. Explanation Pipeline
Author: Forked
Date: 2025-12-14
Purpose: Implements the prompt builder module for the explanation pipeline, supporting prompt construction, packet analysis, or explanation generation.
"""


def _format_tile_coordinate(coord: tuple) -> str:
    """Format a tile coordinate tuple as a natural name like '6-5-9'."""
    if coord is None:
        return "unknown"
    return "-".join(str(x) for x in coord)


def _format_action_value(facts: dict) -> str:
    """Converts the action value into something more readable."""
    action_type = facts["chosen_type"]
    value = facts["chosen_value"]

    if action_type in {"BUILD_SETTLEMENT", "BUILD_CITY"} and value is not None:
        # Try to get tile coordinates if available
        target_node_summary = facts.get("target_node_summary", {})
        tile_coordinates = target_node_summary.get("tile_coordinates", [])

        if tile_coordinates:
            # Format as intersection of tiles, e.g., "where tiles 6-5-9 meet"
            if len(tile_coordinates) == 3:
                tile_names = [
                    _format_tile_coordinate(coord) for coord in sorted(tile_coordinates)
                ]
                return f"intersection where tiles {', '.join(tile_names)} meet"
            else:
                tile_names = [
                    _format_tile_coordinate(coord) for coord in sorted(tile_coordinates)
                ]
                return f"location at tiles {', '.join(tile_names)}"

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
            "TARGET READING LEVEL: Flesch Reading Ease 60-70 (academic, advanced vocabulary acceptable)\n"
        )
    elif familiarity == "LOW":
        return (
            "AUDIENCE: New to Catan, unfamiliar with mechanics.\n"
            "STYLE: Simple, beginner-friendly, no jargon.\n"
            "MUST: Define resources, settlements, cities, roads. Explain basic reasoning and immediate benefit."
            "TARGET READING LEVEL: Flesch Reading Ease 80-90 (very easy, simple words, short sentences)\n"
        )
    else:  # MEDIUM
        return (
            "AUDIENCE: Knows basic Catan rules, not expert.\n"
            "STYLE: Balanced. Intermediate concepts like resource scarcity and position value.\n"
            "TONE: Clear, no heavy jargon."
            "TARGET READING LEVEL: Flesch Reading Ease 70-80 (conversational, clear, accessible)\n"
        )


def _get_output_format_instruction(familiarity: str) -> str:
    """Return output format instruction based on familiarity level."""
    if familiarity == "HIGH":
        return (
            "OUTPUT FORMAT (REQUIRED):\n"
            "- Write 3-4 paragraphs of comprehensive analysis\n"
            "- Paragraph 1: Direct explanation of the move choice (2-3 sentences)\n"
            "- Paragraph 2: Strategic context and position evaluation (3-4 sentences)\n"
            "- Paragraph 3: Key factors and tradeoffs analysis (3-4 sentences)\n"
            "- Paragraph 4 (optional): Long-term implications or competitive positioning (2-3 sentences)\n"
            "- Use PLAIN TEXT ONLY: no asterisks, no dashes for bullets, no markdown formatting, no code-like descriptions of actions.\n"
            "- Reference specific strategic concepts (production chains, settlement clusters, blocking, etc.)"
        )
    elif familiarity == "LOW":
        return (
            "OUTPUT FORMAT (REQUIRED):\n"
            "- Write exactly one paragraph of 3-5 sentences\n"
            "- Use PLAIN TEXT ONLY: no asterisks, no dashes for bullets, no markdown formatting\n"
            "- Reference the move and its 2-3 most important factors from below\n"
            "- Write naturally as flowing prose"
        )
    else:  # MEDIUM
        return (
            "OUTPUT FORMAT (REQUIRED):\n"
            "- Write 2 paragraphs of balanced detail\n"
            "- Paragraph 1: Why this move was chosen (2-3 sentences)\n"
            "- Paragraph 2: Context and strategic reasoning (3-4 sentences)\n"
            "- Use PLAIN TEXT ONLY: no asterisks, no dashes for bullets, no markdown formatting\n"
            "- Reference the move and its 3-4 most important factors from below\n"
            "- Write naturally as flowing prose"
        )


def build_llm_prompt(det_explanation: dict, familiarity: str = "MEDIUM") -> str:
    """Generates a prompt for LLM move explanation based on familiarity level."""
    facts = det_explanation["facts_used"]
    familiarity_instruction = _get_familiarity_instruction(familiarity)
    output_format_instruction = _get_output_format_instruction(familiarity)

    # Use numbered format instead of markdown bullets for considerations
    considerations = "\n".join(
        f"{i+1}. {reason}" for i, reason in enumerate(det_explanation["explanation"])
    )

    return f"""EXPLAIN WHY THIS CATAN BOT CHOSE ITS MOVE

AUDIENCE AND STYLE:
{familiarity_instruction}

{output_format_instruction}

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
