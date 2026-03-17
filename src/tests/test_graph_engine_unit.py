import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib

class TestGraphEngineImports(unittest.TestCase):
    """
    Test cases for the import logic of NetworkX in Graph Engine.
    Uses localized mocking to avoid polluting the global sys.modules.
    """

    def setUp(self):
        # Save original sys.modules to restore after tests
        self._orig_modules = sys.modules.copy()

        # Define dependencies that might be missing and would cause import errors
        # We only mock them if they are not already present to minimize side effects
        self.needed_mocks = [
            'requests', 'cv2', 'ultralytics', 'PIL', 'vaderSentiment',
            'statsmodels', 'scipy', 'numpy', 'matplotlib',
            'python-louvain', 'community', 'aiohttp'
        ]

        for module in self.needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

    def tearDown(self):
        # Restore original sys.modules
        # We need to be careful not to remove things that were loaded during the test
        # but also to remove our mocks.
        for module in self.needed_mocks:
            if module in sys.modules and sys.modules[module] != self._orig_modules.get(module):
                if module in self._orig_modules:
                    sys.modules[module] = self._orig_modules[module]
                else:
                    del sys.modules[module]

    def test_networkx_import_failure(self):
        """Test that the module handles missing networkx correctly."""
        # Use patch.dict to remove 'networkx' from sys.modules
        with patch.dict('sys.modules', {'networkx': None, 'networkx.algorithms': None}):
            # Reload the module to trigger the try-except block
            # We import it here to ensure it's in sys.modules before reloading
            import intelligence.graph_engine as graph_engine
            importlib.reload(graph_engine)

            # Verify the constants
            self.assertFalse(graph_engine.NETWORKX_AVAILABLE)
            self.assertIsNone(graph_engine.nx)

    def test_networkx_import_success(self):
        """Test that the module handles present networkx correctly."""
        # Mock networkx and its algorithms
        mock_nx = MagicMock()
        mock_community = MagicMock()

        with patch.dict('sys.modules', {
            'networkx': mock_nx,
            'networkx.algorithms': MagicMock(),
            'networkx.algorithms.community': mock_community
        }):
            # Reload the module
            import intelligence.graph_engine as graph_engine
            importlib.reload(graph_engine)

            # Verify the constants
            self.assertTrue(graph_engine.NETWORKX_AVAILABLE)
            self.assertIsNotNone(graph_engine.nx)

class TestGraphDatabase(unittest.TestCase):
    """
    Test cases for GraphDatabase exceptions.
    """

    def setUp(self):
        # Mock modules just like TestGraphEngineImports does
        self._orig_modules = sys.modules.copy()
        self.needed_mocks = [
            'requests', 'cv2', 'ultralytics', 'PIL', 'vaderSentiment',
            'statsmodels', 'scipy', 'numpy', 'matplotlib',
            'python-louvain', 'community', 'aiohttp', 'nodriver'
        ]

        for module in self.needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

    def tearDown(self):
        for module in self.needed_mocks:
            if module in sys.modules and sys.modules[module] != self._orig_modules.get(module):
                if module in self._orig_modules:
                    sys.modules[module] = self._orig_modules[module]
                else:
                    del sys.modules[module]

    def test_get_all_nodes_exception(self):
        """Test that get_all_nodes handles exceptions correctly and returns an empty list."""
        from intelligence.graph_engine import GraphDatabase

        # Instantiate without the mock so that __init__ and _init_db execute correctly
        db = GraphDatabase(":memory:")

        with patch('sqlite3.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = Exception("Simulated database cursor error")
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            with patch('intelligence.graph_engine.logger.error') as mock_logger:
                result = db.get_all_nodes()
                self.assertEqual(result, [])
                mock_logger.assert_called_once_with("Erro ao obter nós: Simulated database cursor error")


if __name__ == '__main__':
    unittest.main()
