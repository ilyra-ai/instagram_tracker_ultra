import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib

class TestAIVisionDownloadImage(unittest.TestCase):
    def setUp(self):
        self._orig_modules = sys.modules.copy()

        # Mock dependencies that might not be installed
        self.needed_mocks = ['PIL', 'numpy', 'onnxruntime', 'ultralytics', 'requests']
        for module in self.needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

        # Import the class to test after mocking
        import intelligence.ai_vision as ai_vision
        importlib.reload(ai_vision)
        self.ai_vision_module = ai_vision

        # Prevent the __init__ from doing too much, specifically not downloading the model
        with patch.object(self.ai_vision_module.AIVision, '_load_model', return_value=True):
            self.vision = self.ai_vision_module.AIVision()

    def tearDown(self):
        for module in self.needed_mocks:
            if module in sys.modules and sys.modules[module] != self._orig_modules.get(module):
                if module in self._orig_modules:
                    sys.modules[module] = self._orig_modules[module]
                else:
                    del sys.modules[module]

    @patch('intelligence.ai_vision.requests.get')
    def test_download_image_request_exception(self, mock_get):
        """Test that _download_image correctly catches requests exceptions and returns None."""
        # Create a mock exception class since we mocked the requests module entirely
        class MockTimeoutException(Exception):
            pass

        # Configure the mock to raise our exception
        mock_get.side_effect = MockTimeoutException("Connection timed out")

        # Call the method
        test_url = "https://example.com/test_image.jpg"
        result = self.vision._download_image(test_url)

        # Verify the exception was caught and None was returned
        self.assertIsNone(result)
        mock_get.assert_called_once_with(
            test_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'},
            timeout=30
        )

if __name__ == '__main__':
    unittest.main()
