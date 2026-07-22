"""
Knowledge Graph Agent
Populates the NetworkX knowledge graph from extracted entities
"""
import logging
import re
from typing import Dict, Any, List
from datetime import datetime

from core.knowledge_graph import knowledge_graph

logger = logging.getLogger(__name__)


def build_graph_from_entities(entities: Dict[str, Any], document_id: int, document_name: str):
    """
    Populate knowledge graph from extracted entities.
    Creates nodes and edges for all extracted entities.
    """
    doc_node_id = f"doc_{document_id}"

    # Add document node
    knowledge_graph.add_entity(
        entity_id=doc_node_id,
        entity_type="document",
        label=document_name,
        properties={"document_id": str(document_id), "name": document_name},
    )

    # Process equipment
    for eq in entities.get("equipment", []):
        eq_id = _normalize_id(eq.get("id") or eq.get("name", "unknown"))
        eq_node = f"equipment_{eq_id}"
        knowledge_graph.add_entity(
            entity_id=eq_node,
            entity_type="equipment",
            label=eq.get("name", eq_id),
            properties={
                "equipment_id": eq.get("id", eq_id),
                "equipment_type": eq.get("type", "unknown"),
                "name": eq.get("name", eq_id),
            },
        )
        knowledge_graph.add_relationship(doc_node_id, eq_node, "MENTIONS_EQUIPMENT")

    # Process operators
    for op in entities.get("operators", []):
        op_id = _normalize_id(op.get("name", "unknown"))
        op_node = f"operator_{op_id}"
        knowledge_graph.add_entity(
            entity_id=op_node,
            entity_type="operator",
            label=op.get("name", op_id),
            properties={"name": op.get("name", op_id), "role": op.get("role", "")},
        )
        knowledge_graph.add_relationship(doc_node_id, op_node, "INVOLVES_OPERATOR")

    # Process locations
    for loc in entities.get("locations", []):
        loc_id = _normalize_id(loc.get("name", "unknown"))
        loc_node = f"location_{loc_id}"
        knowledge_graph.add_entity(
            entity_id=loc_node,
            entity_type="location",
            label=loc.get("name", loc_id),
            properties={"name": loc.get("name", loc_id), "zone": loc.get("zone", "")},
        )

    # Process failure modes — connect to equipment
    for failure in entities.get("failure_modes", []):
        eq_ref = failure.get("equipment", "")
        failure_id = _normalize_id(f"{failure.get('mode', 'unknown')}_{eq_ref}")
        failure_node = f"failure_{failure_id}"
        failure_date = _find_date_from_entities(entities)

        knowledge_graph.add_entity(
            entity_id=failure_node,
            entity_type="failure_event",
            label=failure.get("mode", "Unknown Failure"),
            properties={
                "failure_mode": failure.get("mode", ""),
                "equipment": eq_ref,
                "date": failure_date,
                "document": document_name,
            },
        )

        # Connect failure to equipment
        eq_ref_id = _normalize_id(eq_ref)
        eq_node = f"equipment_{eq_ref_id}"
        if eq_node in knowledge_graph.graph.nodes:
            knowledge_graph.add_relationship(eq_node, failure_node, "HAD_FAILURE")
        knowledge_graph.add_relationship(doc_node_id, failure_node, "DOCUMENTS_FAILURE")

    # Process maintenance actions
    for maint in entities.get("maintenance_actions", []):
        eq_ref = maint.get("equipment", "")
        maint_id = _normalize_id(f"maint_{maint.get('action', 'unknown')}_{eq_ref}")
        maint_node = f"maintenance_{maint_id}"

        knowledge_graph.add_entity(
            entity_id=maint_node,
            entity_type="maintenance_event",
            label=maint.get("action", "Maintenance"),
            properties={
                "action": maint.get("action", ""),
                "equipment": eq_ref,
                "maintenance_type": maint.get("type", ""),
                "document": document_name,
            },
        )

        eq_ref_id = _normalize_id(eq_ref)
        eq_node = f"equipment_{eq_ref_id}"
        if eq_node in knowledge_graph.graph.nodes:
            knowledge_graph.add_relationship(eq_node, maint_node, "UNDERWENT_MAINTENANCE")

    # Link operators to equipment via maintenance
    for op in entities.get("operators", []):
        op_node = f"operator_{_normalize_id(op.get('name', 'unknown'))}"
        for eq in entities.get("equipment", []):
            eq_node = f"equipment_{_normalize_id(eq.get('id') or eq.get('name', 'unknown'))}"
            if op_node in knowledge_graph.graph.nodes and eq_node in knowledge_graph.graph.nodes:
                knowledge_graph.add_relationship(op_node, eq_node, "MAINTAINS")

    # Link equipment to locations
    for loc in entities.get("locations", []):
        loc_node = f"location_{_normalize_id(loc.get('name', 'unknown'))}"
        for eq in entities.get("equipment", []):
            eq_node = f"equipment_{_normalize_id(eq.get('id') or eq.get('name', 'unknown'))}"
            if loc_node in knowledge_graph.graph.nodes and eq_node in knowledge_graph.graph.nodes:
                knowledge_graph.add_relationship(eq_node, loc_node, "LOCATED_IN")

    # Save after updates
    knowledge_graph.save()
    logger.info(f"✅ KG updated: {knowledge_graph.graph.number_of_nodes()} nodes, {knowledge_graph.graph.number_of_edges()} edges")


def _normalize_id(text: str) -> str:
    """Create a valid node ID from text"""
    return re.sub(r"[^a-zA-Z0-9_]", "_", str(text).lower())[:50]


def _find_date_from_entities(entities: Dict[str, Any]) -> str:
    """Extract first date from entities dict"""
    dates = entities.get("dates", [])
    if dates:
        return dates[0].get("date", "")
    return ""
