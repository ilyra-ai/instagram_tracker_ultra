import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Mock dependencies
sys.modules['nodriver'] = MagicMock()
sys.modules['curl_cffi'] = MagicMock()
sys.modules['aiohttp'] = MagicMock()
sys.modules['bs4'] = MagicMock()
sys.modules['tenacity'] = MagicMock()

from core.browser_manager import SessionManager


class TestSessionManager(unittest.TestCase):
    def setUp(self):
        # Ensure SESSION_ENCRYPTION_KEY is not set by default during tests
        if 'SESSION_ENCRYPTION_KEY' in os.environ:
            del os.environ['SESSION_ENCRYPTION_KEY']

    def test_session_manager_init_with_password(self):
        """Test that SessionManager initializes successfully with a provided password."""
        sm = SessionManager(password="my_secure_password")
        self.assertEqual(sm.password, "my_secure_password")

    @patch.dict(os.environ, {'SESSION_ENCRYPTION_KEY': 'env_secure_password'})
    def test_session_manager_init_with_env_var(self):
        """Test that SessionManager initializes successfully using the environment variable."""
        sm = SessionManager()
        self.assertEqual(sm.password, "env_secure_password")

    def test_session_manager_init_without_password_or_env_var(self):
        """Test that SessionManager raises ValueError when neither password nor env var is provided."""
        with self.assertRaises(ValueError) as context:
            SessionManager()

        self.assertIn("SESSION_ENCRYPTION_KEY environment variable is missing", str(context.exception))

if __name__ == '__main__':
    unittest.main()
