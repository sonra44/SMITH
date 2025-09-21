"""Registries for tools, policies, and other components."""

from __future__ import annotations

from collections.abc import Callable, ItemsView
from typing import cast

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

    def __contains__(self, key: str) -> bool:
        return key in self._entries


ToolFactory = Callable[..., object]
PolicyFactory = Callable[..., object]

tool_registry: Registry[ToolFactory] = Registry(name="tool")
policy_registry: Registry[PolicyFactory] = Registry(name="policy")


def register_default_components() -> None:
    """Populate registries with default tool and policy factories."""

    from smith.runtime.policies import AllowListPolicy, DenyAllPolicy
    from smith.tools.files import FilesTool
    from smith.tools.shell import ShellTool

    _register_if_absent(tool_registry, "files", cast(ToolFactory, FilesTool))
    _register_if_absent(tool_registry, "shell", cast(ToolFactory, ShellTool))
    _register_if_absent(
        policy_registry,
        "allow-list",
        cast(PolicyFactory, AllowListPolicy),
    )
    _register_if_absent(
        policy_registry,
        "deny-all",
        cast(PolicyFactory, DenyAllPolicy),
    )


def _register_if_absent[T](registry: Registry[T], key: str, value: T) -> None:
    if key in registry:
        return
    try:
        registry.register(key, value)
    except SmithError:
        # Another importer may have registered concurrently; ignore duplicates.
        pass


register_default_components()
