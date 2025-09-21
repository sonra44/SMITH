"""Command-line interface for the SMITH agent."""

from __future__ import annotations

import sys

import typer

from smith.core.fsm import FiniteStateMachine, State, Transition
from smith.core.planner import Goal, Planner
from smith.core.registry import policy_registry, tool_registry
from smith.io.config import SmithConfig
from smith.io.telemetry import JSONTelemetryLogger, TelemetryEvent, configure_logging
from smith.utils.errors import SmithError

app = typer.Typer(help="SMITH agent command-line interface")


def _bootstrap(goal: str) -> None:
    """Prepare subsystems for execution."""

    config = SmithConfig.load()
    logger = configure_logging(stream=sys.stdout)
    telemetry = JSONTelemetryLogger(logger)
    telemetry.emit(
        TelemetryEvent(
            code=100,
            message="run-command-start",
            payload={"goal": goal},
        )
    )

    planner = Planner()
    states = [State(name="idle"), State(name="executing"), State(name="done")]
    machine = FiniteStateMachine(
        states=states,
        transitions=[
            Transition(source=states[0], target=states[1]),
            Transition(source=states[1], target=states[2]),
        ],
        initial=states[0],
    )
    plan = planner.generate_plan(Goal(goal), available_states=states)
    telemetry.emit(
        TelemetryEvent(
            code=200,
            message="plan-generated",
            payload={"steps": [step.name for step in plan]},
        )
    )
    telemetry.emit(
        TelemetryEvent(
            code=210,
            message="fsm-initial-state",
            payload={"state": machine.current.name},
        )
    )
    telemetry.emit(
        TelemetryEvent(
            code=900,
            message="run-command-finished",
            payload={
                "sandbox_root": str(config.sandbox_root),
                "policies": [name for name, _ in policy_registry.items()],
                "tools": [name for name, _ in tool_registry.items()],
            },
        )
    )


@app.command()
def run(
    goal: str = typer.Option(
        ...,
        "--goal",
        help="Desired outcome for the agent to pursue.",
    ),
) -> None:
    """Execute the SMITH agent with the provided goal."""

    try:
        _bootstrap(goal)
    except SmithError as error:
        typer.secho(f"Error: {error}", err=True, fg=typer.colors.RED)
        raise typer.Exit(code=1) from error


def main() -> None:
    """Entrypoint used by the console script."""

    app()


if __name__ == "__main__":
    main()
