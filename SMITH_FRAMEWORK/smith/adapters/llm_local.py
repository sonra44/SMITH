"""Local LLM adapter placeholder."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class LocalLLMConfig:
    """Configuration for the local model."""

    model_path: str
    max_tokens: int = 512


class LocalLLM:
    """A minimal interface for local inference."""

    def __init__(self, config: LocalLLMConfig) -> None:
        self._config = config

    def generate(self, prompt: str, *, stop: Iterable[str] | None = None) -> str:
        """Generate a response for the prompt."""

        del stop  # placeholder for future logic
        prefix = f"[local-llm:{self._config.model_path}] "
        response = f"{prefix}{prompt}"
        return response[: self._config.max_tokens]
