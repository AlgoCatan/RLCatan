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
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus lacus purus, viverra quis pharetra non, tincidunt at lectus.
Nulla id efficitur quam, sed scelerisque orci. Mauris ut velit accumsan, posuere sapien nec, dapibus odio. Aliquam eu libero vitae arcu pharetra accumsan.
ellentesque lacinia at quam in molestie. Vivamus porta justo eget ex gravida, vitae blandit libero scelerisque. Proin rhoncus felis sed est sodales fermentum.
liquam ultricies aliquet justo. Maecenas porta gravida semper. Sed justo ipsum, consequat quis ante at, tempor condimentum lacus.
hasellus lacus lectus, bibendum tempor sollicitudin non, laoreet semper mi. Integer placerat congue risus non porta. In blandit.
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