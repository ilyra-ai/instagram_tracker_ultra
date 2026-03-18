import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib
import tempfile
import os

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
    Test cases for GraphDatabase exception handling.
    Tests error paths using mocked connections.
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

    @patch('sqlite3.connect')
    def test_save_node_error(self, mock_connect):
        """Test that save_node returns False when an exception occurs."""
        from intelligence.graph_engine import GraphDatabase, GraphNode, NodeType

        # Make the connection throw an exception to test the except block
        mock_connect.side_effect = Exception("Mock DB error")

        # Disable _init_db to prevent creating the table during initialization
        with patch.object(GraphDatabase, '_init_db'):
            db = GraphDatabase(db_path=":memory:")

        node = GraphNode(
            id="test_node",
            node_type=NodeType.USER,
            label="Test Node",
            data={}
        )

        result = db.save_node(node)
        self.assertFalse(result)

    @patch('sqlite3.connect')
    def test_save_edge_error(self, mock_connect):
        """Test that save_edge returns False when an exception occurs."""
        from intelligence.graph_engine import GraphDatabase, GraphEdge, EdgeType

        mock_connect.side_effect = Exception("Mock DB error")

        with patch.object(GraphDatabase, '_init_db'):
            db = GraphDatabase(db_path=":memory:")

        edge = GraphEdge(
            source="user1",
            target="user2",
            edge_type=EdgeType.FOLLOWS
        )

        result = db.save_edge(edge)
        self.assertFalse(result)


class TestGraphDatabaseOperations(unittest.TestCase):
    """
    Integration-level tests for GraphDatabase CRUD operations.
    Uses a real temporary file database for each test to ensure isolation.
    """

    @classmethod
    def setUpClass(cls):
        # Mock dependencies missing in testing environment before importing
        cls._class_orig_modules = sys.modules.copy()
        cls.needed_mocks = [
            'requests', 'cv2', 'ultralytics', 'PIL', 'vaderSentiment',
            'statsmodels', 'scipy', 'numpy', 'matplotlib',
            'python-louvain', 'community', 'aiohttp'
        ]
        for module in cls.needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

    @classmethod
    def tearDownClass(cls):
        for module in cls.needed_mocks:
            if module in sys.modules and sys.modules[module] != cls._class_orig_modules.get(module):
                if module in cls._class_orig_modules:
                    sys.modules[module] = cls._class_orig_modules[module]
                else:
                    del sys.modules[module]

    def setUp(self):
        # Import inside setUp to ensure class-level mocks are active
        from intelligence.graph_engine import GraphDatabase, GraphNode, NodeType, CommunityRole, EdgeType
        self.GraphDatabase = GraphDatabase
        self.GraphNode = GraphNode
        self.NodeType = NodeType
        self.CommunityRole = CommunityRole
        self.EdgeType = EdgeType
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

    def test_get_node_success(self):
        """Test retrieving an existing node successfully."""
        import json
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

        retrieved_node = self.db.get_node("test_user")

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
        """Test error handling when retrieving a node fails."""
        with patch('sqlite3.connect', side_effect=Exception("Database error")):
            retrieved_node = self.db.get_node("test_user")
            self.assertIsNone(retrieved_node)

    def test_save_node_insert(self):
        """Test that a new node is successfully inserted into the database."""
        import sqlite3
        import json

        node = self.GraphNode(
            id="user123",
            node_type=self.NodeType.USER,
            label="user123_label",
            data={"follower_count": 100},
            degree_centrality=0.5,
            betweenness_centrality=0.1,
            closeness_centrality=0.2,
            pagerank=0.05,
            community_id=1,
            role=self.CommunityRole.LEADER,
            color="#FFFFFF",
            size=2.5,
            x=10.0,
            y=20.0,
            z=30.0
        )

        result = self.db.save_node(node)
        self.assertTrue(result)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM nodes WHERE id = ?", ("user123",))
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "user123")
        self.assertEqual(row[1], "user")
        self.assertEqual(row[2], "user123_label")
        self.assertEqual(json.loads(row[3]), {"follower_count": 100})
        self.assertEqual(row[4], 0.5)
        self.assertEqual(row[5], 0.1)
        self.assertEqual(row[6], 0.2)
        self.assertEqual(row[7], 0.05)
        self.assertEqual(row[8], 1)
        self.assertEqual(row[9], "leader")
        self.assertEqual(row[10], "#FFFFFF")
        self.assertEqual(row[11], 2.5)
        self.assertEqual(row[12], 10.0)
        self.assertEqual(row[13], 20.0)
        self.assertEqual(row[14], 30.0)

    def test_save_node_update(self):
        """Test that saving an existing node updates its values (upsert)."""
        import sqlite3
        import json

        node = self.GraphNode(
            id="user_update",
            node_type=self.NodeType.USER,
            label="initial_label",
            data={"status": "initial"}
        )
        self.db.save_node(node)

        node.label = "updated_label"
        node.data = {"status": "updated"}
        node.pagerank = 0.99
        node.color = "#FF0000"

        result = self.db.save_node(node)
        self.assertTrue(result)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT label, data, pagerank, color FROM nodes WHERE id = ?", ("user_update",))
        row = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) FROM nodes WHERE id = ?", ("user_update",))
        count = cursor.fetchone()[0]
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "updated_label")
        self.assertEqual(json.loads(row[1]), {"status": "updated"})
        self.assertEqual(row[2], 0.99)
        self.assertEqual(row[3], "#FF0000")
        self.assertEqual(count, 1)


class TestBuildGraphFromFollowers(unittest.TestCase):
    """
    Test cases for build_graph_from_followers in SocialGraphAnalyzer.
    """
    def setUp(self):
        # We need to mock the database to avoid actual file system changes
        # Mock dependencies in sys.modules like in the other test class if needed
        self._orig_modules = sys.modules.copy()
        self.needed_mocks = [
            'requests', 'cv2', 'ultralytics', 'PIL', 'vaderSentiment',
            'statsmodels', 'scipy', 'numpy', 'matplotlib',
            'python-louvain', 'community', 'aiohttp'
        ]

        for module in self.needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

        # Import modules after mocks
        from intelligence.graph_engine import SocialGraphAnalyzer, GraphDatabase

        # Create the mock database
        self.mock_db = MagicMock(spec=GraphDatabase)

        # Instantiate analyzer with mocked DB
        self.analyzer = SocialGraphAnalyzer(database=self.mock_db)

    def tearDown(self):
        for module in self.needed_mocks:
            if module in sys.modules and sys.modules[module] != self._orig_modules.get(module):
                if module in self._orig_modules:
                    sys.modules[module] = self._orig_modules[module]
                else:
                    del sys.modules[module]

    def test_empty_lists(self):
        from intelligence.graph_engine import NodeType

        # Act
        self.analyzer.build_graph_from_followers('target_user', [], [])

        # Assert
        # Should only contain the central node
        self.assertEqual(len(self.analyzer.nodes), 1)
        self.assertIn('target_user', self.analyzer.nodes)

        central_node = self.analyzer.nodes['target_user']
        self.assertEqual(central_node.node_type, NodeType.USER)
        self.assertTrue(central_node.data.get('is_central'))

        # Should have 0 edges
        self.assertEqual(len(self.analyzer.edges), 0)

        # Verify db was saved once for node, 0 for edge
        self.mock_db.save_node.assert_called()
        self.mock_db.save_edge.assert_not_called()

    def test_followers_only_no_mutual(self):
        from intelligence.graph_engine import EdgeType

        # Arrange
        followers = [
            {'username': 'user1', 'full_name': 'User One'},
            {'username': 'user2', 'full_name': 'User Two'}
        ]
        following = []

        # Act
        self.analyzer.build_graph_from_followers('target_user', followers, following)

        # Assert
        # 1 central node + 2 follower nodes
        self.assertEqual(len(self.analyzer.nodes), 3)
        self.assertIn('user1', self.analyzer.nodes)
        self.assertIn('user2', self.analyzer.nodes)

        # 2 edges pointing to the central node
        self.assertEqual(len(self.analyzer.edges), 2)
        for edge in self.analyzer.edges:
            self.assertEqual(edge.target, 'target_user')
            self.assertIn(edge.source, ['user1', 'user2'])
            self.assertEqual(edge.edge_type, EdgeType.FOLLOWS)
            self.assertEqual(edge.weight, 1.0)

    def test_following_only_no_mutual(self):
        from intelligence.graph_engine import EdgeType

        # Arrange
        followers = []
        following = [
            {'username': 'user3', 'full_name': 'User Three'},
            {'username': 'user4', 'full_name': 'User Four'}
        ]

        # Act
        self.analyzer.build_graph_from_followers('target_user', followers, following)

        # Assert
        # 1 central node + 2 followed nodes
        self.assertEqual(len(self.analyzer.nodes), 3)
        self.assertIn('user3', self.analyzer.nodes)
        self.assertIn('user4', self.analyzer.nodes)

        # 2 edges pointing from the central node
        self.assertEqual(len(self.analyzer.edges), 2)
        for edge in self.analyzer.edges:
            self.assertEqual(edge.source, 'target_user')
            self.assertIn(edge.target, ['user3', 'user4'])
            self.assertEqual(edge.edge_type, EdgeType.FOLLOWS)
            self.assertEqual(edge.weight, 1.0)

    def test_mutual_connections(self):
        from intelligence.graph_engine import EdgeType

        # Arrange
        followers = [{'username': 'mutual1', 'full_name': 'Mutual One'}]
        following = [{'username': 'mutual1', 'full_name': 'Mutual One'}]

        # Act
        self.analyzer.build_graph_from_followers('target_user', followers, following)

        # Assert
        # 1 central node + 1 mutual node
        self.assertEqual(len(self.analyzer.nodes), 2)
        self.assertIn('mutual1', self.analyzer.nodes)
        self.assertTrue(self.analyzer.nodes['mutual1'].data.get('is_mutual'))

        # 1 edge pointing to target_user with MUTUAL edge_type and weight 2.0
        self.assertEqual(len(self.analyzer.edges), 1)
        edge = self.analyzer.edges[0]
        self.assertEqual(edge.source, 'mutual1')
        self.assertEqual(edge.target, 'target_user')
        self.assertEqual(edge.edge_type, EdgeType.MUTUAL)
        self.assertEqual(edge.weight, 2.0)

    def test_mixed_scenario_and_missing_username(self):
        from intelligence.graph_engine import EdgeType

        # Arrange
        followers = [
            {'username': 'mutual', 'full_name': 'Mutual User'},
            {'username': 'just_follower', 'full_name': 'Just Follower'},
            {'full_name': 'Missing Username'}  # Should be ignored
        ]
        following = [
            {'username': 'mutual', 'full_name': 'Mutual User'},
            {'username': 'just_following', 'full_name': 'Just Following'},
            {}  # Should be ignored
        ]

        # Act
        self.analyzer.build_graph_from_followers('target_user', followers, following)

        # Assert
        # 1 central + 1 mutual + 1 follower + 1 following = 4 nodes
        self.assertEqual(len(self.analyzer.nodes), 4)

        # 3 edges: 1 mutual, 1 follower -> target, 1 target -> following
        self.assertEqual(len(self.analyzer.edges), 3)

        # Verify specific edges
        edges = {(e.source, e.target): e for e in self.analyzer.edges}

        # mutual edge
        mutual_edge = edges.get(('mutual', 'target_user'))
        self.assertIsNotNone(mutual_edge)
        self.assertEqual(mutual_edge.edge_type, EdgeType.MUTUAL)

        # just follower edge
        follower_edge = edges.get(('just_follower', 'target_user'))
        self.assertIsNotNone(follower_edge)
        self.assertEqual(follower_edge.edge_type, EdgeType.FOLLOWS)

        # just following edge
        following_edge = edges.get(('target_user', 'just_following'))
        self.assertIsNotNone(following_edge)
        self.assertEqual(following_edge.edge_type, EdgeType.FOLLOWS)


if __name__ == '__main__':
    unittest.main()
