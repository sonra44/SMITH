import unittest
import os
import json
import subprocess
import sys
import tempfile
import shutil

# This assumes the script is in the parent directory
SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "task_manager.py")

class TestTaskManager(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory and a unique tasks file for each test."""
        self.test_dir = tempfile.mkdtemp()
        self.tasks_file = os.path.join(self.test_dir, "tasks.json")
        os.environ["TASKS_FILE_OVERRIDE"] = self.tasks_file
        # Create an empty one
        with open(self.tasks_file, "w") as f:
            json.dump([], f)

    def tearDown(self):
        """Clean up the test environment after each test."""
        shutil.rmtree(self.test_dir)
        del os.environ["TASKS_FILE_OVERRIDE"]

    def run_script(self, args):
        """Helper function to run the task manager script as a subprocess."""
        command = [sys.executable, SCRIPT_PATH] + args
        return subprocess.run(command, capture_output=True, text=True)

    def test_01_add_task(self):
        """Test adding a new task."""
        result = self.run_script(
            ["add", "--description", "Test Task 1", "--project", "TEST"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Successfully added task", result.stdout)

        with open(self.tasks_file, "r") as f:
            tasks = json.load(f)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]["description"], "Test Task 1")

    def test_02_list_tasks(self):
        """Test listing tasks."""
        self.run_script(
            ["add", "--description", "Task A", "--project", "PROJ1"]
        )
        self.run_script(
            ["add", "--description", "Task B", "--project", "PROJ2"]
        )

        result = self.run_script(["list"])
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Task A", result.stdout)
        self.assertIn("Task B", result.stdout)

    def test_03_complete_task(self):
        """Test completing a task."""
        self.run_script(
            ["add", "--description", "Task to complete", "--project", "TEST"]
        )

        result = self.run_script(["update", "1", "--status", "done"])
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("status updated to 'done'", result.stdout)

        with open(self.tasks_file, "r") as f:
            tasks = json.load(f)
        self.assertEqual(tasks[0]["status"], "done")

    def test_04_error_on_missing_task(self):
        """Test that completing a non-existent task fails."""
        result = self.run_script(["update", "999", "--status", "done"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Task with ID 999 not found", result.stderr)
