"""Registries for tools, policies, and other components."""

from __future__ import annotations

from collections.abc import Callable, ItemsView

from smith.utils.errors import SmithError


class Registry[T]:
    """A minimal in-memory registry keyed by name."""

    def __init__(self, *, name: str) -> None:
        self._name = name
        self._entries: dict[str, T] = {}

    def register(self, key: str, value: T) -> None:
        """Register a new component."""

        if key in self._entries:
            raise SmithError(f"{self._name} '{key}' already registered")
        self._entries[key] = value

    def get(self, key: str) -> T:
        """Fetch a component by name."""

        try:
            return self._entries[key]
        except KeyError as exc:
            raise SmithError(f"{self._name} '{key}' is not registered") from exc

    def items(self) -> ItemsView[str, T]:
        """Return registered items."""

        return self._entries.items()


ToolFactory = Callable[..., object]
PolicyFactory = Callable[..., object]

tool_registry: Registry[ToolFactory] = Registry(name="tool")
policy_registry: Registry[PolicyFactory] = Registry(name="policy")
