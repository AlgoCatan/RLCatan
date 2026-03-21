import json
import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    enabled: bool
    api_key: str
    model: str
    timeout: float


class LLMExplanationClient:
    """LLM client with deterministic local fallback when unavailable."""

    def __init__(self):
        self.config = LLMConfig(
            enabled=os.getenv("CATAN_LLM_ENABLED", "0") == "1",
            api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            model=os.getenv("CATAN_LLM_MODEL", "gpt-4.1-mini"),
            timeout=float(os.getenv("CATAN_LLM_TIMEOUT", "10")),
        )
        self._client = None

    def explain_packet(self, packet):
        if not self.config.enabled:
            return self._fallback(packet, "LLM disabled")
        if not self.config.api_key:
            return self._fallback(packet, "missing API key")

        try:
            from openai import OpenAI

            if self._client is None:
                self._client = OpenAI(api_key=self.config.api_key, timeout=self.config.timeout)

            response = self._client.responses.create(
                model=self.config.model,
                temperature=0.2,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You explain Catan moves briefly and concretely. "
                            "Use only provided context and mention tradeoffs."
                        ),
                    },
                    {
                        "role": "user",
                        "content": "Explain this move packet:\n" + json.dumps(packet, separators=(",", ":")),
                    },
                ],
            )
            text = (getattr(response, "output_text", "") or "").strip()
            if text:
                return text
            return self._fallback(packet, "empty LLM output")
        except Exception as exc:
            reason = self._classify_exception(exc)
            return self._fallback(packet, reason)

    def _classify_exception(self, exc):
        msg = str(exc).lower()
        if "insufficient_quota" in msg or "quota" in msg or "credit" in msg:
            return "quota exceeded"
        if "rate" in msg and "limit" in msg:
            return "rate limited"
        return "LLM request failed"

    def _fallback(self, packet, reason):
        action = (packet.get("action_context") or {}).get("action_type") or "UNKNOWN"
        board = packet.get("board_context") or {}
        gap = board.get("actor_visible_vp_gap_to_leader")
        legal = board.get("num_legal_actions")
        return (
            f"Fallback explanation ({reason}). "
            f"Chose action {action}. "
            f"Visible VP gap to leader: {gap}. "
            f"Legal actions available: {legal}."
        )

