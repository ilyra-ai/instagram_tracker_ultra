import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib
import sqlite3
import uuid

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
    """Test cases for GraphDatabase."""

    def setUp(self):
        self._orig_modules = sys.modules.copy()

        # Mock dependencies that might be missing
        self.needed_mocks = [
            'requests', 'cv2', 'ultralytics', 'PIL', 'vaderSentiment',
            'statsmodels', 'scipy', 'numpy', 'matplotlib',
            'python-louvain', 'community', 'aiohttp'
        ]

        for module in self.needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

        # Import after mocking to avoid ModuleNotFoundError
        from intelligence.graph_engine import GraphDatabase, GraphNode, NodeType, CommunityRole

        # Create an in-memory database for testing
        # Use a unique shared memory database for each test to ensure isolation
        self.db_path = f"file:memdb_{uuid.uuid4().hex}?mode=memory&cache=shared"

        # We need to keep one connection open to keep the shared memory DB alive
        self.keepalive_conn = sqlite3.connect(self.db_path, uri=True)

        # Patch sqlite3.connect to pass uri=True when connecting to our path
        self.original_connect = sqlite3.connect
        def mock_connect(database, *args, **kwargs):
            if database == self.db_path:
                return self.original_connect(database, uri=True, *args, **kwargs)
            return self.original_connect(database, *args, **kwargs)

        self.connect_patcher = patch('sqlite3.connect', side_effect=mock_connect)
        self.mock_connect = self.connect_patcher.start()

        self.db = GraphDatabase(db_path=self.db_path)
        self.GraphNode = GraphNode
        self.NodeType = NodeType
        self.CommunityRole = CommunityRole

    def tearDown(self):
        if hasattr(self, 'connect_patcher'):
            self.connect_patcher.stop()
        if hasattr(self, 'keepalive_conn'):
            self.keepalive_conn.close()

        # Restore original sys.modules
        for module in self.needed_mocks:
            if module in sys.modules and sys.modules[module] != self._orig_modules.get(module):
                if module in self._orig_modules:
                    sys.modules[module] = self._orig_modules[module]
                else:
                    del sys.modules[module]

    def test_get_node_success(self):
        """Test retrieving an existing node successfully."""
        # Create and save a node
        test_node = self.GraphNode(
            id="test_user",
            node_type=self.NodeType.USER,
            label="Test User",
            data={"follower_count": 100},
            degree_centrality=0.5,
            betweenness_centrality=0.2,
            closeness_centrality=0.3,
            pagerank=0.1,
            community_id=1,
            role=self.CommunityRole.MEMBER,
            color="#FF0000",
            size=2.0,
            x=10.0,
            y=20.0,
            z=30.0
        )
        self.db.save_node(test_node)

        # Retrieve the node
        retrieved_node = self.db.get_node("test_user")

        # Verify
        self.assertIsNotNone(retrieved_node)
        self.assertEqual(retrieved_node.id, "test_user")
        self.assertEqual(retrieved_node.node_type, self.NodeType.USER)
        self.assertEqual(retrieved_node.label, "Test User")
        self.assertEqual(retrieved_node.data, {"follower_count": 100})
        self.assertEqual(retrieved_node.degree_centrality, 0.5)
        self.assertEqual(retrieved_node.betweenness_centrality, 0.2)
        self.assertEqual(retrieved_node.closeness_centrality, 0.3)
        self.assertEqual(retrieved_node.pagerank, 0.1)
        self.assertEqual(retrieved_node.community_id, 1)
        self.assertEqual(retrieved_node.role, self.CommunityRole.MEMBER)
        self.assertEqual(retrieved_node.color, "#FF0000")
        self.assertEqual(retrieved_node.size, 2.0)
        self.assertEqual(retrieved_node.x, 10.0)
        self.assertEqual(retrieved_node.y, 20.0)
        self.assertEqual(retrieved_node.z, 30.0)

    def test_get_node_not_found(self):
        """Test retrieving a non-existent node returns None."""
        retrieved_node = self.db.get_node("non_existent_user")
        self.assertIsNone(retrieved_node)

    def test_get_node_error(self):
        """Test error handling when retrieving a node."""
        # Patch sqlite3.connect within the test to raise an Exception
        with patch('sqlite3.connect', side_effect=Exception("Database error")):
            retrieved_node = self.db.get_node("test_user")
            self.assertIsNone(retrieved_node)

if __name__ == '__main__':
    unittest.main()
