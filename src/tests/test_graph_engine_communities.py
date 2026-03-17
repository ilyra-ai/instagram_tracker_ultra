import unittest
from unittest.mock import patch, MagicMock
import sys
import importlib

class TestGraphEngineCommunities(unittest.TestCase):
    """
    Test cases for the detect_communities method in Graph Engine.
    Uses localized mocking to avoid polluting the global sys.modules.
    """

    def setUp(self):
        # Save original sys.modules to restore after tests
        self._orig_modules = sys.modules.copy()

        # Define dependencies that might be missing and would cause import errors
        self.needed_mocks = [
            'requests', 'cv2', 'ultralytics', 'PIL', 'vaderSentiment',
            'statsmodels', 'scipy', 'matplotlib',
            'aiohttp'
        ]

        for module in self.needed_mocks:
            if module not in sys.modules:
                sys.modules[module] = MagicMock()

    def tearDown(self):
        # Restore original sys.modules
        for module in self.needed_mocks:
            if module in sys.modules and sys.modules[module] != self._orig_modules.get(module):
                if module in self._orig_modules:
                    sys.modules[module] = self._orig_modules[module]
                else:
                    del sys.modules[module]

    def test_detect_communities_with_networkx(self):
        """Test community detection using the Louvain algorithm via networkx."""
        import intelligence.graph_engine as graph_engine

        if not graph_engine.NETWORKX_AVAILABLE:
            self.skipTest("NetworkX is not available, cannot test Louvain algorithm")

        with patch.object(graph_engine.GraphDatabase, 'save_node', return_value=True), \
             patch.object(graph_engine.GraphDatabase, 'save_edge', return_value=True):

            analyzer = graph_engine.SocialGraphAnalyzer(database=graph_engine.GraphDatabase())
            analyzer.nodes.clear()
            analyzer.edges.clear()

            # Create a mock graph with 2 distinct communities

            # Community 1: A, B, C, D (K4)
            comm1_nodes = ['A', 'B', 'C', 'D']
            for node_id in comm1_nodes:
                analyzer.nodes[node_id] = graph_engine.GraphNode(
                    id=node_id, node_type=graph_engine.NodeType.USER, label=node_id, data={}
                )
            for i in range(len(comm1_nodes)):
                for j in range(i+1, len(comm1_nodes)):
                    analyzer.edges.append(graph_engine.GraphEdge(comm1_nodes[i], comm1_nodes[j], graph_engine.EdgeType.FOLLOWS))

            # Community 2: X, Y, Z, W (K4)
            comm2_nodes = ['X', 'Y', 'Z', 'W']
            for node_id in comm2_nodes:
                analyzer.nodes[node_id] = graph_engine.GraphNode(
                    id=node_id, node_type=graph_engine.NodeType.USER, label=node_id, data={}
                )
            for i in range(len(comm2_nodes)):
                for j in range(i+1, len(comm2_nodes)):
                    analyzer.edges.append(graph_engine.GraphEdge(comm2_nodes[i], comm2_nodes[j], graph_engine.EdgeType.FOLLOWS))

            # Bridge between communities
            analyzer.edges.append(graph_engine.GraphEdge('A', 'X', graph_engine.EdgeType.FOLLOWS))

            # Force centrality calculation to ensure bridge roles can be identified
            # Note: betweenness centrality assigns > 0 to nodes on paths between other nodes
            analyzer.nodes['A'].betweenness_centrality = 0.2
            analyzer.nodes['X'].betweenness_centrality = 0.2

            # Force pagerank calculation to ensure leader roles can be identified
            analyzer.nodes['A'].pagerank = 0.5
            analyzer.nodes['X'].pagerank = 0.5

            communities = analyzer.detect_communities()

            # We expect exactly 2 communities
            self.assertEqual(len(communities), 2)

            members_list = [set(c.members) for c in communities]

            # Both communities should be identified
            self.assertIn(set(comm1_nodes), members_list)
            self.assertIn(set(comm2_nodes), members_list)

            # Ensure leader and bridge roles were set
            # A and X have high centrality
            self.assertIn(analyzer.nodes['A'].role, [graph_engine.CommunityRole.LEADER, graph_engine.CommunityRole.BRIDGE])
            self.assertIn(analyzer.nodes['X'].role, [graph_engine.CommunityRole.LEADER, graph_engine.CommunityRole.BRIDGE])

            # Regular nodes should be MEMBER
            self.assertEqual(analyzer.nodes['B'].role, graph_engine.CommunityRole.MEMBER)

    def test_detect_communities_fallback(self):
        """Test community detection fallback when networkx is not available."""
        import intelligence.graph_engine as graph_engine

        with patch.object(graph_engine, 'NETWORKX_AVAILABLE', False):
            with patch.object(graph_engine.GraphDatabase, 'save_node', return_value=True), \
                 patch.object(graph_engine.GraphDatabase, 'save_edge', return_value=True):

                analyzer = graph_engine.SocialGraphAnalyzer(database=graph_engine.GraphDatabase())
                analyzer.nodes.clear()
                analyzer.edges.clear()

                # The fallback looks for nodes pointing to a central node
                analyzer.nodes['central'] = graph_engine.GraphNode(
                    id='central', node_type=graph_engine.NodeType.USER, label='central', data={'is_central': True}
                )
                analyzer.nodes['A'] = graph_engine.GraphNode(
                    id='A', node_type=graph_engine.NodeType.USER, label='A', data={}
                )
                analyzer.nodes['B'] = graph_engine.GraphNode(
                    id='B', node_type=graph_engine.NodeType.USER, label='B', data={}
                )

                # A and B point to central
                analyzer.edges.append(graph_engine.GraphEdge('A', 'central', graph_engine.EdgeType.FOLLOWS))
                analyzer.edges.append(graph_engine.GraphEdge('B', 'central', graph_engine.EdgeType.FOLLOWS))

                communities = analyzer.detect_communities()

                # Should find 1 community (the fallback community of central node's followers)
                self.assertEqual(len(communities), 1)
                self.assertEqual(communities[0].id, 0)
                self.assertEqual(set(communities[0].members), {'A', 'B'})
                self.assertEqual(communities[0].label, "Comunidade Principal")

    def test_detect_communities_empty_graph(self):
        """Test community detection on an empty graph."""
        import intelligence.graph_engine as graph_engine

        with patch.object(graph_engine.GraphDatabase, 'save_node', return_value=True), \
             patch.object(graph_engine.GraphDatabase, 'save_edge', return_value=True):

            analyzer = graph_engine.SocialGraphAnalyzer(database=graph_engine.GraphDatabase())
            analyzer.nodes.clear()
            analyzer.edges.clear()

            communities = analyzer.detect_communities()
            self.assertEqual(len(communities), 0)

    def test_louvain_failure_fallback(self):
        """Test fallback to label_propagation_communities when louvain fails."""
        import intelligence.graph_engine as graph_engine

        if not graph_engine.NETWORKX_AVAILABLE:
            self.skipTest("NetworkX is not available")

        with patch.object(graph_engine.GraphDatabase, 'save_node', return_value=True), \
             patch.object(graph_engine.GraphDatabase, 'save_edge', return_value=True):

            analyzer = graph_engine.SocialGraphAnalyzer(database=graph_engine.GraphDatabase())
            analyzer.nodes.clear()
            analyzer.edges.clear()

            # Minimal graph
            analyzer.nodes['A'] = graph_engine.GraphNode(id='A', node_type=graph_engine.NodeType.USER, label='A', data={})
            analyzer.nodes['B'] = graph_engine.GraphNode(id='B', node_type=graph_engine.NodeType.USER, label='B', data={})
            analyzer.edges.append(graph_engine.GraphEdge('A', 'B', graph_engine.EdgeType.FOLLOWS))

            # Force Louvain to raise an Exception
            with patch('networkx.algorithms.community.louvain_communities', side_effect=Exception("Louvain failed")):
                # Mock label_propagation_communities to return a specific outcome
                with patch('networkx.algorithms.community.label_propagation_communities', return_value=[{'A', 'B'}]):
                    communities = analyzer.detect_communities()

                    self.assertEqual(len(communities), 1)
                    self.assertEqual(set(communities[0].members), {'A', 'B'})

if __name__ == '__main__':
    unittest.main()
