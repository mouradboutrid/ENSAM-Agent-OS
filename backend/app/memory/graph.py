from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional

import networkx as nx


class GraphMemory:
    def __init__(self, persist_dir: str = "./data/graph"):
        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._graph_file = self._persist_dir / "knowledge_graph.json"
        self.graph = nx.DiGraph()
        self._load()

    def _load(self):
        if self._graph_file.exists():
            with open(self._graph_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data)

    def _save(self):
        data = nx.node_link_data(self.graph)
        with open(self._graph_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_entity(self, entity_id: str, entity_type: str, properties: Optional[dict] = None):
        props = properties or {}
        props["entity_type"] = entity_type
        self.graph.add_node(entity_id, **props)
        self._save()

    def add_relationship(self, source: str, target: str, relation_type: str, properties: Optional[dict] = None):
        props = properties or {}
        props["relation_type"] = relation_type
        self.graph.add_edge(source, target, **props)
        self._save()

    def get_entity(self, entity_id: str) -> Optional[dict]:
        if entity_id in self.graph:
            return {"id": entity_id, **dict(self.graph.nodes[entity_id])}
        return None

    def get_relationships(self, entity_id: str) -> list[dict]:
        rels = []
        if entity_id in self.graph:
            for _, target, data in self.graph.out_edges(entity_id, data=True):
                rels.append({"source": entity_id, "target": target, **data})
            for source, _, data in self.graph.in_edges(entity_id, data=True):
                rels.append({"source": source, "target": entity_id, **data})
        return rels

    def get_neighbors(self, entity_id: str, depth: int = 1) -> dict:
        if entity_id not in self.graph:
            return {"nodes": [], "edges": []}
        nodes_set = {entity_id}
        current_level = {entity_id}
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                next_level.update(self.graph.successors(node))
                next_level.update(self.graph.predecessors(node))
            nodes_set.update(next_level)
            current_level = next_level
        subgraph = self.graph.subgraph(nodes_set)
        nodes = [{"id": n, **dict(subgraph.nodes[n])} for n in subgraph.nodes]
        edges = [{"source": u, "target": v, **d} for u, v, d in subgraph.edges(data=True)]
        return {"nodes": nodes, "edges": edges}

    def search_entities(self, entity_type: Optional[str] = None, properties: Optional[dict] = None) -> list[dict]:
        results = []
        for node_id, data in self.graph.nodes(data=True):
            if entity_type and data.get("entity_type") != entity_type:
                continue
            if properties:
                if not all(data.get(k) == v for k, v in properties.items()):
                    continue
            results.append({"id": node_id, **data})
        return results

    def delete_entity(self, entity_id: str) -> bool:
        if entity_id in self.graph:
            self.graph.remove_node(entity_id)
            self._save()
            return True
        return False

    def delete_user_data(self, user_id: str) -> int:
        nodes_to_remove = [
            n for n, d in self.graph.nodes(data=True)
            if d.get("user_id") == user_id or n == user_id
        ]
        for n in nodes_to_remove:
            self.graph.remove_node(n)
        if nodes_to_remove:
            self._save()
        return len(nodes_to_remove)

    def get_stats(self) -> dict:
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "entity_types": list(set(d.get("entity_type", "unknown") for _, d in self.graph.nodes(data=True))),
        }

    def get_full_graph(self) -> dict:
        nodes = [{"id": n, **dict(d)} for n, d in self.graph.nodes(data=True)]
        edges = [{"source": u, "target": v, **d} for u, v, d in self.graph.edges(data=True)]
        return {"nodes": nodes, "edges": edges}

    def link_document_to_entity(self, doc_id: str, entity_id: str, relation: str = "belongs_to"):
        if doc_id not in self.graph:
            self.add_entity(doc_id, "document")
        self.add_relationship(doc_id, entity_id, relation)
