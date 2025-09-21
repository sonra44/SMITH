"""Finite state machine primitives for SMITH."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from smith.utils.errors import SmithError


@dataclass(frozen=True)
class State:
    """A logical state within the SMITH agent."""

    name: str
    description: str | None = None


@dataclass(frozen=True)
class Transition:
    """Describes an allowed transition between two states."""

    source: State
    target: State
    guard: Callable[[FiniteStateMachine], bool] | None = None


class FiniteStateMachine:
    """A minimal, type-safe finite state machine engine."""

    def __init__(
        self,
        states: Iterable[State],
        transitions: Iterable[Transition],
        *,
        initial: State,
    ) -> None:
        self._states = {state.name: state for state in states}
        if initial.name not in self._states:
            raise SmithError(f"Initial state '{initial.name}' is not registered")
        self._transitions: dict[str, list[Transition]] = {}
        for transition in transitions:
            if (
                transition.source.name not in self._states
                or transition.target.name not in self._states
            ):
                raise SmithError("Transitions must reference known states")
            self._transitions.setdefault(transition.source.name, []).append(transition)
        self._current: State = initial

    @property
    def current(self) -> State:
        """Return the current state."""

        return self._current

    def can_transition(self, target: str) -> bool:
        """Check whether a transition to *target* is allowed."""

        for transition in self._transitions.get(self._current.name, []):
            if transition.target.name == target and (
                transition.guard is None or transition.guard(self)
            ):
                return True
        return False

    def transition(self, target: str) -> State:
        """Move to the target state if possible."""

        if not self.can_transition(target):
            raise SmithError(
                f"Invalid transition from {self._current.name} to {target}"
            )
        self._current = self._states[target]
        return self._current
