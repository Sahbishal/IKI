"""Documents router — list, get, delete documents"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select, desc

from core.database import AsyncSessionLocal, Document, Entity, MaintenanceRecord

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def list_documents(
    status: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
):
    """List all documents with optional filters"""
    async with AsyncSessionLocal() as db:
        query = select(Document).order_by(desc(Document.upload_date))
        if status:
            query = query.where(Document.status == status)
        if file_type:
            query = query.where(Document.file_type == file_type)
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        docs = result.scalars().all()

    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.original_name,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "status": d.status,
                "page_count": d.page_count,
                "chunk_count": d.chunk_count,
                "upload_date": d.upload_date.isoformat() if d.upload_date else None,
                "summary": d.summary,
            }
            for d in docs
        ],
        "total": len(docs),
    }


@router.get("/{document_id}")
async def get_document(document_id: int):
    """Get document details including extracted entities"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Get entities
        ent_result = await db.execute(
            select(Entity).where(Entity.document_id == document_id).limit(50)
        )
        entities = ent_result.scalars().all()

    return {
        "id": doc.id,
        "filename": doc.original_name,
        "file_type": doc.file_type,
        "status": doc.status,
        "page_count": doc.page_count,
        "chunk_count": doc.chunk_count,
        "upload_date": doc.upload_date.isoformat() if doc.upload_date else None,
        "processed_date": doc.processed_date.isoformat() if doc.processed_date else None,
        "summary": doc.summary,
        "entities": [
            {
                "type": e.entity_type,
                "value": e.entity_value,
                "context": e.context,
            }
            for e in entities
        ],
    }


@router.delete("/{document_id}")
async def delete_document(document_id: int):
    """Delete document and its chunks"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete file
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        file_path = os.path.join(upload_dir, doc.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove from vector store
        from core.vectorstore import delete_document_chunks
        delete_document_chunks(str(document_id))

        await db.delete(doc)
        await db.commit()

    return {"message": f"Document {document_id} deleted successfully"}


@router.get("/{document_id}/status")
async def get_processing_status(document_id: int):
    """Get real-time processing status"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": doc.id,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "page_count": doc.page_count,
        "error": doc.error_message,
    }
