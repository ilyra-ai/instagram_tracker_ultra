import sys
import importlib
import unittest
from unittest.mock import MagicMock, patch

class TestAIVisionSingleton(unittest.TestCase):
    def setUp(self):
        # Create a dictionary of mocks for the missing dependencies
        self.mock_modules = {
            'PIL': MagicMock(),
            'PIL.Image': MagicMock(),
            'numpy': MagicMock(),
            'onnxruntime': MagicMock(),
            'ultralytics': MagicMock(),
            'requests': MagicMock()
        }

        # Start the patcher for sys.modules
        self.patcher = patch.dict('sys.modules', self.mock_modules)
        self.patcher.start()

        # Now import the module. If it was already imported, reload it to ensure
        # it picks up the mocked dependencies.
        import intelligence.ai_vision
        importlib.reload(intelligence.ai_vision)
        self.ai_vision_module = intelligence.ai_vision

    def tearDown(self):
        # Stop the patcher to clean up sys.modules
        self.patcher.stop()

    def test_get_ai_vision_singleton(self):
        """Test that get_ai_vision returns the same AIVision instance (singleton pattern)."""
        instance1 = self.ai_vision_module.get_ai_vision()
        self.assertIsInstance(instance1, self.ai_vision_module.AIVision, "get_ai_vision should return an AIVision instance")

        instance2 = self.ai_vision_module.get_ai_vision()
        self.assertIs(instance1, instance2, "Multiple calls to get_ai_vision should return the exact same instance")

if __name__ == '__main__':
    unittest.main()
