"""Chat router — conversational RAG with session history"""
import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime

from agents.rag_agent import rag_query
from agents.maintenance_agent import analyze_equipment
from agents.compliance_agent import check_compliance
from agents.lessons_agent import get_lessons_learned
from core.database import AsyncSessionLocal, ChatSession
from sqlalchemy import select

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory session store (sufficient for demo)
_sessions: dict = {}

SUGGESTED_QUESTIONS = [
    "Why is Pump P-101 repeatedly failing?",
    "Show all maintenance performed on Compressor C-22",
    "Is Boiler B-5 compliant with safety regulations?",
    "Which equipment has the highest failure rate?",
    "What are the most common failure modes in the plant?",
    "Generate a summary of recent maintenance activities",
    "What preventive maintenance is overdue?",
    "Explain the root cause of the last bearing failure",
]


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[dict] = []
    agent_steps: List[dict] = []
    intent: str = "rag"
    timestamp: str


@router.post("/")
async def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint — routes to appropriate agent"""
    session_id = request.session_id or str(uuid.uuid4())

    # Initialize session
    if session_id not in _sessions:
        _sessions[session_id] = []

    history = _sessions[session_id]
    message = request.message.strip()

    # Detect intent
    intent = _detect_intent(message)
    logger.info(f"Chat [{session_id}]: intent={intent}, msg={message[:60]}")

    try:
        if intent == "maintenance_analysis":
            equipment_id = _extract_equipment_id(message)
            result = await analyze_equipment(equipment_id)
            answer = result.get("ai_analysis", str(result))
            citations = []
            agent_steps = [
                {"step": "Equipment ID Detection", "status": "done", "detail": equipment_id},
                {"step": "Maintenance DB Query", "status": "done", "detail": f"{result.get('total_maintenance_events', 0)} records found"},
                {"step": "MTBF Analysis", "status": "done", "detail": f"Risk: {result.get('risk_score', 'Unknown')}"},
                {"step": "AI Analysis", "status": "done", "detail": "Gemini 2.0 Flash"},
            ]

        elif intent == "compliance":
            result = await check_compliance(regulation_query=message)
            answer = result.get("ai_analysis", "Compliance analysis complete")
            citations = []
            agent_steps = [
                {"step": "SOP Retrieval", "status": "done", "detail": f"{len(result.get('sop_sources', []))} SOP documents"},
                {"step": "Inspection Retrieval", "status": "done", "detail": f"{len(result.get('inspection_sources', []))} inspection docs"},
                {"step": "Gap Analysis", "status": "done", "detail": f"Score: {result.get('compliance_score', 0)}%"},
                {"step": "AI Report", "status": "done", "detail": "Gemini 2.0 Flash"},
            ]

        elif intent == "lessons_learned":
            result = await get_lessons_learned()
            answer = result.get("ai_lessons_summary", "Lessons learned analysis complete")
            citations = []
            agent_steps = [
                {"step": "Failure Pattern Analysis", "status": "done", "detail": f"{result.get('total_failure_events', 0)} failures analyzed"},
                {"step": "AI Summarization", "status": "done", "detail": "Gemini 2.0 Flash"},
            ]

        else:
            # Default: RAG
            result = await rag_query(message, session_history=history)
            answer = result["answer"]
            citations = result["citations"]
            agent_steps = result["agent_steps"]

    except Exception as e:
        logger.error(f"Chat error: {e}")
        answer = f"I encountered an error processing your request: {str(e)}. Please ensure your documents are uploaded and try again."
        citations = []
        agent_steps = []

    # Update session history
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": answer})

    # Keep last 20 messages
    if len(history) > 20:
        _sessions[session_id] = history[-20:]

    return ChatResponse(
        session_id=session_id,
        answer=answer,
        citations=citations,
        agent_steps=agent_steps,
        intent=intent,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/suggestions")
async def get_suggestions():
    """Return suggested questions for the UI"""
    return {"suggestions": SUGGESTED_QUESTIONS}


@router.delete("/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session"""
    _sessions.pop(session_id, None)
    return {"message": "Session cleared"}


def _detect_intent(message: str) -> str:
    msg_lower = message.lower()
    if any(k in msg_lower for k in ["failure", "mtbf", "predict", "breakdown", "vibration", "maintenance history"]):
        return "maintenance_analysis"
    if any(k in msg_lower for k in ["comply", "compliance", "regulation", "sop", "safety check", "factory act"]):
        return "compliance"
    if any(k in msg_lower for k in ["lessons", "recurring", "pattern", "common failure", "most frequent"]):
        return "lessons_learned"
    return "rag"


def _extract_equipment_id(message: str) -> str:
    import re
    # Match patterns like P-101, C-22, B-5, Pump-1
    match = re.search(r"[A-Za-z]+-?\d+", message)
    if match:
        return match.group().upper()
    # Fall back to noun extraction
    words = message.split()
    for w in words:
        if w[0].isupper() and len(w) > 2:
            return w
    return "UNKNOWN"
