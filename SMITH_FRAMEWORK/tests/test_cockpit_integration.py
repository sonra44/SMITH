
import unittest
from unittest.mock import MagicMock
import sys
import os

# This setup is crucial. It mimics how a real script would need to see the project structure.
# We add the root of the project, not the script's own directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestCockpitIntegration(unittest.TestCase):

    def test_import_and_initialization(self):
        """
        Tests if interactive_cockpit.py can be imported and its main UI class
        can be initialized without the 'ModuleNotFoundError'.
        This is the primary integration check.
        """
        try:
            # We try to import the module now that the path is set up correctly
            from SMITH_FRAMEWORK import interactive_cockpit
            
            # We simulate the basic objects needed to initialize the UI class
            mock_queue = MagicMock()
            cockpit_ui = interactive_cockpit.CockpitUI(mock_queue, "test_prompt", "/fake/root")
            
            # If we get here, it means the import and initialization succeeded.
            self.assertIsNotNone(cockpit_ui, "CockpitUI object should be created successfully.")
            
        except ImportError as e:
            self.fail(f"CRITICAL: Failed to import interactive_cockpit. The path setup is likely still incorrect. Error: {e}")
        except Exception as e:
            self.fail(f"An unexpected error occurred during UI initialization: {e}")

if __name__ == '__main__':
    unittest.main()
