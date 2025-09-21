"""Configuration loading for SMITH."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SmithConfig:
    """Runtime configuration for the agent."""

    sandbox_root: Path
    telemetry_stream: str = "stdout"

    @classmethod
    def load(cls) -> SmithConfig:
        """Load configuration from environment variables."""

        sandbox_root = Path(os.getenv("SMITH_SANDBOX_ROOT", ".")).resolve()
        telemetry_stream = os.getenv("SMITH_TELEMETRY_STREAM", "stdout")
        return cls(sandbox_root=sandbox_root, telemetry_stream=telemetry_stream)
