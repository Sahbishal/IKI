"""
Entity Extraction Agent
Uses Gemini to extract structured entities from industrial text:
- Equipment IDs, Operators, Locations, Dates, Temperatures, Failure Modes
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.llm import invoke_llm

logger = logging.getLogger(__name__)

ENTITY_SYSTEM_PROMPT = """You are an industrial document intelligence AI. 
Extract all structured entities from the given industrial text.

Return a JSON object with these fields:
{
  "equipment": [{"id": "P-101", "name": "Pump P-101", "type": "pump"}],
  "operators": [{"name": "Ravi Kumar", "role": "maintenance engineer"}],
  "locations": [{"name": "Section A", "zone": "Production"}],
  "dates": [{"date": "2024-03-20", "context": "failure date"}],
  "parameters": [{"name": "temperature", "value": "170", "unit": "°C"}],
  "failure_modes": [{"mode": "seal leakage", "equipment": "P-101"}],
  "maintenance_actions": [{"action": "bearing replacement", "equipment": "P-101", "type": "corrective"}],
  "compliance_items": [{"requirement": "safety helmet", "status": "compliant"}],
  "summary": "One sentence summary of this document section"
}

Return ONLY valid JSON, no markdown, no explanations."""


def extract_entities(text: str, document_id: int = 0) -> Dict[str, Any]:
    """Extract entities from text using Gemini"""
    if not text or len(text.strip()) < 20:
        return _empty_entities()

    # Truncate to fit context window
    text_sample = text[:3000]

    prompt = f"""Extract all industrial entities from this text:

---
{text_sample}
---

Return structured JSON with all entities found."""

    try:
        response = invoke_llm(prompt, system_prompt=ENTITY_SYSTEM_PROMPT, temperature=0.0)

        # Parse JSON from response
        entities = _parse_json_response(response)
        entities["document_id"] = document_id
        entities["extracted_at"] = datetime.utcnow().isoformat()

        logger.info(f"Extracted entities: {len(entities.get('equipment', []))} equipment, "
                    f"{len(entities.get('operators', []))} operators, "
                    f"{len(entities.get('failure_modes', []))} failures")
        return entities

    except Exception as e:
        logger.error(f"Entity extraction error: {e}")
        return _empty_entities()


def extract_maintenance_record(text: str) -> Optional[Dict[str, Any]]:
    """Extract a structured maintenance record from text"""
    prompt = f"""Extract maintenance record details from this text:

{text[:2000]}

Return JSON:
{{
  "equipment_id": "P-101",
  "equipment_name": "Pump P-101",
  "maintenance_type": "corrective|preventive|emergency",
  "description": "what was done",
  "operator": "name",
  "location": "section/zone",
  "maintenance_date": "YYYY-MM-DD",
  "failure_mode": "what failed",
  "risk_score": "Low|Medium|High|Critical"
}}

Return ONLY JSON."""

    try:
        response = invoke_llm(prompt, temperature=0.0)
        return _parse_json_response(response)
    except Exception as e:
        logger.error(f"Maintenance record extraction error: {e}")
        return None


def _parse_json_response(response: str) -> Dict[str, Any]:
    """Robustly parse JSON from LLM response"""
    # Remove markdown code blocks if present
    response = re.sub(r"```(?:json)?", "", response).strip()
    response = response.rstrip("`").strip()

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to find JSON object in response
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            return json.loads(match.group())
        return _empty_entities()


def _empty_entities() -> Dict[str, Any]:
    return {
        "equipment": [],
        "operators": [],
        "locations": [],
        "dates": [],
        "parameters": [],
        "failure_modes": [],
        "maintenance_actions": [],
        "compliance_items": [],
        "summary": "",
    }
