import argparse
import json
import sys
import os
import yaml
from datetime import datetime, timezone
from filelock import FileLock, Timeout

CONFIG = {}


def load_config():
    """Loads the framework configuration from config.yaml."""
    global CONFIG
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError("Framework config.yaml not found!")
    with open(config_path, "r") as f:
        CONFIG = yaml.safe_load(f)


def get_tasks_file_path():
    """Constructs the path to the tasks.json file based on config."""
    # Allow overriding for testing purposes
    if "TASKS_FILE_OVERRIDE" in os.environ:
        return os.environ["TASKS_FILE_OVERRIDE"]

    smith_root = CONFIG.get("smith_root_dir")
    if not smith_root:
        raise ValueError("smith_root_dir not set in config.yaml")
    return os.path.join(smith_root, ".gemini", "memory", "tasks.json")


def get_tasks(tasks_file):
    """Reads tasks from the JSON file. Creates the file if it doesn't exist."""
    lock_path = tasks_file + ".lock"
    lock = FileLock(lock_path, timeout=5)
    try:
        with lock:
            if not os.path.exists(tasks_file):
                with open(tasks_file, "w") as f:
                    json.dump([], f)
                return []
            with open(tasks_file, "r") as f:
                return json.load(f)
    except Timeout:
        raise IOError(
            f"Could not acquire lock on {tasks_file}. Another process may be using it."
        )
    except json.JSONDecodeError:
        raise ValueError(f"Could not decode JSON from {tasks_file}.")


def save_tasks(tasks, tasks_file):
    """Saves the list of tasks back to the JSON file."""
    lock_path = tasks_file + ".lock"
    lock = FileLock(lock_path, timeout=5)
    try:
        with lock:
            with open(tasks_file, "w") as f:
                json.dump(tasks, f, indent=2)
    except Timeout:
        raise IOError(
            f"Could not acquire lock on {tasks_file}. Another process may be using it."
        )


def add_task(description, project, tasks_file):
    """Adds a new task."""
    tasks = get_tasks(tasks_file)
    new_id = max([task.get("id", 0) for task in tasks], default=0) + 1

    new_task = {
        "id": new_id,
        "description": description,
        "status": "pending",  # Allowed: pending, in_progress, done, failed, paused
        "project": project,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "history": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": "created",
            }
        ],
    }
    tasks.append(new_task)
    save_tasks(tasks, tasks_file)
    return new_task


def update_task_status(task_id, new_status, tasks_file):
    """Updates the status of a task and records the change in its history."""
    tasks = get_tasks(tasks_file)
    task_found = False
    for task in tasks:
        if task["id"] == task_id:
            task["status"] = new_status
            task["updated_at"] = datetime.now(timezone.utc).isoformat()
            task.setdefault("history", []).append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "action": f"status changed to {new_status}",
                }
            )
            if new_status == "done":
                task["completed_at"] = datetime.now(timezone.utc).isoformat()
            task_found = True
            break

    if not task_found:
        raise ValueError(f"Task with ID {task_id} not found.")

    save_tasks(tasks, tasks_file)
    return task


def main():
    """Main CLI handler."""
    try:
        load_config()
        tasks_file = get_tasks_file_path()
    except (FileNotFoundError, ValueError) as e:
        print(f"[FATAL] {e}", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(description="SMITH's Task Manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new task")
    add_parser.add_argument(
        "--description", required=True, help="The task description"
    )
    add_parser.add_argument(
        "--project", required=True, help="The project the task belongs to"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List tasks")
    list_parser.add_argument("--project", help="Filter by project name")
    list_parser.add_argument("--status", help="Filter by status")
    list_parser.add_argument(
        "--json", action="store_true", help="Output the results in JSON format"
    )

    # Update status command
    update_parser = subparsers.add_parser(
        "update", help="Update a task's status"
    )
    update_parser.add_argument(
        "id", type=int, help="The ID of the task to update"
    )
    update_parser.add_argument(
        "--status",
        required=True,
        choices=["pending", "in_progress", "done", "failed", "paused"],
        help="The new status",
    )

    args = parser.parse_args()

    try:
        if args.command == "add":
            new_task = add_task(args.description, args.project, tasks_file)
            print(
                f"Successfully added task {new_task['id']}: '{new_task['description']}'"
            )

        elif args.command == "list":
            tasks = get_tasks(tasks_file)
            filtered_tasks = tasks
            if args.project:
                filtered_tasks = [
                    t
                    for t in filtered_tasks
                    if t.get("project") == args.project
                ]
            if args.status:
                filtered_tasks = [
                    t for t in filtered_tasks if t.get("status") == args.status
                ]

            if args.json:
                print(json.dumps(filtered_tasks, indent=2))
            elif not filtered_tasks:
                print("No tasks found matching the criteria.")
            else:
                print(
                    f"{'ID':<4} | {'Status':<12} | {'Project':<15} | {'Description'}"
                )
                print("-" * 70)
                for task in filtered_tasks:
                    print(
                        f"{task['id']:<4} | {task.get('status', 'N/A'):<12} | {task.get('project', 'N/A'):<15} | {task.get('description', 'N/A')}"
                    )

        elif args.command == "update":
            updated_task = update_task_status(args.id, args.status, tasks_file)
            print(
                f"Task {updated_task['id']} status updated to '{updated_task['status']}'."
            )

    except (ValueError, IOError, FileNotFoundError) as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
