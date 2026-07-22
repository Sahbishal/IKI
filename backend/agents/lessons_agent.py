"""
Lessons Learned Agent
Summarizes recurring failure patterns across all documents
"""
import logging
from typing import Dict, Any, List
from collections import Counter

from core.vectorstore import search_similar
from core.database import AsyncSessionLocal, MaintenanceRecord
from core.llm import ainvoke_llm
from sqlalchemy import select

logger = logging.getLogger(__name__)

LESSONS_SYSTEM_PROMPT = """You are an Industrial Knowledge Management AI.
Analyze recurring failures and maintenance patterns across the facility.
Identify systemic issues, root causes, and lessons learned.
Provide actionable recommendations to prevent future failures.
Format as a clear lessons learned report."""


async def get_lessons_learned() -> Dict[str, Any]:
    """Summarize recurring failures and lessons across all documents"""
    # Get failure records from DB
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MaintenanceRecord))
        records = result.scalars().all()

    # Count failure modes
    failure_modes = [r.failure_mode for r in records if r.failure_mode]
    equipment_failures = {}
    for r in records:
        if r.maintenance_type in ("corrective", "emergency") and r.equipment_id:
            equipment_failures.setdefault(r.equipment_id, []).append(r.failure_mode or "Unknown")

    mode_counter = Counter(failure_modes)
    top_failures = mode_counter.most_common(10)

    # Search vector DB for failure patterns
    failure_chunks = search_similar("failure mode root cause recurring problem breakdown", n_results=8)
    failure_text = "\n".join([c["text"][:500] for c in failure_chunks])

    prompt = f"""Analyze these industrial failure patterns:

TOP RECURRING FAILURES:
{chr(10).join([f"- {mode}: {count} occurrences" for mode, count in top_failures])}

EQUIPMENT WITH MOST FAILURES:
{chr(10).join([f"- {eq}: {len(failures)} failures ({', '.join(set(failures[:3]))})" for eq, failures in list(equipment_failures.items())[:10]])}

DOCUMENT INSIGHTS:
{failure_text[:1500]}

Provide:
1. Top 5 lessons learned with actionable prevention measures
2. Systemic issues identified
3. Priority actions for management
4. Training recommendations for operators"""

    ai_summary = await ainvoke_llm(prompt, system_prompt=LESSONS_SYSTEM_PROMPT, temperature=0.3)

    return {
        "status": "analyzed",
        "top_failure_modes": [{"mode": m, "count": c} for m, c in top_failures],
        "equipment_failure_summary": [
            {"equipment_id": eq, "failure_count": len(fails), "common_modes": list(set(fails))[:3]}
            for eq, fails in sorted(equipment_failures.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        ],
        "total_failure_events": len([r for r in records if r.maintenance_type in ("corrective", "emergency")]),
        "ai_lessons_summary": ai_summary,
        "analyzed_documents": len(set(r.document_id for r in records)),
    }
