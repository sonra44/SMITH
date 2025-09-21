"""File manipulation tool adapter."""

from __future__ import annotations

from pathlib import Path

from smith.utils.errors import SmithError


class FilesTool:
    """Perform simple file operations inside the sandbox."""

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def _resolve(self, relative_path: str) -> Path:
        target = (self._root / relative_path).resolve()
        try:
            target.relative_to(self._root)
        except ValueError as error:
            raise SmithError("Attempt to escape sandbox root") from error
        return target

    def read(self, relative_path: str) -> str:
        """Read text file from sandbox."""

        path = self._resolve(relative_path)
        return path.read_text(encoding="utf-8")

    def write(self, relative_path: str, content: str) -> None:
        """Write text content to sandbox."""

        path = self._resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
