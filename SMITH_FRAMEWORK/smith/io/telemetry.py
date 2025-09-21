"""Telemetry utilities with JSON logging."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

_EVENT_CODE_MIN = 100
_EVENT_CODE_MAX = 999


@dataclass(slots=True)
class TelemetryEvent:
    """Structured telemetry event."""

    code: int
    message: str
    severity: str = "info"
    payload: Mapping[str, Any] | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_json(self) -> str:
        """Serialize the event to a JSON string."""

        if not (_EVENT_CODE_MIN <= self.code <= _EVENT_CODE_MAX):
            raise ValueError("Event code must be within 100-999")
        body = {
            "ts": self.timestamp.isoformat(),
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }
        if self.payload:
            body["payload"] = dict(self.payload)
        return json.dumps(body, ensure_ascii=False)


class JSONTelemetryLogger:
    """Emit telemetry events via the standard logging framework."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("smith.telemetry")

    def emit(self, event: TelemetryEvent) -> None:
        """Emit the event as a structured log entry."""

        serialized = event.to_json()
        self._logger.log(_map_severity(event.severity), serialized)


def _map_severity(severity: str) -> int:
    levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    return levels.get(severity.lower(), logging.INFO)


def configure_logging(*, stream: Any) -> logging.Logger:
    """Configure logging to output JSON to the provided stream."""

    logger = logging.getLogger("smith")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.handlers.clear()
    logger.addHandler(handler)
    logging.getLogger("smith.telemetry").handlers = logger.handlers
    logging.getLogger("smith.telemetry").setLevel(logging.INFO)
    return logger
