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
    """Test cases for the GraphDatabase class, specifically the save_node method."""

    def setUp(self):
        # We need to test save_node which creates its own connection using self.db_path
        # So we can use a temporary file for the database to ensure connections share the same data.
        import tempfile
        import os

        # Mock dependencies that might be missing in test environment
        self._orig_modules = sys.modules.copy()
        self.needed_mocks = [
            'requests', 'cv2', 'ultralytics', 'PIL', 'vaderSentiment',
            'statsmodels', 'scipy', 'numpy', 'matplotlib',
            'python-louvain', 'community', 'aiohttp'
        ]

        for module in self.needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

        from intelligence.graph_engine import GraphDatabase
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.temp_db_fd)

        # Initialize GraphDatabase with the temp path
        self.db = GraphDatabase(self.temp_db_path)

    def tearDown(self):
        import os
        if os.path.exists(self.temp_db_path):
            os.remove(self.temp_db_path)

        # Restore sys.modules
        for module in self.needed_mocks:
            if module in sys.modules and sys.modules[module] != self._orig_modules.get(module):
                if module in self._orig_modules:
                    sys.modules[module] = self._orig_modules[module]
                else:
                    del sys.modules[module]

    def test_save_node_insert(self):
        """Test that a new node is successfully inserted into the database."""
        from intelligence.graph_engine import GraphNode, NodeType, CommunityRole
        import sqlite3
        import json

        # Create a sample node
        node = GraphNode(
            id="user123",
            node_type=NodeType.USER,
            label="user123_label",
            data={"follower_count": 100},
            degree_centrality=0.5,
            betweenness_centrality=0.1,
            closeness_centrality=0.2,
            pagerank=0.05,
            community_id=1,
            role=CommunityRole.LEADER,
            color="#FFFFFF",
            size=2.5,
            x=10.0,
            y=20.0,
            z=30.0
        )

        # Save the node
        result = self.db.save_node(node)
        self.assertTrue(result)

        # Verify it was saved correctly
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM nodes WHERE id = ?", ("user123",))
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "user123")  # id
        self.assertEqual(row[1], "user")  # node_type
        self.assertEqual(row[2], "user123_label")  # label
        self.assertEqual(json.loads(row[3]), {"follower_count": 100})  # data
        self.assertEqual(row[4], 0.5)  # degree_centrality
        self.assertEqual(row[5], 0.1)  # betweenness_centrality
        self.assertEqual(row[6], 0.2)  # closeness_centrality
        self.assertEqual(row[7], 0.05)  # pagerank
        self.assertEqual(row[8], 1)  # community_id
        self.assertEqual(row[9], "leader")  # role
        self.assertEqual(row[10], "#FFFFFF")  # color
        self.assertEqual(row[11], 2.5)  # size
        self.assertEqual(row[12], 10.0)  # x
        self.assertEqual(row[13], 20.0)  # y
        self.assertEqual(row[14], 30.0)  # z

    def test_save_node_update(self):
        """Test that saving an existing node updates its values."""
        from intelligence.graph_engine import GraphNode, NodeType, CommunityRole
        import sqlite3

        # Create and save initial node
        node = GraphNode(
            id="user_update",
            node_type=NodeType.USER,
            label="initial_label",
            data={"status": "initial"}
        )
        self.db.save_node(node)

        # Modify the node
        node.label = "updated_label"
        node.data = {"status": "updated"}
        node.pagerank = 0.99
        node.color = "#FF0000"

        # Save again (should update)
        result = self.db.save_node(node)
        self.assertTrue(result)

        # Verify it was updated
        conn = sqlite3.connect(self.temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT label, data, pagerank, color FROM nodes WHERE id = ?", ("user_update",))
        row = cursor.fetchone()

        # Verify row count
        cursor.execute("SELECT COUNT(*) FROM nodes WHERE id = ?", ("user_update",))
        count = cursor.fetchone()[0]
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "updated_label")
        import json
        self.assertEqual(json.loads(row[1]), {"status": "updated"})
        self.assertEqual(row[2], 0.99)
        self.assertEqual(row[3], "#FF0000")

        # Should still be exactly 1 row for this id
        self.assertEqual(count, 1)

    def test_save_node_error(self):
        """Test that save_node returns False and handles exceptions on error."""
        from intelligence.graph_engine import GraphNode, NodeType

        # Create a node missing required fields to trigger an SQLite error.
        # However, GraphNode dataclass requires the fields, so we can't easily make a malformed one
        # that passes Python type checking but fails SQL.
        # Instead, we can mock sqlite3.connect to raise an Exception.
        node = GraphNode(id="error_node", node_type=NodeType.USER, label="error_label", data={})

        with patch('sqlite3.connect', side_effect=Exception("Simulated database error")):
            result = self.db.save_node(node)
            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
