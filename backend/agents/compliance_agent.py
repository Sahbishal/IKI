"""
Compliance Agent
Compares SOP/regulations against inspection reports,
identifies gaps and violations
"""
import logging
from typing import Dict, Any, List

from core.vectorstore import search_similar
from core.llm import ainvoke_llm

logger = logging.getLogger(__name__)

COMPLIANCE_SYSTEM_PROMPT = """You are an Industrial Safety & Compliance AI.
Compare requirements from regulations/SOPs against actual inspection findings.

For each requirement found:
- State the requirement
- State whether it was found to be compliant or violated
- Provide evidence from the inspection report
- Assign severity: Critical / Major / Minor / OK

Return a structured compliance report."""


async def check_compliance(
    regulation_query: str = "safety requirements",
    equipment_filter: str = "",
) -> Dict[str, Any]:
    """
    Compare regulation/SOP requirements against inspection findings
    """
    # Search for regulation/SOP content
    sop_chunks = search_similar(
        f"safety requirements regulations SOP {regulation_query}",
        n_results=5,
        where=None,
    )

    # Search for inspection findings
    inspection_chunks = search_similar(
        f"inspection findings compliance status {regulation_query} {equipment_filter}",
        n_results=5,
    )

    if not sop_chunks and not inspection_chunks:
        return {
            "status": "no_data",
            "message": "No compliance documents found. Please upload SOP/regulation and inspection report documents.",
            "compliance_score": 0,
            "items": [],
        }

    sop_text = "\n".join([c["text"] for c in sop_chunks])
    inspection_text = "\n".join([c["text"] for c in inspection_chunks])

    prompt = f"""REGULATION/SOP REQUIREMENTS:
{sop_text[:2000] if sop_text else "No SOP documents found"}

INSPECTION FINDINGS:
{inspection_text[:2000] if inspection_text else "No inspection documents found"}

Equipment Filter: {equipment_filter if equipment_filter else "All equipment"}

Analyze compliance and return:
1. A table of requirements vs. findings (Compliant/Violated/Unknown)
2. List of violations with severity (Critical/Major/Minor)  
3. Overall compliance percentage
4. Recommendations to achieve full compliance

Format as a clear, structured report."""

    analysis = await ainvoke_llm(prompt, system_prompt=COMPLIANCE_SYSTEM_PROMPT, temperature=0.1)

    # Extract structured items (simplified)
    compliance_items = _extract_compliance_items(sop_chunks, inspection_chunks)
    compliance_score = _calculate_compliance_score(compliance_items)

    return {
        "status": "analyzed",
        "compliance_score": compliance_score,
        "total_requirements": len(compliance_items),
        "violations": sum(1 for i in compliance_items if i["status"] == "Violated"),
        "compliant": sum(1 for i in compliance_items if i["status"] == "Compliant"),
        "items": compliance_items,
        "ai_analysis": analysis,
        "sop_sources": [c["metadata"].get("document_name") for c in sop_chunks],
        "inspection_sources": [c["metadata"].get("document_name") for c in inspection_chunks],
    }


def _extract_compliance_items(sop_chunks: List, inspection_chunks: List) -> List[Dict]:
    """Build compliance items list from chunks"""
    items = []

    # Common industrial compliance keywords
    requirements = [
        "Personal Protective Equipment (PPE)",
        "Emergency exit clearance",
        "Fire extinguisher inspection",
        "Equipment grounding",
        "Pressure vessel certification",
        "Safety valve calibration",
        "Hazardous material labeling",
        "Lockout/Tagout procedure",
        "Operator certification",
        "Maintenance log completeness",
    ]

    inspection_text = " ".join([c["text"].lower() for c in inspection_chunks])

    for req in requirements:
        req_lower = req.lower()
        status = "Unknown"
        if any(word in inspection_text for word in req_lower.split()[:2]):
            if any(neg in inspection_text for neg in ["failed", "missing", "not found", "violation", "blocked", "absent"]):
                status = "Violated"
            elif any(pos in inspection_text for pos in ["passed", "ok", "compliant", "found", "present"]):
                status = "Compliant"
            else:
                status = "Partial"

        items.append({
            "requirement": req,
            "status": status,
            "severity": "Critical" if status == "Violated" and req in ["Emergency exit clearance", "Lockout/Tagout procedure"] else "Major" if status == "Violated" else "OK",
        })

    return items


def _calculate_compliance_score(items: List[Dict]) -> float:
    if not items:
        return 0.0
    compliant = sum(1 for i in items if i["status"] == "Compliant")
    return round((compliant / len(items)) * 100, 1)
