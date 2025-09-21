"""Lightweight in-memory stores for SMITH."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class MemoryRecord:
    """A unit of contextual data stored by the agent."""

    key: str
    value: str
    tags: tuple[str, ...] = ()


class MemoryStore:
    """A simple in-memory store for agent state."""

    def __init__(self) -> None:
        self._records: dict[str, MemoryRecord] = {}

    def put(self, record: MemoryRecord) -> None:
        """Store or replace a record."""

        self._records[record.key] = record

    def get(self, key: str) -> MemoryRecord | None:
        """Fetch a record by key."""

        return self._records.get(key)

    def list(self) -> Iterable[MemoryRecord]:
        """Return all stored records."""

        return self._records.values()

    def delete(self, key: str) -> None:
        """Delete a record if it exists."""

        self._records.pop(key, None)
