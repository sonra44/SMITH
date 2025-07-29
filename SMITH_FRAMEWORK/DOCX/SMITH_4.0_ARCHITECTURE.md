# SMITH 4.0: Canon Architecture Document

## 1. Vision and Principles

**SMITH Framework** is an autonomous, interactive AI agent designed to act as a competent partner for software engineers. It automates routine tasks, performs complex refactoring, and maintains code quality.

- **Safety:** Operations are predictable and require user confirmation.
- **Autonomy:** The agent can decompose high-level tasks into concrete steps.
- **Adaptability:** The agent learns and adapts to the project's conventions.
- **Transparency:** All actions and decisions are logged and explainable.

## 2. Core Architecture: Mind, Hands, Memory

The framework is composed of three core vectors, located in the isolated `SMITH_FRAMEWORK` directory.

### 2.1. The "Mind": `smith_agent.py`

The core orchestrator responsible for planning and execution.

- **Prompt Parser:** Uses NLP to understand user intent (e.g., "add function", "refactor") and extract entities (file names, function names).
- **Dynamic Planner:** Generates a Directed Acyclic Graph (DAG) of tasks. This plan is adaptive, supporting conditional branches, parallel execution, and human feedback loops.
- **Plan Executor:** Executes the plan, manages data flow between tools, and handles errors.

### 2.2. The "Hands": `smith_tools/`

A collection of atomic, single-purpose tools.

- **`code_ops.py`:** Performs complex, AST-based code modifications (e.g., replacing libraries, refactoring God Objects, adding API endpoints).
- **`context_engine.py`:** Provides deep semantic code analysis, including finding usages, building import graphs, and constructing call graphs.
- **`project_verifier.py`:** Ensures code quality by running tests (`pytest`) and linters (`ruff`, `flake8`).
- **`human_feedback_tool.py`:** Formalizes user interaction, asking for confirmation on critical steps. Behavior can be controlled via the `SMITH_AUTO_CONFIRM` environment variable.
- **`task_manager.py`:** A CLI for managing the project's task list.

### 2.3. The "Memory": `.gemini/memory/`

The agent's long-term storage for learning and adaptation.

- **`tasks.json`:** A database of all tasks, linking them to the plans, logs, and outcomes.
- **`.project_meta.json`:** An auto-generated "passport" for each project, storing its language, frameworks, test commands, and coding style. The agent consults this file to adapt its behavior.
- **`reflections.log`:** The agent's learning journal. After each task, the agent reflects on the outcome, analyzes failures, and derives new rules to avoid repeating mistakes.

## 3. Maturity Criteria

The framework is considered mature when it can autonomously handle complex requests such as:

1.  "Add a new API endpoint `/users/{id}` to our FastAPI project and cover it with a unit test."
2.  "Replace all usages of the `requests` library with `httpx`, updating the syntax to be async."
3.  "Refactor the `GodObject.py` class into smaller, single-responsibility classes."

This document represents the single source of truth for the SMITH 4.0 architecture.