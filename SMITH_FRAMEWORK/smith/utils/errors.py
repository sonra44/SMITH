"""Custom exception hierarchy for SMITH."""

from __future__ import annotations


class SmithError(Exception):
    """Base exception for recoverable agent errors."""


class PolicyViolationError(SmithError):
    """Raised when an execution policy denies an action."""
