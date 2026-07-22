"""Graph router — knowledge graph data for visualization"""
import logging
from fastapi import APIRouter, Query
from typing import Optional

from core.knowledge_graph import knowledge_graph

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def get_graph():
    """Get full knowledge graph for visualization"""
    return knowledge_graph.to_vis_format()


@router.get("/stats")
async def get_graph_stats():
    return knowledge_graph.get_stats()


@router.get("/entity/{entity_id}")
async def get_entity(entity_id: str):
    """Get entity details and its connections"""
    result = knowledge_graph.get_entity_neighbors(entity_id)
    if not result["entity"]:
        return {"error": "Entity not found", "entity_id": entity_id}
    return result


@router.get("/search")
async def search_entities(q: str = Query(..., min_length=1)):
    """Search entities by name"""
    results = knowledge_graph.search_entity(q)
    return {"results": results[:20], "total": len(results)}


@router.get("/equipment/{equipment_id}/timeline")
async def get_equipment_timeline(equipment_id: str):
    """Get timeline of events for an equipment"""
    timeline = knowledge_graph.get_equipment_timeline(f"equipment_{equipment_id.lower()}")
    return {"equipment_id": equipment_id, "timeline": timeline}
