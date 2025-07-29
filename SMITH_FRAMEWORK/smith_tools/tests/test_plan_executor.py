
import unittest
import os
import tempfile
import shutil
import sys
from unittest.mock import patch

# Adjust path to import smith_tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from smith_tools.plan_executor import PlanExecutor

class TestPlanExecutor(unittest.TestCase):
    def setUp(self):
        self.test_project_dir = tempfile.mkdtemp(prefix="test_proj_")
        self.test_smith_dir = tempfile.mkdtemp(prefix="test_smith_")
        self.executor = PlanExecutor(project_root=self.test_project_dir, smith_root=self.test_smith_dir)

    def tearDown(self):
        shutil.rmtree(self.test_project_dir)
        shutil.rmtree(self.test_smith_dir)

    def test_execute_step_unknown_action(self):
        step = {"action": "non_existent_action"}
        result = self.executor.execute_step(step)
        self.assertEqual(result["status"], "failed")
        self.assertIn("Unknown action", result["error"])

    @patch('smith_tools.human_feedback_tool.HumanFeedbackTool.request_confirmation')
    def test_human_feedback_confirmed(self, mock_request_confirmation):
        mock_request_confirmation.return_value = True
        step = {"action": "human_feedback", "question": "Proceed?"}
        result = self.executor.execute_step(step)
        self.assertEqual(result["status"], "succeeded")

    @patch('smith_tools.human_feedback_tool.HumanFeedbackTool.request_confirmation')
    def test_human_feedback_denied(self, mock_request_confirmation):
        mock_request_confirmation.return_value = False
        step = {"action": "human_feedback", "question": "Proceed?"}
        result = self.executor.execute_step(step)
        self.assertEqual(result["status"], "failed")
        self.assertIn("cancelled by user", result["error"])

    @patch('smith_tools.code_ops.replace_library')
    def test_modify_code_replace_library(self, mock_replace_library):
        mock_replace_library.return_value = {"status": "succeeded", "summary": "Replaced requests with httpx"}
        step = {
            "action": "modify_code",
            "operation": "replace_library",
            "old_lib": "requests",
            "new_lib": "httpx"
        }
        result = self.executor.execute_step(step)
        self.assertEqual(result["status"], "succeeded")
        mock_replace_library.assert_called_once_with(self.test_project_dir, "requests", "httpx")

    @patch('smith_tools.project_verifier.ProjectVerifier.run_pytest')
    def test_verify_code_pytest(self, mock_run_pytest):
        mock_run_pytest.return_value = {"status": "succeeded", "output": "All tests passed"}
        step = {"action": "verify_code", "tool": "pytest"}
        result = self.executor.execute_step(step)
        self.assertEqual(result["status"], "succeeded")
        mock_run_pytest.assert_called_once()

    def test_run_command_success(self):
        step = {"action": "run_command", "command": "echo 'hello'"}
        result = self.executor.execute_step(step)
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["stdout"].strip(), "hello")

    def test_run_command_failure(self):
        step = {"action": "run_command", "command": "non_existent_command"}
        result = self.executor.execute_step(step)
        self.assertEqual(result["status"], "failed")
        self.assertIn("failed", result["error"])

if __name__ == "__main__":
    unittest.main()
