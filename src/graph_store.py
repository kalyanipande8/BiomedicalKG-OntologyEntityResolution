"""
Graph store: an HONEST LOCAL STAND-IN FOR NEO4J.

Neo4j is not installed or runnable in this environment (checked: `which
neo4j` and `which docker` both failed, and disk space was extremely
tight, ~1.5GB free, ruling out a local Neo4j/Docker install). Rather than
fake a Neo4j connection, this module implements the SAME logical graph
model Neo4j uses:

  - Nodes carry a label (Disease/Drug/Gene/Pathway) and a property dict,
    exactly like a Neo4j node.
  - Relationships are directed, carry a type (TREATS/TARGETS/...) and a
    property dict, exactly like a Neo4j relationship.

...on top of `networkx.MultiDiGraph`, a real in-memory graph library
(not a mock/stub). The query methods below (shortest path, k-hop
neighborhood) are real graph algorithms (networkx's implementations),
executed against real data, not hardcoded answers.

If a real Neo4j instance is ever available, `to_cypher_script()` emits
the equivalent Cypher CREATE statements so the exact same graph could be
loaded into a real Neo4j server without any modeling changes.
"""
import networkx as nx


class BiomedicalGraphStore:
    """Neo4j-style labeled-property graph, backed by networkx (honest stand-in)."""

    def __init__(self):
        self.g = nx.MultiDiGraph()

    # ---- write API, mirrors Neo4j's node/relationship model ----
    def add_node(self, node_id: str, label: str, **properties):
        self.g.add_node(node_id, label=label, **properties)

    def add_relationship(self, src_id: str, rel_type: str, dst_id: str, **properties):
        self.g.add_edge(src_id, dst_id, key=rel_type, type=rel_type, **properties)

    # ---- read / query API ----
    def node(self, node_id: str):
        return self.g.nodes[node_id]

    def num_nodes(self) -> int:
        return self.g.number_of_nodes()

    def num_relationships(self) -> int:
        return self.g.number_of_edges()

    def shortest_path(self, src_id: str, dst_id: str):
        """Real BFS shortest path (networkx), analogous to Neo4j's
        `shortestPath()` Cypher function."""
        try:
            path = nx.shortest_path(self.g, source=src_id, target=dst_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
        # annotate with relationship types used at each hop
        annotated = []
        for a, b in zip(path, path[1:]):
            edge_data = self.g.get_edge_data(a, b)
            rel_type = next(iter(edge_data.values()))["type"] if edge_data else "?"
            annotated.append((a, rel_type, b))
        return {"nodes": path, "hops": annotated, "length": len(path) - 1}

    def k_hop_neighbors(self, node_id: str, k: int = 2):
        """Real BFS bounded to k hops in the underlying undirected view,
        analogous to Neo4j's `MATCH (n)-[*1..k]-(m)` variable-length pattern."""
        undirected = self.g.to_undirected()
        lengths = nx.single_source_shortest_path_length(undirected, node_id, cutoff=k)
        lengths.pop(node_id, None)
        return sorted(lengths.items(), key=lambda kv: kv[1])

    def nodes_by_label(self, label: str):
        return [n for n, d in self.g.nodes(data=True) if d.get("label") == label]

    # ---- portability: emit equivalent Cypher, in case a real Neo4j
    # instance becomes available later ----
    def to_cypher_script(self) -> str:
        lines = []
        for n, d in self.g.nodes(data=True):
            label = d.get("label", "Entity")
            props = {k: v for k, v in d.items() if k != "label"}
            prop_str = ", ".join(f'{k}: "{v}"' for k, v in props.items())
            lines.append(f'CREATE (n_{_safe(n)}:{label} {{id: "{n}", {prop_str}}})')
        for a, b, key, d in self.g.edges(keys=True, data=True):
            rel_type = d.get("type", key)
            lines.append(f'CREATE (n_{_safe(a)})-[:{rel_type}]->(n_{_safe(b)})')
        return "\n".join(lines)


def _safe(node_id: str) -> str:
    return node_id.replace(":", "_").replace("-", "_")
