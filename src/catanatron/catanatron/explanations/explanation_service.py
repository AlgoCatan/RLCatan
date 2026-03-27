from typing import Protocol, Any
import os
import re
import time
import random
import threading
import json
from collections import deque

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
    def __init__(self, accumulator, llm: PromptLLM):
        self.accumulator = accumulator
        self.llm = llm

        # Stable cache across repeated timeline scrubbing.
        self._cache: dict[str, str] = {}

        # In-flight dedup for concurrent identical requests.
        self._inflight: dict[str, threading.Event] = {}
        self._lock = threading.Lock()

        # Built-in sensible defaults (no env vars needed, but could add later if needed).
        self._rpm_limit = 30  # ~2 requests/second
        self._min_interval_sec = 0.1  # 100ms min between calls
        self._retry_attempts = 2  # up to 3 total attempts on transient quota
        self._retry_base_ms = 250  # exponential backoff base
        self._prompt_version = "v1"

        # Track request timestamps for rolling RPM control.
        self._request_times: deque[float] = deque()
        self._last_request_time = 0.0

    def _deterministic_fallback(self, action_index: int, det: Any, reason: str) -> str:
        return (
            f"Turn {action_index}: showing deterministic explanation ({reason}).\n\n"
            f"{det}"
        )

    def _response_is_grounded(self, text: str, action_index: int) -> bool:
        if not text or not text.strip():
            return False

        lower = text.lower()
        hallucination_markers = (
            "future turn",
            "later in the game",
            "as seen previously",
            "unknown card drawn",
        )
        if any(marker in lower for marker in hallucination_markers):
            return False

        # If the model references a turn number, it should match the requested index.
        turn_numbers = re.findall(r"\bturn\s*(\d+)\b", lower)
        return not turn_numbers or all(int(n) == action_index for n in turn_numbers)

    def _make_cache_key(self, game_id: str, action_index: int) -> str:
        """Generate stable cache key based on game, action identity (not changing game state)."""
        model_name = getattr(self.llm, "_model", self.llm.__class__.__name__)
        return f"{self._prompt_version}|{game_id}|{model_name}|{action_index}"

    def _acquire_rate_slot(self) -> None:
        """Block until rate limits allow a new request (RPM + min interval)."""
        while True:
            now = time.monotonic()
            with self._lock:
                # Prune timestamps outside 60s window.
                window_start = now - 60.0
                while self._request_times and self._request_times[0] < window_start:
                    self._request_times.popleft()

                # Compute how long to wait for min interval.
                interval_wait = max(0.0, self._min_interval_sec - (now - self._last_request_time))

                # Compute how long to wait for RPM slot.
                rpm_wait = 0.0
                if len(self._request_times) >= self._rpm_limit:
                    rpm_wait = max(0.0, self._request_times[0] + 60.0 - now)

                wait_for = max(interval_wait, rpm_wait)
                if wait_for <= 0.0:
                    self._request_times.append(now)
                    self._last_request_time = now
                    return

            time.sleep(min(wait_for, 0.5))

    def _call_llm_with_retries(self, prompt: str) -> str:
        """Call LLM with bounded exponential backoff retry on transient quota errors."""
        attempts = self._retry_attempts + 1
        for attempt in range(attempts):
            self._acquire_rate_slot()
            try:
                return self.llm.explain_prompt(prompt)
            except LLMQuotaExceededError:
                if attempt >= self._retry_attempts:
                    raise
                # Exponential backoff with jitter for transient throttling.
                delay = (self._retry_base_ms / 1000.0) * (2 ** attempt) + random.uniform(0.0, 0.15)
                time.sleep(delay)

        raise RuntimeError("Unreachable retry state")

    def explain_action(self, game_id: str, action_index: int) -> str:
        packet = self.accumulator.get_packet(action_index)
        det = explain_packet(packet)
        key = self._make_cache_key(game_id, action_index)

        # Check cache and register in-flight request.
        with self._lock:
            cached = self._cache.get(key)
            if cached is not None:
                return cached

            existing_event = self._inflight.get(key)
            if existing_event is None:
                event = threading.Event()
                self._inflight[key] = event
                is_owner = True
            else:
                event = existing_event
                is_owner = False

        # If not owner, wait for owner to finish.
        if not is_owner:
            event.wait(timeout=15.0)
            with self._lock:
                cached = self._cache.get(key)
            if cached is not None:
                return cached
            # Owner may have failed; continue as fallback.

        # Owner path: call LLM.
        prompt = build_llm_prompt(det, action_index)
        explanation_text = None

        try:
            explanation_text = self._call_llm_with_retries(prompt)
            if not self._response_is_grounded(explanation_text, action_index):
                explanation_text = self._deterministic_fallback(
                    action_index,
                    det,
                    "LLM response failed grounding checks",
                )
        except LLMQuotaExceededError:
            explanation_text = self._deterministic_fallback(
                action_index,
                det,
                "LLM quota/rate limit reached",
            )
        except Exception:
            explanation_text = self._deterministic_fallback(
                action_index,
                det,
                "LLM request failed",
            )
        finally:
            if explanation_text is None:
                explanation_text = self._deterministic_fallback(
                    action_index,
                    det,
                    "unexpected error (no explanation generated)",
                )
            with self._lock:
                self._cache[key] = explanation_text
                inflight_event = self._inflight.pop(key, None)
                if inflight_event is not None:
                    inflight_event.set()

        return explanation_text
