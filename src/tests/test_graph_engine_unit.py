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
            {'full_name': 'Missing Username'} # Should be ignored
        ]
        following = [
            {'username': 'mutual', 'full_name': 'Mutual User'},
            {'username': 'just_following', 'full_name': 'Just Following'},
            {} # Should be ignored
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
