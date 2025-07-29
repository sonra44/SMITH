import unittest
import os
import tempfile
import shutil
import sys

# Ensure the smith_tools package is importable when running tests directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from smith_tools import code_ops


class TestCodeOps(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_code_ops_")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_replace_library(self):
        file_path = os.path.join(self.temp_dir, "example.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("import requests\nrequests.get('http://example.com')\n")
        summary = code_ops.replace_library(self.temp_dir, "requests", "httpx")
        # Should scan one file and modify it
        self.assertEqual(summary["files_scanned"], 1)
        self.assertEqual(summary["files_modified"], 1)
        content = open(file_path, "r", encoding="utf-8").read()
        self.assertIn("import httpx", content)
        self.assertIn("httpx.get", content)

    def test_update_dependency(self):
        req_path = os.path.join(self.temp_dir, "requirements.txt")
        with open(req_path, "w", encoding="utf-8") as f:
            f.write("pandas==1.0.0\n")
        summary = code_ops.update_dependency(self.temp_dir, "pandas", "2.0.0")
        self.assertEqual(summary["old_line"].strip(), "pandas==1.0.0")
        self.assertEqual(summary["new_line"], "pandas==2.0.0")
        with open(req_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
        self.assertIn("pandas==2.0.0", lines)

    def test_add_fastapi_endpoint(self):
        # create a FastAPI main file
        main_path = os.path.join(self.temp_dir, "main.py")
        with open(main_path, "w", encoding="utf-8") as f:
            f.write("from fastapi import FastAPI\napp = FastAPI()\n")
        summary = code_ops.add_fastapi_endpoint(self.temp_dir, "/hello", "fastapi")
        self.assertEqual(summary["file"], main_path)
        with open(main_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("@router.get(\"/hello\")", content)

    def test_add_flask_endpoint(self):
        # create a Flask app file
        app_path = os.path.join(self.temp_dir, "app.py")
        open(app_path, "w").close()
        summary = code_ops.add_fastapi_endpoint(self.temp_dir, "/hello", "flask")
        self.assertEqual(summary["file"], app_path)
        content = open(app_path, "r", encoding="utf-8").read()
        self.assertIn("@blueprint.route(\"/hello\", methods=['GET'])", content)

    def test_refactor_godobject(self):
        file_path = os.path.join(self.temp_dir, "GodObject.py")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(
                "class GodObject:\n"
                "    def m1(self): pass\n"
                "    def m2(self): pass\n"
                "    def m3(self): pass\n"
                "    def m4(self): pass\n"
                "    def m5(self): pass\n"
            )
        summary = code_ops.refactor_godobject(self.temp_dir, None)
        self.assertEqual(summary["status"], "succeeded")
        # All new files should exist
        for new_file in summary["new_files"]:
            self.assertTrue(os.path.isfile(os.path.join(self.temp_dir, new_file)))


if __name__ == "__main__":
    unittest.main()