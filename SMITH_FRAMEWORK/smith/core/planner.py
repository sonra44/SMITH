"""Planning primitives for SMITH."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from smith.core.fsm import State
from smith.core.memory import MemoryStore
from smith.utils.errors import SmithError


@dataclass(frozen=True)
class Goal:
    """Represents a user goal or task statement."""

    description: str


@dataclass
class PlanStep:
    """A step in an execution plan."""

    name: str
    required_state: State | None = None
    notes: str | None = None


class Planner:
    """Produces execution plans for goals."""

    def __init__(self, *, memory: MemoryStore | None = None) -> None:
        self._memory = memory

    def validate_goal(self, goal: Goal) -> None:
        """Validate goal semantics."""

        if not goal.description.strip():
            raise SmithError("Goal description cannot be empty")

    def generate_plan(
        self,
        goal: Goal,
        available_states: Sequence[State],
    ) -> list[PlanStep]:
        """Generate a simple skeleton plan for the goal."""

        self.validate_goal(goal)
        steps: list[PlanStep] = []
        if available_states:
            steps.append(
                PlanStep(name="analyze_goal", required_state=available_states[0])
            )
        steps.append(PlanStep(name="synthesize_plan"))
        steps.append(PlanStep(name="execute_plan"))
        if self._memory is not None:
            steps.append(PlanStep(name="store_outcome"))
        return steps
