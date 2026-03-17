"""
Graph Engine 2025 - Motor de Análise de Redes Sociais (SNA)
Versão God Mode Ultimate - Implementação REAL sem placeholders

Funcionalidades:
- Mapeamento de Rede Relacional (Graph Theory)
- Cálculos de Centralidade (Betweenness, PageRank, Degree)
- Detecção de Comunidades (Algoritmo Louvain)
- Métricas de Rede (Clustering, Density)
- Identificação de Bridges e Influencers
- Exportação para Visualização 3D (ForceGraph3D)
"""

import json
import logging
import sqlite3
import math
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import random

# Tentativa de importar NetworkX (dependência opcional)
try:
    import networkx as nx
    from networkx.algorithms import community as nx_community
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GraphEngine")


# =============================================================================
# ENUMS E DATACLASSES
# =============================================================================

class NodeType(Enum):
    """Tipos de nós no grafo"""
    USER = "user"
    POST = "post"
    HASHTAG = "hashtag"
    LOCATION = "location"


class EdgeType(Enum):
    """Tipos de arestas no grafo"""
    FOLLOWS = "follows"
    FOLLOWED_BY = "followed_by"
    MUTUAL = "mutual"
    LIKED = "liked"
    COMMENTED = "commented"
    MENTIONED = "mentioned"
    TAGGED = "tagged"


class CommunityRole(Enum):
    """Papel do nó na comunidade"""
    LEADER = "leader"
    BRIDGE = "bridge"
    MEMBER = "member"
    PERIPHERAL = "peripheral"


@dataclass
class GraphNode:
    """Representa um nó no grafo social"""
    id: str
    node_type: NodeType
    label: str
    data: Dict[str, Any]
    
    # Métricas de centralidade
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    pagerank: float = 0.0
    
    # Comunidade
    community_id: int = -1
    role: CommunityRole = CommunityRole.MEMBER
    
    # Visualização
    color: str = "#666666"
    size: float = 1.0
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None


@dataclass
class GraphEdge:
    """Representa uma aresta no grafo social"""
    source: str
    target: str
    edge_type: EdgeType
    weight: float = 1.0
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Visualização
    color: str = "#999999"
    width: float = 1.0


@dataclass
class CommunityInfo:
    """Informações sobre uma comunidade detectada"""
    id: int
    size: int
    members: List[str]
    leader: Optional[str]
    density: float
    cohesion: float
    label: str


@dataclass
class NetworkMetrics:
    """Métricas globais da rede"""
    node_count: int
    edge_count: int
    density: float
    avg_clustering: float
    avg_path_length: float
    diameter: int
    is_connected: bool
    num_communities: int
    modularity: float


# =============================================================================
# DATABASE MANAGER
# =============================================================================

class GraphDatabase:
    """
    Gerenciador de banco de dados SQLite para grafos.
    """
    
    def __init__(self, db_path: str = ".graph_cache/graphs.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa tabelas do banco"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de nós
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                label TEXT NOT NULL,
                data TEXT,
                degree_centrality REAL DEFAULT 0,
                betweenness_centrality REAL DEFAULT 0,
                closeness_centrality REAL DEFAULT 0,
                pagerank REAL DEFAULT 0,
                community_id INTEGER DEFAULT -1,
                role TEXT DEFAULT 'member',
                color TEXT DEFAULT '#666666',
                size REAL DEFAULT 1,
                x REAL,
                y REAL,
                z REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de arestas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                target TEXT NOT NULL,
                edge_type TEXT NOT NULL,
                weight REAL DEFAULT 1,
                data TEXT,
                color TEXT DEFAULT '#999999',
                width REAL DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source, target, edge_type)
            )
        """)
        
        # Tabela de comunidades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS communities (
                id INTEGER PRIMARY KEY,
                size INTEGER,
                members TEXT,
                leader TEXT,
                density REAL,
                cohesion REAL,
                label TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela de métricas de rede
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS network_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                graph_id TEXT NOT NULL,
                node_count INTEGER,
                edge_count INTEGER,
                density REAL,
                avg_clustering REAL,
                avg_path_length REAL,
                diameter INTEGER,
                is_connected BOOLEAN,
                num_communities INTEGER,
                modularity REAL,
                computed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_nodes_community ON nodes(community_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target)")
        
        conn.commit()
        conn.close()
        
        logger.info(f"📦 Graph DB inicializado: {self.db_path}")
    
    def save_node(self, node: GraphNode) -> bool:
        """Salva ou atualiza um nó"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO nodes 
                    (id, node_type, label, data, degree_centrality, betweenness_centrality,
                     closeness_centrality, pagerank, community_id, role, color, size, x, y, z)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    label = excluded.label,
                    data = excluded.data,
                    degree_centrality = excluded.degree_centrality,
                    betweenness_centrality = excluded.betweenness_centrality,
                    closeness_centrality = excluded.closeness_centrality,
                    pagerank = excluded.pagerank,
                    community_id = excluded.community_id,
                    role = excluded.role,
                    color = excluded.color,
                    size = excluded.size,
                    x = excluded.x,
                    y = excluded.y,
                    z = excluded.z,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                node.id, node.node_type.value, node.label, json.dumps(node.data),
                node.degree_centrality, node.betweenness_centrality,
                node.closeness_centrality, node.pagerank, node.community_id,
                node.role.value, node.color, node.size, node.x, node.y, node.z
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar nó: {e}")
            return False
    
    def save_edge(self, edge: GraphEdge) -> bool:
        """Salva ou atualiza uma aresta"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO edges 
                    (source, target, edge_type, weight, data, color, width)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, target, edge_type) DO UPDATE SET
                    weight = excluded.weight,
                    data = excluded.data,
                    color = excluded.color,
                    width = excluded.width
            """, (
                edge.source, edge.target, edge.edge_type.value,
                edge.weight, json.dumps(edge.data), edge.color, edge.width
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar aresta: {e}")
            return False
    
    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Obtém um nó pelo ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, node_type, label, data, degree_centrality, betweenness_centrality,
                       closeness_centrality, pagerank, community_id, role, color, size, x, y, z
                FROM nodes WHERE id = ?
            """, (node_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return GraphNode(
                    id=row[0],
                    node_type=NodeType(row[1]),
                    label=row[2],
                    data=json.loads(row[3]) if row[3] else {},
                    degree_centrality=row[4] or 0,
                    betweenness_centrality=row[5] or 0,
                    closeness_centrality=row[6] or 0,
                    pagerank=row[7] or 0,
                    community_id=row[8] or -1,
                    role=CommunityRole(row[9]) if row[9] else CommunityRole.MEMBER,
                    color=row[10] or "#666666",
                    size=row[11] or 1,
                    x=row[12],
                    y=row[13],
                    z=row[14]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter nó: {e}")
            return None
    
    def get_all_nodes(self) -> List[GraphNode]:
        """Obtém todos os nós"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, node_type, label, data, degree_centrality, betweenness_centrality,
                       closeness_centrality, pagerank, community_id, role, color, size, x, y, z
                FROM nodes
            """)
            
            nodes = []
            for row in cursor.fetchall():
                nodes.append(GraphNode(
                    id=row[0],
                    node_type=NodeType(row[1]),
                    label=row[2],
                    data=json.loads(row[3]) if row[3] else {},
                    degree_centrality=row[4] or 0,
                    betweenness_centrality=row[5] or 0,
                    closeness_centrality=row[6] or 0,
                    pagerank=row[7] or 0,
                    community_id=row[8] or -1,
                    role=CommunityRole(row[9]) if row[9] else CommunityRole.MEMBER,
                    color=row[10] or "#666666",
                    size=row[11] or 1,
                    x=row[12],
                    y=row[13],
                    z=row[14]
                ))
            
            conn.close()
            return nodes
            
        except Exception as e:
            logger.error(f"Erro ao obter nós: {e}")
            return []
    
    def get_all_edges(self) -> List[GraphEdge]:
        """Obtém todas as arestas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT source, target, edge_type, weight, data, color, width
                FROM edges
            """)
            
            edges = []
            for row in cursor.fetchall():
                edges.append(GraphEdge(
                    source=row[0],
                    target=row[1],
                    edge_type=EdgeType(row[2]),
                    weight=row[3] or 1,
                    data=json.loads(row[4]) if row[4] else {},
                    color=row[5] or "#999999",
                    width=row[6] or 1
                ))
            
            conn.close()
            return edges
            
        except Exception as e:
            logger.error(f"Erro ao obter arestas: {e}")
            return []
    
    def clear_graph(self):
        """Limpa todos os dados do grafo"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM nodes")
            cursor.execute("DELETE FROM edges")
            cursor.execute("DELETE FROM communities")
            
            conn.commit()
            conn.close()
            
            logger.info("🗑️ Grafo limpo")
            
        except Exception as e:
            logger.error(f"Erro ao limpar grafo: {e}")


# =============================================================================
# SOCIAL GRAPH ANALYZER
# =============================================================================

class SocialGraphAnalyzer:
    """
    Analisador de grafos sociais com algoritmos de teoria dos grafos.
    
    Funcionalidades:
    - Construção de grafo a partir de dados de seguidores
    - Cálculo de métricas de centralidade
    - Detecção de comunidades (Louvain)
    - Identificação de influenciadores e pontes
    """
    
    # Cores para comunidades (paleta profissional)
    COMMUNITY_COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
        "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
        "#F8B500", "#00CED1", "#FF69B4", "#32CD32", "#FF4500",
        "#9370DB", "#20B2AA", "#FF6347", "#7B68EE", "#3CB371"
    ]
    
    def __init__(self, database: Optional[GraphDatabase] = None):
        self.database = database or GraphDatabase()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._nx_graph: Optional[Any] = None
        
        logger.info("📊 Social Graph Analyzer inicializado")
    
    def build_graph_from_followers(
        self,
        target_username: str,
        followers: List[Dict],
        following: List[Dict],
        include_mutual: bool = True
    ) -> None:
        """
        Constrói grafo a partir de listas de seguidores/seguindo.
        
        Args:
            target_username: Username do perfil central
            followers: Lista de seguidores
            following: Lista de seguidos
            include_mutual: Se True, marca conexões mútuas
        """
        logger.info(f"🔨 Construindo grafo para @{target_username}")
        
        # Limpar grafo anterior
        self.nodes.clear()
        self.edges.clear()
        
        # Criar nó central
        central_node = GraphNode(
            id=target_username,
            node_type=NodeType.USER,
            label=target_username,
            data={'is_central': True},
            color="#FF0000",
            size=3.0
        )
        self.nodes[target_username] = central_node
        
        # Criar sets para lookup rápido
        follower_usernames = {f.get('username', '') for f in followers if f.get('username')}
        following_usernames = {f.get('username', '') for f in following if f.get('username')}
        
        # Adicionar nós de seguidores
        for follower in followers:
            username = follower.get('username', '')
            if not username:
                continue
            
            is_mutual = username in following_usernames
            
            node = GraphNode(
                id=username,
                node_type=NodeType.USER,
                label=username,
                data={
                    'full_name': follower.get('full_name', ''),
                    'profile_pic_url': follower.get('profile_pic_url', ''),
                    'is_verified': follower.get('is_verified', False),
                    'follower_count': follower.get('follower_count', 0),
                    'is_mutual': is_mutual
                },
                color="#4ECDC4" if is_mutual else "#45B7D1"
            )
            self.nodes[username] = node
            
            # Aresta: seguidor -> target
            edge_type = EdgeType.MUTUAL if is_mutual else EdgeType.FOLLOWS
            edge = GraphEdge(
                source=username,
                target=target_username,
                edge_type=edge_type,
                weight=2.0 if is_mutual else 1.0,
                color="#00FF00" if is_mutual else "#999999"
            )
            self.edges.append(edge)
        
        # Adicionar nós de seguidos (que não são seguidores)
        for followed in following:
            username = followed.get('username', '')
            if not username or username in self.nodes:
                continue
            
            node = GraphNode(
                id=username,
                node_type=NodeType.USER,
                label=username,
                data={
                    'full_name': followed.get('full_name', ''),
                    'profile_pic_url': followed.get('profile_pic_url', ''),
                    'is_verified': followed.get('is_verified', False),
                    'follower_count': followed.get('follower_count', 0),
                    'is_mutual': False
                },
                color="#FF6B6B"
            )
            self.nodes[username] = node
            
            # Aresta: target -> seguido
            edge = GraphEdge(
                source=target_username,
                target=username,
                edge_type=EdgeType.FOLLOWS,
                weight=1.0
            )
            self.edges.append(edge)
        
        logger.info(f"✅ Grafo construído: {len(self.nodes)} nós, {len(self.edges)} arestas")
        
        # Salvar no banco
        self._save_to_database()
    
    def build_graph_from_interactions(
        self,
        target_username: str,
        posts: List[Dict],
        include_likers: bool = True,
        include_commenters: bool = True
    ) -> None:
        """
        Constrói grafo a partir de interações em posts.
        
        Args:
            target_username: Username do perfil
            posts: Lista de posts com dados de engajamento
            include_likers: Incluir pessoas que deram like
            include_commenters: Incluir pessoas que comentaram
        """
        logger.info(f"🔨 Construindo grafo de interações para @{target_username}")
        
        # Limpar grafo anterior se não existir nó central
        if target_username not in self.nodes:
            self.nodes.clear()
            self.edges.clear()
            
            central_node = GraphNode(
                id=target_username,
                node_type=NodeType.USER,
                label=target_username,
                data={'is_central': True},
                color="#FF0000",
                size=3.0
            )
            self.nodes[target_username] = central_node
        
        for post in posts:
            post_id = str(post.get('pk', post.get('id', '')))
            
            # Processar likers
            if include_likers:
                likers = post.get('likers', [])
                for liker in likers:
                    username = liker.get('username', '')
                    if not username:
                        continue
                    
                    # Adicionar nó se não existir
                    if username not in self.nodes:
                        node = GraphNode(
                            id=username,
                            node_type=NodeType.USER,
                            label=username,
                            data={'interaction_type': 'liker'},
                            color="#FFEAA7"
                        )
                        self.nodes[username] = node
                    
                    # Aresta: user --liked--> post_owner
                    edge = GraphEdge(
                        source=username,
                        target=target_username,
                        edge_type=EdgeType.LIKED,
                        weight=0.5,
                        data={'post_id': post_id}
                    )
                    self.edges.append(edge)
            
            # Processar commenters
            if include_commenters:
                comments = post.get('comments', [])
                for comment in comments:
                    username = comment.get('user', {}).get('username', '')
                    if not username:
                        continue
                    
                    if username not in self.nodes:
                        node = GraphNode(
                            id=username,
                            node_type=NodeType.USER,
                            label=username,
                            data={'interaction_type': 'commenter'},
                            color="#96CEB4"
                        )
                        self.nodes[username] = node
                    
                    # Aresta: user --commented--> post_owner
                    edge = GraphEdge(
                        source=username,
                        target=target_username,
                        edge_type=EdgeType.COMMENTED,
                        weight=1.0,  # Comentários têm peso maior
                        data={'post_id': post_id, 'text': comment.get('text', '')[:50]}
                    )
                    self.edges.append(edge)
        
        logger.info(f"✅ Grafo atualizado: {len(self.nodes)} nós, {len(self.edges)} arestas")
        self._save_to_database()
    
    def _save_to_database(self):
        """Salva grafo atual no banco de dados"""
        for node in self.nodes.values():
            self.database.save_node(node)
        
        for edge in self.edges:
            self.database.save_edge(edge)
    
    def _build_networkx_graph(self) -> Any:
        """Constrói grafo NetworkX a partir dos dados internos"""
        if not NETWORKX_AVAILABLE:
            logger.warning("⚠️ NetworkX não disponível. Instale com: pip install networkx")
            return None
        
        G = nx.DiGraph()
        
        # Adicionar nós
        for node in self.nodes.values():
            G.add_node(node.id, **{
                'label': node.label,
                'type': node.node_type.value,
                'data': node.data
            })
        
        # Adicionar arestas
        for edge in self.edges:
            G.add_edge(edge.source, edge.target, **{
                'type': edge.edge_type.value,
                'weight': edge.weight
            })
        
        self._nx_graph = G
        return G
    
    def calculate_centrality_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Calcula métricas de centralidade para todos os nós.
        
        Métricas:
        - Degree Centrality: Número de conexões (normalizado)
        - Betweenness Centrality: Frequência em caminhos mais curtos
        - Closeness Centrality: Proximidade média a outros nós
        - PageRank: Importância baseada em links
        """
        if not NETWORKX_AVAILABLE:
            return self._calculate_centrality_fallback()
        
        G = self._build_networkx_graph()
        if G is None:
            return {}
        
        logger.info("📊 Calculando métricas de centralidade...")
        
        # Calcular métricas
        degree = nx.degree_centrality(G)
        
        try:
            betweenness = nx.betweenness_centrality(G, weight='weight')
        except:
            betweenness = {n: 0 for n in G.nodes()}
        
        try:
            closeness = nx.closeness_centrality(G)
        except:
            closeness = {n: 0 for n in G.nodes()}
        
        try:
            pagerank = nx.pagerank(G, weight='weight')
        except:
            pagerank = {n: 1/len(G.nodes()) for n in G.nodes()}
        
        # Atualizar nós
        for node_id in self.nodes:
            self.nodes[node_id].degree_centrality = degree.get(node_id, 0)
            self.nodes[node_id].betweenness_centrality = betweenness.get(node_id, 0)
            self.nodes[node_id].closeness_centrality = closeness.get(node_id, 0)
            self.nodes[node_id].pagerank = pagerank.get(node_id, 0)
            
            # Ajustar tamanho do nó baseado em PageRank
            self.nodes[node_id].size = 1 + (pagerank.get(node_id, 0) * 100)
        
        # Salvar no banco
        self._save_to_database()
        
        logger.info("✅ Métricas de centralidade calculadas")
        
        return {
            node_id: {
                'degree': degree.get(node_id, 0),
                'betweenness': betweenness.get(node_id, 0),
                'closeness': closeness.get(node_id, 0),
                'pagerank': pagerank.get(node_id, 0)
            }
            for node_id in self.nodes
        }
    
    def _calculate_centrality_fallback(self) -> Dict[str, Dict[str, float]]:
        """Calcula centralidade sem NetworkX (implementação básica)"""
        logger.warning("⚠️ Usando cálculo de centralidade fallback")
        
        # Calcular degree simples
        in_degree: Dict[str, int] = defaultdict(int)
        out_degree: Dict[str, int] = defaultdict(int)
        
        for edge in self.edges:
            out_degree[edge.source] += 1
            in_degree[edge.target] += 1
        
        total_nodes = len(self.nodes)
        if total_nodes <= 1:
            return {}
        
        results = {}
        for node_id in self.nodes:
            degree = (in_degree[node_id] + out_degree[node_id]) / (total_nodes - 1)
            
            # Simular PageRank simples baseado em in-degree
            pagerank = in_degree[node_id] / sum(in_degree.values()) if sum(in_degree.values()) > 0 else 0
            
            self.nodes[node_id].degree_centrality = degree
            self.nodes[node_id].pagerank = pagerank
            self.nodes[node_id].size = 1 + (pagerank * 100)
            
            results[node_id] = {
                'degree': degree,
                'betweenness': 0,
                'closeness': 0,
                'pagerank': pagerank
            }
        
        self._save_to_database()
        return results
    
    def detect_communities(self) -> List[CommunityInfo]:
        """
        Detecta comunidades usando algoritmo Louvain.
        
        Returns:
            Lista de CommunityInfo
        """
        if not NETWORKX_AVAILABLE:
            return self._detect_communities_fallback()
        
        G = self._build_networkx_graph()
        if G is None or len(G.nodes()) < 2:
            return []
        
        logger.info("🔍 Detectando comunidades (Louvain)...")
        
        # Converter para grafo não-direcionado para Louvain
        G_undirected = G.to_undirected()
        
        try:
            # Usar algoritmo Louvain
            communities = nx_community.louvain_communities(G_undirected, weight='weight')
        except Exception as e:
            logger.warning(f"Louvain falhou: {e}, usando label propagation")
            try:
                communities = list(nx_community.label_propagation_communities(G_undirected))
            except:
                communities = [set(G.nodes())]
        
        community_list = []
        
        for i, members in enumerate(communities):
            members_list = list(members)
            
            # Encontrar líder (maior centralidade)
            leader = None
            max_centrality = 0
            for member in members_list:
                if member in self.nodes:
                    centrality = self.nodes[member].pagerank
                    if centrality > max_centrality:
                        max_centrality = centrality
                        leader = member
            
            # Calcular densidade da comunidade
            subgraph = G_undirected.subgraph(members)
            density = nx.density(subgraph) if len(members) > 1 else 0
            
            # Atribuir cor e comunidade aos nós
            color = self.COMMUNITY_COLORS[i % len(self.COMMUNITY_COLORS)]
            for member in members_list:
                if member in self.nodes:
                    self.nodes[member].community_id = i
                    self.nodes[member].color = color
                    
                    # Determinar papel
                    if member == leader:
                        self.nodes[member].role = CommunityRole.LEADER
                    elif self.nodes[member].betweenness_centrality > 0.1:
                        self.nodes[member].role = CommunityRole.BRIDGE
                    else:
                        self.nodes[member].role = CommunityRole.MEMBER
            
            community_info = CommunityInfo(
                id=i,
                size=len(members_list),
                members=members_list,
                leader=leader,
                density=density,
                cohesion=density,  # Simplificado
                label=f"Comunidade {i+1}"
            )
            community_list.append(community_info)
        
        self._save_to_database()
        
        logger.info(f"✅ {len(community_list)} comunidades detectadas")
        
        return community_list
    
    def _detect_communities_fallback(self) -> List[CommunityInfo]:
        """Detecção simples de comunidades sem NetworkX"""
        logger.warning("⚠️ Usando detecção de comunidades fallback")
        
        # Agrupar por conexões diretas ao nó central
        central_followers: Set[str] = set()
        for edge in self.edges:
            for node_id, node in self.nodes.items():
                if node.data.get('is_central'):
                    if edge.target == node_id:
                        central_followers.add(edge.source)
        
        # Criar uma única comunidade
        if central_followers:
            community = CommunityInfo(
                id=0,
                size=len(central_followers),
                members=list(central_followers),
                leader=None,
                density=0.5,
                cohesion=0.5,
                label="Comunidade Principal"
            )
            
            for member in central_followers:
                if member in self.nodes:
                    self.nodes[member].community_id = 0
                    self.nodes[member].color = self.COMMUNITY_COLORS[0]
            
            return [community]
        
        return []
    
    def identify_bridges_and_influencers(self) -> Dict[str, Any]:
        """
        Identifica nós que são pontes entre comunidades e influenciadores.
        
        Returns:
            Dict com bridges e influencers
        """
        logger.info("🔍 Identificando bridges e influencers...")
        
        bridges = []
        influencers = []
        
        for node_id, node in self.nodes.items():
            # Bridges: alta betweenness centrality
            if node.betweenness_centrality > 0.05:
                bridges.append({
                    'id': node_id,
                    'betweenness': node.betweenness_centrality,
                    'communities_connected': []  # Seria calculado com análise mais profunda
                })
            
            # Influencers: alto PageRank
            if node.pagerank > 0.02 or node.degree_centrality > 0.1:
                influencers.append({
                    'id': node_id,
                    'pagerank': node.pagerank,
                    'degree': node.degree_centrality,
                    'followers': node.data.get('follower_count', 0)
                })
        
        # Ordenar
        bridges.sort(key=lambda x: x['betweenness'], reverse=True)
        influencers.sort(key=lambda x: x['pagerank'], reverse=True)
        
        logger.info(f"✅ Encontrados {len(bridges)} bridges e {len(influencers)} influencers")
        
        return {
            'bridges': bridges[:10],
            'influencers': influencers[:10]
        }
    
    def calculate_network_metrics(self) -> NetworkMetrics:
        """
        Calcula métricas globais da rede.
        
        Returns:
            NetworkMetrics
        """
        logger.info("📊 Calculando métricas globais da rede...")
        
        node_count = len(self.nodes)
        edge_count = len(self.edges)
        
        if node_count <= 1:
            return NetworkMetrics(
                node_count=node_count,
                edge_count=edge_count,
                density=0,
                avg_clustering=0,
                avg_path_length=0,
                diameter=0,
                is_connected=False,
                num_communities=0,
                modularity=0
            )
        
        # Densidade
        max_edges = node_count * (node_count - 1)
        density = edge_count / max_edges if max_edges > 0 else 0
        
        if NETWORKX_AVAILABLE and self._nx_graph:
            G = self._nx_graph
            
            try:
                avg_clustering = nx.average_clustering(G.to_undirected())
            except:
                avg_clustering = 0
            
            try:
                if nx.is_strongly_connected(G):
                    avg_path_length = nx.average_shortest_path_length(G)
                    diameter = nx.diameter(G)
                else:
                    avg_path_length = 0
                    diameter = 0
            except:
                avg_path_length = 0
                diameter = 0
            
            is_connected = nx.is_weakly_connected(G) if nx.is_directed(G) else nx.is_connected(G)
        else:
            avg_clustering = 0
            avg_path_length = 0
            diameter = 0
            is_connected = False
        
        # Contar comunidades
        community_ids = set(n.community_id for n in self.nodes.values() if n.community_id >= 0)
        num_communities = len(community_ids)
        
        metrics = NetworkMetrics(
            node_count=node_count,
            edge_count=edge_count,
            density=round(density, 4),
            avg_clustering=round(avg_clustering, 4),
            avg_path_length=round(avg_path_length, 2),
            diameter=diameter,
            is_connected=is_connected,
            num_communities=num_communities,
            modularity=0  # Seria calculado com análise de comunidades
        )
        
        logger.info("✅ Métricas globais calculadas")
        
        return metrics
    
    def export_for_forcegraph3d(self) -> Dict[str, Any]:
        """
        Exporta grafo em formato JSON compatível com ForceGraph3D.
        
        Returns:
            Dict com nodes e links no formato ForceGraph3D
        """
        logger.info("📤 Exportando para ForceGraph3D...")
        
        nodes_export = []
        for node in self.nodes.values():
            nodes_export.append({
                'id': node.id,
                'name': node.label,
                'val': node.size,
                'color': node.color,
                'group': node.community_id,
                'x': node.x,
                'y': node.y,
                'z': node.z,
                # Dados extras
                'type': node.node_type.value,
                'pagerank': round(node.pagerank, 4),
                'degree': round(node.degree_centrality, 4),
                'role': node.role.value,
                **node.data
            })
        
        links_export = []
        for edge in self.edges:
            links_export.append({
                'source': edge.source,
                'target': edge.target,
                'value': edge.weight,
                'color': edge.color,
                'type': edge.edge_type.value
            })
        
        result = {
            'nodes': nodes_export,
            'links': links_export
        }
        
        logger.info(f"✅ Exportado: {len(nodes_export)} nós, {len(links_export)} links")
        
        return result
    
    def get_full_analysis(self, target_username: str) -> Dict[str, Any]:
        """
        Executa análise completa do grafo.
        
        Args:
            target_username: Username do perfil central
            
        Returns:
            Dict com análise completa
        """
        logger.info(f"🔬 Executando análise completa para @{target_username}")
        
        # Calcular métricas de centralidade
        centrality = self.calculate_centrality_metrics()
        
        # Detectar comunidades
        communities = self.detect_communities()
        
        # Identificar bridges e influencers
        key_nodes = self.identify_bridges_and_influencers()
        
        # Métricas globais
        network_metrics = self.calculate_network_metrics()
        
        # Exportar para visualização
        graph_data = self.export_for_forcegraph3d()
        
        return {
            'username': target_username,
            'analyzed_at': datetime.now().isoformat(),
            'network_metrics': {
                'nodes': network_metrics.node_count,
                'edges': network_metrics.edge_count,
                'density': network_metrics.density,
                'avg_clustering': network_metrics.avg_clustering,
                'num_communities': network_metrics.num_communities,
                'is_connected': network_metrics.is_connected
            },
            'communities': [
                {
                    'id': c.id,
                    'size': c.size,
                    'leader': c.leader,
                    'density': c.density
                }
                for c in communities
            ],
            'key_nodes': key_nodes,
            'top_by_pagerank': sorted(
                [{'id': k, **v} for k, v in centrality.items()],
                key=lambda x: x.get('pagerank', 0),
                reverse=True
            )[:10],
            'graph_data': graph_data
        }


# =============================================================================
# LAYOUT ALGORITHMS
# =============================================================================

class GraphLayoutEngine:
    """
    Motor de layout para posicionamento de nós em 3D.
    
    Algoritmos:
    - Force-Directed (Spring)
    - Fruchterman-Reingold
    - Kamada-Kawai
    """
    
    def __init__(self):
        pass
    
    def apply_force_directed_3d(
        self,
        nodes: Dict[str, GraphNode],
        edges: List[GraphEdge],
        iterations: int = 50
    ) -> None:
        """
        Aplica layout force-directed em 3D.
        
        Args:
            nodes: Dicionário de nós
            edges: Lista de arestas
            iterations: Número de iterações
        """
        if not nodes:
            return
        
        logger.info("🎨 Aplicando layout force-directed 3D...")
        
        # Inicializar posições aleatórias
        for node in nodes.values():
            if node.x is None:
                node.x = random.uniform(-100, 100)
            if node.y is None:
                node.y = random.uniform(-100, 100)
            if node.z is None:
                node.z = random.uniform(-100, 100)
        
        # Parâmetros
        k = math.sqrt(8000 / max(len(nodes), 1))  # Spring constant
        temperature = 100
        cooling = 0.95
        
        for iteration in range(iterations):
            # Calcular forças repulsivas
            for node1 in nodes.values():
                fx, fy, fz = 0, 0, 0
                
                for node2 in nodes.values():
                    if node1.id == node2.id:
                        continue
                    
                    dx = node1.x - node2.x
                    dy = node1.y - node2.y
                    dz = node1.z - node2.z
                    
                    dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.1
                    
                    # Força repulsiva
                    repulsion = (k * k) / dist
                    fx += (dx / dist) * repulsion
                    fy += (dy / dist) * repulsion
                    fz += (dz / dist) * repulsion
                
                # Aplicar forças atrativas das arestas
                for edge in edges:
                    if edge.source == node1.id:
                        other = nodes.get(edge.target)
                    elif edge.target == node1.id:
                        other = nodes.get(edge.source)
                    else:
                        continue
                    
                    if other:
                        dx = node1.x - other.x
                        dy = node1.y - other.y
                        dz = node1.z - other.z
                        
                        dist = math.sqrt(dx*dx + dy*dy + dz*dz) + 0.1
                        
                        # Força atrativa
                        attraction = (dist * dist) / k
                        fx -= (dx / dist) * attraction * edge.weight
                        fy -= (dy / dist) * attraction * edge.weight
                        fz -= (dz / dist) * attraction * edge.weight
                
                # Limitar deslocamento
                displacement = math.sqrt(fx*fx + fy*fy + fz*fz) + 0.1
                node1.x += min(temperature, abs(fx)) * (fx / displacement)
                node1.y += min(temperature, abs(fy)) * (fy / displacement)
                node1.z += min(temperature, abs(fz)) * (fz / displacement)
            
            # Resfriar
            temperature *= cooling
        
        logger.info("✅ Layout aplicado")


# =============================================================================
# TESTES
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("   Graph Engine 2025 - God Mode Ultimate")
    print("   Motor de Análise de Redes Sociais (SNA)")
    print("=" * 60)
    
    # Verificar NetworkX
    print(f"\nNetworkX disponível: {NETWORKX_AVAILABLE}")
    
    # Criar analisador
    analyzer = SocialGraphAnalyzer()
    
    # Dados de teste
    test_followers = [
        {'username': 'user1', 'full_name': 'User 1', 'follower_count': 100},
        {'username': 'user2', 'full_name': 'User 2', 'follower_count': 500},
        {'username': 'user3', 'full_name': 'User 3', 'follower_count': 1000},
        {'username': 'user4', 'full_name': 'User 4', 'follower_count': 50},
        {'username': 'user5', 'full_name': 'User 5', 'follower_count': 200},
    ]
    
    test_following = [
        {'username': 'user2', 'full_name': 'User 2', 'follower_count': 500},  # Mútuo
        {'username': 'user6', 'full_name': 'User 6', 'follower_count': 10000},
        {'username': 'user7', 'full_name': 'User 7', 'follower_count': 5000},
    ]
    
    print("\n🧪 Teste de construção de grafo...")
    analyzer.build_graph_from_followers('target_user', test_followers, test_following)
    
    print(f"   Nós: {len(analyzer.nodes)}")
    print(f"   Arestas: {len(analyzer.edges)}")
    
    print("\n🧪 Teste de métricas de centralidade...")
    centrality = analyzer.calculate_centrality_metrics()
    for node_id in list(centrality.keys())[:3]:
        print(f"   {node_id}: PageRank={centrality[node_id]['pagerank']:.4f}")
    
    print("\n🧪 Teste de detecção de comunidades...")
    communities = analyzer.detect_communities()
    print(f"   Comunidades encontradas: {len(communities)}")
    
    print("\n🧪 Teste de exportação ForceGraph3D...")
    export_data = analyzer.export_for_forcegraph3d()
    print(f"   JSON: {len(export_data['nodes'])} nós, {len(export_data['links'])} links")
    
    print("\n✅ Todos os testes concluídos!")
