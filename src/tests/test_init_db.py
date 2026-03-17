import unittest
import tempfile
import sqlite3
import os
import sys
import importlib
from unittest.mock import patch, MagicMock

class TestInitDb(unittest.TestCase):
    def setUp(self):
        # Create a temporary file to use as the database
        self.fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(self.fd) # Close so sqlite can use it

        # Define dependencies that might be missing and would cause import errors
        # in other parts of the application that are imported indirectly
        self.mocked_modules = {
            'aiohttp': MagicMock(),
            'flask': MagicMock(),
            'flask_cors': MagicMock(),
            'flask_socketio': MagicMock(),
            'werkzeug': MagicMock(),
            'werkzeug.security': MagicMock(),
            'dotenv': MagicMock(),
            'nodriver': MagicMock(),
        }

        # Start a patch.dict on sys.modules to mock these dependencies
        self.patcher = patch.dict('sys.modules', self.mocked_modules)
        self.patcher.start()

        # Import the module to test and store it
        import api.init_db as init_db_module
        self.init_db_module = init_db_module

        # We also need to reload it in case it was already loaded WITHOUT our mocks or WITH other mocks
        importlib.reload(self.init_db_module)

    def tearDown(self):
        # Stop the patcher to restore original sys.modules
        self.patcher.stop()

        # Remove the temporary file if it exists
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

        # Clean up any cached api modules from sys.modules that might have captured our mocks
        modules_to_remove = [m for m in sys.modules if m.startswith('api.') or m == 'api']
        for m in modules_to_remove:
            del sys.modules[m]

    def test_init_database_creates_tables(self):
        """Test that init_database creates the expected tables."""
        init_database = self.init_db_module.init_database

        # Run init_database
        result = init_database(self.db_path)

        # Verify it reports success
        self.assertTrue(result)

        # Connect to the created database to verify schema
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

        # Use direct cursor iteration to minimize memory overhead per project guidelines
        tables = [row[0] for row in cursor]
        conn.close()

        # Check that required tables are present
        self.assertIn('post_history', tables)
        self.assertIn('settings', tables)
        self.assertIn('tracking_logs', tables)

        # sqlite_sequence is created automatically for AUTOINCREMENT columns
        self.assertIn('sqlite_sequence', tables)

    def test_init_database_error_handling(self):
        """Test that init_database handles connection errors gracefully."""
        init_database = self.init_db_module.init_database

        # Provide an invalid path that cannot be written to
        invalid_path = '/invalid_directory/that_does_not_exist/db.sqlite'

        # Expected to fail and return False
        result = init_database(invalid_path)

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
