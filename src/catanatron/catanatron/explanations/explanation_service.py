from typing import Protocol, Any
import os

from catanatron.explanations.deterministic_explainers import explain_packet
from catanatron.explanations.prompt_builder import build_llm_prompt


class LLMQuotaExceededError(RuntimeError):
    """Raised when Gemini quota/free-tier tokens are exhausted."""


class PromptLLM(Protocol):
    def explain_prompt(self, prompt: str) -> str:
        """Given a prompt, return an explanation string."""
        ...


class FakeLLM(PromptLLM):
    def explain_prompt(self, prompt: str) -> str:
        """Just a random prompt response for testing purposes."""

        return """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus lacus purus, viverra quis pharetra non, tincidunt at lectus.
Nulla id efficitur quam, sed scelerisque orci. Mauris ut velit accumsan, posuere sapien nec, dapibus odio. Aliquam eu libero vitae arcu pharetra accumsan.
ellentesque lacinia at quam in molestie. Vivamus porta justo eget ex gravida, vitae blandit libero scelerisque. Proin rhoncus felis sed est sodales fermentum.
liquam ultricies aliquet justo. Maecenas porta gravida semper. Sed justo ipsum, consequat quis ante at, tempor condimentum lacus.
hasellus lacus lectus, bibendum tempor sollicitudin non, laoreet semper mi. Integer placerat congue risus non porta. In blandit.
        """


class GeminiLLM(PromptLLM):
    """Gemini Google AI Studio implementation of PromptLLM."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.5-flash-lite",
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing GEMINI_API_KEY for GeminiLLM")

        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError(
                "google-genai is required for GeminiLLM. Install it in web dependencies."
            ) from exc

        self._genai = genai
        self._client = genai.Client(api_key=self.api_key)
        self._model = model

    def explain_prompt(self, prompt: str) -> str:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
            )
            text = getattr(response, "text", None)
            if text and text.strip():
                return text.strip()
            raise RuntimeError("Gemini returned an empty explanation")
        except Exception as exc:
            message = str(exc).lower()
            quota_markers = (
                "quota",
                "rate limit",
                "resource_exhausted",
                "429",
                "503",
                "service unavailable",
                "too many requests",
                "exceeded",
                "free tier",
            )
            if any(marker in message for marker in quota_markers):
                raise LLMQuotaExceededError(
                    "Gemini free-tier token quota has been exhausted. Please try again later."
                ) from exc
            raise


class ExplanationService:
    def __init__(self, accumulator, llm: PromptLLM, familiarity: str = "MEDIUM"):
        self.accumulator = accumulator
        self.llm = llm
        self.familiarity = familiarity

    def explain_action(self, action_index: int) -> str:
        packet = self.accumulator.get_packet(action_index)
        det = explain_packet(packet)
        prompt = build_llm_prompt(det, familiarity=self.familiarity)
        explanation_text = self.llm.explain_prompt(prompt)

        return explanation_text
