"""
Proof‑of‑Concept (PoC) TUI for the SMITH Cockpit.

This script lays out the basic screen structure described in the technical
specification using `prompt_toolkit`. It does not connect to the live agent
backend and instead uses static, hard‑coded data to illustrate how the
Cockpit might look when displaying a plan, execution log and contextual
information.

Run this script directly to view the mock interface. Press Ctrl‑C to exit.
"""

from __future__ import annotations

import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.layout import HSplit, VSplit, Layout
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style


def main() -> None:
    """Entry point for the PoC TUI."""
    # Static content as described in the specification
    prompt_text = "Задача: Рефакторинг класса GodObject.py\nСтатус: EXECUTING (Шаг 2 из 4)"
    plan_text = """[✔] 1. Analyze project structure
[▶] 2. Refactor GodObject.py
    [ ] 2.1. Find usages of GodObject
    [ ] 2.2. Extract DataProcessor class
[ ] 3. Run unit tests"""
    log_text = """> Вызов project_verifier.py...\n> ================= test session starts =================\n> collected 15 items\n> tests/test_logic.py::test_addition PASSED  [ 6%]\n> ..."""
    context_text = "Project: QIKI_DTMP | Language: Python | Tests: pytest | (Ctrl-C to Abort)"

    # Create read‑only text areas for each panel
    status_area = TextArea(text=prompt_text, focusable=False, read_only=True)
    plan_area = TextArea(text=plan_text, focusable=False, read_only=True, scrollbar=True)
    log_area = TextArea(text=log_text, focusable=False, read_only=True, scrollbar=True)
    context_area = TextArea(text=context_text, focusable=False, read_only=True)

    # Compose layout: top status, then left/right panes, then bottom context
    body = HSplit([
        status_area,
        VSplit([
            plan_area,
            log_area,
        ], padding=1),
        context_area,
    ])

    layout = Layout(body)

    # Define key bindings. Ctrl‑C exits the application.
    kb = KeyBindings()

    @kb.add("c-c")
    def _(event) -> None:
        event.app.exit()

    # Basic style
    style = Style.from_dict({
        "textarea": "bg:#1e1e1e #d4d4d4",
    })

    app = Application(layout=layout, key_bindings=kb, full_screen=True, style=style)
    try:
        asyncio.run(app.run_async())
    except (KeyboardInterrupt, EOFError):
        # Graceful exit when Ctrl‑C is pressed outside of prompt_toolkit's handler
        pass


if __name__ == "__main__":
    main()