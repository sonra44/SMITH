"""Execution policies for sandboxed commands."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence


class ExecutionPolicy(ABC):
    """Base class for command execution policies."""

    @abstractmethod
    def is_allowed(self, command: Sequence[str]) -> bool:
        """Return True if the command is allowed to run."""


class AllowListPolicy(ExecutionPolicy):
    """Allow commands based on an allow-list."""

    def __init__(self, allowed_binaries: Sequence[str]) -> None:
        self._allowed = set(allowed_binaries)

    def is_allowed(self, command: Sequence[str]) -> bool:
        return False if not command else command[0] in self._allowed


class DenyAllPolicy(ExecutionPolicy):
    """Policy that rejects every command."""

    def is_allowed(self, command: Sequence[str]) -> bool:  # noqa: D401 - short description is enough
        return False
