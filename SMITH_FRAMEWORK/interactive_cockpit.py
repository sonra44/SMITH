"""
interactive_cockpit.py
----------------------

The new, reliable, interactive TUI for the SMITH Agent.
Built on a working foundation and with correct import handling.
"""

from __future__ import annotations

import logging
import sys
import os

# Setup basic logging for debugging
log_file = os.path.join(os.path.dirname(__file__), 'cockpit_debug.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
    filemode='w' # Overwrite log on each run
)

# Correctly set up Python path to handle package imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import argparse
import asyncio
import json
import queue
import threading
from typing import Any, Dict, List, Tuple, Optional

from prompt_toolkit.application import Application
from prompt_toolkit.layout import HSplit, VSplit, Layout
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from smith_tools.dynamic_planner import DynamicPlanner
from smith_tools.smith_agent import PlanExecutor


Event = Tuple[str, Any, Any, Any]


class CockpitUI:
    """Controller class responsible for rendering and updating the TUI."""

    def __init__(self, event_queue: queue.Queue, prompt: str, project_root: str) -> None:
        self.event_queue = event_queue
        self.prompt = prompt
        self.project_root = project_root
        self.plan: List[Dict[str, Any]] = []
        self.step_status: Dict[int, str] = {}
        self.current_step: Optional[int] = None
        self.final_status: Optional[str] = None
        self.status_area = TextArea(focusable=False, read_only=True, height=2, style="class:status")
        self.plan_area = TextArea(focusable=False, read_only=True, scrollbar=True, style="class:plan")
        self.log_area = TextArea(focusable=False, read_only=True, scrollbar=True, style="class:log")
        self.context_area = TextArea(focusable=False, read_only=True, height=1, style="class:context")
        self._init_context()
        self._update_status()
        body = HSplit([
            self.status_area,
            VSplit([self.plan_area, self.log_area], padding=1),
            self.context_area,
        ])
        self.layout = Layout(body)
        kb = KeyBindings()
        @kb.add("c-c")
        def _(event) -> None:
            logging.info("Ctrl-C pressed. Exiting.")
            event.app.exit()
        self.style = Style.from_dict({
            "status":  "fg:#ffffff bg:#005f87 bold",
            "plan":    "bg:#0d0d0d fg:#00ff41",
            "log":     "bg:#0d0d0d fg:#00d7ff",
            "context": "bg:#0d0d0d fg:#ffaf00",
        })
        self.application = Application(
            layout=self.layout, key_bindings=kb, full_screen=True, style=self.style
        )

    def _init_context(self) -> None:
        parts: List[str] = [f"Проект: {os.path.basename(self.project_root)}"]
        parts.append("(Ctrl-C для выхода)")
        self.context_area.text = " | ".join(parts)

    def _update_status(self) -> None:
        status_map = {
            "succeeded": "УСПЕШНО ЗАВЕРШЕНО",
            "failed": "ПРЕРВАНО С ОШИБКОЙ",
            "running": "ВЫПОЛНЕНИЕ",
            "pending": "ОЖИДАНИЕ"
        }
        if self.final_status is not None:
            status_line = f"Статус: {status_map.get(self.final_status, self.final_status.upper())}"
        elif self.current_step is not None:
            status_line = f"Статус: {status_map['running']} (Шаг {self.current_step})"
        else:
            status_line = "Статус: ПЛАНИРОВАНИЕ"
        self.status_area.text = f"Задача: {self.prompt}\n{status_line}"

    def _add_step_to_plan(self, step: Dict[str, Any]):
        """Adds a new step to the plan display."""
        self.plan.append(step)
        self.step_status[step["id"]] = "pending"
        self._update_plan()

    def _update_plan(self) -> None:
        lines: List[str] = []
        for step in self.plan:
            step_id = step.get("id")
            desc = step.get("description", "")
            status = self.step_status.get(step_id, "pending")
            indent_level = str(step_id).count('.') if isinstance(step_id, str) else 0
            indent = "  " * indent_level
            prefix = {"success": "[✔]", "failed": "[✘]", "running": "[▶]"}.get(status, "[ ]")
            id_str = f"{step_id}. " if step_id is not None else ""
            lines.append(f"{prefix} {indent}{id_str}{desc}")
        self.plan_area.text = "\n".join(lines)

    def _append_log(self, message: str) -> None:
        if not message: return
        if self.log_area.text:
            self.log_area.text += "\n" + message
        else:
            self.log_area.text = message

    async def _process_events(self) -> None:
        logging.info("Event processing loop started.")
        while True:
            try:
                event = self.event_queue.get_nowait()
                logging.info(f"Event received: {event[0]}")
            except queue.Empty:
                await asyncio.sleep(0.1)
                continue
            if not isinstance(event, tuple) or not event: continue
            event_type, payload = event[0], event[1:]
            if event_type == "AGENT_FINISHED":
                logging.info("AGENT_FINISHED event received. Stopping event loop.")
                self.final_status = payload[0]
                self.current_step = None
                if len(payload) > 1 and payload[1]: self._append_log(str(payload[1]))
                self._update_plan()
                self._update_status()
                self.application.invalidate()
                break # Exit the loop
            elif event_type == "NEW_STEP":
                self._add_step_to_plan(payload[0])
            elif event_type == "STEP_STARTED":
                step_id = payload[0]
                self.current_step = step_id
                self.step_status[step_id] = "running"
            elif event_type == "TOOL_OUTPUT":
                self._append_log(payload[1])
            elif event_type == "STEP_FINISHED":
                step_id, status, error_message = payload
                self.step_status[step_id] = "success" if status == "succeeded" else "failed"
                if error_message: self._append_log(error_message)
            self._update_plan()
            self._update_status()
            self.application.invalidate()
        logging.info("Event processing loop finished.")

    async def run(self) -> None:
        logging.info("UI run started.")
        asyncio.get_event_loop().create_task(self._process_events())
        await self.application.run_async()
        logging.info("UI run finished.")

import time

def run_agent_in_thread(prompt: str, project_root: str, event_queue: queue.Queue) -> None:
    """The main agent loop, now fully dynamic."""
    logging.info("Dynamic agent thread started.")
    time.sleep(0.5) # Give UI time to initialize
    try:
        planner = DynamicPlanner(prompt, project_root)
        # The executor now requires both the project root and the framework's own root.
        smith_root = os.path.dirname(__file__)
        executor = PlanExecutor(project_root, smith_root)
        
        while not planner.is_finished():
            # 1. Get the next step from the dynamic planner
            next_step = planner.get_next_step()
            if not next_step:
                logging.info("Planner has no more steps. Finishing.")
                break

            # 2. Announce the new step to the TUI
            event_queue.put(("NEW_STEP", next_step))
            # Add a small delay for visualization, so we can see the step appear
            time.sleep(0.3)

            # 3. Execute the step
            step_id = next_step.get("id")
            event_queue.put(("STEP_STARTED", step_id))
            result = executor.execute_step(next_step)
            
            # 4. Record the result for the planner to use in its next decision
            result["step"] = next_step # Add the step itself to the result for context
            planner.record_step_result(result)
            
            # 5. Announce the result to the TUI
            status = result.get("status", "failed")
            err_msg = result.get("error", result.get("stderr", "")) or ""
            event_queue.put(("STEP_FINISHED", step_id, status, err_msg))

            # 6. Halt on failure
            if status != "succeeded":
                logging.warning(f"Step {step_id} failed. Halting execution.")
                break

            # 7. Add a final delay for visualization
            time.sleep(0.3)

    except Exception as exc:
        logging.exception("An unhandled exception occurred in the agent thread.")
        event_queue.put(("AGENT_FINISHED", "failed", str(exc)))
    finally:
        logging.info("Agent thread finished. Sending AGENT_FINISHED event.")
        event_queue.put(("AGENT_FINISHED", "succeeded"))

def main() -> None:
    logging.info("Main function started.")
    parser = argparse.ArgumentParser(description="SMITH Cockpit: real‑time TUI for the SMITH Agent.")
    parser.add_argument("--prompt", required=True, help="The high‑level task for the agent to perform.")
    parser.add_argument("--project-root", required=True, help="Absolute path to the project root directory.")
    args = parser.parse_args()
    evt_queue: queue.Queue = queue.Queue()
    agent_thread = threading.Thread(
        target=run_agent_in_thread,
        args=(args.prompt, args.project_root, evt_queue),
        daemon=True,
        name="AgentThread"
    )
    agent_thread.start()
    logging.info("Agent thread kicked off.")
    ui = CockpitUI(evt_queue, args.prompt, args.project_root)
    try:
        asyncio.run(ui.run())
    except (KeyboardInterrupt, EOFError):
        logging.info("Keyboard interrupt received. Exiting gracefully.")
    finally:
        logging.info("Main function finished.")

if __name__ == "__main__":
    main()