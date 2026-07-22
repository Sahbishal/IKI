"""Dashboard router — aggregate KPI stats"""
import logging
from fastapi import APIRouter
from sqlalchemy import select, func
from datetime import datetime, timedelta

from core.database import AsyncSessionLocal, Document, MaintenanceRecord, AuditReport, Entity
from core.vectorstore import get_chunk_count
from core.knowledge_graph import knowledge_graph

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats():
    """Main dashboard KPIs"""
    async with AsyncSessionLocal() as db:
        total_docs = (await db.execute(select(func.count(Document.id)))).scalar() or 0
        ready_docs = (await db.execute(select(func.count(Document.id)).where(Document.status == "ready"))).scalar() or 0
        processing_docs = (await db.execute(select(func.count(Document.id)).where(Document.status == "processing"))).scalar() or 0

        records = (await db.execute(select(MaintenanceRecord))).scalars().all()
        total_reports = (await db.execute(select(func.count(AuditReport.id)))).scalar() or 0

    equipment_ids = set(r.equipment_id for r in records if r.equipment_id)
    failures = [r for r in records if r.maintenance_type in ("corrective", "emergency")]
    pending = [r for r in records if r.status != "completed"]
    critical = [r for r in records if r.risk_score in ("Critical", "High")]

    # Risk distribution
    risk_dist = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}
    for r in records:
        score = r.risk_score or "Low"
        risk_dist[score] = risk_dist.get(score, 0) + 1

    # Overall risk level
    if risk_dist["Critical"] > 0:
        overall_risk = "Critical"
    elif risk_dist["High"] > 0:
        overall_risk = "High"
    elif risk_dist["Medium"] > 0:
        overall_risk = "Medium"
    else:
        overall_risk = "Low"

    # Monthly maintenance trend (last 6 months)
    monthly = _get_monthly_trend(records)

    kg_stats = knowledge_graph.get_stats()

    return {
        "total_documents": total_docs,
        "ready_documents": ready_docs,
        "processing_documents": processing_docs,
        "total_equipment": len(equipment_ids),
        "total_maintenance_events": len(records),
        "failure_events": len(failures),
        "pending_maintenance": len(pending),
        "critical_equipment": len(critical),
        "compliance_score": 92.0,
        "overall_risk": overall_risk,
        "risk_distribution": risk_dist,
        "total_audit_reports": total_reports,
        "vector_chunks": get_chunk_count(),
        "knowledge_graph": kg_stats,
        "monthly_maintenance_trend": monthly,
        "recent_activity": await _get_recent_activity(),
    }


def _get_monthly_trend(records):
    """Maintenance events per month for last 6 months"""
    now = datetime.utcnow()
    months = []
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30 * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=31)).replace(day=1)
        count = sum(
            1 for r in records
            if r.maintenance_date and month_start <= r.maintenance_date < month_end
        )
        months.append({
            "month": month_start.strftime("%b %Y"),
            "count": count,
        })
    return months


async def _get_recent_activity():
    async with AsyncSessionLocal() as db:
        docs = (await db.execute(
            select(Document).order_by(Document.upload_date.desc()).limit(5)
        )).scalars().all()
        records = (await db.execute(
            select(MaintenanceRecord).order_by(MaintenanceRecord.created_at.desc()).limit(5)
        )).scalars().all()

    activity = []
    for d in docs:
        activity.append({
            "type": "document",
            "description": f"Document uploaded: {d.original_name}",
            "status": d.status,
            "timestamp": d.upload_date.isoformat() if d.upload_date else None,
        })
    for r in records:
        activity.append({
            "type": "maintenance",
            "description": f"{r.maintenance_type or 'Maintenance'} on {r.equipment_name or r.equipment_id}",
            "status": r.risk_score or "Low",
            "timestamp": r.created_at.isoformat() if r.created_at else None,
        })

    activity.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
    return activity[:8]
