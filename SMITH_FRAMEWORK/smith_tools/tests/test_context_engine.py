import unittest
import os
import sys
import tempfile
import shutil

# Add the smith_tools directory to the Python path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from context_engine import analyze_file, analyze_code


class TestContextEngine(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_test_file(self, content):
        file_path = os.path.join(self.test_dir, "test_file.py")
        with open(file_path, "w") as f:
            f.write(content)
        return file_path

    def test_analyze_valid_file(self):
        """Test analyzing a file with a mix of classes and functions."""
        mock_code = (
            "import os\n"
            "\n"
            "class MyClass:\n"
            "    def method_one(self):\n"
            "        pass\n"
            "\n"
            "def top_level_function():\n"
            "    pass\n"
            "\n"
            "async def async_function():\n"
            "    pass\n"
        )
        file_path = self._create_test_file(mock_code)
        result = analyze_file(file_path)

        self.assertEqual(len(result["classes"]), 1)
        self.assertEqual(result["classes"][0]["name"], "MyClass")
        self.assertEqual(result["classes"][0]["methods"], ["method_one"])

        self.assertEqual(len(result["functions"]), 2)
        func_names = {f["name"] for f in result["functions"]}
        self.assertEqual(func_names, {"top_level_function", "async_function"})

    def test_analyze_file_not_found(self):
        """Test handling of a non-existent file."""
        with self.assertRaises(FileNotFoundError):
            analyze_file("non_existent_file.py")

    def test_analyze_syntax_error(self):
        """Test handling of a file with syntax errors."""
        file_path = self._create_test_file("def invalid_syntax(")
        with self.assertRaises(ValueError):
            analyze_file(file_path)

    def test_no_classes_or_functions(self):
        """Test analyzing a file with no classes or functions."""
        file_path = self._create_test_file("print('Hello, World!')\nx = 10")
        result = analyze_file(file_path)
        self.assertEqual(result["classes"], [])
        self.assertEqual(result["functions"], [])


if __name__ == "__main__":
    unittest.main()
