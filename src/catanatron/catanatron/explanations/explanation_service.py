from typing import Protocol, Any

from catanatron.explanations.deterministic_explainers import explain_packet
from catanatron.explanations.prompt_builder import build_llm_prompt


class PromptLLM(Protocol):
    def explain_prompt(self, prompt: str) -> str:
        """Given a prompt, return an explanation string."""
        ...

class FakeLLM(Protocol):
    def explain_prompt(self, prompt: str) -> str:
        """Just a random prompt response for testing purposes."""

        return """
The bot likely bought a development card because it had limited immediate options and saw value in converting surplus resources into flexible, potentially hidden advantages. With no available settlement placements and only one alternative (ending its turn), investing in a development card offered a way to progress while maintaining a strong position in the mid-game, especially since it was already leading.

- It had no legal settlement builds and no brick, making typical expansion moves unavailable, so spending resources productively was preferable to passing.
- Holding 7+ cards increased the risk of losing resources to the robber, so converting some into a development card reduced that risk.
- With a lead at 6 points, a development card could provide safe, hidden value (e.g., victory points or tactical plays) without overextending.
- The choice trades immediate board presence for future flexibility, which may be slightly slower but safer given its current advantage and lack of strong alternatives.
        """


class ExplanationService:
    def __init__(self, accumulator, llm: PromptLLM):
        self.accumulator = accumulator
        self.llm = llm

    def explain_action(self, action_index: int) -> str:
        packet = self.accumulator.get_packet(action_index)
        det = explain_packet(packet)
        prompt = build_llm_prompt(det)
        explanation_text = self.llm.explain_prompt(prompt)

        return explanation_text