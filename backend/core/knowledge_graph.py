"""
Knowledge Graph — NetworkX based
Builds entity relationship graph from extracted entities
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import networkx as nx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

KG_PATH = os.getenv("KNOWLEDGE_GRAPH_PATH", "./knowledge_graph.json")


class KnowledgeGraph:
    """NetworkX-based knowledge graph for industrial entities"""

    def __init__(self):
        self.graph = nx.DiGraph()
        self._node_counter = 0

    def load(self):
        """Load graph from JSON file"""
        if os.path.exists(KG_PATH):
            try:
                with open(KG_PATH, "r") as f:
                    data = json.load(f)
                self.graph = nx.node_link_graph(data)
                logger.info(f"✅ Knowledge graph loaded: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph: {e}. Starting fresh.")
                self.graph = nx.DiGraph()
        else:
            logger.info("No existing knowledge graph found. Starting fresh.")

    def save(self):
        """Save graph to JSON file"""
        try:
            data = nx.node_link_data(self.graph)
            with open(KG_PATH, "w") as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"💾 Knowledge graph saved: {self.graph.number_of_nodes()} nodes")
        except Exception as e:
            logger.error(f"Failed to save knowledge graph: {e}")

    def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        label: str,
        properties: Optional[Dict] = None,
    ) -> str:
        """Add or update a node"""
        if entity_id not in self.graph:
            self.graph.add_node(
                entity_id,
                type=entity_type,
                label=label,
                created_at=datetime.utcnow().isoformat(),
                **(properties or {}),
            )
        else:
            # Update properties
            self.graph.nodes[entity_id].update(properties or {})
        return entity_id

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict] = None,
    ):
        """Add or update an edge"""
        self.graph.add_edge(
            source_id,
            target_id,
            relation=relation_type,
            created_at=datetime.utcnow().isoformat(),
            **(properties or {}),
        )

    def get_entity_neighbors(self, entity_id: str) -> Dict[str, Any]:
        """Get all connected entities"""
        if entity_id not in self.graph:
            return {"entity": None, "connections": []}

        node_data = dict(self.graph.nodes[entity_id])
        connections = []

        for neighbor in self.graph.neighbors(entity_id):
            edge_data = self.graph.edges[entity_id, neighbor]
            neighbor_data = dict(self.graph.nodes[neighbor])
            connections.append({
                "id": neighbor,
                "label": neighbor_data.get("label", neighbor),
                "type": neighbor_data.get("type", "unknown"),
                "relation": edge_data.get("relation", "RELATED_TO"),
            })

        # Also check predecessors
        for predecessor in self.graph.predecessors(entity_id):
            edge_data = self.graph.edges[predecessor, entity_id]
            pred_data = dict(self.graph.nodes[predecessor])
            connections.append({
                "id": predecessor,
                "label": pred_data.get("label", predecessor),
                "type": pred_data.get("type", "unknown"),
                "relation": f"← {edge_data.get('relation', 'RELATED_TO')}",
            })

        return {
            "entity": {"id": entity_id, **node_data},
            "connections": connections,
        }

    def search_entity(self, query: str) -> List[Dict]:
        """Find entities by label (case-insensitive)"""
        results = []
        query_lower = query.lower()
        for node_id, attrs in self.graph.nodes(data=True):
            label = attrs.get("label", "").lower()
            if query_lower in label or query_lower in node_id.lower():
                results.append({"id": node_id, **attrs})
        return results

    def get_equipment_timeline(self, equipment_id: str) -> List[Dict]:
        """Get all events related to an equipment"""
        events = []
        if equipment_id not in self.graph:
            return events

        for neighbor in self.graph.neighbors(equipment_id):
            edge_data = self.graph.edges[equipment_id, neighbor]
            neighbor_data = dict(self.graph.nodes[neighbor])
            if neighbor_data.get("type") in ["failure_event", "maintenance_event", "inspection_event"]:
                events.append({
                    "id": neighbor,
                    "relation": edge_data.get("relation"),
                    **neighbor_data,
                })

        return sorted(events, key=lambda x: x.get("date", ""), reverse=True)

    def to_vis_format(self) -> Dict[str, List]:
        """Export graph for React Flow / visualization"""
        type_colors = {
            "equipment": "#3b82f6",
            "operator": "#10b981",
            "location": "#f59e0b",
            "failure_event": "#ef4444",
            "maintenance_event": "#8b5cf6",
            "inspection_event": "#06b6d4",
            "document": "#6b7280",
            "regulation": "#f97316",
            "default": "#64748b",
        }

        nodes = []
        for node_id, attrs in self.graph.nodes(data=True):
            node_type = attrs.get("type", "default")
            nodes.append({
                "id": node_id,
                "label": attrs.get("label", node_id),
                "type": node_type,
                "color": type_colors.get(node_type, type_colors["default"]),
                "data": dict(attrs),
            })

        edges = []
        for source, target, attrs in self.graph.edges(data=True):
            edges.append({
                "id": f"{source}_{target}",
                "source": source,
                "target": target,
                "label": attrs.get("relation", "RELATED_TO"),
                "data": dict(attrs),
            })

        return {"nodes": nodes, "edges": edges, "stats": {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
        }}

    def get_stats(self) -> Dict:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "equipment_count": sum(1 for _, d in self.graph.nodes(data=True) if d.get("type") == "equipment"),
            "failure_events": sum(1 for _, d in self.graph.nodes(data=True) if d.get("type") == "failure_event"),
        }


# Global singleton
knowledge_graph = KnowledgeGraph()
