import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, mock_open

# Add the smith_tools directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

# Now, mcp_gateway can be imported
from mcp_gateway import is_path_safe, read_file, write_file, load_config

class TestMCPGateway(unittest.TestCase):

    def setUp(self):
        """Create a temporary directory to act as the project root."""
        self.project_root = tempfile.mkdtemp()
        self.safe_dir = os.path.join(self.project_root, "test_dir")
        os.makedirs(self.safe_dir, exist_ok=True)
        self.safe_file = os.path.join(self.safe_dir, "safe_file.txt")
        self.unsafe_file = "/etc/passwd"  # A known path outside the project root

        # Create a dummy config for tests
        self.config_patch = patch('mcp_gateway.CONFIG', {
            'default_project_root': self.project_root
        })
        self.config_patch.start()


    def tearDown(self):
        """Remove the temporary directory and its contents."""
        shutil.rmtree(self.project_root)
        self.config_patch.stop()

    # --- Test is_path_safe ---
    def test_path_is_safe(self):
        self.assertTrue(is_path_safe(self.safe_file, self.project_root))

    def test_path_is_unsafe(self):
        self.assertFalse(is_path_safe(self.unsafe_file, self.project_root))

    def test_path_traversal_attack(self):
        malicious_path = os.path.join(self.safe_dir, "../../../../etc/hosts")
        self.assertFalse(is_path_safe(malicious_path, self.project_root))

    def test_project_root_itself_is_safe(self):
        self.assertTrue(is_path_safe(self.project_root, self.project_root))

    # --- Test read_file ---
    def test_read_file_safe_path_returns_content(self):
        """read_file should return the content, not print it."""
        mock_content = "file content"
        # Create a real file to be read
        with open(self.safe_file, "w") as f:
            f.write(mock_content)

        content = read_file(self.safe_file, project_root=self.project_root)
        self.assertEqual(content, mock_content)

    def test_read_file_unsafe_path_raises_error(self):
        with self.assertRaises(ValueError):
            read_file(self.unsafe_file, project_root=self.project_root)

    def test_read_nonexistent_file_raises_error(self):
        non_existent_file = os.path.join(self.project_root, "nonexistent.txt")
        with self.assertRaises(FileNotFoundError):
            read_file(non_existent_file, project_root=self.project_root)


    # --- Test write_file ---
    def test_write_file_safe_path_writes_content(self):
        """write_file should successfully write content to a safe path."""
        new_content = "new content"
        write_file(self.safe_file, new_content, project_root=self.project_root)

        with open(self.safe_file, "r") as f:
            content = f.read()
        self.assertEqual(content, new_content)


    def test_write_file_unsafe_path_raises_error(self):
        with self.assertRaises(ValueError):
            write_file(self.unsafe_file, "content", project_root=self.project_root)


if __name__ == "__main__":
    unittest.main()
