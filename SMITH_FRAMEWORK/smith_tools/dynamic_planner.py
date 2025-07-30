"""
Dynamic Planner (v3 - LLM-Powered)
------------------------------------

This version of the planner offloads the decision-making process to a
Large Language Model via the MCPGateway. It is responsible for constructing
the system prompt and parsing the LLM's response.
"""

from typing import List, Dict, Any, Optional

from .project_navigator import ProjectNavigator

MAX_HISTORY_ITEMS = 5
MAX_FILE_LIST = 20
MAX_CODE_PREVIEW = 500

# We now import the gateway to the LLM
from .mcp_gateway import MCPGateway

class DynamicPlanner:
    """Generates a plan by querying an LLM on each step."""

    def __init__(self, prompt: str, project_root: str):
        self.prompt = prompt
        self.project_root = project_root
        self.history: List[Dict[str, Any]] = []
        self._task_complete = False
        self._step_counter = 0
        # The planner now has a gateway to the "Master Control Program"
        self.gateway = MCPGateway()
        self.navigator = ProjectNavigator()

    def record_step_result(self, result: Dict[str, Any]):
        """Records the result of a step and marks the task as complete on failure."""
        self.history.append(result)
        if result.get("status") == "failed":
            self._task_complete = True

    def get_next_step(self) -> Optional[Dict[str, Any]]:
        """Constructs a system prompt and queries the LLM for the next step."""
        if self._task_complete:
            return None

        # Construct the detailed system prompt for the LLM
        system_prompt = self._build_system_prompt()

        # Query the LLM for the next step
        llm_response = self.gateway.generate_step(system_prompt)

        # If the LLM decides to finish, we stop.
        if not llm_response or llm_response.get("action") == "finish_task":
            self._task_complete = True
            return None

        # Prepare the step for the executor
        step = self._create_step_from_llm_response(llm_response)
        return step

    def _build_system_prompt(self) -> str:
        """Builds the complete context for the LLM to make a decision."""
        project_map = self.navigator.create_project_map(self.project_root)
        project_files = list(project_map.get("files", {}).keys())[:MAX_FILE_LIST]
        structure_lines = ["## СТРУКТУРА ПРОЕКТА:"]
        structure_lines.append(f"Файлы Python: {project_files}")
        structure_lines.append("Основные модули:")
        for fname in project_files:
            info = project_map["files"].get(fname, {})
            if "error" in info:
                continue
            classes = [f"{c['name']} ({', '.join(c['methods'])})" for c in info.get("classes", [])]
            funcs = [f"{f['name']}()" for f in info.get("functions", [])]
            details = ", ".join(filter(None, classes + funcs))
            if details:
                structure_lines.append(f"- {fname}: {details}")
        project_section = "\n".join(structure_lines)

        prompt_template = f"""
Ты — ИИ-агент SMITH, эксперт по Python-разработке.
Твоя задача: {self.prompt}
Ты находишься в проекте: {self.project_root}
{project_section}

## ИСТОРИЯ ВЫПОЛНЕННЫХ ШАГОВ:
{self._format_history()}

## ДОСТУПНЫЕ ИНСТРУМЕНТЫ (ACTIONS):
- `run_command`: {{ "command": "<shell_command>" }} - Выполняет любую shell-команду.
- `modify_code`: {{ "operation": "<op_name>", ... }} - Изменяет код (например, `replace_library`).
- `verify_code`: {{ "tool": "<tool_name>" }} - Запускает тесты или линтеры (`pytest`, `flake8`).
- `human_feedback`: {{ "question": "<text>" }} - Запрашивает подтверждение у пользователя.
- `finish_task`: {{ "reason": "<text>" }} - Завершает всю задачу.

## ПРИМЕРЫ УСПЕШНЫХ ОПЕРАЦИЙ:
1. Добавление endpoint:
   - Нашли main.py
   - Добавили импорт: from routes import new_router
   - Добавили: app.include_router(new_router)
2. Рефакторинг:
   - Нашли большой класс
   - Разделили на 3 файла
   - Обновили импорты

## ЗАДАНИЕ:
Проанализируй историю и основную цель. Какой **один** следующий шаг нужно сделать?
Отвечай ТОЛЬКО в формате JSON:
{{
  "action": "run_command|modify_code|verify_code",
  "parameters": {{}},
  "description": "Что делаем",
  "reasoning": "Почему это нужно"
}}
"""
        return prompt_template.strip()

    def _format_history(self) -> str:
        if not self.history:
            return "История пуста. Это самый первый шаг."
        
        formatted_lines = []
        recent = self.history[-MAX_HISTORY_ITEMS:]
        for i, record in enumerate(recent):
            step = record.get("step", {})
            result = record.get("result", {})
            status = result.get("status", "unknown")
            
            line = f"{i+1}. ШАГ: {step.get('description', 'N/A')}\n   ДЕЙСТВИЕ: {step.get('action')}, ПАРАМЕТРЫ: {step.get('parameters', {})}\n   СТАТУС: {status.upper()}\n"
            
            if status == "failed":
                line += f"   ОШИБКА: {result.get('error', 'N/A')}\n"
            elif result.get("stdout"):
                line += f"   ВЫВОД: {result.get('stdout').strip()}\n"
            formatted_lines.append(line)
            
        return "\n".join(formatted_lines)

    def _create_step_from_llm_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Converts the LLM's JSON response into a step for the executor."""
        self._step_counter += 1
        # We merge the parameters directly into the top-level step dictionary
        # for the executor to use.
        step = {
            "id": self._step_counter,
            "action": response.get("action"),
            "description": response.get("description", "Шаг, сгенерированный LLM."),
            **(response.get("parameters", {}))
        }
        return step

    def is_finished(self) -> bool:
        return self._task_complete
