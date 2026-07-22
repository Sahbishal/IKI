"""Reports router — audit report generation and download"""
import os
import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from agents.audit_agent import generate_audit_report, get_all_reports
from agents.compliance_agent import check_compliance
from agents.lessons_agent import get_lessons_learned
from agents.maintenance_agent import get_fleet_health

logger = logging.getLogger(__name__)
router = APIRouter()
REPORTS_DIR = "./reports"


class ReportRequest(BaseModel):
    report_type: str = "monthly"  # monthly, quarterly, compliance, equipment


@router.get("/")
async def list_reports():
    """List all generated audit reports"""
    reports = await get_all_reports()
    return {"reports": reports, "total": len(reports)}


@router.post("/generate")
async def create_report(request: ReportRequest, background_tasks: BackgroundTasks):
    """Generate a new audit report"""
    result = await generate_audit_report(report_type=request.report_type)
    return {
        "message": "Audit report generated successfully",
        "report": result,
    }


@router.get("/download/{filename}")
async def download_report(filename: str):
    """Download a generated PDF report"""
    file_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
    )


@router.get("/compliance")
async def get_compliance_report(equipment: Optional[str] = None):
    """Run compliance analysis"""
    result = await check_compliance(equipment_filter=equipment or "")
    return result


@router.get("/lessons-learned")
async def get_lessons():
    """Get lessons learned analysis"""
    return await get_lessons_learned()


@router.get("/fleet-health")
async def get_fleet():
    """Get fleet health overview"""
    return await get_fleet_health()


@router.get("/maintenance/{equipment_id}")
async def get_maintenance_analysis(equipment_id: str):
    """Get maintenance intelligence for specific equipment"""
    from agents.maintenance_agent import analyze_equipment
    return await analyze_equipment(equipment_id)
