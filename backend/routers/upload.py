"""Upload router — handles file upload and processing pipeline"""
import os
import uuid
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import aiofiles

from core.database import AsyncSessionLocal, Document
from agents.ingestion_agent import ingest_document
from agents.entity_agent import extract_entities, extract_maintenance_record
from agents.kg_agent import build_graph_from_entities

logger = logging.getLogger(__name__)
router = APIRouter()
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".csv"}


@router.post("/")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
):
    """Upload one or more files and start processing pipeline"""
    results = []
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            results.append({"filename": file.filename, "status": "error", "message": f"Unsupported type: {ext}"})
            continue

        # Save to disk
        safe_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(UPLOAD_DIR, safe_name)

        async with aiofiles.open(file_path, "wb") as out:
            content = await file.read()
            await out.write(content)

        # Create DB record
        async with AsyncSessionLocal() as db:
            doc = Document(
                filename=safe_name,
                original_name=file.filename,
                file_type=ext.lstrip("."),
                file_size=len(content),
                status="processing",
            )
            db.add(doc)
            await db.commit()
            await db.refresh(doc)
            doc_id = doc.id

        # Process in background
        background_tasks.add_task(process_document, file_path, doc_id, file.filename)

        results.append({
            "document_id": doc_id,
            "filename": file.filename,
            "size": len(content),
            "status": "processing",
            "message": "Document queued for processing",
        })

    return {"uploaded": len(results), "files": results}


async def process_document(file_path: str, document_id: int, original_name: str):
    """Background task: full processing pipeline"""
    try:
        # Step 1: Extract text and embed
        result = await ingest_document(file_path, document_id, original_name)
        if not result["success"]:
            await _update_doc_status(document_id, "failed", error=result.get("error"))
            return

        # Step 2: Extract entities
        entities = extract_entities(result["full_text"], document_id)

        # Step 3: Build knowledge graph
        build_graph_from_entities(entities, document_id, original_name)

        # Step 4: Extract maintenance record if present
        maint = extract_maintenance_record(result["full_text"])
        if maint and maint.get("equipment_id"):
            await _save_maintenance_record(maint, document_id)

        # Generate summary
        summary = entities.get("summary", "")

        # Update DB status
        await _update_doc_status(
            document_id, "ready",
            page_count=result["page_count"],
            chunk_count=result["chunk_count"],
            summary=summary,
        )
        logger.info(f"✅ Document {document_id} ({original_name}) fully processed")

    except Exception as e:
        logger.error(f"Processing failed for doc {document_id}: {e}")
        await _update_doc_status(document_id, "failed", error=str(e))


async def _update_doc_status(doc_id: int, status: str, **kwargs):
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = status
            doc.processed_date = datetime.utcnow()
            for k, v in kwargs.items():
                if hasattr(doc, k):
                    setattr(doc, k, v)
            await db.commit()


async def _save_maintenance_record(maint: dict, doc_id: int):
    from core.database import MaintenanceRecord
    from datetime import date
    async with AsyncSessionLocal() as db:
        record = MaintenanceRecord(
            document_id=doc_id,
            equipment_id=maint.get("equipment_id", ""),
            equipment_name=maint.get("equipment_name", ""),
            maintenance_type=maint.get("maintenance_type", "corrective"),
            description=maint.get("description", ""),
            operator=maint.get("operator", ""),
            location=maint.get("location", ""),
            failure_mode=maint.get("failure_mode", ""),
            risk_score=maint.get("risk_score", "Medium"),
            status="completed",
        )
        db.add(record)
        await db.commit()
