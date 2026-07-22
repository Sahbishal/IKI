"""
Maintenance Intelligence Agent
Analyzes maintenance history, calculates MTBF, predicts failures
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, and_

from core.database import AsyncSessionLocal, MaintenanceRecord
from core.llm import ainvoke_llm

logger = logging.getLogger(__name__)

MAINTENANCE_SYSTEM_PROMPT = """You are a Predictive Maintenance AI for industrial equipment.
Analyze maintenance history and provide:
1. Root cause analysis of recurring failures
2. Failure pattern identification  
3. Predictive maintenance recommendations
4. Risk assessment (Low/Medium/High/Critical)
5. Estimated time to next failure (if pattern detected)

Be specific, cite dates and failure modes. Use engineering terminology appropriately."""


async def analyze_equipment(equipment_id: str) -> Dict[str, Any]:
    """
    Full maintenance intelligence analysis for one equipment
    """
    # Fetch maintenance records
    records = await _get_maintenance_records(equipment_id)

    if not records:
        return {
            "equipment_id": equipment_id,
            "status": "no_data",
            "message": "No maintenance records found for this equipment",
            "risk_score": "Unknown",
        }

    # Calculate MTBF
    mtbf_analysis = _calculate_mtbf(records)

    # Failure pattern analysis
    failure_patterns = _analyze_failure_patterns(records)

    # Build context for LLM
    records_text = _format_records_for_llm(records)

    prompt = f"""Analyze maintenance history for equipment {equipment_id}:

MAINTENANCE RECORDS:
{records_text}

MTBF Analysis:
- Total maintenance events: {mtbf_analysis['total_events']}
- Failure events: {mtbf_analysis['failure_count']}
- Average days between failures: {mtbf_analysis['avg_days_between_failures']}
- Last failure: {mtbf_analysis['last_failure_date']}
- Recurring failure modes: {', '.join(failure_patterns.get('top_failures', []))}

Provide:
1. Summary of equipment health
2. Root cause of recurring issues
3. Risk assessment with justification
4. Specific maintenance recommendations
5. Predicted next failure window (if applicable)"""

    llm_analysis = await ainvoke_llm(prompt, system_prompt=MAINTENANCE_SYSTEM_PROMPT, temperature=0.2)

    # Determine overall risk
    risk_score = _calculate_risk_score(mtbf_analysis, failure_patterns)

    return {
        "equipment_id": equipment_id,
        "status": "analyzed",
        "risk_score": risk_score,
        "mtbf_days": mtbf_analysis["avg_days_between_failures"],
        "total_maintenance_events": mtbf_analysis["total_events"],
        "failure_count": mtbf_analysis["failure_count"],
        "last_failure_date": mtbf_analysis["last_failure_date"],
        "top_failure_modes": failure_patterns.get("top_failures", []),
        "predicted_next_failure": _predict_next_failure(mtbf_analysis),
        "ai_analysis": llm_analysis,
        "records": records,
        "analyzed_at": datetime.utcnow().isoformat(),
    }


async def get_fleet_health() -> Dict[str, Any]:
    """Get health status of all equipment"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(MaintenanceRecord))
        all_records = result.scalars().all()

    # Group by equipment
    equipment_map: Dict[str, List] = {}
    for r in all_records:
        eid = r.equipment_id or "UNKNOWN"
        equipment_map.setdefault(eid, []).append(r)

    fleet_stats = []
    for eq_id, records in equipment_map.items():
        failures = [r for r in records if r.maintenance_type in ("corrective", "emergency")]
        last_date = max((r.maintenance_date for r in records if r.maintenance_date), default=None)
        fleet_stats.append({
            "equipment_id": eq_id,
            "equipment_name": records[0].equipment_name or eq_id,
            "total_events": len(records),
            "failure_count": len(failures),
            "risk_score": records[-1].risk_score if records else "Low",
            "last_maintenance": last_date.isoformat() if last_date else None,
            "location": records[0].location or "",
        })

    return {
        "equipment_list": fleet_stats,
        "total_equipment": len(fleet_stats),
        "high_risk_count": sum(1 for e in fleet_stats if e["risk_score"] in ("High", "Critical")),
        "pending_maintenance": sum(1 for e in fleet_stats if e["failure_count"] > 0),
    }


async def _get_maintenance_records(equipment_id: str) -> List[Dict]:
    """Fetch records from DB for equipment"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(MaintenanceRecord).where(
                MaintenanceRecord.equipment_id.ilike(f"%{equipment_id}%")
            ).order_by(MaintenanceRecord.maintenance_date)
        )
        records = result.scalars().all()

    return [
        {
            "id": r.id,
            "equipment_id": r.equipment_id,
            "equipment_name": r.equipment_name,
            "type": r.maintenance_type,
            "description": r.description,
            "operator": r.operator,
            "date": r.maintenance_date.isoformat() if r.maintenance_date else None,
            "failure_mode": r.failure_mode,
            "risk_score": r.risk_score,
        }
        for r in records
    ]


def _calculate_mtbf(records: List[Dict]) -> Dict[str, Any]:
    """Mean Time Between Failures"""
    failure_records = [
        r for r in records
        if r.get("type") in ("corrective", "emergency") and r.get("date")
    ]

    failure_dates = sorted([
        datetime.fromisoformat(r["date"]) for r in failure_records if r["date"]
    ])

    if len(failure_dates) < 2:
        avg_days = None
    else:
        gaps = [(failure_dates[i+1] - failure_dates[i]).days for i in range(len(failure_dates)-1)]
        avg_days = sum(gaps) / len(gaps) if gaps else None

    last_failure = failure_dates[-1].strftime("%Y-%m-%d") if failure_dates else None

    return {
        "total_events": len(records),
        "failure_count": len(failure_records),
        "avg_days_between_failures": round(avg_days, 1) if avg_days else "N/A",
        "last_failure_date": last_failure,
        "failure_dates": [d.strftime("%Y-%m-%d") for d in failure_dates],
    }


def _analyze_failure_patterns(records: List[Dict]) -> Dict[str, Any]:
    """Count recurring failure modes"""
    from collections import Counter
    modes = [r.get("failure_mode") for r in records if r.get("failure_mode")]
    counter = Counter(modes)
    top_failures = [mode for mode, _ in counter.most_common(5)]
    return {"top_failures": top_failures, "failure_counts": dict(counter)}


def _format_records_for_llm(records: List[Dict]) -> str:
    lines = []
    for r in records[-15:]:  # Last 15 records
        lines.append(
            f"- [{r.get('date', 'N/A')}] {r.get('type', '').upper()}: {r.get('description', '')} "
            f"(Failure: {r.get('failure_mode', 'N/A')}, Risk: {r.get('risk_score', 'N/A')})"
        )
    return "\n".join(lines)


def _calculate_risk_score(mtbf: Dict, patterns: Dict) -> str:
    failure_count = mtbf.get("failure_count", 0)
    avg_days = mtbf.get("avg_days_between_failures", 999)
    if isinstance(avg_days, str):
        avg_days = 999

    if failure_count >= 5 and avg_days < 30:
        return "Critical"
    elif failure_count >= 3 and avg_days < 60:
        return "High"
    elif failure_count >= 2 or avg_days < 90:
        return "Medium"
    return "Low"


def _predict_next_failure(mtbf: Dict) -> Optional[str]:
    """Estimate next failure date based on MTBF"""
    last_failure = mtbf.get("last_failure_date")
    avg_days = mtbf.get("avg_days_between_failures")

    if not last_failure or not avg_days or avg_days == "N/A":
        return None

    try:
        last_date = datetime.strptime(last_failure, "%Y-%m-%d")
        predicted = last_date + timedelta(days=float(avg_days))
        return predicted.strftime("%Y-%m-%d")
    except Exception:
        return None
