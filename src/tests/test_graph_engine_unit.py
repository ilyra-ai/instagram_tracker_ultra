import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib
import tempfile
import os

class TestGraphDatabase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Mock dependencies missing in testing environment before importing
        needed_mocks = [
            'requests', 'cv2', 'ultralytics', 'PIL', 'vaderSentiment',
            'statsmodels', 'scipy', 'numpy', 'matplotlib',
            'python-louvain', 'community', 'aiohttp'
        ]
        for module in needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

    @classmethod
    def tearDownClass(cls):
        # We can clean up, but it's not strictly necessary for this file.
        pass

    """
    Test cases for GraphDatabase.
    """
    def setUp(self):
        # Import inside setUp to ensure mocks are active
        from intelligence.graph_engine import GraphDatabase, GraphNode, NodeType
        self.GraphNode = GraphNode
        self.NodeType = NodeType
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_graphs.db")
        self.db = GraphDatabase(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_all_nodes(self):
        """Test that get_all_nodes correctly retrieves all saved nodes."""
        node1 = self.GraphNode(
            id="user1",
            node_type=self.NodeType.USER,
            label="user1",
            data={'is_central': True}
        )
        node2 = self.GraphNode(
            id="user2",
            node_type=self.NodeType.USER,
            label="user2",
            data={'is_central': False}
        )

        self.db.save_node(node1)
        self.db.save_node(node2)

        nodes = self.db.get_all_nodes()
        self.assertEqual(len(nodes), 2)

        node_ids = {n.id for n in nodes}
        self.assertIn("user1", node_ids)
        self.assertIn("user2", node_ids)


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

if __name__ == '__main__':
    unittest.main()
