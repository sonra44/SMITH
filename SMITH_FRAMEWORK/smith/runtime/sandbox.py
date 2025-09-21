"""Sandbox runtime primitives."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from smith.utils.errors import SmithError


class Sandbox:
    """Represents a working directory sandbox."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        if not self._root.exists():
            self._root.mkdir(parents=True, exist_ok=True)
        if not self._root.is_dir():
            raise SmithError("Sandbox root must be a directory")

    @property
    def root(self) -> Path:
        """Return the absolute sandbox root."""

        return self._root

    @contextmanager
    def activate(self) -> Iterator[Path]:
        """Context manager providing sandbox access."""

        yield self._root
