
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Mock dependencies that might be missing
sys.modules['requests'] = MagicMock()
sys.modules['tenacity'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

from ai.ollama_client import OllamaClient

class TestOllamaClientSSRF(unittest.TestCase):
    @patch('requests.get')
    def test_ssrf_vulnerability_fixed(self, mock_get):
        # Simulate an attacker providing a malicious URL via environment variable
        malicious_url = "http://169.254.169.254/latest/meta-data/"
        with patch.dict(os.environ, {"OLLAMA_API_BASE_URL": malicious_url}):
            client = OllamaClient()
            # _check_connection should NOT be called because URL validation fails
            mock_get.assert_not_called()
            self.assertFalse(client.is_configured)
            print("SSRF attempt blocked successfully.")

    @patch('requests.get')
    def test_valid_local_url(self, mock_get):
        # Mock requests.get to return a response object
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Use a valid local URL
        valid_url = "http://localhost:11434"
        with patch.dict(os.environ, {"OLLAMA_API_BASE_URL": valid_url}):
            client = OllamaClient()
            # _check_connection SHOULD be called
            self.assertTrue(mock_get.called)
            print("Valid local URL allowed.")

if __name__ == '__main__':
    unittest.main()
