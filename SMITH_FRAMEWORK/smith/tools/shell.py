"""Shell execution tool adapter."""

from __future__ import annotations

import shlex
import subprocess
from collections.abc import Sequence
from pathlib import Path

from smith.runtime.policies import ExecutionPolicy
from smith.utils.errors import SmithError


class ShellTool:
    """Execute shell commands subject to sandbox policies."""

    def __init__(self, *, sandbox_root: Path, policy: ExecutionPolicy) -> None:
        self._sandbox_root = sandbox_root.resolve()
        self._policy = policy

    def run(
        self,
        command: Sequence[str] | str,
        *,
        timeout: float = 60.0,
    ) -> subprocess.CompletedProcess[str]:
        """Run a command inside the sandbox."""

        if isinstance(command, str):
            command_args = shlex.split(command)
        else:
            command_args = [str(part) for part in command]
        if not command_args:
            raise SmithError("Shell command cannot be empty")
        command_tuple = tuple(command_args)
        if not self._policy.is_allowed(command_tuple):
            raise SmithError("Command is rejected by the execution policy")
        return subprocess.run(
            command_tuple,
            capture_output=True,
            cwd=self._sandbox_root,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
        )
